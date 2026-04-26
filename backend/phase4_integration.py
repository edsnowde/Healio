"""
Phase 4: Connect Everything
Integrates all components:
- Push patient cards to Firestore
- Cluster detection for outbreak alerts
- Gemini Vision image analysis integration
- Complete end-to-end pipeline with real-time Firebase updates

This module orchestrates the complete Healio system
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, List

import firebase_admin
from firebase_admin import firestore

from agents.agent1_intake import run_agent1
from agents.agent2_reasoning import run_agent2
from agents.agent3_handoff import run_agent3
from agents.vision_agent import analyze_clinical_image, analyze_multiple_images
from firebase.queue_manager import get_queue_manager
from firebase.surveillance import get_surveillance

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HealioPhase4Pipeline:
    """Complete Phase 4 pipeline with all integrations"""
    
    def __init__(self):
        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app()
        
        self.db = firestore.client()
        self.queue_manager = get_queue_manager()
        self.surveillance = get_surveillance()
    
    def analyze_patient_with_images(
        self,
        symptom_text: str,
        audio_transcript: Optional[str] = None,
        image_paths: Optional[List[str]] = None,
        verbose: bool = True
    ) -> dict:
        """
        Complete patient analysis with multimodal input
        
        Args:
            symptom_text: Patient symptoms
            audio_transcript: Kannada/Hindi transcription (optional)
            image_paths: Clinical image paths for Vision analysis (optional)
            verbose: Print detailed output
        
        Returns:
            Complete result with Firestore patient_id and outbreak alerts
        """
        
        if verbose:
            print("\n" + "=" * 80)
            print("🏥 HEALIO PHASE 4: COMPLETE INTEGRATION PIPELINE")
            print("=" * 80)
        
        # ============================================================
        # STEP 1: VISION ANALYSIS (if images provided)
        # ============================================================
        vision_findings = {}
        if image_paths:
            if verbose:
                print(f"\n[VISION] 📸 Analyzing {len(image_paths)} clinical image(s)...")
                print("-" * 80)
            
            vision_findings = analyze_multiple_images(image_paths)
            
            if vision_findings.get("images_analyzed", 0) > 0:
                if verbose:
                    print(f"✅ Analyzed {vision_findings['images_analyzed']} images")
                    print(f"   Conditions: {vision_findings.get('all_conditions', [])}")
                    print(f"   Severity: {vision_findings.get('max_severity')}")
                    print(f"   Confidence: {vision_findings.get('overall_confidence', 0):.2f}")
        
        # ============================================================
        # AGENT 1: MULTIMODAL INTAKE
        # ============================================================
        if verbose:
            print(f"\n[AGENT 1] 🎤 Multimodal Intake Agent")
            print(f"Input: '{symptom_text[:60]}...'")
            print("-" * 80)
        
        patient_data = run_agent1(
            symptom_text=symptom_text,
            audio_transcript=audio_transcript,
            image_paths=image_paths
        )
        
        if verbose:
            print(f"✅ Chief Complaint: {patient_data.get('chief_complaint')}")
            print(f"   Symptoms: {patient_data.get('symptoms')}")
            print(f"   Multimodal Findings: {bool(patient_data.get('multimodal_findings'))}")
        
        # ============================================================
        # AGENT 2: CLINICAL REASONING (enriched with Vision)
        # ============================================================
        if verbose:
            print(f"\n[AGENT 2] 🔬 Clinical Reasoning Agent")
            print("Applying two-layer safety (confidence scoring + multi-signal gating)")
            print("-" * 80)
        
        # Optionally enrich Agent 2 input with Vision findings
        if vision_findings.get("images_analyzed", 0) > 0:
            patient_data["vision_insights"] = {
                "conditions": vision_findings.get("all_conditions", []),
                "severity": vision_findings.get("max_severity"),
                "confidence": vision_findings.get("overall_confidence"),
                "red_flags": vision_findings.get("all_red_flags", [])
            }
        
        triage_result = run_agent2(patient_data)
        
        if verbose:
            print(f"✅ Risk Score: {triage_result.get('risk_score'):.2f}")
            print(f"   Triage Color: {triage_result.get('triage_color')}")
            print(f"   Signals: {triage_result.get('clinical_signals')}")
        
        # ============================================================
        # AGENT 3: HANDOFF & SURVEILLANCE
        # ============================================================
        if verbose:
            print(f"\n[AGENT 3] 📋 Handoff & Surveillance Agent")
            print("-" * 80)
        
        handoff_payload = run_agent3(patient_data, triage_result)
        patient_card = handoff_payload["patient_card"]
        
        if verbose:
            print(f"✅ Patient Card Generated")
            print(f"   Department: {patient_card.get('assigned_department')}")
            print(f"   Doctor: {patient_card.get('assigned_doctor')}")
            print(f"   Queue Position: {patient_card.get('queue_position')}")
        
        # ============================================================
        # FIRESTORE: PUSH PATIENT CARD
        # ============================================================
        if verbose:
            print(f"\n[FIRESTORE] 💾 Pushing to Database")
            print("-" * 80)
        
        patient_id = self._push_to_firestore(handoff_payload, image_paths)
        
        if verbose:
            print(f"✅ Pushed to Firestore")
            print(f"   Patient ID: {patient_id}")
            print(f"   Collection: patients/{patient_id}")
        
        # ============================================================
        # FIREBASE QUEUE: ADD TO REAL-TIME QUEUE
        # ============================================================
        if verbose:
            print(f"\n[QUEUE] 📊 Adding to Real-Time Queue")
            print("-" * 80)
        
        queue_id = self.queue_manager.add_patient_to_queue(patient_card)
        
        if verbose:
            print(f"✅ Added to queue")
            print(f"   Queue ID: {queue_id}")
            print(f"   Priority: {handoff_payload.get('queue_priority')}")
        
        # ============================================================
        # SURVEILLANCE: RECORD DATA + CHECK CLUSTERS
        # ============================================================
        if verbose:
            print(f"\n[SURVEILLANCE] 🔍 Recording & Checking Clusters")
            print("-" * 80)
        
        surveillance_id = self.surveillance.record_surveillance_data(
            handoff_payload["surveillance_data"]
        )
        
        # Check for outbreak clusters
        clusters = self.surveillance.get_active_clusters()
        outbreak_alerts = []
        
        if clusters:
            for cluster in clusters:
                outbreak_alerts.append({
                    "cluster_id": cluster.get("cluster_id"),
                    "symptoms": cluster.get("symptoms"),
                    "patient_count": cluster.get("patient_count"),
                    "severity": cluster.get("severity"),
                    "action_required": cluster.get("action_required", False)
                })
            
            if verbose:
                print(f"🚨 OUTBREAK CLUSTERS DETECTED: {len(clusters)}")
                for alert in outbreak_alerts:
                    print(f"   ⚠️  {alert['patient_count']} patients - {alert['symptoms']}")
        else:
            if verbose:
                print(f"✅ No outbreak clusters detected")
        
        # ============================================================
        # COMPLETE RESULT
        # ============================================================
        complete_result = {
            "status": "success",
            "phase": "Phase 4",
            "timestamp": datetime.now().isoformat(),
            "patient": {
                "patient_id": patient_id,
                "firestore_id": patient_id,
                "queue_id": queue_id,
                "surveillance_id": surveillance_id,
                "chief_complaint": patient_card.get("chief_complaint"),
                "triage_color": patient_card.get("triage_color"),
                "risk_score": patient_card.get("risk_score"),
                "assigned_doctor": patient_card.get("assigned_doctor"),
                "assigned_department": patient_card.get("assigned_department")
            },
            "vision": {
                "images_analyzed": vision_findings.get("images_analyzed", 0),
                "conditions": vision_findings.get("all_conditions", []),
                "severity": vision_findings.get("max_severity", "unknown"),
                "confidence": vision_findings.get("overall_confidence", 0.0)
            },
            "outbreak_alerts": outbreak_alerts,
            "requires_anm_confirmation": handoff_payload.get("requires_anm_confirmation", False),
            "anm_message": patient_card.get("anm_confirmation_message", "")
        }
        
        if verbose:
            print("\n" + "=" * 80)
            print("✅ PHASE 4 COMPLETE - PATIENT FULLY INTEGRATED")
            print("=" * 80)
            print(json.dumps(complete_result, indent=2))
        
        return complete_result
    
    def _push_to_firestore(self, handoff_payload: dict, image_paths: Optional[List[str]] = None) -> str:
        """
        Push patient card to Firestore with vision data
        
        Args:
            handoff_payload: Complete handoff from Agent 3
            image_paths: Paths to analyzed images (optional)
        
        Returns:
            patient_id (document ID in Firestore)
        """
        
        try:
            patient_id = str(uuid.uuid4())[:12]
            patient_card = handoff_payload["patient_card"]
            surveillance_data = handoff_payload["surveillance_data"]
            
            # Add metadata
            patient_card["firestore_id"] = patient_id
            patient_card["images_analyzed"] = len(image_paths) if image_paths else 0
            
            # Push patient card to Firestore
            self.db.collection("patients").document(patient_id).set(patient_card)
            
            # Push surveillance data
            self.db.collection("surveillance").document(patient_id).set(surveillance_data)
            
            # Push queue entry
            queue_entry = {
                "patient_id": patient_id,
                "triage_color": patient_card.get("triage_color"),
                "queue_position": patient_card.get("queue_position"),
                "timestamp": datetime.now().isoformat(),
                "status": "waiting"
            }
            self.db.collection("queue").document(patient_id).set(queue_entry)
            
            logger.info(f"✅ Patient {patient_id} pushed to Firestore")
            
            return patient_id
        
        except Exception as e:
            logger.error(f"Error pushing to Firestore: {str(e)}")
            raise
    
    def get_dashboard_status(self) -> dict:
        """Get real-time dashboard status"""
        
        try:
            queue = self.queue_manager.get_queue_by_priority()
            clusters = self.surveillance.get_active_clusters()
            stats = self.queue_manager.get_stats()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "queue": {
                    "total_waiting": len(queue),
                    "patients": queue,
                    "stats": stats
                },
                "outbreaks": {
                    "active_clusters": len(clusters),
                    "clusters": clusters
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting dashboard status: {str(e)}")
            return {"error": str(e)}


# Convenience functions
def run_phase4_analysis(symptom_text: str, image_paths: Optional[List[str]] = None) -> dict:
    """Quick wrapper to run Phase 4 analysis"""
    pipeline = HealioPhase4Pipeline()
    return pipeline.analyze_patient_with_images(symptom_text, image_paths=image_paths)


if __name__ == "__main__":
    # Phase 4 Integration Example
    
    print("🏥 Healio Phase 4: Complete Integration Test\n")
    
    # Test case
    symptom_text = "I have high fever since 2 days and red rash on my arms and legs"
    
    # Create pipeline
    pipeline = HealioPhase4Pipeline()
    
    # Run complete analysis
    result = pipeline.analyze_patient_with_images(
        symptom_text=symptom_text,
        image_paths=None,  # Add image paths if you have test images
        verbose=True
    )
    
    print("\n" + "=" * 80)
    print("FINAL RESULT")
    print("=" * 80)
    print(json.dumps(result, indent=2))
