"""
Firebase Real-Time Queue Manager
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PURPOSE:
  - Manages the patient queue in Firebase Firestore
  - Patients are stored with triage color, doctor assignment, wait time
  - Queue is sorted Red → Yellow → Green (priority order)
  - Supports real-time listeners: any change in Firestore pushes update to WebSocket

CALLED BY:
  - api/main.py → adds patients, gets queue, updates status
  - phase4_integration.py → pushes patient card after Agent 3
  - WebSocket /ws/queue → listens for live queue changes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import firebase_admin
from firebase_admin import firestore
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
import asyncio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s │ %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("healio.firebase.queue")


@dataclass
class QueuedPatient:
    """Represents a patient in the queue"""
    patient_id: str
    chief_complaint: str
    triage_color: str
    risk_score: float
    timestamp: str
    queue_position: int
    estimated_wait_mins: int
    assigned_doctor: str
    assigned_department: str
    status: str = "waiting"  # waiting, in_consultation, completed


class FirebaseQueueManager:
    """Manages real-time patient queue in Firebase"""

    def __init__(self):
        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app()

        self.db                 = firestore.client()
        self.patients_collection = "patients"          # Full patient records
        self.queue_collection    = "patient_queue"     # Real-time triage queue
        self.active_listeners    = {}

    # -------------------------------------------------------------------------
    # NEW: Write full patient record to `patients` collection
    # This is the canonical patient record — all other collections reference it
    # -------------------------------------------------------------------------
    def write_patient_record(self, patient_full: dict) -> str:
        """
        Write the COMPLETE patient record to the `patients` collection.

        Stores everything — including name, all agent outputs, raw Gemini responses,
        prompts sent to Gemini, reasoning, signals, surveillance data, and metadata.

        Returns:
            firestore_patient_id — the Firestore doc ID, used as canonical patient_id
                                   across patient_queue and outbreak_surveillance.
        """
        try:
            patient_record = {
                # ── Patient Identity ──────────────────────────────────────
                "name":                  patient_full.get("name", "Unknown Patient"),
                "original_text_input":   patient_full.get("original_text_input", ""),
                "status":                "waiting",
                "created_at":            datetime.now().isoformat(),

                # ── AGENT 1: Full Gemini Intake Output ────────────────────
                # Everything Agent 1 extracted + the raw Gemini text it got back
                "agent1_chief_complaint":    patient_full.get("chief_complaint", ""),
                "agent1_symptoms":           patient_full.get("symptoms", []),
                "agent1_duration":           patient_full.get("duration", "Unknown"),
                "agent1_severity":           patient_full.get("severity", "unknown"),
                "agent1_additional_info":    patient_full.get("additional_info", {}),
                "agent1_multimodal_findings": patient_full.get("multimodal_findings", {}),
                "agent1_gemini_raw_response": patient_full.get("agent1_gemini_raw", ""),   # Raw Gemini text
                "agent1_prompt_sent":        patient_full.get("agent1_prompt", ""),        # Prompt we sent
                "agent1_input_text":         patient_full.get("agent1_input_text", ""),   # Combined text input
                "agent1_full_output":        patient_full.get("agent1_output", {}),        # Complete dict

                # ── AGENT 2: Full Gemini Clinical Reasoning Output ────────
                # Triage decision + raw Gemini reasoning text + prompt
                "agent2_triage_color":       patient_full.get("triage_color", "Green"),
                "agent2_risk_score":         patient_full.get("risk_score", 0.5),
                "agent2_clinical_signals":   patient_full.get("clinical_signals", []),
                "agent2_red_flags":          patient_full.get("red_flags", []),
                "agent2_reasoning":          patient_full.get("reasoning", ""),
                "agent2_gemini_raw_response": patient_full.get("agent2_gemini_raw", ""),  # Raw Gemini text
                "agent2_prompt_sent":        patient_full.get("agent2_prompt", ""),       # Prompt we sent
                "agent2_full_output":        patient_full.get("agent2_output", {}),        # Complete dict

                # ── AGENT 3: Full Handoff & Routing Output ────────────────
                # Doctor assignment, department routing, ANM flow, surveillance data
                "agent3_assigned_doctor":    patient_full.get("assigned_doctor", "Unassigned"),
                "agent3_assigned_department": patient_full.get("assigned_department", "General"),
                "agent3_queue_position":     patient_full.get("queue_position", 999),
                "agent3_estimated_wait_mins": patient_full.get("estimated_wait_mins", 15),
                "agent3_requires_anm":       patient_full.get("requires_anm_confirmation", False),
                "agent3_routing_decision":   patient_full.get("routing_decision", ""),
                "agent3_full_output":        patient_full.get("agent3_output", {}),        # Complete dict

                # ── Pipeline Metadata ─────────────────────────────────────
                "session_id":            patient_full.get("session_id", ""),
                "agents_executed":       patient_full.get("agents_executed", []),

                # ── Cross-references (filled in by link_patient_to_collections) ──
                "queue_id":              None,     # → patient_queue/{queue_id}
                "surveillance_id":       None,     # → outbreak_surveillance/{surveillance_id}
            }

            doc_ref = self.db.collection(self.patients_collection).add(patient_record)
            firestore_patient_id = doc_ref[1].id

            triage_color = patient_full.get("triage_color", "Green")
            color_icon   = {"Red": "🔴", "Yellow": "🟡", "Green": "🟢"}.get(triage_color, "⚪")
            logger.info(f"✅ [PATIENTS] Full patient record written to `patients` collection:")
            logger.info(f"   ├─ firestore_patient_id    : {firestore_patient_id}")
            logger.info(f"   ├─ name                    : {patient_full.get('name', 'Unknown Patient')}")
            logger.info(f"   ├─ chief_complaint         : {patient_full.get('chief_complaint')}")
            logger.info(f"   ├─ triage_color            : {color_icon} {triage_color}")
            logger.info(f"   ├─ agent1_gemini_raw (len) : {len(patient_full.get('agent1_gemini_raw', ''))} chars")
            logger.info(f"   ├─ agent2_gemini_raw (len) : {len(patient_full.get('agent2_gemini_raw', ''))} chars")
            logger.info(f"   └─ severity                : {patient_full.get('severity')}")

            return firestore_patient_id

        except Exception as e:
            logger.error(f"[PATIENTS] Error writing patient record: {str(e)}")
            raise


    def link_patient_to_collections(
        self,
        firestore_patient_id: str,
        queue_id: str,
        surveillance_id: str
    ) -> bool:
        """
        After all three collections are written, go back and update the `patients`
        document with the cross-collection IDs so everything is linked.

        patients/{firestore_patient_id}
            └── queue_id        → patient_queue/{queue_id}
            └── surveillance_id → outbreak_surveillance/{surveillance_id}
        """
        try:
            self.db.collection(self.patients_collection).document(firestore_patient_id).update({
                "queue_id":        queue_id,
                "surveillance_id": surveillance_id,
                "linked_at":       datetime.now().isoformat(),
            })
            logger.info(f"✅ [PATIENTS] Cross-references linked on patient {firestore_patient_id}:")
            logger.info(f"   ├─ queue_id        → patient_queue/{queue_id}")
            logger.info(f"   └─ surveillance_id → outbreak_surveillance/{surveillance_id}")
            return True
        except Exception as e:
            logger.error(f"[PATIENTS] Error linking patient collections: {str(e)}")
            return False

    def add_patient_to_queue(self, patient_card: dict, firestore_patient_id: str = None) -> str:
        """
        Add patient to real-time `patient_queue` collection.

        Args:
            patient_card:          Patient data (triage color, doctor, department etc.)
            firestore_patient_id:  The canonical ID from `patients` collection.
                                   Stored here so queue entries can be traced back to patient record.
        Returns:
            queue_id — Firestore document ID in `patient_queue/`
        """
        try:
            queue_entry = {
                # Cross-reference back to `patients` collection
                "patient_id":          firestore_patient_id,   # ← THE LINK
                "name":                patient_card.get("name", "Unknown Patient"),  # ← ADD PATIENT NAME
                "chief_complaint":     patient_card.get("chief_complaint", ""),
                "symptoms":            patient_card.get("symptoms", []),
                "triage_color":        patient_card.get("triage_color", "Green"),
                "risk_score":          patient_card.get("risk_score", 0.5),
                "timestamp":           datetime.now().isoformat(),
                "queue_position":      patient_card.get("queue_position", 999),
                "estimated_wait_mins": patient_card.get("estimated_wait_mins", 15),
                "assigned_doctor":     patient_card.get("assigned_doctor", "Unassigned"),
                "assigned_department": patient_card.get("assigned_department", "General"),
                "status":              "waiting",
                "anm_notes":           "",
                "urgent_flag":         patient_card.get("triage_color") == "Red",
            }

            doc_ref  = self.db.collection(self.queue_collection).add(queue_entry)
            queue_id = doc_ref[1].id

            triage_color = patient_card.get("triage_color", "Green")
            color_icon   = {"Red": "🔴", "Yellow": "🟡", "Green": "🟢"}.get(triage_color, "⚪")
            logger.info(f"✅ [QUEUE] Patient added to `patient_queue`:")
            logger.info(f"   ├─ queue_id        : {queue_id}")
            logger.info(f"   ├─ patient_id (ref): {firestore_patient_id}")
            logger.info(f"   ├─ chief_complaint : {patient_card.get('chief_complaint')}")
            logger.info(f"   ├─ triage_color    : {color_icon} {triage_color}")
            logger.info(f"   ├─ assigned_doctor : {patient_card.get('assigned_doctor', 'Unassigned')}")
            logger.info(f"   └─ department      : {patient_card.get('assigned_department', 'General')}")

            return queue_id

        except Exception as e:
            logger.error(f"[QUEUE] Error adding patient to queue: {str(e)}")
            raise

    
    def update_patient_status(self, patient_id: str, status: str, notes: str = "") -> bool:
        """
        Update patient status in queue
        
        Args:
            patient_id: Patient document ID
            status: New status (waiting, in_consultation, completed)
            notes: Optional update notes
        
        Returns:
            Success boolean
        """
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.now().isoformat(),
            }
            
            if notes:
                update_data["anm_notes"] = notes
            
            self.db.collection(self.queue_collection).document(patient_id).update(update_data)
            logger.info(f"Patient {patient_id} status updated to: {status}")
            return True
        
        except Exception as e:
            logger.error(f"Error updating patient status: {str(e)}")
            return False
    
    def get_queue_by_priority(self) -> List[Dict]:
        """
        Get current queue sorted by priority (Red → Yellow → Green)
        
        Returns:
            List of patients ordered by triage priority
        """
        try:
            priority_order = {"Red": 0, "Yellow": 1, "Green": 2}
            
            # Get all waiting patients
            docs = (
                self.db.collection(self.queue_collection)
                .where("status", "==", "waiting")
                .stream()
            )
            
            patients = []
            for doc in docs:
                patient_data = doc.to_dict()
                patient_data["patient_id"] = doc.id
                patients.append(patient_data)
            
            # Sort by priority, then by timestamp
            patients.sort(
                key=lambda p: (
                    priority_order.get(p.get("triage_color", "Green"), 3),
                    p.get("timestamp", "")
                )
            )
            
            return patients
        
        except Exception as e:
            logger.error(f"Error retrieving queue: {str(e)}")
            return []
    
    def get_department_queue(self, department: str) -> List[Dict]:
        """Get queue for specific department"""
        try:
            docs = (
                self.db.collection(self.queue_collection)
                .where("assigned_department", "==", department)
                .where("status", "==", "waiting")
                .stream()
            )
            
            patients = []
            for doc in docs:
                patient_data = doc.to_dict()
                patient_data["patient_id"] = doc.id
                patients.append(patient_data)
            
            return patients
        
        except Exception as e:
            logger.error(f"Error retrieving department queue: {str(e)}")
            return []
    
    def listen_to_queue_changes(
        self, 
        callback: Callable,
        filter_status: str = "waiting"
    ) -> str:
        """
        Real-time listener for queue changes
        Triggers callback whenever queue is updated
        
        Args:
            callback: Function to call on changes - signature: callback(patients: List[Dict])
            filter_status: Status to filter by (default: "waiting")
        
        Returns:
            listener_id (for later unsubscribe)
        """
        try:
            listener_id = f"queue_listener_{datetime.now().timestamp()}"
            
            def on_snapshot(doc_snapshot, changes, read_time):
                """Firebase snapshot callback"""
                patients = []
                for doc in doc_snapshot:
                    patient_data = doc.to_dict()
                    patient_data["patient_id"] = doc.id
                    patients.append(patient_data)
                
                # Sort by priority
                priority_order = {"Red": 0, "Yellow": 1, "Green": 2}
                patients.sort(
                    key=lambda p: (
                        priority_order.get(p.get("triage_color", "Green"), 3),
                        p.get("timestamp", "")
                    )
                )
                
                red_count    = sum(1 for p in patients if p.get("triage_color") == "Red")
                yellow_count = sum(1 for p in patients if p.get("triage_color") == "Yellow")
                green_count  = sum(1 for p in patients if p.get("triage_color") == "Green")
                logger.info(f"📡 [QUEUE LISTENER] Real-time update received — "
                            f"total={len(patients)} (🔴{red_count} 🟡{yellow_count} 🟢{green_count})")
                callback(patients)
            
            # Set up listener
            query = (
                self.db.collection(self.queue_collection)
                .where("status", "==", filter_status)
            )
            
            listener = query.on_snapshot(on_snapshot)
            self.active_listeners[listener_id] = listener
            
            logger.info(f"Real-time queue listener started: {listener_id}")
            return listener_id
        
        except Exception as e:
            logger.error(f"Error setting up queue listener: {str(e)}")
            return None
    
    def stop_listening(self, listener_id: str) -> bool:
        """Stop real-time listener"""
        try:
            if listener_id in self.active_listeners:
                self.active_listeners[listener_id].unsubscribe()
                del self.active_listeners[listener_id]
                logger.info(f"Listener stopped: {listener_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error stopping listener: {str(e)}")
            return False
    
    def get_stats(self) -> Dict:
        """Get queue statistics"""
        try:
            queue = self.get_queue_by_priority()
            
            stats = {
                "total_waiting": len(queue),
                "red_count": len([p for p in queue if p.get("triage_color") == "Red"]),
                "yellow_count": len([p for p in queue if p.get("triage_color") == "Yellow"]),
                "green_count": len([p for p in queue if p.get("triage_color") == "Green"]),
                "avg_wait_time": sum(p.get("estimated_wait_mins", 0) for p in queue) / len(queue) if queue else 0,
                "timestamp": datetime.now().isoformat(),
            }
            
            return stats
        
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {}


# Singleton instance
_queue_manager = None

def get_queue_manager() -> FirebaseQueueManager:
    """Get or create queue manager singleton"""
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = FirebaseQueueManager()
    return _queue_manager
