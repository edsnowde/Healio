"""
Fix missing patient names in patient_queue collection
Run this script to add name field to all documents that don't have it
"""

import firebase_admin
from firebase_admin import firestore
from datetime import datetime
import sys

# Initialize Firebase
try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app()

db = firestore.client()

def fix_patient_names():
    """
    Query all documents in patient_queue collection
    For documents missing 'name' field, assign a generated name
    """
    
    try:
        print("=" * 80)
        print("🔧 FIXING MISSING PATIENT NAMES IN patient_queue")
        print("=" * 80)
        
        # Get all documents from patient_queue collection
        docs = db.collection('patient_queue').stream()
        
        total_docs = 0
        missing_name_docs = 0
        updated_docs = 0
        
        for doc in docs:
            total_docs += 1
            data = doc.to_dict()
            
            # Check if 'name' field exists
            if 'name' not in data or not data.get('name'):
                missing_name_docs += 1
                
                # Generate a name using patient_id or a default
                patient_id = data.get('patient_id', 'Unknown')
                generated_name = f"Patient-{patient_id[:8]}" if patient_id != 'Unknown' else f"Patient-{doc.id[:8]}"
                
                # Update the document with the name
                db.collection('patient_queue').document(doc.id).update({
                    'name': generated_name,
                    'updated_at': datetime.now().isoformat(),
                    '_fixed_by_script': True
                })
                
                updated_docs += 1
                print(f"✅ Updated: {doc.id}")
                print(f"   └─ name set to: {generated_name}")
        
        print("=" * 80)
        print(f"📊 SUMMARY:")
        print(f"   Total documents scanned: {total_docs}")
        print(f"   Missing name field: {missing_name_docs}")
        print(f"   Successfully updated: {updated_docs}")
        print("=" * 80)
        
        if updated_docs > 0:
            print("✨ All missing names have been fixed!")
            print("   New patients will now display correctly on the dashboard")
        else:
            print("ℹ️  No documents needed updating - all have names!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = fix_patient_names()
    sys.exit(0 if success else 1)
