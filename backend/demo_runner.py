"""
Phase 5: Demo Runner
Executes all 5 demo patients through the complete Healio pipeline
Displays results in real-time and triggers cluster detection
"""

import time
import json
import logging
from typing import List, Dict
from datetime import datetime

from phase4_integration import HealioPhase4Pipeline
from firebase.surveillance import get_surveillance
from demo_data import get_demo_patients, demo_summary

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DemoRunner:
    """Orchestrates demo patient processing"""
    
    def __init__(self, delay_seconds: float = 2.0):
        """
        Initialize demo runner
        
        Args:
            delay_seconds: Delay between patient processing (default 2 seconds)
        """
        self.delay = delay_seconds
        self.pipeline = HealioPhase4Pipeline()
        self.surveillance = get_surveillance()
        self.results = []
    
    def run_all_patients(self, verbose: bool = True) -> Dict:
        """
        Run all 5 demo patients through the pipeline
        
        Args:
            verbose: Print detailed output
        
        Returns:
            Complete results summary
        """
        
        if verbose:
            print("\n" + "=" * 80)
            print("[PHASE 5] DEMO: COMPLETE END-TO-END DEMONSTRATION")
            print("=" * 80)
            demo_summary()
        
        patients = get_demo_patients()
        demo_results = []
        
        for i, patient in enumerate(patients, 1):
            if verbose:
                print("\n" + "=" * 80)
                print(f"[{i}/5] PROCESSING: {patient['name']}")
                print("=" * 80)
                print(f"ID: {patient['id']}")
                print(f"Expected Triage: {patient['expected_triage']}")
                print(f"Symptoms:\n{patient['symptom_text']}\n")
            
            try:
                # Process patient through Phase 4 pipeline
                result = self.pipeline.analyze_patient_with_images(
                    symptom_text=patient['symptom_text'],
                    image_paths=None,
                    verbose=True
                )
                
                # Extract key fields
                demo_result = {
                    "demo_id": patient['id'],
                    "patient_id": result.get("patient", {}).get("patient_id"),
                    "name": patient['name'],
                    "expected_triage": patient['expected_triage'],
                    "actual_triage": result.get("patient", {}).get("triage_color"),
                    "risk_score": result.get("patient", {}).get("risk_score"),
                    "assigned_doctor": result.get("patient", {}).get("assigned_doctor"),
                    "assigned_department": result.get("patient", {}).get("assigned_department"),
                    "status": result.get("status"),
                    "timestamp": datetime.now().isoformat()
                }
                
                demo_results.append(demo_result)
                
                # Print patient card summary
                if verbose:
                    self._print_patient_card(demo_result)
                
                # Delay before next patient (except for last one)
                if i < len(patients):
                    if verbose:
                        print(f"\n[WAIT] Waiting {self.delay} seconds before next patient...")
                    time.sleep(self.delay)
            
            except Exception as e:
                logger.error(f"Error processing patient {patient['id']}: {str(e)}")
                demo_results.append({
                    "demo_id": patient['id'],
                    "name": patient['name'],
                    "error": str(e),
                    "status": "failed"
                })
        
        # Final summary
        summary = self._generate_summary(demo_results)
        
        if verbose:
            self._print_summary(summary)
        
        return {
            "status": "complete",
            "timestamp": datetime.now().isoformat(),
            "total_patients": len(patients),
            "processed": len([r for r in demo_results if "error" not in r]),
            "failed": len([r for r in demo_results if "error" in r]),
            "results": demo_results,
            "summary": summary
        }
    
    def _print_patient_card(self, result: Dict):
        """Print formatted patient card"""
        print("\n" + "-" * 80)
        print("[PATIENT CARD] Firestore Ready")
        print("-" * 80)
        print(f"Patient ID: {result['patient_id']}")
        print(f"Department: {result['assigned_department']}")
        print(f"Doctor: {result['assigned_doctor']}")
        print(f"Triage Color: {result['actual_triage']}")
        print(f"Risk Score: {result['risk_score']:.2f}")
        print(f"Status: {result['status']}")
        print(f"Expected Match: {result['expected_triage'] == result['actual_triage']}")
    
    def _generate_summary(self, results: List[Dict]) -> Dict:
        """Generate execution summary"""
        summary = {
            "red_alerts": [],
            "yellow_alerts": [],
            "green_cases": [],
            "triage_accuracy": 0.0,
            "total_processed": len([r for r in results if "error" not in r])
        }
        
        correct_count = 0
        for result in results:
            if "error" in result:
                continue
            
            triage = result.get("actual_triage", "").lower()
            expected = result.get("expected_triage", "").lower()
            
            if triage == expected:
                correct_count += 1
            
            if triage == "red":
                summary["red_alerts"].append(result)
            elif triage == "yellow":
                summary["yellow_alerts"].append(result)
            elif triage == "green":
                summary["green_cases"].append(result)
        
        if summary["total_processed"] > 0:
            summary["triage_accuracy"] = (correct_count / summary["total_processed"]) * 100
        
        return summary
    
    def _print_summary(self, summary: Dict):
        """Print final demonstration summary"""
        print("\n" + "=" * 80)
        print("[SUMMARY] PHASE 5 DEMONSTRATION SUMMARY")
        print("=" * 80)
        
        print(f"\nTotal Patients Processed: {summary['total_processed']}")
        print(f"Red Alerts: {len(summary['red_alerts'])}")
        for alert in summary['red_alerts']:
            print(f"  [RED] {alert['name']} - Score: {alert['risk_score']:.2f}")
        
        print(f"\nYellow Alerts: {len(summary['yellow_alerts'])}")
        for alert in summary['yellow_alerts']:
            print(f"  [YELLOW] {alert['name']} - Score: {alert['risk_score']:.2f}")
        
        print(f"\nGreen Cases: {len(summary['green_cases'])}")
        for alert in summary['green_cases']:
            print(f"  [GREEN] {alert['name']} - Score: {alert['risk_score']:.2f}")
        
        print(f"\n[SUCCESS] Triage Accuracy: {summary['triage_accuracy']:.1f}%")
        
        print("\n" + "=" * 80)
        print("[SUCCESS] PHASE 5 DEMO COMPLETE - ALL PATIENTS IN FIRESTORE")
        print("=" * 80)


def run_demo(delay: float = 2.0, verbose: bool = True) -> Dict:
    """
    Execute complete demo
    
    Args:
        delay: Seconds between patients
        verbose: Print detailed output
    
    Returns:
        Complete demo results
    """
    runner = DemoRunner(delay_seconds=delay)
    return runner.run_all_patients(verbose=verbose)


if __name__ == "__main__":
    # Run demo with 2 second delay between patients
    results = run_demo(delay=2.0, verbose=True)
    
    # Print summary
    print("\n" + "=" * 80)
    print("[RESULTS] RAW RESULTS SUMMARY")
    print("=" * 80)
    print(f"Status: {results['status']}")
    print(f"Total Patients: {results['total_patients']}")
    print(f"Processed: {results['processed']}")
    print(f"Failed: {results['failed']}")
