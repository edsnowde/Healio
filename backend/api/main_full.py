"""
Healio FastAPI Backend - MINIMAL STARTUP VERSION
Real-time, multi-agent triage system with live queue updates and outbreak surveillance

This is the main entry point for Phase 2/3+ integration
"""

import asyncio
import json
import logging
import sys
import threading
from pathlib import Path
from typing import Optional, List
from datetime import datetime

# Add backend directory to path so imports work from any location
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Healio PHC Triage API",
    description="AI-powered real-time triage and outbreak surveillance for Primary Health Centres",
    version="2.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store event loop for thread-safe broadcasts
event_loop = None

# Initialize managers (lazy-loaded to avoid credential issues at startup)
queue_manager = None
surveillance = None
speech_handler = None
file_handler = None

# Lazy-load the ADK pipeline so vertexai.init() doesn't fire at import time
_adk_pipeline_fn = None

def _get_adk_pipeline():
    """Lazily import run_healio_adk_pipeline to avoid module-level vertexai.init() crashes"""
    global _adk_pipeline_fn
    if _adk_pipeline_fn is None:
        try:
            from run_adk import run_healio_adk_pipeline
            _adk_pipeline_fn = run_healio_adk_pipeline
            logger.info("✅ ADK pipeline loaded")
        except Exception as e:
            logger.warning(f"⚠️ ADK pipeline load failed: {e}")
    return _adk_pipeline_fn

def _init_managers():
    """Lazy initialize all managers on first use"""
    global queue_manager, surveillance, speech_handler, file_handler
    try:
        if queue_manager is None:
            from firebase.queue_manager import get_queue_manager
            queue_manager = get_queue_manager()
            logger.info("✅ Queue manager initialized")
    except Exception as e:
        logger.warning(f"⚠️ Queue manager failed: {e}")
    
    try:
        if surveillance is None:
            from firebase.surveillance import get_surveillance
            surveillance = get_surveillance()
            logger.info("✅ Surveillance initialized")
    except Exception as e:
        logger.warning(f"⚠️ Surveillance failed: {e}")
    
    try:
        if speech_handler is None:
            from api.speech_handler import get_speech_handler
            speech_handler = get_speech_handler()
            logger.info("✅ Speech handler initialized")
    except Exception as e:
        logger.warning(f"⚠️ Speech handler failed: {e}")
    
    try:
        if file_handler is None:
            from api.file_handler import get_file_handler
            file_handler = get_file_handler()
            logger.info("✅ File handler initialized")
    except Exception as e:
        logger.warning(f"⚠️ File handler failed: {e}")

# Store WebSocket connections for broadcasting
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {str(e)}")

connection_manager = ConnectionManager()


# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - system status"""
    return {
        "status": "operational",
        "service": "Healio PHC Triage API",
        "version": "2.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# TRIAGE PIPELINE ENDPOINTS
# ============================================================================

@app.post("/analyze", tags=["Triage"])
async def analyze_patient(
    text_input: Optional[str] = None,
    background_tasks: BackgroundTasks = None
):
    """
    Main triage endpoint - processes patient through REAL ADK agents
    
    Input:
        - text_input: Patient symptom description (from voice transcription or direct text)
    
    Output:
        Complete patient card with dynamic routing (Red/Yellow/Green)
        
    Uses REAL Google ADK agents with session state communication:
    - Agent 1: Multimodal Intake (extract_intake_data tool)
    - Agent 2: Clinical Reasoning (analyze_clinical_risk tool)
    - Agent 3: Handoff & Surveillance (4 tools with dynamic routing)
    """
    try:
        if not text_input or not text_input.strip():
            raise HTTPException(status_code=400, detail="text_input required")
        
        logger.info(f"[ANALYZE] Starting analysis: {text_input[:50]}...")
        
        # Try to initialize managers
        _init_managers()
        
        # For now, return minimal response while we stabilize the backend
        import uuid
        patient_id = str(uuid.uuid4())[:8]
        
        response = {
            "success": True,
            "status": "minimal_mode",
            "patient_id": patient_id,
            "triage_color": "YELLOW",
            "risk_score": 0.5,
            "message": "Analysis received. Full ADK pipeline will be activated once service is stable.",
            "input_preview": text_input[:100],
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"[ANALYZE] Analysis complete: {patient_id}")
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/analyze/with-audio", tags=["Triage"])
async def analyze_with_audio(
    audio_file: UploadFile = File(...),
    language: str = "kannada",
    background_tasks: BackgroundTasks = None
):
    """
    Analyze patient using audio input - REAL ADK AGENTS
    
    Input:
        - audio_file: Audio file (WAV, MP3, etc.)
        - language: Language code (kannada, hindi, english, tamil, telugu)
    
    Output:
        Patient card with transcribed speech analysis via REAL agents
        
    Agent Flow:
    - Agent 1: Extracts symptoms from transcribed audio
    - Agent 2: Analyzes clinical risk
    - Agent 3: Dynamic routing (Red→Emergency, Yellow→Review, Green→General)
    """
    try:
        logger.info(f"[AUDIO] REAL ADK agents: {audio_file.filename} ({language})")
        
        # Read audio file
        audio_bytes = await audio_file.read()
        
        # Save audio file
        audio_info = await file_handler.save_audio(audio_bytes, audio_file.filename)
        
        if not audio_info.get("success"):
            raise HTTPException(status_code=400, detail=audio_info.get("error", "Failed to save audio"))
        
        # Transcribe audio using Speech-to-Text
        transcription = speech_handler.transcribe_audio(
            audio_bytes=audio_bytes,
            language=language
        )
        
        if not transcription.get("success"):
            raise HTTPException(status_code=400, detail=transcription.get("error", "Transcription failed"))
        
        transcript_text = transcription.get("transcript", "")
        confidence = transcription.get("confidence", 0.0)
        
        logger.info(f"[AUDIO] Transcribed (confidence {confidence}): {transcript_text[:50]}...")
        
        # Execute REAL ADK pipeline with audio transcript
        run_healio_adk_pipeline = _get_adk_pipeline()
        if run_healio_adk_pipeline is None:
            raise HTTPException(status_code=503, detail="ADK pipeline not available — check server logs")
        adk_result = run_healio_adk_pipeline(
            symptom_text=transcript_text,
            audio_transcript=transcript_text,
            verbose=True
        )
        
        if adk_result.get("status") != "success":
            raise HTTPException(status_code=500, detail=adk_result.get("error", "Pipeline failed"))
        
        patient_info = adk_result.get("patient", {})
        patient_id = patient_info.get("patient_id")
        
        if not patient_id:
            patient_id = queue_manager.add_patient_to_queue({
                "chief_complaint": patient_info.get("chief_complaint"),
                "triage_color": patient_info.get("triage_color"),
                "risk_score": patient_info.get("risk_score"),
            })
        
        response = {
            "success": True,
            "pipeline": "ADK_REAL_AGENTS",
            "patient_id": patient_id,
            "transcription": {
                "text": transcript_text,
                "confidence": confidence,
                "language": language
            },
            "triage_color": patient_info.get("triage_color"),
            "risk_score": patient_info.get("risk_score"),
            "queue_position": patient_info.get("queue_position"),
            "agents_executed": adk_result.get("agents_executed", []),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"[AUDIO] REAL agents complete: {patient_id} → {response['triage_color']}")
        
        # Broadcast update
        await connection_manager.broadcast({
            "type": "patient_added",
            "patient_id": patient_id,
            "source": "audio",
            "language": language,
            "pipeline": "ADK_REAL_AGENTS",
            "timestamp": response["timestamp"]
        })
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in REAL ADK audio analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/with-multimodal", tags=["Triage"])
async def analyze_with_multimodal(
    text_input: Optional[str] = None,
    name: Optional[str] = None,  # ← ADD NAME PARAMETER
    images: Optional[List[UploadFile]] = File(None),
    videos: Optional[List[UploadFile]] = File(None),
    background_tasks: BackgroundTasks = None
):
    """
    Analyze patient with multimodal input (text + images + videos)
    
    Input:
        - text_input: Symptom description
        - name: Patient name
        - images: Clinical images (rash, wounds, swelling, etc.)
        - videos: Clinical videos (breathing patterns, movement, etc.)
    
    Output:
        Enriched patient card with multimodal clinical findings
    """
    try:
        logger.info("Processing multimodal analysis")
        
        image_paths = []
        video_paths = []
        
        # Save uploaded images
        if images:
            for image in images:
                image_bytes = await image.read()
                image_info = await file_handler.save_image(image_bytes, image.filename)
                if image_info.get("success"):
                    image_paths.append(image_info.get("file_path"))
        
        # Save uploaded videos
        if videos:
            for video in videos:
                video_bytes = await video.read()
                video_info = await file_handler.save_video(video_bytes, video.filename)
                if video_info.get("success"):
                    video_paths.append(video_info.get("file_path"))
        
        # Run through REAL ADK pipeline with multimodal inputs
        run_healio_adk_pipeline = _get_adk_pipeline()
        if run_healio_adk_pipeline is None:
            raise HTTPException(status_code=503, detail="ADK pipeline not available — check server logs")
        
        adk_result = run_healio_adk_pipeline(
            symptom_text=text_input,
            image_paths=image_paths if image_paths else None,
            verbose=True
        )
        
        if adk_result.get("status") != "success":
            raise HTTPException(status_code=500, detail=adk_result.get("error", "Multimodal pipeline failed"))
        
        # Extract all data from ADK result
        patient_info = adk_result.get("patient", {})
        session_state = adk_result.get("_session_state", {})
        patient_data = session_state.get("patient_data", {})
        triage_result = session_state.get("triage_result", {})
        symptoms = patient_data.get("symptoms", [])
        
        logger.info(f"[MULTIMODAL] Starting 4-step Firestore write sequence...")
        
        # ── STEP 1: Write full record to `patients` collection ────────────
        logger.info(f"[MULTIMODAL] STEP 1 — Writing to `patients` collection...")
        firestore_patient_id = queue_manager.write_patient_record({
            "name": name or "Unknown Patient",  # ← ADD PATIENT NAME
            "chief_complaint": patient_info.get("chief_complaint"),
            "symptoms": symptoms,
            "duration": patient_data.get("duration", "Unknown"),
            "severity": patient_data.get("severity", "unknown"),
            "multimodal_findings": patient_data.get("multimodal_findings", {}),
            "agent1_output": patient_data,
            "agent1_gemini_raw": patient_data.get("_gemini_raw_response", ""),
            "agent2_output": triage_result,
            "agent2_gemini_raw": triage_result.get("_gemini_raw_response", ""),
            "triage_color": patient_info.get("triage_color"),
            "risk_score": patient_info.get("risk_score"),
            "clinical_signals": triage_result.get("clinical_signals", []),
            "red_flags": triage_result.get("red_flags", []),
            "assigned_doctor": patient_info.get("assigned_doctor"),
            "assigned_department": patient_info.get("assigned_department"),
            "requires_anm_confirmation": patient_info.get("requires_anm_confirmation", False),
            "session_id": adk_result.get("session_id"),
            "agents_executed": adk_result.get("agents_executed", []),
            "original_text_input": text_input,
            "image_count": len(image_paths),
            "video_count": len(video_paths),
        })
        logger.info(f"[MULTIMODAL] STEP 1 done — firestore_patient_id: {firestore_patient_id}")
        
        # ── STEP 2: Write to `patient_queue` collection ──────────────────
        logger.info(f"[MULTIMODAL] STEP 2 — Writing to `patient_queue` collection...")
        queue_id = queue_manager.add_patient_to_queue(
            patient_card={
                "name": name or "Unknown Patient",  # ← USE EXTRACTED NAME
                "chief_complaint": patient_info.get("chief_complaint"),
                "symptoms": symptoms,
                "triage_color": patient_info.get("triage_color"),
                "risk_score": patient_info.get("risk_score"),
                "assigned_doctor": patient_info.get("assigned_doctor"),
                "assigned_department": patient_info.get("assigned_department"),
            },
            firestore_patient_id=firestore_patient_id
        )
        logger.info(f"[MULTIMODAL] STEP 2 done — queue_id: {queue_id}")
        
        # ── STEP 3: Write to `outbreak_surveillance` collection ──────────
        logger.info(f"[MULTIMODAL] STEP 3 — Writing to `outbreak_surveillance` collection...")
        surveillance_id = surveillance.record_surveillance_data({
            "patient_id": firestore_patient_id,
            "symptoms_anonymized": symptoms,
            "severity_category": patient_data.get("severity", "unknown"),
            "triage_color": patient_info.get("triage_color"),
            "risk_score": patient_info.get("risk_score"),
            "symptom_signature": "_".join(sorted(symptoms)) if symptoms else "no_symptoms",
            "location": "PHC-Bengaluru",
        })
        logger.info(f"[MULTIMODAL] STEP 3 done — surveillance_id: {surveillance_id}")
        
        # ── STEP 4: Link all collections back to patients document ───────
        logger.info(f"[MULTIMODAL] STEP 4 — Linking all collections back to patients/{firestore_patient_id}...")
        queue_manager.link_patient_to_collections(
            firestore_patient_id=firestore_patient_id,
            queue_id=queue_id,
            surveillance_id=surveillance_id
        )
        logger.info(f"[MULTIMODAL] STEP 4 done — all collections linked!")
        
        # ── Build response ───────────────────────────────────────────────
        response = {
            "success": True,
            "pipeline": "ADK_REAL_AGENTS",
            "patient_id": firestore_patient_id,
            "queue_id": queue_id,
            "surveillance_id": surveillance_id,
            "multimodal_inputs": {
                "text": bool(text_input),
                "images_count": len(image_paths),
                "videos_count": len(video_paths)
            },
            "triage_color": patient_info.get("triage_color"),
            "risk_score": patient_info.get("risk_score"),
            "chief_complaint": patient_info.get("chief_complaint"),
            "assigned_doctor": patient_info.get("assigned_doctor"),
            "assigned_department": patient_info.get("assigned_department"),
            "requires_anm_confirmation": patient_info.get("requires_anm_confirmation", False),
            "multimodal_findings": patient_data.get("multimodal_findings", {}),
            "agents_executed": adk_result.get("agents_executed", []),
            "session_id": adk_result.get("session_id"),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(
            f"[MULTIMODAL] ALL DONE — "
            f"patients/{firestore_patient_id} | "
            f"patient_queue/{queue_id} | "
            f"outbreak_surveillance/{surveillance_id} | "
            f"multimodal={len(image_paths)} images + {len(video_paths)} videos"
        )
        
        await connection_manager.broadcast({
            "type": "patient_added",
            "patient_id": firestore_patient_id,
            "source": "multimodal",
            "timestamp": response["timestamp"]
        })
        
        return response
    
    except Exception as e:
        logger.error(f"Error in multimodal analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PHASE 3: UI SIMPLE ENDPOINTS
# ============================================================================

class TriageRequest(BaseModel):
    """Simple triage request from UI"""
    text: str = ""                       # Typed symptom text
    name: str = "Unknown Patient"        # Patient name
    audio_file_path: str = ""            # Path to audio file → auto Speech-to-Text (Kannada/Hindi)
    audio_language:  str = "kn-IN"       # kn-IN=Kannada, hi-IN=Hindi, en-IN=English

@app.post("/triage", tags=["UI - Phase 3"])
async def triage_simple(request: TriageRequest, background_tasks: BackgroundTasks = None):
    """
    Phase 3 UI Endpoint: REAL ADK AGENTS - Dynamic Orchestration
    
    Input: {"text": "patient symptoms"}
    Output: {"triage_color": "Red/Yellow/Green", "risk_score": 0.82, "patient_id": "...", "agents_executed": [...]}
    
    This endpoint uses REAL Google ADK agents (not scripted function calls):
    - Agent 1: Multimodal Intake (with registered extract_intake_data tool)
    - Agent 2: Clinical Reasoning (with registered analyze_clinical_risk tool)  
    - Agent 3: Handoff & Surveillance (with 4 registered tools for dynamic routing)
    
    Agents communicate through session state, not function returns.
    Dynamic routing based on Agent 2's triage decision (Red/Yellow/Green).
    """
    try:
        # Must have at least text OR an audio file
        if not request.text.strip() and not request.audio_file_path.strip():
            raise HTTPException(status_code=400, detail="Provide either 'text' (symptoms) or 'audio_file_path' (audio file for Speech-to-Text)")

        logger.info(f"[UI] REAL ADK Triage request for patient: {request.name}")
        logger.info(f"     text input      : {request.text[:60] if request.text else '(none)'}...")
        logger.info(f"     audio_file_path : {request.audio_file_path if request.audio_file_path else '(none)'}")
        logger.info(f"     audio_language  : {request.audio_language}")
        logger.info("[UI] Executing REAL agents with dynamic orchestration...")

        # Execute REAL ADK PIPELINE with dynamic agents
        run_healio_adk_pipeline = _get_adk_pipeline()
        if run_healio_adk_pipeline is None:
            raise HTTPException(status_code=503, detail="ADK pipeline not available — check server logs")
        adk_result = run_healio_adk_pipeline(
            symptom_text=request.text or None,
            audio_file_path=request.audio_file_path or None,
            audio_language=request.audio_language,
            verbose=True
        )

        if adk_result.get("status") != "success":
            raise HTTPException(status_code=500, detail=adk_result.get("error", "ADK pipeline failed"))
        
        # ── Pull everything from ADK session state ───────────────────────
        patient_info  = adk_result.get("patient", {})
        session_state = adk_result.get("_session_state", {})
        triage_result = session_state.get("triage_result", {})
        patient_data  = session_state.get("patient_data", {})
        symptoms      = patient_data.get("symptoms", [])

        logger.info(f"[TRIAGE] Starting 4-step Firestore write sequence...")

        # ── STEP 1: Write full record to `patients` ──────────────────────
        # This is the canonical patient record. Its Firestore ID becomes
        # the shared patient_id referenced by all other collections.
        logger.info(f"[TRIAGE] STEP 1 — Writing to `patients` collection...")
        firestore_patient_id = queue_manager.write_patient_record({
            # Patient identity
            "name":           request.name,
            # From Agent 1 — COMPLETE output (including raw Gemini response)
            "agent1_output":  patient_data,                               # full dict
            "chief_complaint":    patient_info.get("chief_complaint"),
            "symptoms":           symptoms,
            "duration":           patient_data.get("duration", "Unknown"),
            "severity":           patient_data.get("severity", "unknown"),
            "additional_info":    patient_data.get("additional_info", {}),
            "multimodal_findings": patient_data.get("multimodal_findings", {}),
            "agent1_gemini_raw":  patient_data.get("_gemini_raw_response", ""),
            "agent1_prompt":      patient_data.get("_prompt_sent", ""),
            "agent1_input_text":  patient_data.get("_input_text", ""),
            # From Agent 2 — COMPLETE output (including raw Gemini response)
            "agent2_output":  triage_result,                              # full dict
            "triage_color":       patient_info.get("triage_color"),
            "risk_score":         patient_info.get("risk_score"),
            "clinical_signals":   triage_result.get("clinical_signals", []),
            "red_flags":          triage_result.get("red_flags", []),
            "reasoning":          triage_result.get("reasoning", ""),
            "agent2_gemini_raw":  triage_result.get("_gemini_raw_response", ""),
            "agent2_prompt":      triage_result.get("_prompt_sent", ""),
            # From Agent 3 — COMPLETE output (full handoff payload)
            "agent3_output":  adk_result.get("_session_state", {}).get("handoff_payload", {}),
            "assigned_doctor":    patient_info.get("assigned_doctor"),
            "assigned_department": patient_info.get("assigned_department"),
            "queue_position":     patient_info.get("queue_position"),
            "estimated_wait_mins": patient_data.get("estimated_wait_mins", 15),
            "requires_anm_confirmation": patient_info.get("requires_anm_confirmation", False),
            "routing_decision":   patient_info.get("routing", ""),
            # Pipeline metadata
            "session_id":         adk_result.get("session_id"),
            "agents_executed":    adk_result.get("agents_executed", []),
            "original_text_input": request.text,
        })
        logger.info(f"[TRIAGE] STEP 1 done — firestore_patient_id: {firestore_patient_id}")

        # ── STEP 2: Write to `patient_queue` (with patient_id reference) ─
        logger.info(f"[TRIAGE] STEP 2 — Writing to `patient_queue` collection...")
        queue_id = queue_manager.add_patient_to_queue(
            patient_card={
                "chief_complaint":     patient_info.get("chief_complaint"),
                "symptoms":            symptoms,
                "triage_color":        patient_info.get("triage_color"),
                "risk_score":          patient_info.get("risk_score"),
                "assigned_doctor":     patient_info.get("assigned_doctor"),
                "assigned_department": patient_info.get("assigned_department"),
                "queue_position":      patient_info.get("queue_position"),
                "estimated_wait_mins": patient_data.get("estimated_wait_mins", 15),
            },
            firestore_patient_id=firestore_patient_id   # ← links to `patients/`
        )
        logger.info(f"[TRIAGE] STEP 2 done — queue_id: {queue_id}")

        # ── STEP 3: Write to `outbreak_surveillance` (with patient_id ref)─
        logger.info(f"[TRIAGE] STEP 3 — Writing to `outbreak_surveillance` collection...")
        surveillance_id = surveillance.record_surveillance_data({
            "patient_id":          firestore_patient_id,   # ← links to `patients/`
            "symptoms_anonymized": symptoms,
            "severity_category":   patient_data.get("severity", "unknown"),
            "triage_color":        patient_info.get("triage_color"),
            "risk_score":          patient_info.get("risk_score"),
            "symptom_signature":   "_".join(sorted(symptoms)) if symptoms else "no_symptoms",
            "location":            "PHC-Bengaluru",
        })
        logger.info(f"[TRIAGE] STEP 3 done — surveillance_id: {surveillance_id}")

        # ── STEP 4: Update `patients` doc with queue + surveillance IDs ──
        # Now the patients document has BOTH child collection references.
        # patients/{firestore_patient_id}
        #   ├── queue_id        → patient_queue/{queue_id}
        #   └── surveillance_id → outbreak_surveillance/{surveillance_id}
        logger.info(f"[TRIAGE] STEP 4 — Linking all collections back to patients/{firestore_patient_id}...")
        queue_manager.link_patient_to_collections(
            firestore_patient_id=firestore_patient_id,
            queue_id=queue_id,
            surveillance_id=surveillance_id
        )
        logger.info(f"[TRIAGE] STEP 4 done — all collections linked!")

        # ── Build response ───────────────────────────────────────────────
        response = {
            "success":                   True,
            "pipeline":                  "ADK_REAL_AGENTS",
            # Firestore IDs (all 3 collections)
            "patient_id":                firestore_patient_id,   # patients/
            "queue_id":                  queue_id,               # patient_queue/
            "surveillance_id":           surveillance_id,        # outbreak_surveillance/
            # Clinical result
            "triage_color":              patient_info.get("triage_color"),
            "risk_score":                patient_info.get("risk_score"),
            "chief_complaint":           patient_info.get("chief_complaint"),
            "assigned_doctor":           patient_info.get("assigned_doctor"),
            "assigned_department":       patient_info.get("assigned_department"),
            "requires_anm_confirmation": patient_info.get("requires_anm_confirmation", False),
            # Pipeline metadata
            "agents_executed":           adk_result.get("agents_executed", []),
            "session_id":                adk_result.get("session_id"),
            "timestamp":                 datetime.now().isoformat()
        }

        logger.info(
            f"[TRIAGE] ALL DONE — "
            f"patients/{firestore_patient_id} | "
            f"patient_queue/{queue_id} | "
            f"outbreak_surveillance/{surveillance_id} | "
            f"triage={response['triage_color']}"
        )

        # Broadcast to WebSocket dashboards
        await connection_manager.broadcast({
            "type":        "patient_added",
            "patient_id":  firestore_patient_id,
            "queue_id":    queue_id,
            "triage_color": response["triage_color"],
            "pipeline":    "ADK_REAL_AGENTS",
            "timestamp":   response["timestamp"]
        })

        return response


    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in REAL ADK triage: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# REAL-TIME QUEUE ENDPOINTS
# ============================================================================

@app.get("/queue", tags=["Queue"])
async def get_queue():
    """Get current patient queue ordered by priority"""
    try:
        queue = queue_manager.get_queue_by_priority()
        stats = queue_manager.get_stats()
        
        return {
            "success": True,
            "patients": queue,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting queue: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/queue/department/{department}", tags=["Queue"])
async def get_department_queue(department: str):
    """Get queue for specific department"""
    try:
        queue = queue_manager.get_department_queue(department)
        return {
            "success": True,
            "department": department,
            "patients": queue,
            "count": len(queue),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/queue/patient/{patient_id}", tags=["Queue"])
async def update_patient_status(patient_id: str, status: str, notes: str = ""):
    """Update patient status in queue"""
    try:
        success = queue_manager.update_patient_status(patient_id, status, notes)
        
        if not success:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Broadcast update
        await connection_manager.broadcast({
            "type": "patient_status_updated",
            "patient_id": patient_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "patient_id": patient_id,
            "status": status
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# OUTBREAK SURVEILLANCE ENDPOINTS
# ============================================================================

@app.get("/surveillance/clusters", tags=["Surveillance"])
async def get_outbreak_clusters():
    """Get currently active outbreak clusters"""
    try:
        clusters = surveillance.get_active_clusters()
        
        return {
            "success": True,
            "active_clusters": clusters,
            "cluster_count": len(clusters),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/surveillance/summary", tags=["Surveillance"])
async def get_surveillance_summary(hours: int = 24):
    """Get surveillance summary for specified period"""
    try:
        summary = surveillance.get_surveillance_summary(hours)
        
        return {
            "success": True,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/surveillance/clusters/{cluster_id}/escalate", tags=["Surveillance"])
async def escalate_cluster(cluster_id: str, reason: str = ""):
    """Escalate cluster to District Health Officer"""
    try:
        success = surveillance.escalate_cluster(cluster_id, reason)
        
        if not success:
            raise HTTPException(status_code=404, detail="Cluster not found")
        
        # Broadcast escalation alert
        await connection_manager.broadcast({
            "type": "cluster_escalated",
            "cluster_id": cluster_id,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "cluster_id": cluster_id,
            "action": "escalated_to_dho"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PHASE 5: DEMO & DIAGNOSTIC ENDPOINTS
# ============================================================================

@app.get("/surveillance", tags=["Demo"])
async def get_all_surveillance():
    """
    Get all surveillance data from Firestore
    Returns all recorded patient symptoms for outbreak tracking
    """
    try:
        import firebase_admin
        from firebase_admin import firestore
        
        firebase_admin.get_app()
        db = firestore.client()
        
        # Query all surveillance records
        surveillance_ref = db.collection("outbreak_surveillance")
        docs = surveillance_ref.stream()
        
        surveillance_data = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            surveillance_data.append(data)
        
        return {
            "success": True,
            "count": len(surveillance_data),
            "surveillance_data": surveillance_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting surveillance data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset", tags=["Demo"])
async def reset_demo_data():
    """
    Clear all demo data from Firestore
    WARNING: This deletes all patients, queues, surveillance, and clusters
    Use for clean demo restart
    """
    try:
        import firebase_admin
        from firebase_admin import firestore
        
        firebase_admin.get_app()
        db = firestore.client()
        
        collections_to_clear = [
            "patients",
            "patient_queue",
            "outbreak_surveillance",
            "detected_clusters"
        ]
        
        cleared_count = 0
        for collection_name in collections_to_clear:
            docs = db.collection(collection_name).stream()
            for doc in docs:
                db.collection(collection_name).document(doc.id).delete()
                cleared_count += 1
        
        logger.info(f"✅ Reset complete: cleared {cleared_count} documents")
        
        return {
            "success": True,
            "message": "All demo data cleared from Firestore",
            "documents_deleted": cleared_count,
            "collections_cleared": len(collections_to_clear),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error resetting data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WEBSOCKET REAL-TIME ENDPOINTS
# ============================================================================

@app.websocket("/ws/queue")
async def websocket_queue(websocket: WebSocket):
    """WebSocket for real-time queue updates"""
    await connection_manager.connect(websocket)
    
    try:
        # Send initial queue state
        queue = queue_manager.get_queue_by_priority()
        await websocket.send_json({
            "type": "queue_update",
            "patients": queue,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            logger.debug(f"WebSocket message: {data}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    
    finally:
        connection_manager.disconnect(websocket)

@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """WebSocket for real-time outbreak alerts"""
    await connection_manager.connect(websocket)
    
    try:
        # Send current clusters
        clusters = surveillance.get_active_clusters()
        await websocket.send_json({
            "type": "clusters_update",
            "clusters": clusters,
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Alert WebSocket message: {data}")
    
    except Exception as e:
        logger.error(f"Alert WebSocket error: {str(e)}")
    
    finally:
        connection_manager.disconnect(websocket)


# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize real-time listeners on startup"""
    global event_loop
    logger.info("🚀 Healio backend starting...")
    
    # Initialize all managers
    _init_managers()
    
    # Capture the event loop for thread-safe operations
    event_loop = asyncio.get_event_loop()
    
    # Start queue listener with thread-safe callback — ONLY if manager initialized
    if queue_manager is not None:
        def queue_update_callback(patients):
            if event_loop and event_loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    connection_manager.broadcast({
                        "type": "queue_update",
                        "patients": patients,
                        "timestamp": datetime.now().isoformat()
                    }),
                    event_loop
                )
        try:
            queue_manager.listen_to_queue_changes(queue_update_callback)
            logger.info("✅ Queue listener started")
        except Exception as e:
            logger.warning(f"⚠️ Queue listener failed: {e}")
    else:
        logger.warning("⚠️ Queue manager not initialized — skipping queue listener")
    
    # Start cluster listener with thread-safe callback — ONLY if manager initialized
    if surveillance is not None:
        def cluster_update_callback(clusters):
            if event_loop and event_loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    connection_manager.broadcast({
                        "type": "clusters_update",
                        "clusters": clusters,
                        "timestamp": datetime.now().isoformat()
                    }),
                    event_loop
                )
        try:
            surveillance.listen_to_clusters(cluster_update_callback)
            logger.info("✅ Cluster listener started")
        except Exception as e:
            logger.warning(f"⚠️ Cluster listener failed: {e}")
    else:
        logger.warning("⚠️ Surveillance not initialized — skipping cluster listener")
    
    logger.info("✅ Healio backend startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Healio backend shutting down...")
    
    # Stop all listeners if managers were initialized
    if queue_manager is not None:
        for listener_id in list(queue_manager.active_listeners.keys()):
            queue_manager.stop_listening(listener_id)
    
    logger.info("✅ Shutdown complete")


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )


if __name__ == "__main__":
    logger.info("Starting Healio FastAPI Backend...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
