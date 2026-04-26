import firebase_admin
from firebase_admin import firestore
from datetime import datetime

firebase_admin.initialize_app()

db = firestore.client()

db.collection("test_collection").document("phase1_test").set({
    "status": "connected",
    "timestamp": datetime.now().isoformat()
})

doc = db.collection("test_collection").document("phase1_test").get()
print(doc.to_dict())
print("Firestore working!")