"""
Healio Real Google ADK Agents
Each agent is a proper ADK agent with registered tools
Agents communicate through session state, not function returns
Real orchestration with dynamic routing
"""

import json
import logging
from datetime import datetime
from typing import Any

import vertexai
from vertexai.adk import Agent, Tool
from vertexai.generative_models import GenerativeModel

import firebase_admin
from firebase_admin import firestore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Vertex AI
vertexai.init(project="healio-494416", location="us-central1")

# Initialize Firebase
try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app()

db = firestore.client()


# ============================================================================
# TOOL FUNCTIONS - Clinical Logic Tools
# ============================================================================

def extract_intake_data(symptom_text: str, audio_transcript: str = "") -> dict:
    """
    Tool for Agent 1: Extract intake data from symptom text
    
    This is a TOOL that Agent 1 can call, not a direct function
    """
    from agents.agent1_intake import run_agent1
    
    combined_text = audio_transcript if audio_transcript else symptom_text
    if symptom_text and audio_transcript:
        combined_text = audio_transcript + " " + symptom_text
    
    result = run_agent1(symptom_text=combined_text)
    logger.info(f"[TOOL] Intake extraction: {result.get('chief_complaint')}")
    return result


def analyze_clinical_risk(patient_data: dict) -> dict:
    """
    Tool for Agent 2: Perform clinical reasoning and triage
    
    This is a TOOL that Agent 2 can call
    Returns risk score, triage color, clinical signals
    """
    from agents.agent2_reasoning import run_agent2
    
    result = run_agent2(patient_data)
    logger.info(f"[TOOL] Clinical analysis: {result.get('triage_color')} (Score: {result.get('risk_score')})")
    return result


def generate_handoff_and_surveillance(patient_data: dict, triage_result: dict) -> dict:
    """
    Tool for Agent 3: Generate patient card and surveillance data
    
    This is a TOOL that Agent 3 can call
    """
    from agents.agent3_handoff import run_agent3
    
    result = run_agent3(patient_data, triage_result)
    logger.info(f"[TOOL] Handoff generated for: {result['patient_card'].get('assigned_doctor')}")
    return result


def push_to_firestore(handoff_payload: dict, patient_id: str) -> dict:
    """
    Tool for Agent 3: Push patient data to Firestore
    
    This is a TOOL that Agent 3 can call
    """
    try:
        patient_card = handoff_payload.get("patient_card", {})
        
        # Push patient card
        db.collection("patients").document(patient_id).set({
            "timestamp": datetime.now().isoformat(),
            "chief_complaint": patient_card.get("chief_complaint"),
            "triage_color": patient_card.get("triage_color"),
            "risk_score": patient_card.get("risk_score"),
            "assigned_doctor": patient_card.get("assigned_doctor"),
            "assigned_department": patient_card.get("assigned_department"),
            "symptoms": patient_card.get("symptoms", []),
            "red_flags": patient_card.get("red_flags", []),
            "requires_anm_confirmation": handoff_payload.get("requires_anm_confirmation", False),
        })
        
        # Push to queue
        from firebase.queue_manager import get_queue_manager
        queue_manager = get_queue_manager()
        queue_id = queue_manager.add_patient_to_queue(patient_card)
        
        # Push surveillance data
        from firebase.surveillance import get_surveillance
        surveillance = get_surveillance()
        surveillance_id = surveillance.record_surveillance_data(handoff_payload.get("surveillance_data", {}))
        
        logger.info(f"[TOOL] Firestore push complete: {patient_id}")
        
        return {
            "success": True,
            "patient_id": patient_id,
            "queue_id": queue_id,
            "surveillance_id": surveillance_id,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Firestore push error: {str(e)}")
        return {"success": False, "error": str(e)}


def check_outbreak_cluster() -> dict:
    """
    Tool for Agent 3: Check for outbreak clusters
    
    This tool can be called by any agent to check if a cluster is forming
    """
    try:
        from firebase.surveillance import get_surveillance
        surveillance = get_surveillance()
        clusters = surveillance.get_active_clusters()
        
        logger.info(f"[TOOL] Cluster check: {len(clusters)} active clusters")
        
        return {
            "success": True,
            "active_clusters": clusters,
            "cluster_count": len(clusters),
            "outbreak_alerts": len([c for c in clusters if c.get("action_required")])
        }
    except Exception as e:
        logger.error(f"Cluster check error: {str(e)}")
        return {"success": False, "error": str(e), "active_clusters": []}


def get_doctor_assignment(department: str, triage_color: str) -> dict:
    """
    Tool for Agent 3: Get optimal doctor assignment
    
    Can be called dynamically based on triage results
    """
    from agents.agent3_handoff import get_least_busy_doctor
    
    if triage_color == "Red":
        department = "Emergency"
    
    assignment = get_least_busy_doctor(department)
    logger.info(f"[TOOL] Doctor assigned: {assignment['doctor']} ({assignment['department']})")
    return assignment


# ============================================================================
# AGENT 1: MULTIMODAL INTAKE AGENT
# ============================================================================

agent1 = Agent(
    display_name="Agent 1 - Multimodal Intake",
    description="Extracts structured clinical intake data from patient symptoms",
    instructions="""
You are Agent 1: Clinical Intake Specialist at a PHC in Bengaluru.

Your TOOLS:
1. extract_intake_data() - Processes patient symptoms and returns structured intake

Your ROLE:
- You receive patient symptom text
- You CALL extract_intake_data() to process it
- You store the result in session state for Agent 2
- Session state key: "patient_data"

Your OUTPUT:
- Must store patient data in session: patient_data = {chief_complaint, symptoms, duration, severity}
""",
    tools=[
        Tool.from_function(extract_intake_data),
    ]
)


# ============================================================================
# AGENT 2: CLINICAL REASONING AGENT
# ============================================================================

agent2 = Agent(
    display_name="Agent 2 - Clinical Reasoning",
    description="Performs clinical triage with two-layer safety scoring",
    instructions="""
You are Agent 2: Clinical Reasoning & Triage Agent.

Your TOOLS:
1. analyze_clinical_risk() - Analyzes patient data and returns risk score + triage color

Your ROLE:
- You receive patient_data from Agent 1 (from session state)
- You CALL analyze_clinical_risk(patient_data) to score and triage
- You store the result in session state: triage_result = {risk_score, triage_color, red_flags}

IMPORTANT ROUTING RULES:
- If triage_color == "Red" → Session state will trigger Emergency routing
- If triage_color == "Green" → Session state will trigger routine flow
- If triage_color == "Yellow" → Session state will trigger review flow

Your OUTPUT:
- Store triage_result in session for Agent 3
""",
    tools=[
        Tool.from_function(analyze_clinical_risk),
    ]
)


# ============================================================================
# AGENT 3: HANDOFF & SURVEILLANCE AGENT
# ============================================================================

agent3 = Agent(
    display_name="Agent 3 - Handoff & Surveillance",
    description="Generates patient card, assigns doctor, and records surveillance data",
    instructions="""
You are Agent 3: Handoff & Surveillance Specialist.

Your TOOLS:
1. generate_handoff_and_surveillance() - Generates patient card and surveillance payload
2. get_doctor_assignment() - Gets optimal doctor assignment based on triage
3. push_to_firestore() - Pushes patient data to Firestore
4. check_outbreak_cluster() - Checks for active outbreak clusters

Your ROLE:
- You receive patient_data and triage_result from previous agents (from session state)
- You CALL generate_handoff_and_surveillance() to create patient card
- You CALL get_doctor_assignment() to assign optimal doctor (routing by triage_color)
- You CALL push_to_firestore() to save to database
- You CALL check_outbreak_cluster() to detect outbreaks
- You store final result in session: handoff_complete = true

DYNAMIC ROUTING BASED ON TRIAGE:
- Red → Automatically routed to Emergency department
- Yellow → Routed to Doctor Review queue
- Green → Routed to General queue with lower priority

Your OUTPUT:
- Complete patient card in Firestore
- Surveillance data recorded
- Queue position assigned
- Doctor and department assigned
- Outbreak alerts if triggered
""",
    tools=[
        Tool.from_function(generate_handoff_and_surveillance),
        Tool.from_function(get_doctor_assignment),
        Tool.from_function(push_to_firestore),
        Tool.from_function(check_outbreak_cluster),
    ]
)


# ============================================================================
# AGENT EXPORTS
# ============================================================================

def get_agent1():
    """Get Agent 1 instance"""
    return agent1


def get_agent2():
    """Get Agent 2 instance"""
    return agent2


def get_agent3():
    """Get Agent 3 instance"""
    return agent3
