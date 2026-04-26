"""
Agent 3: Handoff, Confirmation & Surveillance Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PURPOSE:
  - Receives patient data (Agent 1) + triage result (Agent 2)
  - Assigns patient to the least-busy doctor/department
  - Generates the complete patient card for the doctor dashboard
  - Builds the ANM confirmation screen message (for Red alerts)
  - Prepares anonymized surveillance data for outbreak cluster detection
  - Returns complete handoff payload ready for Firebase push

ROUTING LOGIC:
  - Red  → Emergency department (any available)
  - Others → Department matched by symptom keywords, then least-queue doctor

ANM CONFIRMATION (human-in-the-loop):
  - Only for Red alerts
  - Shows ANM: "Healio flagged RED because [reasons] — Confirm or Downgrade?"
  - Prevents alert fatigue by catching obvious false positives

CALLED BY:
  - run_adk.py → HealioAgentOrchestrator.run_pipeline()
  - api/main.py → all /analyze endpoints
  - phase4_integration.py → HealioPhase4Pipeline

OUTPUT FORMAT:
  {
    "status": "SUCCESS",
    "patient_card": { chief_complaint, triage_color, risk_score, assigned_doctor, ... },
    "surveillance_data": { symptom_signature, severity_category, ... },
    "requires_anm_confirmation": false,
    "queue_priority": 1|2|3
  }
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
from datetime import datetime
import asyncio
import logging
from typing import Dict, Optional

# ─── Logger Setup ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s │ %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("healio.agent3")

# ─── Department Configuration ─────────────────────────────────────────────────
# All 12 PHC departments + Emergency. Doctors and queue sizes are seeded;
# in production these would be fetched live from Firebase.
DEPARTMENTS = {
    "General Medicine":      {"doctors": ["Dr. Sharma", "Dr. Patel"],    "queue": [3, 7]},
    "Cardiology":            {"doctors": ["Dr. Mehta", "Dr. Iyer"],      "queue": [2, 5]},
    "Paediatrics":           {"doctors": ["Dr. Reddy", "Dr. Rao"],       "queue": [4, 6]},
    "Respiratory Medicine":  {"doctors": ["Dr. Nambiar"],                "queue": [3]},
    "OB&G":                  {"doctors": ["Dr. Priya", "Dr. Lakshmi"],   "queue": [2, 4]},
    "Ophthalmology":         {"doctors": ["Dr. Srinivas"],               "queue": [1]},
    "Dermatology":           {"doctors": ["Dr. Rao"],                    "queue": [2]},
    "General Surgery":       {"doctors": ["Dr. Bhat", "Dr. Kumar"],      "queue": [3, 5]},
    "Psychiatry":            {"doctors": ["Dr. Murthy"],                 "queue": [2]},
    "ENT":                   {"doctors": ["Dr. Hegde"],                  "queue": [3]},
    "Orthopaedics":          {"doctors": ["Dr. Joshi", "Dr. Singh"],     "queue": [4, 2]},
    "Dentistry":             {"doctors": ["Dr. Pillai"],                 "queue": [1]},
    "Emergency":             {"doctors": ["Dr. Nair", "Dr. Krishnan"],   "queue": [1, 3]},
}

# Fallback alias map — handles cases where Agent 2 returns a slightly
# different spelling (e.g. "General" instead of "General Medicine")
DEPARTMENT_ALIASES = {
    "General":    "General Medicine",
    "Pediatrics": "Paediatrics",
    "Paed":       "Paediatrics",
    "Resp":       "Respiratory Medicine",
    "OBG":        "OB&G",
    "Ortho":      "Orthopaedics",
    "Surgery":    "General Surgery",
    "Psych":      "Psychiatry",
}


# ─── Async Wrapper ────────────────────────────────────────────────────────────
async def run_agent3_async(patient_data: dict, triage_result: dict) -> dict:
    """Async wrapper — runs Agent 3 in thread executor so it doesn't block the event loop"""
    logger.info("🔄 [AGENT 3] Async call received — dispatching to thread executor")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, run_agent3, patient_data, triage_result)


# ─── Helpers ──────────────────────────────────────────────────────────────────
def resolve_department(raw_dept: str) -> str:
    """
    Resolve the department name from Agent 2 to one that exists in DEPARTMENTS.
    Handles aliases and falls back to General Medicine.
    """
    if raw_dept in DEPARTMENTS:
        return raw_dept
    aliased = DEPARTMENT_ALIASES.get(raw_dept)
    if aliased and aliased in DEPARTMENTS:
        return aliased
    logger.warning(f"   ⚠️  [AGENT 3] Unknown department '{raw_dept}' — falling back to General Medicine")
    return "General Medicine"


def get_least_busy_doctor(department: str) -> dict:
    """Assign to the doctor with the lowest current queue"""
    dept_data = DEPARTMENTS.get(department, DEPARTMENTS["General Medicine"])
    doctors = dept_data["doctors"]
    queues  = dept_data["queue"]
    min_index = queues.index(min(queues))

    assignment = {
        "doctor":              doctors[min_index],
        "department":          department,
        "current_queue":       queues[min_index],
        "estimated_wait_mins": queues[min_index] * 3
    }
    logger.info(f"   👨‍⚕️  [AGENT 3] Assigned → {assignment['doctor']} "
                f"(dept={department}, queue={queues[min_index]}, wait≈{assignment['estimated_wait_mins']}min)")
    return assignment


# ─── Main Agent Function ──────────────────────────────────────────────────────
def run_agent3(patient_data: dict, triage_result: dict) -> dict:
    """
    Agent 3: Handoff, Confirmation & Surveillance Agent

    Generates the complete patient card + surveillance payload.
    This is the final agent in the Healio pipeline — output goes to Firebase.
    """
    logger.info("━" * 60)
    logger.info("🔵 [AGENT 3] ▶ Starting Handoff & Surveillance Generation")
    logger.info(f"   Input from Agent 1 (patient_data):")
    logger.info(f"   ├─ chief_complaint : \"{patient_data.get('chief_complaint', 'N/A')}\"")
    logger.info(f"   └─ symptoms        : {patient_data.get('symptoms', [])}")
    logger.info(f"   Input from Agent 2 (triage_result):")
    triage_color = triage_result.get("triage_color", "Green")
    risk_score   = triage_result.get("risk_score", 0.5)
    color_icon   = {"Red": "🔴", "Yellow": "🟡", "Green": "🟢"}.get(triage_color, "⚪")
    logger.info(f"   ├─ triage_color    : {color_icon} {triage_color}")
    logger.info(f"   ├─ risk_score      : {risk_score:.2f}")
    logger.info(f"   └─ red_flags       : {triage_result.get('red_flags', [])}")

    # ── Input validation ────────────────────────────────────────────────
    if not patient_data or not triage_result:
        logger.error("❌ [AGENT 3] Missing patient_data or triage_result — cannot generate handoff")
        return {
            "status": "ERROR",
            "error": "Missing patient data or triage result",
            "patient_card": {},
            "surveillance_data": {},
            "requires_anm_confirmation": False,
            "queue_priority": 3
        }

    timestamp = datetime.now().isoformat()
    symptoms  = patient_data.get("symptoms", [])

    # ── Department & doctor assignment ───────────────────────────────────
    logger.info("   🏥 [AGENT 3] Determining department and doctor assignment...")

    if triage_color == "Red":
        # Red always goes to Emergency regardless of Agent 2's recommendation
        department = "Emergency"
        logger.info("   🔴 [AGENT 3] Red triage → forced routing to Emergency department")
    else:
        # Use Agent 2's Gemini-based recommended_department
        raw_dept = triage_result.get("recommended_department", "")
        if raw_dept:
            department = resolve_department(raw_dept)
            logger.info(f"   🏥 [AGENT 3] Using Agent 2 Gemini recommendation: '{raw_dept}' → resolved to '{department}'")
        else:
            # Fallback: Agent 2 didn't return a department (old code path)
            department = "General Medicine"
            logger.info("   🏥 [AGENT 3] No recommended_department from Agent 2 — defaulting to General Medicine")

    assignment = get_least_busy_doctor(department)

    # ── ANM confirmation required for Red ────────────────────────────────
    requires_anm_confirmation = (triage_color == "Red")
    if requires_anm_confirmation:
        logger.warning("   🚨 [AGENT 3] RED ALERT — ANM confirmation screen will be shown before notifying doctor")

    # ── Build patient card ───────────────────────────────────────────────
    logger.info("   📋 [AGENT 3] Building patient card for doctor dashboard...")
    patient_card = {
        "timestamp":               timestamp,
        "chief_complaint":         patient_data.get("chief_complaint", "Unknown"),
        "symptoms":                symptoms,
        "duration":                patient_data.get("duration", "Unknown"),
        "severity":                patient_data.get("severity", "unknown"),
        "triage_color":            triage_color,
        "risk_score":              risk_score,
        "confidence_score_notes":  (
            "Risk score computed by Agent 2 using two-layer safety: "
            "confidence scoring (0.0–1.0) + multi-signal gating (Red requires 2+ signals)"
        ),
        "red_flags":               triage_result.get("red_flags", []),
        "clinical_signals":        triage_result.get("clinical_signals", []),
        "reasoning":               triage_result.get("reasoning", "No additional reasoning"),
        "assigned_department":     assignment["department"],
        "assigned_doctor":         assignment["doctor"],
        "queue_position":          assignment["current_queue"] + 1,
        "estimated_wait_mins":     assignment["estimated_wait_mins"],
    }

    # ── ANM confirmation message (human-in-the-loop) ─────────────────────
    if requires_anm_confirmation:
        flags_str = ", ".join(triage_result.get("red_flags", ["Severe symptoms"])) or "multiple critical signals"
        patient_card["anm_confirmation_message"] = (
            f"🚨 HIGH PRIORITY ALERT 🚨\n\n"
            f"Healio flagged this patient as RED (confidence score: {risk_score:.2f}) due to:\n"
            f"  → {flags_str}\n\n"
            f"[✓ CONFIRM — Notify Doctor Now]  or  [↓ DOWNGRADE TO YELLOW]"
        )
        logger.info(f"   📲 [AGENT 3] ANM confirmation message generated — reason: {flags_str}")

    # ── Build surveillance data ──────────────────────────────────────────
    logger.info("   📊 [AGENT 3] Building anonymized surveillance payload for outbreak detection...")
    symptom_signature = "_".join(sorted(symptoms)) if symptoms else "no_symptoms"
    surveillance_data = {
        "timestamp":            timestamp,
        "symptoms_anonymized":  symptoms,
        "severity_category":    patient_data.get("severity", "unknown"),
        "triage_color":         triage_color,
        "risk_score":           risk_score,
        "department":           department,
        "symptom_signature":    symptom_signature,
        "location":             "PHC-Bengaluru",
    }
    logger.info(f"   🔬 [AGENT 3] Symptom signature for cluster detection: \"{symptom_signature}\"")

    # ── Queue priority ────────────────────────────────────────────────────
    queue_priority = {"Red": 1, "Yellow": 2, "Green": 3}.get(triage_color, 3)

    # ── Assemble final handoff payload ────────────────────────────────────
    handoff_payload = {
        "status":                  "SUCCESS",
        "patient_card":            patient_card,
        "surveillance_data":       surveillance_data,
        "requires_anm_confirmation": requires_anm_confirmation,
        "queue_priority":          queue_priority,
        "doctor_dashboard_route":  "HIGH_PRIORITY_QUEUE" if requires_anm_confirmation else "NORMAL_QUEUE",
    }

    logger.info(f"✅ [AGENT 3] ▶ Handoff complete:")
    logger.info(f"   ├─ triage_color     : {color_icon} {triage_color}")
    logger.info(f"   ├─ assigned_doctor  : {assignment['doctor']}")
    logger.info(f"   ├─ department       : {department}")
    logger.info(f"   ├─ queue_priority   : {queue_priority} (1=Red, 2=Yellow, 3=Green)")
    logger.info(f"   ├─ ANM_confirm      : {requires_anm_confirmation}")
    logger.info(f"   └─ dashboard_route  : {handoff_payload['doctor_dashboard_route']}")
    logger.info("━" * 60)

    return handoff_payload


# ─── Firebase Format Helpers ──────────────────────────────────────────────────
def format_for_firebase(handoff_payload: dict) -> dict:
    """Extract and format the patient card portion for Firestore push"""
    return {
        "patient_card":            handoff_payload.get("patient_card", {}),
        "queue_priority":          handoff_payload.get("queue_priority", 3),
        "doctor_dashboard_route":  handoff_payload.get("doctor_dashboard_route", "NORMAL_QUEUE"),
        "timestamp":               handoff_payload.get("patient_card", {}).get("timestamp", datetime.now().isoformat()),
        "requires_anm_confirmation": handoff_payload.get("requires_anm_confirmation", False)
    }


def format_for_surveillance(handoff_payload: dict) -> dict:
    """Extract and format the surveillance portion for Firestore outbreak tracking"""
    return {
        "surveillance_data": handoff_payload.get("surveillance_data", {}),
        "collected_at":      handoff_payload.get("surveillance_data", {}).get("timestamp", datetime.now().isoformat()),
        "location":          "PHC-Bengaluru"
    }


# ─── CLI Test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  HEALIO — Agent 3 Direct Test")
    print("=" * 60)

    test_patient_data = {
        "chief_complaint": "High fever with rash",
        "symptoms": ["fever", "rash on arms and legs", "joint pain"],
        "duration": "3 days",
        "severity": "moderate"
    }
    test_triage_result = {
        "risk_score": 0.91,
        "triage_color": "Red",
        "clinical_signals": ["high fever", "dengue-pattern rash", "joint pain"],
        "red_flags": ["fever > 39°C", "dengue-pattern rash", "joint pain co-occurring"],
        "reasoning": "3+ co-occurring signals consistent with dengue — Red priority",
        "requires_confirmation": True
    }

    result = run_agent3(test_patient_data, test_triage_result)
    print("\n  ── Agent 3 Output ──")
    print(json.dumps(result, indent=2))
    print("=" * 60)
