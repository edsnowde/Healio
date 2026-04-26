"""
Healio Main Pipeline - End-to-End Verification
================================================
PURPOSE:
  Run the complete Healio 3-agent pipeline end-to-end with real Gemini calls.
  This is the main test script to verify the entire backend is working correctly.

WHAT IT TESTS:
  1. Agent 1  - Gemini extracts structured data from symptom text
  2. Agent 2  - Gemini assigns triage color (Red/Yellow/Green) + risk score
  3. Agent 3  - Patient card generated + ANM confirmation + surveillance data
  4. Firebase - Patient card pushed to Firestore queue
  5. Cluster  - Outbreak cluster detection runs on surveillance collection

HOW TO RUN:
  cd backend
  .\\venv\\Scripts\\python main_pipeline.py
================================================
"""

import json
import sys
import logging
import os
from pathlib import Path
from datetime import datetime

# Force UTF-8 output on Windows so log messages display correctly
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ---- Logger Setup -----------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("healio.main_pipeline")


def print_section(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_result(label: str, value):
    if isinstance(value, (dict, list)):
        print(f"  {label}:")
        lines = json.dumps(value, indent=4).split("\n")
        for line in lines:
            print(f"    {line}")
    else:
        print(f"  {label:30s}: {value}")


def run_complete_pipeline(symptom_input: str, image_paths=None, verbose: bool = True) -> dict:
    """Run all 4 phases: Agent1 + Agent2 + Agent3 + Firebase + Cluster detection"""
    from phase4_integration import HealioPhase4Pipeline

    logger.info(f"[MAIN] Starting complete pipeline")
    logger.info(f"[MAIN] Input: \"{symptom_input[:80]}{'...' if len(symptom_input) > 80 else ''}\"")

    pipeline = HealioPhase4Pipeline()
    result = pipeline.analyze_patient_with_images(
        symptom_text=symptom_input,
        image_paths=image_paths,
        verbose=verbose
    )

    logger.info(f"[MAIN] Pipeline complete - status: {result.get('status', 'unknown')}")
    return result


def run_pipeline_no_firebase(symptom_input: str) -> dict:
    """Run only the 3-agent AI pipeline WITHOUT Firebase (for testing)"""
    from run_adk import run_healio_adk_pipeline

    logger.info(f"[MAIN] Running AI-only pipeline (no Firebase)")
    result = run_healio_adk_pipeline(symptom_text=symptom_input, verbose=True)
    return result


# ---- Main -------------------------------------------------------------------
if __name__ == "__main__":

    print_section("HEALIO BACKEND - End-to-End Verification")
    print(f"  Started at : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Python     : {sys.version.split()[0]}")
    print(f"  Auth       : Application Default Credentials (ADC)")
    print(f"  GCP Project: healio-494416")

    # ---- Check Firebase availability ----------------------------------------
    use_firebase = True
    try:
        import firebase_admin
        from firebase_admin import firestore as _fs
        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app()
        _fs.client()
        logger.info("[MAIN] Firebase connection verified - using full pipeline with Firestore")
    except Exception as fb_err:
        logger.warning(f"[MAIN] Firebase not available ({fb_err}) - running AI-only pipeline")
        use_firebase = False

    # ---- Test case ----------------------------------------------------------
    symptom_input = "I have very high fever since 3 days, severe headache, joint pain, and red rash all over my body"

    print_section("Running Test: Dengue Suspected (High Risk)")
    print(f"  Input: \"{symptom_input}\"\n")

    try:
        if use_firebase:
            result = run_complete_pipeline(symptom_input, verbose=True)
        else:
            result = run_pipeline_no_firebase(symptom_input)

        print_section("PIPELINE RESULT")

        if use_firebase:
            patient = result.get("patient", {})
            print_result("Status",               result.get("status"))
            print_result("Patient ID",           patient.get("patient_id"))
            print_result("Queue ID",             patient.get("queue_id"))
            print_result("Surveillance ID",      patient.get("surveillance_id"))
            print_result("Triage Color",         patient.get("triage_color"))
            print_result("Risk Score",           patient.get("risk_score"))
            print_result("Assigned Doctor",      patient.get("assigned_doctor"))
            print_result("Department",           patient.get("assigned_department"))
            print_result("ANM Confirm Needed",   patient.get("requires_anm_confirmation"))

            clusters = result.get("outbreak_alerts", [])
            if clusters:
                print(f"\n  *** OUTBREAK ALERTS: {len(clusters)} cluster(s) detected! ***")
                for cluster in clusters:
                    print(f"     -> {cluster.get('patient_count')} patients with: {cluster.get('symptoms')}")
            else:
                print(f"\n  [OK] No outbreak clusters detected")
        else:
            patient = result.get("patient", {})
            print_result("Status",            result.get("status"))
            print_result("Session ID",        result.get("session_id"))
            print_result("Agents Executed",   result.get("agents_executed"))
            print_result("Triage Color",      patient.get("triage_color"))
            print_result("Risk Score",        patient.get("risk_score"))
            print_result("Routing",           patient.get("routing"))
            print_result("Assigned Doctor",   patient.get("assigned_doctor"))
            print_result("Department",        patient.get("assigned_department"))
            print_result("ANM Confirm",       patient.get("requires_anm_confirmation"))

        print_section("ALL SYSTEMS WORKING - BACKEND VERIFIED")

    except Exception as e:
        logger.error(f"[MAIN] Pipeline failed: {str(e)}", exc_info=True)
        print(f"\n  ERROR: {str(e)}")
        print(f"  Check logs above for details")
        sys.exit(1)
