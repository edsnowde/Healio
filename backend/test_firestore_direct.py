"""
Direct Firestore Diagnostic Test
Writes a document → reads it back → prints the exact console URL
Run: .\venv\Scripts\python test_firestore_direct.py
"""

import firebase_admin
from firebase_admin import firestore
from datetime import datetime

print("\n" + "=" * 60)
print("  FIRESTORE DIRECT WRITE TEST")
print("=" * 60)

# Step 1 - initialize
print("\n[1] Initializing Firebase...")
try:
    firebase_admin.get_app()
    print("    Firebase already initialized")
except ValueError:
    firebase_admin.initialize_app()
    print("    Firebase initialized fresh")

db = firestore.client()
print("    Firestore client created OK")

# Step 2 - write a test document
print("\n[2] Writing test document to Firestore...")
test_data = {
    "test": True,
    "message": "HEALIO DIRECT WRITE TEST",
    "chief_complaint": "blood oozing from wound",
    "triage_color": "Red",
    "risk_score": 0.95,
    "timestamp": datetime.now().isoformat(),
}

doc_ref = db.collection("patient_queue").add(test_data)
doc_id = doc_ref[1].id
print(f"    Document written! ID = {doc_id}")

# Step 3 - read it back immediately
print("\n[3] Reading it back from Firestore...")
read_back = db.collection("patient_queue").document(doc_id).get()
if read_back.exists:
    data = read_back.to_dict()
    print(f"    READ SUCCESS!")
    print(f"    chief_complaint : {data.get('chief_complaint')}")
    print(f"    triage_color    : {data.get('triage_color')}")
    print(f"    risk_score      : {data.get('risk_score')}")
    print(f"    timestamp       : {data.get('timestamp')}")
else:
    print("    ERROR: Document was written but cannot be read back!")

# Step 4 - print the exact Firestore console URL
print("\n[4] Open this URL in your browser to see the document:")
url = f"https://console.firebase.google.com/project/healio-494416/firestore/data/~2Fpatient_queue~2F{doc_id}"
print(f"\n    {url}\n")

print("=" * 60)
print("  If you see the document at that URL, Firestore IS working.")
print("  If not, you may be logged into the wrong Google account.")
print("=" * 60 + "\n")
