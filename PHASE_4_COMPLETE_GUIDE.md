# Phase 4: Complete Integration Implementation Guide

## Overview
Phase 4 connects all Healio components into a complete real-time system:
- **Vision Agent**: Gemini Vision image analysis
- **Firestore Integration**: Patient cards, surveillance data, real-time updates  
- **Outbreak Surveillance**: Cluster detection and DHO alerts
- **Real-Time Queue**: WebSocket broadcasts to doctor dashboard

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    HEALIO PHASE 4 PIPELINE                  │
└─────────────────────────────────────────────────────────────┘

   Tablet/Mobile Input
        │
        ├─ Text: "I have fever and rash"
        ├─ Audio: Kannada speech
        └─ Images: Clinical photos (rash, wounds, etc)
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ VISION AGENT (vision_agent.py)                              │
│ Gemini Vision: Analyze clinical images                       │
│ Output: {conditions[], severity, confidence, signals[]}      │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ AGENT 1: MULTIMODAL INTAKE (agent1_intake.py)               │
│ Extract: chief_complaint, symptoms[], duration              │
│ Multimodal fusion: text + audio transcript + vision         │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ AGENT 2: CLINICAL REASONING (agent2_reasoning.py)           │
│ Two-Layer Safety:                                            │
│   Layer A: Confidence score (0.0-1.0)                       │
│   Layer B: Multi-signal gating (Red requires 2+ signals)     │
│ Output: {risk_score, triage_color, signals[], red_flags[]}  │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ AGENT 3: HANDOFF (agent3_handoff.py)                        │
│ Generate: patient_card + surveillance_data                  │
│ Route: Department + Doctor assignment                       │
│ Flag: ANM confirmation if Red alert                         │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ FIRESTORE PUSH (phase4_integration.py)                      │
│ Collections:                                                 │
│   - patients/{patient_id}: Patient card                     │
│   - surveillance/{patient_id}: Outbreak data                │
│   - queue/{patient_id}: Real-time queue entry               │
└─────────────────────────────────────────────────────────────┘
        │
        ├─ Real-Time Listeners (firebase/queue_manager.py)
        │  Broadcast to WebSocket clients
        │
        └─ Surveillance Engine (firebase/surveillance.py)
           Cluster Detection: 3+ patients → DHO alert
           
        ▼
┌─────────────────────────────────────────────────────────────┐
│ DASHBOARD OUTPUT                                             │
│                                                               │
│ Doctor Dashboard:                                            │
│   - Live queue with Red/Yellow/Green patients               │
│   - Patient card with chief complaint & risk score          │
│   - Clinical signals and red flags                          │
│   - Vision findings (if images analyzed)                    │
│                                                               │
│ DHO Dashboard:                                               │
│   - Active outbreak clusters                                │
│   - Patient count per cluster                               │
│   - Auto-escalation alerts for 3+ patients                  │
└─────────────────────────────────────────────────────────────┘
```

## Files Created/Modified

### 1. `backend/agents/vision_agent.py` (NEW)
**Purpose**: Gemini Vision image analysis for clinical images

**Key Functions**:
- `analyze_clinical_image(image_path)` - Single image analysis
  - Input: Path to clinical image (JPEG, PNG, GIF, WebP)
  - Output: `{visual_findings, possible_conditions[], severity, confidence, red_flags[]}`
  
- `analyze_multiple_images(image_paths)` - Multiple image analysis
  - Returns aggregated findings across all images
  - Deduplicates conditions and signals

**Usage Example**:
```python
from agents.vision_agent import analyze_clinical_image

result = analyze_clinical_image("patient_rash.jpg")
# Returns: {
#   "success": True,
#   "visual_findings": "Red macular rash on arms and legs",
#   "possible_conditions": ["dengue", "measles"],
#   "severity_assessment": "moderate",
#   "confidence": 0.85,
#   "red_flags": ["widespread rash", "high fever"]
# }
```

### 2. `backend/phase4_integration.py` (NEW)
**Purpose**: Complete Phase 4 orchestration with Firestore integration

**Main Class**: `HealioPhase4Pipeline`

**Key Methods**:
- `analyze_patient_with_images(symptom_text, image_paths, verbose)` - Complete pipeline
  - Calls all 3 agents in sequence
  - Analyzes images with Vision Agent
  - Pushes to Firestore
  - Checks outbreak clusters
  - Returns complete result with patient_id

- `_push_to_firestore(handoff_payload, image_paths)` - Firestore push
  - Creates patient card document in `patients/{id}`
  - Creates surveillance document in `surveillance/{id}`
  - Creates queue entry in `queue/{id}`
  - Returns patient_id

- `get_dashboard_status()` - Real-time status
  - Returns queue state + active clusters

**Usage Example**:
```python
from phase4_integration import HealioPhase4Pipeline

pipeline = HealioPhase4Pipeline()
result = pipeline.analyze_patient_with_images(
    symptom_text="High fever and red rash",
    image_paths=["rash.jpg", "wound.jpg"],
    verbose=True
)

print(result["patient"]["patient_id"])  # d4882561-ddf
print(result["patient"]["triage_color"])  # Yellow
print(result["outbreak_alerts"])  # List of clusters detected
```

### 3. `backend/main_pipeline.py` (UPDATED)
**Purpose**: Main entry point for complete system

**Functions**:
- `run_complete_pipeline(symptom_input, image_paths, verbose)` - Execute full pipeline
- `test_multiple_cases()` - Test with 3 clinical scenarios

**Execution Flow**:
```
Symptom Input + Images
    ↓
HealioPhase4Pipeline.analyze_patient_with_images()
    ├─ Vision analysis (if images)
    ├─ Agent 1: Intake extraction
    ├─ Agent 2: Clinical reasoning
    ├─ Agent 3: Patient card + surveillance
    ├─ Firestore push
    ├─ Queue add
    └─ Outbreak cluster check
    ↓
Complete Result with patient_id, queue_id, alerts
```

## Firestore Collections

### Collection: `patients/{patient_id}`
Stores complete patient card for doctor dashboard
```json
{
  "patient_id": "d4882561-ddf",
  "chief_complaint": "High fever and red rash",
  "symptoms": ["high fever", "red rash on arms and legs"],
  "triage_color": "Yellow",
  "risk_score": 0.82,
  "assigned_doctor": "Dr. Sharma",
  "assigned_department": "General",
  "queue_position": 4,
  "timestamp": "2026-04-26T04:09:39",
  "clinical_signals": ["high fever", "rash"],
  "red_flags": [],
  "images_analyzed": 2,
  "requires_anm_confirmation": false
}
```

### Collection: `surveillance/{patient_id}`
Stores data for outbreak cluster detection
```json
{
  "patient_id": "d4882561-ddf",
  "chief_complaint": "High fever and red rash",
  "symptoms": ["high fever", "red rash"],
  "severity": "moderate",
  "timestamp": "2026-04-26T04:09:39",
  "location": "Bengaluru, India",
  "department": "General"
}
```

### Collection: `queue/{patient_id}`
Real-time queue state for WebSocket broadcasts
```json
{
  "patient_id": "d4882561-ddf",
  "triage_color": "Yellow",
  "queue_position": 4,
  "timestamp": "2026-04-26T04:09:39",
  "status": "waiting"
}
```

### Collection: `detected_clusters/{cluster_id}`
Outbreak alerts with auto-escalation
```json
{
  "cluster_id": "cls-fever-rash-001",
  "symptoms": ["high fever", "red rash"],
  "patient_count": 5,
  "patient_ids": ["d4882561-ddf", "p2", "p3", "p4", "p5"],
  "severity": "high",
  "time_window_hours": 48,
  "confidence": 0.92,
  "action_required": true,
  "created_at": "2026-04-26T04:09:39",
  "escalation_alert": "DHO_NOTIFIED"
}
```

## Two-Layer Clinical Safety System

### Layer A: Confidence Scoring (0.0-1.0)
Continuous risk assessment across all signals

**Scoring Criteria**:
- Fever duration: Longer → higher score
- Symptom count: More symptoms → higher score
- Symptom severity: "Severe" keywords → higher score
- Red flag presence: Any red flag → boost score
- Vision findings confidence: From Gemini Vision

**Result**:
- Green: 0.0 - 0.65 (Low risk)
- Yellow: 0.65 - 0.90 (Medium risk)
- Red: 0.90 - 1.0 (High risk)

### Layer B: Multi-Signal Gating (Red Requires 2+ Signals)
Additional safety check for high-risk classification

**Rule**: To classify as RED (highest priority), system must identify 2+ independent clinical signals:
1. Fever (high temperature mentioned)
2. Rash (skin manifestation)
3. Respiratory distress (breathing difficulty)
4. Chest pain (cardiac concern)
5. Severe headache (neurological concern)
6. Bleeding signs (hemorrhagic component)
7. Dehydration markers (severe symptoms)

**Purpose**: Prevents false positives, ensures only truly critical patients get Red priority

**Example**:
```
Input: "I have high fever and red rash"
Signals: [fever, rash] = 2 signals ✓
Score: 0.82
Triage: Yellow (not Red, because 0.82 < 0.90)

Input: "I have severe fever, rash, and difficulty breathing"
Signals: [fever, rash, respiratory_distress] = 3 signals ✓
Score: 0.95
Triage: Red ✓ (both score > 0.90 AND 3 signals)
```

## Real-Time Updates via WebSocket

### WebSocket Endpoint: `ws://localhost:8000/ws/queue`
Broadcasts real-time queue updates to all connected doctor dashboards

**Message Format** (on every queue change):
```json
{
  "type": "queue_update",
  "queue": [
    {
      "patient_id": "d4882561-ddf",
      "triage_color": "Red",
      "position": 1,
      "chief_complaint": "Chest pain and breathing difficulty"
    },
    {
      "patient_id": "p2",
      "triage_color": "Yellow",
      "position": 2,
      "chief_complaint": "High fever and rash"
    }
  ],
  "timestamp": "2026-04-26T04:09:39"
}
```

### WebSocket Endpoint: `ws://localhost:8000/ws/alerts`
Real-time outbreak alerts to DHO dashboard

**Message Format** (on cluster detection):
```json
{
  "type": "outbreak_alert",
  "alert": {
    "cluster_id": "cls-fever-rash-001",
    "symptoms": ["high fever", "red rash"],
    "patient_count": 3,
    "severity": "high",
    "action_required": true
  }
}
```

## Outbreak Cluster Detection Algorithm

**Trigger**: New patient added to surveillance

**Algorithm**:
1. Extract symptoms from new entry
2. Query surveillance collection for matching patterns
3. Use Jaccard similarity to compare symptom sets
   - Formula: `similarity = |A ∩ B| / |A ∪ B|`
   - Threshold: > 0.6 (60% symptom overlap)
4. Filter results to 48-hour window
5. If 3+ patients match → Create cluster alert

**Example**:
```
New Patient: symptoms = {fever, rash}
Existing patients: 
  - Patient 2: {fever, rash, headache} → similarity 2/3 = 0.67 ✓
  - Patient 3: {fever, rash, joint_pain} → similarity 2/3 = 0.67 ✓
  - Patient 4: {cough, cold} → similarity 0/4 = 0.0 ✗

Match Count: 3 patients ✓
Action: Create cluster alert, notify DHO
```

## Testing Phase 4

### Test Case 1: Single Patient (No Outbreak)
```bash
cd backend
python main_pipeline.py
```

Expected output:
```
Patient stored in Firestore: d4882561-ddf
Added to real-time queue: XiEJ44Gitknk9sWKSaDa
Surveillance data recorded: u9YFI1a67jYbNkx3AzcX
No outbreak clusters detected
```

### Test Case 2: Multiple Similar Patients (Outbreak Detected)
```python
from phase4_integration import HealioPhase4Pipeline

pipeline = HealioPhase4Pipeline()

# Add 3 patients with similar symptoms within 2 hours
for i in range(3):
    result = pipeline.analyze_patient_with_images(
        symptom_text="High fever since 2 days and red rash on arms and legs",
        verbose=True
    )
    print(f"Patient {i+1} ID: {result['patient']['patient_id']}")
    
# Check for outbreak alerts
status = pipeline.get_dashboard_status()
print(f"Active clusters: {status['outbreaks']['active_clusters']}")
# Expected: 1 cluster with 3+ patients
```

### Test Case 3: With Image Analysis
```python
from phase4_integration import HealioPhase4Pipeline

pipeline = HealioPhase4Pipeline()
result = pipeline.analyze_patient_with_images(
    symptom_text="I have a rash on my body",
    image_paths=["rash_photo.jpg"],
    verbose=True
)

print(f"Images analyzed: {result['vision']['images_analyzed']}")
print(f"Conditions found: {result['vision']['conditions']}")
# Expected: Vision findings integrated into patient card
```

## API Integration

### REST Endpoint: POST `/analyze/with-multimodal`
Upload symptom text + images for complete analysis

**Request**:
```json
{
  "symptom_text": "High fever and red rash",
  "images": ["base64_encoded_image"]
}
```

**Response**:
```json
{
  "patient_id": "d4882561-ddf",
  "triage_color": "Yellow",
  "risk_score": 0.82,
  "doctor": "Dr. Sharma",
  "department": "General",
  "vision_findings": "Red macular rash on arms",
  "outbreak_alerts": []
}
```

### WebSocket: Real-Time Updates
Client connects to `ws://localhost:8000/ws/queue`
Receives live queue updates and outbreak alerts

## Production Deployment Checklist

- [ ] Create Firestore composite index for `detected_clusters` (status + timestamp)
- [ ] Enable Firestore backup
- [ ] Configure Firebase Security Rules (authenticated doctors only)
- [ ] Set up Cloud Logging for surveillance data
- [ ] Create DHO escalation notification workflow
- [ ] Test with real clinical image samples
- [ ] Configure Gemini Vision API quota limits
- [ ] Deploy FastAPI to Cloud Run
- [ ] Set up monitoring/alerting for cluster detection

## Troubleshooting

### Issue: "Firestore index required"
**Cause**: Complex query needs composite index
**Solution**: Run query once to get index creation link, create from Firebase console

### Issue: "No outbreak clusters detected"
**Cause**: Not enough matching patients or time window expired
**Solution**: Add 3+ patients with similar symptoms within 48 hours

### Issue: Vision images not analyzed
**Cause**: Image file not found or unsupported format
**Solution**: Verify file path and use JPEG/PNG/WebP format

### Issue: WebSocket not connecting
**Cause**: FastAPI server not running
**Solution**: Ensure `python main.py` running on port 8000

## Next Steps (Phase 5)

- Mobile app UI integration with Phase 4 endpoints
- Notification system for DHO alerts
- Historical data analytics for outbreak trends
- Patient follow-up workflow
- Integration with ICMR/health authority systems
