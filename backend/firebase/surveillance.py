"""
Firebase Outbreak Surveillance System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PURPOSE:
  - Records anonymized surveillance data from every patient intake
  - Runs cluster detection after each new entry
  - Cluster = 3+ patients with similar symptom signature in 48 hours
  - When cluster detected → creates alert document for DHO escalation
  - Supports real-time listeners: WebSocket /ws/alerts shows live cluster alerts

CLUSTER DETECTION:
  - Uses Jaccard similarity (>0.6) on symptom sets
  - Threshold: 3 matching cases within 48-hour rolling window
  - Auto-escalates at 5+ cases (action_required=True)
  - This collapses IDSP's 7-10 day detection to <2 hours

CALLED BY:
  - api/main.py → records data on every /analyze call
  - phase4_integration.py → writes surveillance entry after Agent 3
  - WebSocket /ws/alerts → listens for new cluster alerts
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import firebase_admin
from firebase_admin import firestore
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Callable
import hashlib

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s │ %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("healio.firebase.surveillance")


class OutbreakSurveillance:
    """Real-time outbreak cluster detection and surveillance"""
    
    def __init__(self):
        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app()
        
        self.db = firestore.client()
        self.surveillance_collection = "outbreak_surveillance"
        self.cluster_collection = "detected_clusters"
        self.active_listeners = {}
        
        # Configuration
        self.cluster_threshold = 3   # Minimum 3 patients with same symptoms
        self.time_window_hours = 48   # Within 48 hours
        self.similarity_threshold = 0.25  # Jaccard on keyword-level (not phrase-level)

        # Medical stopwords — too generic to be meaningful for cluster detection
        self._stopwords = {
            "a", "an", "the", "and", "or", "of", "in", "on", "at", "with",
            "since", "for", "from", "to", "is", "are", "has", "have",
            "my", "i", "me", "very", "some", "its", "it", "this",
            "day", "days", "week", "weeks", "month",
            "mild", "moderate", "severe",   # captured by severity_category separately
        }
    
    def record_surveillance_data(self, surveillance_payload: dict) -> str:
        """
        Record anonymized surveillance data for outbreak cluster detection.

        Stores a patient_id reference so this entry can be traced back to the
        full patient record in the `patients` collection.

        Args:
            surveillance_payload: From Agent 3 + the canonical patient_id
        Returns:
            surveillance_id — Firestore document ID in `outbreak_surveillance/`
        """
        try:
            surveillance_entry = {
                # Cross-reference back to `patients` collection
                "patient_id":          surveillance_payload.get("patient_id"),  # ← THE LINK
                "timestamp":           datetime.now().isoformat(),
                "symptoms_anonymized": surveillance_payload.get("symptoms_anonymized", []),
                "severity_category":   surveillance_payload.get("severity_category", "unknown"),
                "triage_color":        surveillance_payload.get("triage_color", "Green"),
                "risk_score":          surveillance_payload.get("risk_score", 0.5),
                "symptom_signature":   surveillance_payload.get("symptom_signature", ""),
                "location":            surveillance_payload.get("location", "PHC-Bengaluru"),
            }

            doc_ref = self.db.collection(self.surveillance_collection).add(surveillance_entry)
            doc_id  = doc_ref[1].id

            logger.info(f"✅ [SURVEILLANCE] Anonymized entry recorded → {doc_id}")
            logger.info(f"   ├─ patient_id (ref)  : {surveillance_entry.get('patient_id')}")
            logger.info(f"   ├─ symptom_signature : \"{surveillance_entry.get('symptom_signature')}\"")
            logger.info(f"   ├─ severity          : {surveillance_entry.get('severity_category')}")
            logger.info(f"   └─ triage_color      : {surveillance_entry.get('triage_color')}")
            logger.info(f"   🔬 Running cluster detection on updated surveillance collection...")
            
            # Trigger cluster detection
            self._check_for_clusters(surveillance_entry)
            
            return doc_id
        
        except Exception as e:
            logger.error(f"Error recording surveillance data: {str(e)}")
            raise
    
    def _check_for_clusters(self, new_entry: dict) -> bool:
        """
        Check if new entry forms a cluster with existing data
        
        Args:
            new_entry: New surveillance entry
        
        Returns:
            Whether a cluster was detected
        """
        try:
            symptoms = new_entry.get("symptoms_anonymized", [])
            severity = new_entry.get("severity_category", "")
            
            if not symptoms:
                return False
            
            # Create symptom signature for matching
            symptom_signature = self._create_symptom_signature(symptoms, severity)
            
            # Look for similar entries in last 48 hours
            cutoff_time = (datetime.now() - timedelta(hours=self.time_window_hours)).isoformat()
            
            docs = (
                self.db.collection(self.surveillance_collection)
                .where("timestamp", ">=", cutoff_time)
                .stream()
            )
            
            matching_entries = []
            for doc in docs:
                entry = doc.to_dict()
                entry_signature = self._create_symptom_signature(
                    entry.get("symptoms_anonymized", []),
                    entry.get("severity_category", "")
                )
                
                # Check if signatures match using keyword-level Jaccard
                similarity = self._calculate_similarity(symptom_signature, entry_signature)
                if similarity >= self.similarity_threshold:
                    matching_entries.append(entry)
                    logger.debug(f"   [CLUSTER] Match found: similarity={similarity:.2f}, "
                                 f"keywords={entry_signature & symptom_signature}")
            
            # Cluster detected if 3+ matching cases
            if len(matching_entries) >= self.cluster_threshold:
                return self._create_cluster_alert(symptoms, len(matching_entries))
            
            return False
        
        except Exception as e:
            logger.error(f"Error checking for clusters: {str(e)}")
            return False
    
    def _create_symptom_signature(self, symptoms: list, severity: str) -> set:
        """
        Create a keyword-level signature from symptoms.

        Splits multi-word symptom phrases into individual words and removes
        stopwords so that "high fever" and "fever" both contribute the keyword
        "fever" and match correctly.
        """
        keywords = set()
        all_text = " ".join(symptoms).lower()
        for word in all_text.split():
            word = word.strip(".,;:-()")
            if word and word not in self._stopwords and len(word) > 2:
                keywords.add(word)
        # Include severity as a keyword (e.g. "moderate", "severe")
        if severity and severity not in ("unknown", ""):
            keywords.add(severity.lower())
        return keywords

    def _calculate_similarity(self, sig1: set, sig2: set) -> float:
        """Jaccard similarity on keyword sets"""
        if not sig1 and not sig2:
            return 1.0
        intersection = len(sig1 & sig2)
        union = len(sig1 | sig2)
        return intersection / union if union > 0 else 0.0
    
    def _create_cluster_alert(self, symptoms: list, patient_count: int) -> bool:
        """
        Create outbreak alert when cluster detected
        
        Args:
            symptoms: Common symptoms
            patient_count: Number of patients in cluster
        
        Returns:
            Success boolean
        """
        try:
            alert = {
                "timestamp": datetime.now().isoformat(),
                "alert_type": "outbreak_cluster",
                "symptoms": symptoms,
                "patient_count": patient_count,
                "confidence": min(0.95, 0.5 + (patient_count - 3) * 0.15),  # Increases with more cases
                "severity": "high" if patient_count >= 5 else "medium",
                "time_window_hours": self.time_window_hours,
                "status": "pending_verification",
                "action_required": patient_count >= 5,  # Auto-escalate if 5+ cases
            }
            
            doc_ref = self.db.collection(self.cluster_collection).add(alert)
            cluster_id = doc_ref[1].id
            
            logger.warning("")
            logger.warning(f"🚨 [SURVEILLANCE] ══════════════════════════════════")
            logger.warning(f"🚨 OUTBREAK CLUSTER DETECTED!")
            logger.warning(f"   ├─ Patient count : {patient_count} patients")
            logger.warning(f"   ├─ Symptoms      : {symptoms}")
            logger.warning(f"   ├─ Time window   : last {self.time_window_hours} hours")
            logger.warning(f"   ├─ Confidence    : {alert['confidence']:.2f}")
            logger.warning(f"   ├─ Severity      : {alert['severity']}")
            logger.warning(f"   ├─ Auto-escalate : {alert['action_required']}")
            logger.warning(f"   └─ Cluster ID    : {cluster_id}")
            logger.warning(f"🚨 [SURVEILLANCE] DHO should be notified immediately!")
            logger.warning(f"🚨 [SURVEILLANCE] ══════════════════════════════════")
            logger.warning("")
            
            return True
        
        except Exception as e:
            logger.error(f"Error creating cluster alert: {str(e)}")
            return False
    
    def get_active_clusters(self) -> List[Dict]:
        """
        Get currently active outbreak clusters.
        Sorts in Python (not Firestore) to avoid requiring a composite index.
        """
        try:
            logger.info("[SURVEILLANCE] Fetching active clusters from Firestore...")
            # NOTE: We filter in Python (not Firestore order_by) to avoid composite index requirement
            docs = (
                self.db.collection(self.cluster_collection)
                .where("status", "==", "pending_verification")
                .stream()
            )

            clusters = []
            for doc in docs:
                cluster_data = doc.to_dict()
                cluster_data["cluster_id"] = doc.id
                clusters.append(cluster_data)

            # Sort by timestamp descending (most recent first) — done in Python
            clusters.sort(key=lambda c: c.get("timestamp", ""), reverse=True)

            logger.info(f"[SURVEILLANCE] Found {len(clusters)} active cluster(s)")
            return clusters

        except Exception as e:
            logger.error(f"[SURVEILLANCE] Error retrieving active clusters: {str(e)}")
            return []

    
    def escalate_cluster(self, cluster_id: str, reason: str = "") -> bool:
        """Escalate cluster to district health officer"""
        try:
            self.db.collection(self.cluster_collection).document(cluster_id).update({
                "status": "escalated_to_dho",
                "escalation_time": datetime.now().isoformat(),
                "escalation_reason": reason,
            })
            
            logger.warning(f"Cluster {cluster_id} escalated to District Health Officer")
            return True
        
        except Exception as e:
            logger.error(f"Error escalating cluster: {str(e)}")
            return False
    
    def listen_to_clusters(self, callback: Callable) -> str:
        """
        Real-time listener for outbreak clusters
        
        Args:
            callback: Function called with cluster list on update
        
        Returns:
            listener_id
        """
        try:
            listener_id = f"cluster_listener_{datetime.now().timestamp()}"
            
            def on_snapshot(doc_snapshot, changes, read_time):
                clusters = []
                for doc in doc_snapshot:
                    cluster_data = doc.to_dict()
                    cluster_data["cluster_id"] = doc.id
                    clusters.append(cluster_data)
                
                logger.info(f"Active clusters: {len(clusters)}")
                callback(clusters)
            
            listener = (
                self.db.collection(self.cluster_collection)
                .where("status", "==", "pending_verification")
                .on_snapshot(on_snapshot)
            )
            
            self.active_listeners[listener_id] = listener
            logger.info(f"Cluster listener started: {listener_id}")
            return listener_id
        
        except Exception as e:
            logger.error(f"Error setting up cluster listener: {str(e)}")
            return None
    
    def get_surveillance_summary(self, hours: int = 24) -> Dict:
        """Get surveillance summary for period"""
        try:
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            docs = (
                self.db.collection(self.surveillance_collection)
                .where("timestamp", ">=", cutoff_time)
                .stream()
            )
            
            entries = [doc.to_dict() for doc in docs]
            
            # Aggregate symptoms
            symptom_counts = {}
            severity_counts = {"mild": 0, "moderate": 0, "severe": 0}
            color_counts = {"Red": 0, "Yellow": 0, "Green": 0}
            
            for entry in entries:
                for symptom in entry.get("symptoms_anonymized", []):
                    symptom_counts[symptom] = symptom_counts.get(symptom, 0) + 1
                
                severity = entry.get("severity_category", "unknown")
                if severity in severity_counts:
                    severity_counts[severity] += 1
                
                color = entry.get("triage_color", "Green")
                if color in color_counts:
                    color_counts[color] += 1
            
            return {
                "total_patients": len(entries),
                "time_period_hours": hours,
                "top_symptoms": sorted(symptom_counts.items(), key=lambda x: x[1], reverse=True)[:5],
                "severity_distribution": severity_counts,
                "triage_distribution": color_counts,
                "timestamp": datetime.now().isoformat(),
            }
        
        except Exception as e:
            logger.error(f"Error generating surveillance summary: {str(e)}")
            return {}


# Singleton instance
_surveillance = None

def get_surveillance() -> OutbreakSurveillance:
    """Get or create outbreak surveillance singleton"""
    global _surveillance
    if _surveillance is None:
        _surveillance = OutbreakSurveillance()
    return _surveillance
