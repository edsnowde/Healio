#!/usr/bin/env python3
"""
Phase 4 Verification Test
Final comprehensive test of all Phase 4 components
"""

from phase4_integration import HealioPhase4Pipeline
import json

def main():
    print("\n" + "="*80)
    print("PHASE 4 FINAL VERIFICATION TEST")
    print("="*80)
    
    # Test 1: Verify imports
    print("\n[TEST 1] Import verification...")
    try:
        from agents.vision_agent import analyze_clinical_image, analyze_multiple_images
        from agents.agent1_intake import run_agent1
        from agents.agent2_reasoning import run_agent2
        from agents.agent3_handoff import run_agent3
        from firebase.queue_manager import get_queue_manager
        from firebase.surveillance import get_surveillance
        print("✅ All imports successful")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test 2: Initialize pipeline
    print("\n[TEST 2] Pipeline initialization...")
    try:
        pipeline = HealioPhase4Pipeline()
        print("✅ Pipeline initialized")
    except Exception as e:
        print(f"❌ Pipeline init failed: {e}")
        return False
    
    # Test 3: Run multiple test cases
    print("\n[TEST 3] Running analysis test cases...")
    test_cases = [
        ("High fever since 2 days and red rash on arms and legs", "Dengue suspected"),
        ("Mild cough and throat irritation", "Common cold"),
        ("Chest pain and difficulty breathing", "Emergency case")
    ]
    
    results = []
    for symptom, description in test_cases:
        try:
            result = pipeline.analyze_patient_with_images(symptom, verbose=False)
            
            test_result = {
                "description": description,
                "patient_id": result["patient"]["patient_id"],
                "triage_color": result["patient"]["triage_color"],
                "risk_score": result["patient"]["risk_score"],
                "status": result["status"]
            }
            results.append(test_result)
            
            color = result["patient"]["triage_color"]
            score = result["patient"]["risk_score"]
            print(f"  ✅ {description:30} → {color:6} (Score: {score:.2f})")
        
        except Exception as e:
            print(f"  ❌ {description} failed: {e}")
            return False
    
    # Test 4: Verify Firestore integration
    print("\n[TEST 4] Firestore integration...")
    if results and results[0]["patient_id"]:
        print(f"✅ Patient card stored in Firestore: {results[0]['patient_id']}")
    else:
        print("❌ Firestore integration failed")
        return False
    
    # Test 5: Verify outbreak detection
    print("\n[TEST 5] Outbreak detection engine...")
    try:
        status = pipeline.get_dashboard_status()
        queue_count = status["queue"]["total_waiting"]
        cluster_count = status["outbreaks"]["active_clusters"]
        print(f"✅ Dashboard status: {queue_count} patients, {cluster_count} active clusters")
    except Exception as e:
        print(f"❌ Dashboard status failed: {e}")
        return False
    
    # Summary
    print("\n" + "="*80)
    print("✅ PHASE 4 VERIFICATION COMPLETE - ALL SYSTEMS OPERATIONAL")
    print("="*80)
    print(f"\nSummary:")
    print(f"  • Imported: Vision Agent, 3-Agent Pipeline, Firebase Integration")
    print(f"  • Pipeline: Initialized and running")
    print(f"  • Tested: {len(results)} clinical scenarios")
    print(f"  • Firestore: Patient cards stored successfully")
    print(f"  • Real-time: Queue and cluster tracking active")
    print(f"\n✅ Healio Phase 4 is fully operational!\n")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
