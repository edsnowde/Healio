"""
Agent 2: Clinical Reasoning Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PURPOSE:
  - Receives structured patient data from Agent 1
  - Applies Healio's TWO-LAYER SAFETY DESIGN using Gemini 2.5 Flash
  - Layer A: Confidence scoring (continuous 0.0–1.0, not binary thresholds)
  - Layer B: Multi-signal gating (Red requires 2+ independent signals, mirrors NEWS2)
  - Returns: risk_score, triage_color (Red/Yellow/Green), red_flags, reasoning

TRIAGE RULES:
  • risk_score > 0.90  AND  2+ signals  →  Red  (escalate immediately)
  • risk_score 0.65–0.90               →  Yellow (doctor review suggested)
  • risk_score < 0.65                  →  Green  (routine)

CALLED BY:
  - run_adk.py → HealioAgentOrchestrator.run_pipeline()
  - api/main.py → all /analyze endpoints

OUTPUT FORMAT:
  {
    "risk_score": 0.87,
    "triage_color": "Yellow",
    "clinical_signals": [...],
    "red_flags": [...],
    "reasoning": "...",
    "requires_confirmation": false
  }
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import vertexai
from vertexai.generative_models import GenerativeModel
import json
import re
import asyncio
import logging
from typing import Dict

# ─── Logger Setup ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s │ %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("healio.agent2")

# ─── Gemini Initialization ───────────────────────────────────────────────────
logger.info("⚙️  [AGENT 2] Initializing Vertex AI (project=healio-494416, location=us-central1)")
vertexai.init(project="healio-494416", location="us-central1")
model = GenerativeModel("gemini-2.5-flash")
logger.info("✅ [AGENT 2] Gemini 2.5 Flash loaded for clinical reasoning")


# ─── Department Symptom Mapping ───────────────────────────────────────────────
# Used by Gemini to allocate the correct PHC department based on symptoms.
# Red triage always overrides to Emergency regardless of this mapping.
DEPARTMENT_MAPPING = {
    "departments": [
        "General Medicine",
        "Cardiology",
        "Paediatrics",
        "Respiratory Medicine",
        "OB&G",
        "Ophthalmology",
        "Dermatology",
        "General Surgery",
        "Psychiatry",
        "ENT",
        "Orthopaedics",
        "Dentistry",
        "Emergency"
    ],
    "symptom_hints": {
        "General Medicine":     ["fatigue", "fever", "headache", "generalized pain", "cold",
                                  "injuries", "muscle pain", "body ache", "chills", "weakness",
                                  "loss of appetite", "sore throat"],
        "Cardiology":           ["chest pain", "chest pressure", "heart palpitations",
                                  "shortness of breath", "fainting", "irregular heartbeat",
                                  "sweating with chest discomfort", "pain in left arm", "jaw pain",
                                  "cardiac fatigue"],
        "Paediatrics":          ["fever in children", "cough in child", "vomiting in child",
                                  "diarrhea", "ear pain in child", "rash in child", "poor feeding",
                                  "irritability", "runny nose", "growth concerns", "developmental delays"],
        "Respiratory Medicine": ["cough", "wheezing", "shortness of breath", "chest tightness",
                                  "phlegm", "night sweats", "chronic cough", "difficulty breathing",
                                  "coughing up blood"],
        "OB&G":                 ["pelvic pain", "irregular menstruation", "vaginal discharge",
                                  "breast tenderness", "cramps", "heavy bleeding",
                                  "pregnancy concerns", "postpartum issues"],
        "Ophthalmology":        ["eye pain", "blurred vision", "redness in eyes", "dry eyes",
                                  "vision loss"],
        "Dermatology":          ["itching", "rashes", "redness", "swelling", "eczema",
                                  "acne", "blisters"],
        "General Surgery":      ["abdominal pain", "hernia", "appendicitis symptoms",
                                  "lumps", "abscess", "cysts"],
        "Psychiatry":           ["anxiety", "depression", "sleep disturbances",
                                  "hallucinations", "stress"],
        "ENT":                  ["ear pain", "sore throat", "nasal congestion",
                                  "hearing loss", "sinus pressure"],
        "Orthopaedics":         ["joint pain", "fractures", "back pain", "arthritis",
                                  "muscle weakness", "bone pain", "leg pain", "arm pain",
                                  "knee pain", "shoulder pain"],
        "Dentistry":            ["toothache", "gum swelling", "bleeding gums",
                                  "jaw pain", "mouth sores"],
        "Emergency":            ["uncontrolled bleeding", "unconscious", "severe chest pain",
                                  "stroke symptoms", "severe trauma", "poisoning",
                                  "cardiac arrest", "severe allergic reaction"]
    }
}


# ─── Async Wrapper ────────────────────────────────────────────────────────────
async def run_agent2_async(patient_data: dict) -> dict:
    """Async wrapper — runs Agent 2 in thread executor so it doesn't block the event loop"""
    logger.info("🔄 [AGENT 2] Async call received — dispatching to thread executor")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, run_agent2, patient_data)


# ─── Main Agent Function ──────────────────────────────────────────────────────
def run_agent2(patient_data: dict) -> dict:
    """
    Agent 2: Clinical Reasoning Agent

    Applies two-layer safety design (confidence scoring + multi-signal gating).
    Uses Gemini to reason over structured patient data and output risk assessment.
    """
    logger.info("━" * 60)
    logger.info("🟡 [AGENT 2] ▶ Starting Clinical Reasoning")
    logger.info(f"   Patient data received from Agent 1:")
    logger.info(f"   ├─ chief_complaint : \"{patient_data.get('chief_complaint', 'N/A')}\"")
    logger.info(f"   ├─ symptoms        : {patient_data.get('symptoms', [])}")
    logger.info(f"   ├─ duration        : \"{patient_data.get('duration', 'N/A')}\"")
    logger.info(f"   └─ severity        : \"{patient_data.get('severity', 'N/A')}\"")

    # ── Input validation ────────────────────────────────────────────────
    if not patient_data:
        logger.error("❌ [AGENT 2] No patient data provided — returning safe Yellow default")
        return {
            "error": "No patient data provided",
            "risk_score": 0.5,
            "triage_color": "Yellow",
            "red_flags": [],
            "reasoning": "Invalid input — defaulted to Yellow for safety"
        }

    # ── Build clinical reasoning prompt ─────────────────────────────────
    logger.info("   🤖 [AGENT 2] Building clinical reasoning prompt for Gemini...")

    # Serialize the department mapping so Gemini knows exactly what's available
    dept_hints_text = "\n".join(
        f"  - {dept}: {', '.join(hints[:6])}"
        for dept, hints in DEPARTMENT_MAPPING["symptom_hints"].items()
    )
    dept_list = ", ".join(DEPARTMENT_MAPPING["departments"])

    prompt = f"""
You are a clinical triage AI for a PHC (Primary Health Centre) in Bengaluru, India.

Patient Data (from Agent 1 intake):
{json.dumps(patient_data, indent=2)}

Apply Healio's TWO-LAYER CLINICAL TRIAGE PROTOCOL:

LAYER A — CONFIDENCE SCORING (0.0 to 1.0):
Assess overall clinical risk. Consider:
  - Symptom severity and duration
  - High-risk symptom patterns (fever + rash → possible dengue/measles, chest pain → cardiac, etc.)
  - Number of co-occurring warning signals

LAYER B — MULTI-SIGNAL GATING (mirrors NEWS2):
Red priority REQUIRES 2+ independent clinical signals. Examples:
  - Fever >39°C alone           → Yellow
  - Fever + rash                → Yellow-High
  - Fever + rash + breathlessness → Red (3 independent signals)

DEPARTMENT ALLOCATION:
Based on the patient's symptoms, assign the single most appropriate PHC department.
Available departments: {dept_list}

Department routing hints (match symptoms to most relevant):
{dept_hints_text}

IMPORTANT RULES for department allocation:
  • If triage_color is Red → ALWAYS set recommended_department to "Emergency"
  • If symptoms are clearly cardiac (chest pain, palpitations, left arm pain) → "Cardiology"
  • If patient mentions child/baby/infant → "Paediatrics"
  • Use clinical reasoning — don't just keyword match. A patient saying "my leg bone hurts" → "Orthopaedics"
  • If symptoms don't clearly match a specialty → "General Medicine"

RETURN ONLY valid JSON (no markdown, no extra text):
{{
    "risk_score": (float 0.0–1.0),
    "triage_color": "Red" or "Yellow" or "Green",
    "clinical_signals": (array of specific concerning signals identified),
    "red_flags": (array of specific high-risk warning signs),
    "reasoning": (single line: why this triage color was assigned),
    "requires_confirmation": (boolean — true only if triage_color is Red),
    "recommended_department": (one of: {dept_list}),
    "department_reasoning": (single line: why this department was chosen)
}}

TRIAGE RULES (strictly follow):
  • score > 0.90  AND  2+ signals → Red  → recommended_department MUST be "Emergency"
  • score 0.65–0.90               → Yellow
  • score < 0.65                  → Green
Return ONLY JSON. No markdown. No explanations outside the JSON.
"""

    try:
        # ── Call Gemini ──────────────────────────────────────────────────
        logger.info("   🤖 [AGENT 2] Sending clinical reasoning request to Gemini 2.5 Flash...")
        response = model.generate_content(prompt)
        text = response.text.strip()
        logger.info(f"   📨 [AGENT 2] Gemini responded ({len(text)} chars)")
        logger.debug(f"   Raw response: {text[:300]}")

        # ── Parse JSON ───────────────────────────────────────────────────
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            json_str = match.group()
            triage_result = json.loads(json_str)

            # Sanitize mandatory fields
            risk_score  = triage_result.get("risk_score", 0.5)
            triage_color = triage_result.get("triage_color", "Yellow")
            red_flags    = triage_result.get("red_flags", [])
            signals      = triage_result.get("clinical_signals", [])

            # Validate business rules (safety net)
            if risk_score > 0.90 and len(signals) < 2:
                logger.warning(f"   ⚠️  [AGENT 2] Risk score {risk_score:.2f} > 0.90 but only {len(signals)} signal(s) — "
                               "downgrading to Yellow per multi-signal gate rule")
                triage_result["triage_color"] = "Yellow"
                triage_result["reasoning"] += " [Downgraded: single-signal gating rule]"

            # Enforce Red → Emergency override
            recommended_dept = triage_result.get("recommended_department", "General Medicine")
            if triage_result.get("triage_color") == "Red":
                recommended_dept = "Emergency"
                triage_result["recommended_department"] = "Emergency"

            # Validate department is one of the allowed values
            if recommended_dept not in DEPARTMENT_MAPPING["departments"]:
                logger.warning(f"   ⚠️  [AGENT 2] Unknown department '{recommended_dept}' — falling back to General Medicine")
                recommended_dept = "General Medicine"
                triage_result["recommended_department"] = "General Medicine"

            triage_result["risk_score"]  = risk_score
            triage_result["triage_color"] = triage_color = triage_result.get("triage_color", "Yellow")

            # Store raw Gemini text so it can be saved to Firestore
            triage_result["_gemini_raw_response"] = text
            triage_result["_prompt_sent"]         = prompt.strip()

            # ── Log triage decision ──────────────────────────────────────
            color_icon = {"Red": "🔴", "Yellow": "🟡", "Green": "🟢"}.get(triage_color, "⚪")
            logger.info(f"   ✅ [AGENT 2] Triage decision: {color_icon} {triage_color}")
            logger.info(f"   ├─ risk_score             : {risk_score:.2f}")
            logger.info(f"   ├─ recommended_department : {recommended_dept}")
            logger.info(f"   ├─ department_reasoning   : \"{triage_result.get('department_reasoning', '')}\"")
            logger.info(f"   ├─ clinical_signals       : {signals}")
            logger.info(f"   ├─ red_flags              : {red_flags}")
            logger.info(f"   ├─ reasoning              : \"{triage_result.get('reasoning')}\"")
            logger.info(f"   └─ requires_ANM_confirm   : {triage_result.get('requires_confirmation', False)}")

            logger.info(f"✅ [AGENT 2] ▶ Clinical reasoning complete — {color_icon} {triage_color} (score={risk_score:.2f}) → dept={recommended_dept}")
            logger.info("━" * 60)
            return triage_result

        else:
            logger.warning("   ⚠️  [AGENT 2] Could not parse JSON from Gemini response — returning safe Yellow fallback")
            return {
                "error": "Could not parse triage response from AI",
                "risk_score": 0.5,
                "triage_color": "Yellow",
                "clinical_signals": [],
                "red_flags": [],
                "reasoning": "AI response could not be parsed — defaulted to Yellow for safety",
                "raw_response": text[:200]
            }

    except Exception as e:
        logger.error(f"❌ [AGENT 2] Exception during clinical reasoning: {str(e)}", exc_info=True)
        return {
            "error": str(e),
            "risk_score": 0.5,
            "triage_color": "Yellow",
            "clinical_signals": [],
            "red_flags": ["Error in AI processing — escalate manually"],
            "reasoning": f"Exception occurred: {str(e)}"
        }


# ─── CLI Test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  HEALIO — Agent 2 Direct Test")
    print("=" * 60)
    test_patient_data = {
        "chief_complaint": "High fever with rash spreading across the body",
        "symptoms": ["high fever", "red rash on arms and legs", "severe joint pain", "headache"],
        "duration": "3 days",
        "severity": "moderate",
        "additional_info": {"temperature_reported": "39.5°C"}
    }
    print(f"  Test input:\n{json.dumps(test_patient_data, indent=2)}\n")

    result = run_agent2(test_patient_data)
    print("\n  ── Agent 2 Output ──")
    print(json.dumps(result, indent=2))
    print("=" * 60)
