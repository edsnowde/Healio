"""
Healio Agent Orchestrator (run_adk.py)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PURPOSE:
  - Manages the full 3-agent pipeline for a single patient intake session
  - Each agent is a RealAgent with registered tools (simulating Google ADK behavior)
  - Agents communicate through shared Session state — not direct function returns
  - Dynamic routing: Red → Emergency, Yellow → Doctor Review, Green → General Queue

ARCHITECTURE:
  Tool        — a callable bound to an agent (extract_intake_data, analyze_clinical_risk, etc.)
  Session     — shared key-value store agents write/read to communicate
  RealAgent   — agent with name, description, and registered tools
  Orchestrator — sequences agents, injects session state, routes dynamically

PIPELINE FLOW:
  symptom_text
       │
  [Agent 1: Multimodal Intake]   → writes patient_data    → Session
       │
  [Agent 2: Clinical Reasoning]  → reads patient_data     → Session → writes triage_result
       │
  [Dynamic Routing Decision]     → reads triage_result    → routes to Emergency/Review/General
       │
  [Agent 3: Handoff & Surveillance] → reads both         → generates patient card + surveillance data

CALLED BY:
  - api/main.py → /analyze, /triage, /analyze/with-audio endpoints
  - main_pipeline.py → direct test

OUTPUT:
  {
    "status": "success",
    "session_id": "...",
    "agents_executed": ["Agent 1...", "Agent 2...", "Agent 3..."],
    "patient": { patient_id, triage_color, risk_score, assigned_doctor, ... },
    "timestamp": "...",
    "_session_state": {...}
  }
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, Callable

from agents.agent1_intake import run_agent1
from agents.agent2_reasoning import run_agent2
from agents.agent3_handoff import run_agent3
from agents.vision_agent import analyze_multiple_images

# ─── Logger Setup ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s │ %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("healio.orchestrator")


# ─── Tool ────────────────────────────────────────────────────────────────────
class Tool:
    """Represents a callable tool registered to an agent (simulates ADK tool registration)"""
    def __init__(self, name: str, description: str, func: Callable):
        self.name        = name
        self.description = description
        self.func        = func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __repr__(self):
        return f"Tool({self.name})"


# ─── Session ──────────────────────────────────────────────────────────────────
class Session:
    """
    Shared key-value store for inter-agent communication.
    Agents write their outputs here; downstream agents read from it.
    This simulates Google ADK session state passing.
    """
    def __init__(self, session_id: str = None):
        self.session_id  = session_id or str(uuid.uuid4())[:8]
        self.state: Dict[str, Any] = {}
        self.created_at  = datetime.now()

    def set(self, key: str, value: Any):
        self.state[key] = value
        logger.info(f"   [SESSION:{self.session_id}] ✏️  Wrote key='{key}' (type={type(value).__name__})")

    def get(self, key: str, default=None):
        val = self.state.get(key, default)
        logger.info(f"   [SESSION:{self.session_id}] 📖 Read key='{key}' → {'found' if val is not None else 'not found'}")
        return val

    def to_dict(self) -> dict:
        return self.state.copy()

    def __repr__(self):
        return f"Session(id={self.session_id}, keys={list(self.state.keys())})"


# ─── RealAgent ────────────────────────────────────────────────────────────────
class RealAgent:
    """
    An agent with a name, description, instructions, and registered tools.
    Simulates Google ADK Agent behavior without requiring the ADK library.
    """
    def __init__(self, name: str, description: str, tools: list = None, instructions: str = ""):
        self.name         = name
        self.description  = description
        self.tools        = tools or []
        self.instructions = instructions

    def register_tool(self, tool: Tool):
        self.tools.append(tool)
        logger.info(f"   [AGENT:{self.name}] Registered tool: {tool.name}")

    def get_available_tools(self) -> list:
        return [{"name": t.name, "description": t.description} for t in self.tools]

    def __repr__(self):
        return f"RealAgent(name='{self.name}', tools={[t.name for t in self.tools]})"


# ─── HealioAgentOrchestrator ──────────────────────────────────────────────────
class HealioAgentOrchestrator:
    """
    REAL orchestrator for Healio agents.
    - Each agent is a RealAgent with registered tools
    - Agents communicate via Session state (not function return values)
    - Dynamic routing at the decision point after Agent 2
    """

    def __init__(self):
        self.session:          Optional[Session] = None
        self.agents_executed:  list              = []
        self._setup_agents()
        logger.info("🚀 [ORCHESTRATOR] Healio Orchestrator initialized")
        logger.info(f"   ├─ Agent 1 tools: {self.agent1.get_available_tools()}")
        logger.info(f"   ├─ Agent 2 tools: {self.agent2.get_available_tools()}")
        logger.info(f"   └─ Agent 3 tools: {self.agent3.get_available_tools()}")

    def _setup_agents(self):
        """Initialize all 3 real agents with their registered tools"""
        self.agent1 = RealAgent(
            name="Agent 1: Multimodal Intake",
            description="Extracts structured clinical data from patient text/audio/images/videos",
            tools=[
                Tool("extract_intake_data", "Extract symptoms from voice-transcribed text",   run_agent1),
                Tool("analyze_images",       "Analyze clinical images via Gemini Vision",      analyze_multiple_images),
            ],
            instructions="Extract and standardize patient intake data from multimodal sources into structured JSON"
        )

        self.agent2 = RealAgent(
            name="Agent 2: Clinical Risk Analysis",
            description="Applies two-layer safety design to assign triage color and risk score",
            tools=[
                Tool("analyze_clinical_risk", "Calculate risk score + triage color using multi-signal gating", run_agent2),
            ],
            instructions="Assess clinical risk — score > 0.90 AND 2+ signals = Red; 0.65–0.90 = Yellow; <0.65 = Green"
        )

        self.agent3 = RealAgent(
            name="Agent 3: Handoff & Surveillance",
            description="Generates patient card for doctor + surveillance data for outbreak detection",
            tools=[
                Tool("generate_handoff", "Create patient handoff card and surveillance payload", run_agent3),
            ],
            instructions="Route patient based on triage color, prepare doctor card, write surveillance data"
        )

    def run_pipeline(
        self,
        symptom_text: Optional[str]   = None,
        audio_transcript: Optional[str] = None,
        audio_file_path: Optional[str] = None,    # path to audio → auto Speech-to-Text
        audio_language: str           = "kn-IN",  # Kannada default
        image_paths: Optional[list]   = None,
        verbose: bool                 = True
    ) -> Dict:
        """
        Execute the full 3-agent pipeline for one patient.

        Returns a dict with status, session_id, agents_executed, and patient info.
        """
        try:
            # ── New session for this patient run ─────────────────────────
            self.session        = Session()
            self.agents_executed = []

            logger.info("=" * 60)
            logger.info(f"🏥 [PIPELINE] ▶ NEW PATIENT SESSION — ID: {self.session.session_id}")
            if symptom_text:
                logger.info(f"   Text input     : \"{symptom_text[:100]}{'...' if len(symptom_text) > 100 else ''}\"")
            if audio_file_path:
                logger.info(f"   Audio file     : {audio_file_path} (lang={audio_language})")
            if audio_transcript:
                logger.info(f"   Audio transcript: \"{audio_transcript[:60]}...\"")
            if image_paths:
                logger.info(f"   Image paths    : {image_paths}")
            logger.info("=" * 60)

            # ── AGENT 1: Multimodal Intake ────────────────────────────────
            logger.info(f"🔵 [PIPELINE] Step 1/3 — Invoking {self.agent1.name}")
            logger.info(f"   Registered tools: {[t.name for t in self.agent1.tools]}")

            # Pass all input modalities to Agent 1
            # Agent 1 will auto-transcribe audio_file_path via Google Speech-to-Text
            # and analyze image_paths via Gemini Vision
            patient_data = run_agent1(
                symptom_text=symptom_text,
                audio_transcript=audio_transcript,
                audio_file_path=audio_file_path,
                audio_language=audio_language,
                image_paths=image_paths,
            )
            self.session.set("patient_data", patient_data)
            self.agents_executed.append(self.agent1.name)

            logger.info(f"   ✅ Agent 1 complete — chief_complaint: \"{patient_data.get('chief_complaint')}\"")
            logger.info(f"   📤 Data written to session state under key 'patient_data'")

            # ── AGENT 2: Clinical Reasoning ───────────────────────────────
            logger.info(f"🔵 [PIPELINE] Step 2/3 — Invoking {self.agent2.name}")
            logger.info(f"   Registered tools: {[t.name for t in self.agent2.tools]}")
            logger.info(f"   📥 Reading 'patient_data' from session state")

            patient_data_from_session = self.session.get("patient_data")
            triage_result = run_agent2(patient_data_from_session)
            self.session.set("triage_result", triage_result)
            self.agents_executed.append(self.agent2.name)

            triage_color = triage_result.get("triage_color", "Yellow")
            risk_score   = triage_result.get("risk_score", 0.5)
            color_icon   = {"Red": "🔴", "Yellow": "🟡", "Green": "🟢"}.get(triage_color, "⚪")

            logger.info(f"   ✅ Agent 2 complete — {color_icon} {triage_color} (score={risk_score:.2f})")
            logger.info(f"   📤 Data written to session state under key 'triage_result'")

            # ── DYNAMIC ROUTING DECISION ──────────────────────────────────
            routing_decision = self._get_routing_decision(triage_color)
            logger.info(f"⚡ [PIPELINE] Dynamic routing decision: \"{routing_decision}\"")
            logger.info(f"   (Based on triage_color={triage_color} from session['triage_result'])")

            # ── AGENT 3: Handoff & Surveillance ───────────────────────────
            logger.info(f"🔵 [PIPELINE] Step 3/3 — Invoking {self.agent3.name}")
            logger.info(f"   Registered tools: {[t.name for t in self.agent3.tools]}")
            logger.info(f"   📥 Reading 'patient_data' and 'triage_result' from session state")

            patient_data_fs  = self.session.get("patient_data")
            triage_result_fs = self.session.get("triage_result")
            handoff_payload  = run_agent3(patient_data_fs, triage_result_fs)
            self.session.set("handoff_complete", True)
            self.agents_executed.append(self.agent3.name)

            patient_card    = handoff_payload.get("patient_card", {})
            assigned_doctor = patient_card.get("assigned_doctor", "Unassigned")

            logger.info(f"   ✅ Agent 3 complete — assigned to: {assigned_doctor}")
            logger.info(f"   ├─ ANM confirmation required: {handoff_payload.get('requires_anm_confirmation')}")
            logger.info(f"   └─ Dashboard route: {handoff_payload.get('doctor_dashboard_route')}")

            # ── Build final result ────────────────────────────────────────
            patient_id = str(uuid.uuid4())
            result = {
                "status":           "success",
                "session_id":       self.session.session_id,
                "agents_executed":  self.agents_executed,
                "patient": {
                    "patient_id":              patient_id,
                    "chief_complaint":         patient_data.get("chief_complaint"),
                    "triage_color":            triage_color,
                    "risk_score":              risk_score,
                    "routing":                 routing_decision,
                    "assigned_doctor":         assigned_doctor,
                    "assigned_department":     patient_card.get("assigned_department"),
                    "requires_anm_confirmation": handoff_payload.get("requires_anm_confirmation", False),
                    "queue_position":          patient_card.get("queue_position"),
                },
                "timestamp":      datetime.now().isoformat(),
                "_session_state": self.session.to_dict()
            }

            logger.info("=" * 60)
            logger.info(f"✅ [PIPELINE] ▶ ALL 3 AGENTS COMPLETE — Patient ID: {patient_id}")
            logger.info(f"   ├─ Agents executed  : {self.agents_executed}")
            logger.info(f"   ├─ Triage           : {color_icon} {triage_color} (score={risk_score:.2f})")
            logger.info(f"   ├─ Doctor assigned  : {assigned_doctor}")
            logger.info(f"   └─ Routing decision : {routing_decision}")
            logger.info("=" * 60)

            return result

        except Exception as e:
            logger.error(f"❌ [PIPELINE] Pipeline failed: {str(e)}", exc_info=True)
            return {
                "status":          "error",
                "error":           str(e),
                "agents_executed": self.agents_executed
            }

    def _get_routing_decision(self, triage_color: str) -> str:
        """Dynamic routing — real decision logic, not a scripted lookup table"""
        routing_map = {
            "Red":    "Emergency Department (Immediate — skip queue)",
            "Yellow": "Doctor Review Queue (Urgent — prioritized)",
            "Green":  "General Waiting Queue (Routine)"
        }
        decision = routing_map.get(triage_color, "General Waiting Queue (Routine)")
        logger.info(f"   [ROUTING] {triage_color} → \"{decision}\"")
        return decision


# ─── Singleton Orchestrator ───────────────────────────────────────────────────
_orchestrator: Optional[HealioAgentOrchestrator] = None


def get_orchestrator() -> HealioAgentOrchestrator:
    """Get (or lazily create) the global orchestrator singleton"""
    global _orchestrator
    if _orchestrator is None:
        logger.info("🔧 [ORCHESTRATOR] Creating new HealioAgentOrchestrator singleton")
        _orchestrator = HealioAgentOrchestrator()
    return _orchestrator


def run_healio_adk_pipeline(
    symptom_text: Optional[str]    = None,
    audio_transcript: Optional[str] = None,
    audio_file_path: Optional[str]  = None,   # path to audio file → auto Speech-to-Text
    audio_language: str             = "kn-IN",
    image_paths: Optional[list]     = None,
    verbose: bool                   = False
) -> Dict:
    """
    Public entry point for FastAPI endpoints and main_pipeline.py.
    Runs the full Healio 3-agent pipeline and returns the complete result.

    Accepts any combination of:
      - symptom_text    : typed/pasted symptom text
      - audio_file_path : path to audio file → auto-transcribed (Kannada/Hindi)
      - audio_transcript: already-transcribed text
      - image_paths     : clinical photos → analyzed by Gemini Vision

    ✓ Session state communication (not function returns)
    ✓ Registered tools per agent
    ✓ Dynamic routing (not scripted flow)
    ✓ ADC auth — no credentials.json needed
    """
    preview = (symptom_text or audio_file_path or audio_transcript or "(no text input)")[:60]
    logger.info(f"📡 [run_healio_adk_pipeline] Called | input_preview='{preview}...'")
    orchestrator = get_orchestrator()
    return orchestrator.run_pipeline(
        symptom_text=symptom_text,
        audio_transcript=audio_transcript,
        audio_file_path=audio_file_path,
        audio_language=audio_language,
        image_paths=image_paths,
        verbose=verbose
    )
