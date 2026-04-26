"""
Phase 5: Demo Data Generator
Creates 5 realistic patient profiles for end-to-end Healio demonstration
Includes Red alerts, Yellow warnings, and Green cases
"""

DEMO_PATIENTS = [
    {
        "id": "DEMO001",
        "name": "Patient A - Meningitis Suspected",
        "symptom_text": "I have been feeling very sick for 2 days. High fever of 39.5°C, severe headache, neck stiffness, and I have a red rash with petechiae (small purple spots) all over my body. I feel nauseous and have been vomiting. This started suddenly after a fever at night.",
        "expected_triage": "Red",
        "clinical_significance": "Meningitis/sepsis red flag - fever + rash + petechiae + neck stiffness"
    },
    {
        "id": "DEMO002",
        "name": "Patient B - Cardiac Emergency",
        "symptom_text": "I am experiencing severe chest pain that radiates to my left arm. I am having difficulty breathing and feel like I might collapse. My heart is racing and I feel sweaty. This started 30 minutes ago while I was resting. I have a history of high blood pressure.",
        "expected_triage": "Red",
        "clinical_significance": "Acute coronary syndrome - chest pain + dyspnea + radiation + diaphoresis + risk factors"
    },
    {
        "id": "DEMO003",
        "name": "Patient C - Dengue Fever",
        "symptom_text": "I have had high fever for 4 days, reaching 38.8°C. I have severe joint pain and muscle aches throughout my body. I developed a red rash on my face and arms yesterday. I also have a headache behind my eyes and feel very tired.",
        "expected_triage": "Yellow",
        "clinical_significance": "Dengue fever - high fever + arthralgia + myalgia + rash + headache"
    },
    {
        "id": "DEMO004",
        "name": "Patient D - Common Viral Illness",
        "symptom_text": "I have had a mild cough for 2 days and a slight sore throat. I don't have fever. I feel a bit tired but otherwise okay. It's just a scratchy feeling in my throat.",
        "expected_triage": "Green",
        "clinical_significance": "Upper respiratory infection - mild symptoms, no fever, low risk"
    },
    {
        "id": "DEMO005",
        "name": "Patient E - Moderate Gastroenteritis",
        "symptom_text": "I have been having loose stools for 1 day and mild abdominal cramps. I have a low-grade fever of 37.8°C. I feel a bit weak and have lost appetite. No vomiting or blood in stool.",
        "expected_triage": "Yellow",
        "clinical_significance": "Gastroenteritis - diarrhea + mild fever + weakness, needs monitoring"
    }
]


def get_demo_patients():
    """Returns all demo patients"""
    return DEMO_PATIENTS


def get_patient_by_id(patient_id: str):
    """Get a specific demo patient"""
    for patient in DEMO_PATIENTS:
        if patient["id"] == patient_id:
            return patient
    return None


def get_red_alert_patients():
    """Get only Red alert cases"""
    return [p for p in DEMO_PATIENTS if p["expected_triage"] == "Red"]


def get_yellow_alert_patients():
    """Get only Yellow alert cases"""
    return [p for p in DEMO_PATIENTS if p["expected_triage"] == "Yellow"]


def get_green_patients():
    """Get only Green cases"""
    return [p for p in DEMO_PATIENTS if p["expected_triage"] == "Green"]


def demo_summary():
    """Print demo data summary"""
    print("\n" + "="*80)
    print("PHASE 5 DEMO DATA SUMMARY")
    print("="*80)
    print(f"\nTotal Demo Patients: {len(DEMO_PATIENTS)}")
    print(f"  • Red Alerts (Emergency): {len(get_red_alert_patients())}")
    print(f"  • Yellow Alerts (Moderate): {len(get_yellow_alert_patients())}")
    print(f"  • Green Cases (Low Risk): {len(get_green_patients())}")
    
    print("\n" + "-"*80)
    print("PATIENT PROFILES:")
    print("-"*80)
    
    for i, patient in enumerate(DEMO_PATIENTS, 1):
        print(f"\n{i}. {patient['name']} ({patient['id']})")
        print(f"   Expected Triage: {patient['expected_triage']}")
        print(f"   Clinical Significance: {patient['clinical_significance']}")
        print(f"   Symptoms: {patient['symptom_text'][:80]}...")


if __name__ == "__main__":
    demo_summary()
