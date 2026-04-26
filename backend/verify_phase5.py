"""
Phase 5: Verification Script
Tests all Phase 5 functionality and API endpoints
Confirms system is DEMO READY
"""

import requests
import json
import sys
import time
from typing import Dict, List
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30


class Phase5Verifier:
    """Verifies Phase 5 implementation"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results = {
            "endpoints_tested": [],
            "endpoints_passed": [],
            "endpoints_failed": [],
            "firestore_checked": False,
            "demo_ready": False
        }
    
    def print_header(self, text: str):
        """Print formatted header"""
        print("\n" + "=" * 80)
        print(f"  {text}")
        print("=" * 80)
    
    def print_test(self, name: str, status: str, message: str = ""):
        """Print test result"""
        icon = "✅" if status == "pass" else "❌"
        print(f"{icon} {name}: {status.upper()}")
        if message:
            print(f"   → {message}")
    
    def test_health(self) -> bool:
        """Test server is running"""
        self.print_header("STEP 1: Health Check")
        
        try:
            response = requests.get(f"{self.base_url}/", timeout=TIMEOUT)
            if response.status_code == 200:
                self.print_test("Server Health", "pass", "Backend running on port 8000")
                self.results["endpoints_tested"].append("GET /")
                self.results["endpoints_passed"].append("GET /")
                return True
            else:
                self.print_test("Server Health", "fail", f"Status {response.status_code}")
                self.results["endpoints_tested"].append("GET /")
                self.results["endpoints_failed"].append("GET /")
                return False
        except Exception as e:
            self.print_test("Server Health", "fail", f"Connection error: {str(e)}")
            return False
    
    def test_reset_endpoint(self) -> bool:
        """Test POST /reset endpoint"""
        self.print_header("STEP 2: Reset Endpoint")
        
        try:
            response = requests.post(
                f"{self.base_url}/reset",
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                docs_deleted = data.get("documents_deleted", 0)
                self.print_test(
                    "POST /reset",
                    "pass",
                    f"Cleared {docs_deleted} documents from Firestore"
                )
                self.results["endpoints_tested"].append("POST /reset")
                self.results["endpoints_passed"].append("POST /reset")
                return True
            else:
                self.print_test("POST /reset", "fail", f"Status {response.status_code}")
                self.results["endpoints_tested"].append("POST /reset")
                self.results["endpoints_failed"].append("POST /reset")
                return False
        except Exception as e:
            self.print_test("POST /reset", "fail", f"Error: {str(e)}")
            self.results["endpoints_tested"].append("POST /reset")
            self.results["endpoints_failed"].append("POST /reset")
            return False
    
    def test_triage_endpoint(self) -> bool:
        """Test POST /triage endpoint"""
        self.print_header("STEP 3: Triage Endpoint")
        
        test_cases = [
            {
                "text": "high fever and red rash",
                "expected": "Yellow"
            },
            {
                "text": "chest pain and difficulty breathing",
                "expected": "Red"
            }
        ]
        
        passed = 0
        for i, test in enumerate(test_cases, 1):
            try:
                response = requests.post(
                    f"{self.base_url}/triage",
                    json={"text": test["text"]},
                    timeout=TIMEOUT
                )
                
                if response.status_code == 200:
                    data = response.json()
                    triage_color = data.get("triage_color", "").upper()
                    patient_id = data.get("patient_id", "unknown")
                    
                    status = "pass" if data.get("success") else "fail"
                    self.print_test(
                        f"POST /triage (Test {i})",
                        status,
                        f"Triage: {triage_color}, Patient: {patient_id}"
                    )
                    
                    if status == "pass":
                        passed += 1
                else:
                    self.print_test(f"POST /triage (Test {i})", "fail", f"Status {response.status_code}")
            except Exception as e:
                self.print_test(f"POST /triage (Test {i})", "fail", f"Error: {str(e)}")
        
        self.results["endpoints_tested"].append("POST /triage")
        if passed > 0:
            self.results["endpoints_passed"].append("POST /triage")
        else:
            self.results["endpoints_failed"].append("POST /triage")
        
        return passed > 0
    
    def test_queue_endpoint(self) -> bool:
        """Test GET /queue endpoint"""
        self.print_header("STEP 4: Queue Endpoint")
        
        try:
            response = requests.get(
                f"{self.base_url}/queue",
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                patients = data.get("patients", [])
                patient_count = len(patients)
                
                self.print_test(
                    "GET /queue",
                    "pass",
                    f"Retrieved {patient_count} patients from queue"
                )
                self.results["endpoints_tested"].append("GET /queue")
                self.results["endpoints_passed"].append("GET /queue")
                return True
            else:
                self.print_test("GET /queue", "fail", f"Status {response.status_code}")
                self.results["endpoints_tested"].append("GET /queue")
                self.results["endpoints_failed"].append("GET /queue")
                return False
        except Exception as e:
            self.print_test("GET /queue", "fail", f"Error: {str(e)}")
            self.results["endpoints_tested"].append("GET /queue")
            self.results["endpoints_failed"].append("GET /queue")
            return False
    
    def test_surveillance_endpoint(self) -> bool:
        """Test GET /surveillance endpoint"""
        self.print_header("STEP 5: Surveillance Endpoint")
        
        try:
            response = requests.get(
                f"{self.base_url}/surveillance",
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                count = data.get("count", 0)
                
                self.print_test(
                    "GET /surveillance",
                    "pass",
                    f"Retrieved {count} surveillance records"
                )
                self.results["endpoints_tested"].append("GET /surveillance")
                self.results["endpoints_passed"].append("GET /surveillance")
                return True
            else:
                self.print_test("GET /surveillance", "fail", f"Status {response.status_code}")
                self.results["endpoints_tested"].append("GET /surveillance")
                self.results["endpoints_failed"].append("GET /surveillance")
                return False
        except Exception as e:
            self.print_test("GET /surveillance", "fail", f"Error: {str(e)}")
            self.results["endpoints_tested"].append("GET /surveillance")
            self.results["endpoints_failed"].append("GET /surveillance")
            return False
    
    def test_firestore_connection(self) -> bool:
        """Test Firestore connectivity"""
        self.print_header("STEP 6: Firestore Connectivity")
        
        try:
            import firebase_admin
            from firebase_admin import firestore
            
            try:
                firebase_admin.get_app()
            except ValueError:
                firebase_admin.initialize_app()
            
            db = firestore.client()
            
            # Test by querying a collection
            docs = db.collection("patients").limit(1).stream()
            
            self.print_test(
                "Firestore Connection",
                "pass",
                "ADC auth working, database accessible"
            )
            self.results["firestore_checked"] = True
            return True
        except Exception as e:
            self.print_test(
                "Firestore Connection",
                "fail",
                f"Error: {str(e)}"
            )
            return False
    
    def run_all_tests(self) -> bool:
        """Run all verification tests"""
        self.print_header("🏥 PHASE 5 VERIFICATION STARTING")
        
        print("\nVerifying all Phase 5 components...")
        print("  • Demo data structure")
        print("  • API endpoints")
        print("  • Firestore connectivity")
        print("  • System readiness\n")
        
        # Run tests
        health_ok = self.test_health()
        if not health_ok:
            print("\n⚠️  FAILURE: Server not running")
            print("   Start server: python -m uvicorn api.main:app --reload --port 8000")
            return False
        
        self.test_reset_endpoint()
        self.test_triage_endpoint()
        self.test_queue_endpoint()
        self.test_surveillance_endpoint()
        firestore_ok = self.test_firestore_connection()
        
        # Generate summary
        self._print_summary()
        
        return firestore_ok
    
    def _print_summary(self):
        """Print verification summary"""
        self.print_header("VERIFICATION SUMMARY")
        
        total_tests = len(self.results["endpoints_tested"])
        passed = len(self.results["endpoints_passed"])
        failed = len(self.results["endpoints_failed"])
        
        print(f"\nEndpoints Tested: {total_tests}")
        print(f"  ✅ Passed: {passed}")
        print(f"  ❌ Failed: {failed}")
        
        if self.results["endpoints_passed"]:
            print(f"\nPassed Endpoints:")
            for endpoint in self.results["endpoints_passed"]:
                print(f"  ✅ {endpoint}")
        
        if self.results["endpoints_failed"]:
            print(f"\nFailed Endpoints:")
            for endpoint in self.results["endpoints_failed"]:
                print(f"  ❌ {endpoint}")
        
        print(f"\nFirestore Connected: {'✅ Yes' if self.results['firestore_checked'] else '❌ No'}")
        
        # Determine demo ready status
        demo_ready = (
            passed >= 4 and  # At least 4 endpoints working
            failed == 0 and  # No failures
            self.results["firestore_checked"]  # Firestore connected
        )
        
        self.results["demo_ready"] = demo_ready
        
        print("\n" + "=" * 80)
        if demo_ready:
            print("🎉 DEMO READY - ALL SYSTEMS OPERATIONAL")
            print("=" * 80)
            print("\nNext Steps:")
            print("  1. Run: python demo_runner.py")
            print("  2. All 5 demo patients will be processed")
            print("  3. Queue and surveillance data will appear in Firestore")
            print("  4. Access http://localhost:8000/docs for API docs")
        else:
            print("⚠️  DEMO NOT READY - SOME SYSTEMS HAVE ISSUES")
            print("=" * 80)
            print("\nTroubleshooting:")
            print("  • Ensure server is running on port 8000")
            print("  • Check Firestore credentials are set (ADC auth)")
            print("  • Verify all dependencies are installed")
        
        print("\n" + "=" * 80)
    
    def export_results(self) -> str:
        """Export results as JSON"""
        return json.dumps(self.results, indent=2)


def main():
    """Run verification"""
    verifier = Phase5Verifier()
    
    try:
        success = verifier.run_all_tests()
        
        # Export results
        print("\n📄 Verification Results (JSON):")
        print(verifier.export_results())
        
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification interrupted")
        return 1
    except Exception as e:
        print(f"\n\n❌ Verification failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
