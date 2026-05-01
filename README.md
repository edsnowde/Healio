# Healio: AI-Powered PHC Triage & Real-Time Outbreak Surveillance

**Theme:** Disease Prevention & Treatment  
**Built for:** Build For Bengaluru Hackathon — Reva University  
**Status:** ✅ **DEPLOYED & LIVE** — Both Frontend & Backend Running on Google Cloud Run

---

## 📅 LATEST DEPLOYMENT UPDATE (May 1, 2026)

### 🎉 **PRODUCTION STATUS: LIVE & OPERATIONAL**

| Component | Status | URL |
|-----------|--------|-----|
| **Frontend** | ✅ LIVE | https://healio-frontend-322299516577.us-central1.run.app |
| **Backend** | ✅ LIVE | https://healio-backend-322299516577.us-central1.run.app |
| **Google Maps** | ✅ ACTIVE | Interactive Bengaluru outbreak cluster map |
| **Database** | ✅ CONNECTED | Google Cloud Firestore (real-time) |
| **AI Pipeline** | ✅ RUNNING | Gemini 2.5 Flash (3-agent orchestration) |

### 📝 **CHANGES & FEATURES IMPLEMENTED (This Session)**

#### **FRONTEND ENHANCEMENTS**

1. **✅ Fixed Image Upload Button**
   - Changed from non-functional `<div>` to proper `<button>` with hidden file input
   - Added click-to-trigger mechanism: `input.click()`
   - Users can now upload clinical images from intake form

2. **✅ Added Mobile Camera Support**
   - Implemented camera input with `capture="environment"` attribute
   - Added dual-button system: Camera (direct capture) + Gallery (file picker)
   - Mobile users can capture images/videos directly without file explorer

3. **✅ Unified Submit Handler**
   - Consolidated duplicate `handleSubmit()` and `handleSubmitWithImages()` into single `handleSubmitForTriage()`
   - Smart routing: 
     - Text-only → `/triage` endpoint
     - Text + Media → `/analyze/with-multimodal` endpoint
   - Eliminates confusion, reduces button clutter

4. **✅ Dynamic Voice Recognition Language**
   - Fixed hardcoded language (`RECOGNITION_LANG = 'en-US'` issue)
   - Implemented language-aware speech recognition: `formData.audioLanguage`
   - Supports: Kannada (`kn-IN`), Hindi (`hi-IN`), English (`en-IN`)
   - Language selector buttons now properly control microphone input

5. **✅ Google Maps Integration (Outbreak Surveillance)**
   - Replaced static SVG grid map with interactive Google Maps API
   - Added `@react-google-maps/api` library for real-time rendering
   - **Map Features:**
     - 🗺️ Centered on Bengaluru (13.0827°N, 77.5933°E)
     - 📍 Cluster markers with patient counts
     - 🔴 Red markers = High severity (5+ patients, requires action)
     - 🟠 Orange markers = Medium severity (3-4 patients)
     - 💬 Click markers for detailed info windows (symptoms, confidence %)
     - 🎮 Full map controls: zoom, pan, fullscreen, map type
   - API Key configured: `frontend/.env.local`

6. **✅ Patient Details Page**
   - Created `/patient/[id]` dynamic route page (~700 lines)
   - Fetches complete patient record from Firestore
   - **Display Sections:**
     - Header: Name, ID, triage color, risk score, status
     - Chief complaint (prominent display)
     - Symptoms + Duration + Severity
     - Agent 1 output (multimodal findings)
     - Agent 2 output (clinical reasoning)
     - Agent 3 output (doctor assignment)
     - Original text input
     - Raw Gemini responses
     - Metadata (session ID, queue ID)
   - Date formatting in IST (Indian Standard Time)

7. **✅ Clickable Queue Board**
   - Made patient cards in queue clickable
   - Added `Link` navigation: patient card → `/patient/[id]`
   - Hover effects: shadow, scale transition
   - Shows patient name with fallback: "Unknown" if name missing

#### **BACKEND ENHANCEMENTS**

1. **✅ Geographic Coordinates for Outbreak Clusters**
   - Added `phc_locations` dictionary with 10 Bengaluru PHC areas
   - Coordinates extracted: (lat, lng) for each location
   - Cluster detection now includes latitude/longitude fields
   - Enables geographic visualization on map

2. **✅ Fixed Firestore Data Flow**
   - Investigated patient name population issue
   - Created `fix_patient_names.py` script for retroactive name population
   - New patients now automatically receive names
   - 4-step write sequence ensures referential integrity

#### **INFRASTRUCTURE & DEPLOYMENT**

1. **✅ TypeScript Configuration Fix**
   - Fixed `ignoreDeprecations` compilation error in `tsconfig.json`
   - Removed problematic deprecated config option
   - Frontend now builds without errors

2. **✅ Environment Variable Setup**
   - Created `.env.local` with:
     - `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY`: Active API key
     - `NEXT_PUBLIC_API_URL`: Points to Cloud Run backend
   - Frontend now correctly connects to backend API

3. **✅ Google Cloud Permissions (IAM)**
   - Granted `roles/aiplatform.user` → Vertex AI access
   - Granted `roles/datastore.user` → Firestore access
   - Cloud Run service account: `322299516577-compute@developer.gserviceaccount.com`
   - Resolved "403 Missing or insufficient permissions" error

4. **✅ Full Production Deployment**
   - **Frontend Build:** `npm run build` → 12 pages compiled, 0 errors
   - **Docker Build:** `gcloud builds submit --config cloudbuild-frontend.yaml .` → Built & pushed to Artifact Registry
   - **Frontend Deploy:** Cloud Run on 512MB/1CPU at port 3000
   - **Backend Deploy:** Cloud Run on 2GB/2CPU at port 8080 (FastAPI + Python 3.11)
   - Both services now serving 100% traffic, fully public

### 🔧 **TECHNICAL STACK (CURRENT)**

**Frontend:**
- Next.js 14.2.3 + React 18 + TypeScript
- Tailwind CSS for styling
- Firebase Admin SDK (Firestore real-time listeners)
- @react-google-maps/api (interactive maps)
- Web Speech Recognition API (multimodal voice)
- Lucide React icons

**Backend:**
- FastAPI (Python 3.11) + Uvicorn
- Vertex AI Generative Models (Gemini 2.5 Flash)
- Google Cloud Speech-to-Text
- Firebase Admin SDK (Firestore writes)
- Healio ADK (multi-agent orchestration)

**Cloud Infrastructure:**
- Google Cloud Run (serverless compute)
- Google Cloud Firestore (NoSQL database)
- Google Cloud Artifact Registry (Docker images)
- Vertex AI API (Gemini + Vision)
- Google Cloud Speech-to-Text API

### ✅ **WHAT WORKS NOW**

1. **Voice Input:** Users speak in Kannada/Hindi/English → transcribed via Google Speech-to-Text
2. **Image Upload:** Clinical images analyzed by Gemini Vision
3. **Triage Pipeline:** 3-agent orchestration → Red/Yellow/Green classification
4. **Real-time Queue:** Dashboard updates live as new patients submitted
5. **Patient Details:** Click any patient in queue → see complete medical record
6. **Outbreak Surveillance:** Interactive Google Map shows cluster locations
7. **Geographic Intelligence:** Clusters automatically plotted by PHC location
8. **Multi-agent AI:** Agent 1 (intake) → Agent 2 (reasoning) → Agent 3 (handoff)

### 🚀 **DEPLOYMENT COMMANDS EXECUTED**

```bash
# Frontend build locally
cd frontend && npm install && npm run build && cd ..

# Build Docker & push to registry
gcloud builds submit --config cloudbuild-frontend.yaml .

# Deploy frontend to Cloud Run
gcloud run deploy healio-frontend \
  --image us-central1-docker.pkg.dev/healio-494416/cloud-run-source-deploy/healio-frontend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 3000 --memory 512Mi --cpu 1

# Deploy backend to Cloud Run
cd backend
gcloud run deploy healio-backend \
  --source . \
  --project healio-494416 \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi --cpu 2 \
  --timeout 300 \
  --port 8080 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=healio-494416
cd ..

# Grant IAM permissions
gcloud projects add-iam-policy-binding healio-494416 \
  --member=serviceAccount:322299516577-compute@developer.gserviceaccount.com \
  --role=roles/aiplatform.user

gcloud projects add-iam-policy-binding healio-494416 \
  --member=serviceAccount:322299516577-compute@developer.gserviceaccount.com \
  --role=roles/datastore.user

# Verify deployment
gcloud run services list --region us-central1
```

### 📊 **DEPLOYMENT METRICS**

| Metric | Value |
|--------|-------|
| **Frontend Build Time** | ~3 minutes |
| **Backend Build Time** | ~5 minutes |
| **Total Deployment Time** | ~10 minutes |
| **API Response Time** | < 10 seconds (3-agent pipeline) |
| **Map Load Time** | < 2 seconds |
| **Database Sync** | Real-time (Firestore listeners) |

### 🎯 **NEXT STEPS / KNOWN LIMITATIONS**

- [ ] Add CORS restriction (currently allows all origins for testing)
- [ ] Implement user authentication (currently public)
- [ ] Add rate limiting to prevent abuse
- [ ] Test multimodal inputs (video analysis for respiratory distress)
- [ ] Scale to 5+ PHC locations across Bengaluru
- [ ] Add offline sync capability
- [ ] Performance testing with 100+ concurrent users

---
📋 Summary of Steps You Completed:
Step	Status	Command
1. Navigate to backend	✅ Done	    cd backend
2. Create virtual env	✅ Done	      python -m venv myenv
3. Activate venv	✅ Done	          .\myenv\Scripts\Activate.ps1
4. Install dependencies	✅ Done	    pip install -r requirements.txt
5. Run backend	🔄 Ready	           python -m uvicorn api.main:app --port 8080 --log-level info


frontend:
cd frontend 
npm run dev




## 🚀 Quick Start which was pervious stuff 

```powershell
# 1. Navigate to backend
cd "C:\Users\User\Desktop\activities_ABULANCE\Build For Bengaluru Hackathon_Reva university_roactract\Healio\backend"

# 2. Start the server
.\venv\Scripts\python -m uvicorn api.main:app --port 8080 --log-level info

# 3. Test a triage (new terminal)
Invoke-RestMethod -Uri "http://localhost:8080/triage" -Method POST -ContentType "application/json" -Body '{"text": "high fever since 3 days, red rash on arms and legs, severe joint pain", "name": "Patient Ravi"}'
```
Invoke-RestMethod -Uri "http://127.0.0.1:8080/triage" -Method POST -ContentType "application/json" -Body '{"text": "high fever since 3 days, red rash on arms and legs, severe joint pain", "name": "Patient Ravi"}'


---

## 1. Problem Understanding

Primary Health Centres (PHCs) in Bengaluru's peri-urban areas handle **150–300 walk-in patients daily** with a single on-duty doctor. Average consultation time is **3.2 minutes** (NHM Karnataka), with **40% spent on basic history taking**. This leaves **under 2 minutes for actual clinical decision-making**.

### Four Compounding Crises

**Crisis 1: No Structured Triage at Entry Point**
- Patients with TB, dengue, hypertension crises queue alongside minor ailments
- ANMs perform informal verbal triage with zero decision support and no clinical training
- High-risk cases go undetected at the first touchpoint — not because doctors are incompetent, but because the system gives them no early warning

**Crisis 2: Language, Literacy & Modality Wall**
- Over 60% of PHC walk-ins speak Kannada or local dialects as primary language
- Every digital health tool in India (Aarogya Setu, NHM RCH portal) is English-only, text-only
- Patients with visible symptoms (rashes, wounds) have no way to communicate them visually before reaching the consultation room

**Crisis 3: Zero Data Exhaust — Surveillance Blindspot**
- Every paper-based consultation is a permanently lost epidemiological signal
- Karnataka: highest NCD disease burden of any Indian state — 25,790 DALYs per 100,000 population
- 60% of PHC labs lack NCD testing facilities; district health officers have zero real-time visibility

**Crisis 4: IDSP's 7–10 Day Outbreak Detection Gap**
- India's IDSP takes 7–10 days from symptom emergence to outbreak detection — relying on paper S-forms submitted weekly
- One-third of outbreaks reported late under IDSP; follow-up reports unavailable for 97.2% of zoonotic outbreaks
- 91% of PHC health workers unaware of trigger thresholds; only 9% could describe any trigger event
- When a cluster of identical-symptom patients walks into the same PHC over 48 hours, it goes completely undetected

| Existing Tool | Limitation |
|---|---|
| Aarogya Setu | Passive symptom checker; English-only; no triage output; no doctor handoff; no data layer |
| NHM HMIS Portal | Retrospective data entry by clerks; not real-time; not patient-facing |
| Practo / mfine | Urban, English-speaking, smartphone-owning patients only; absent from PHC workflows |
| **No existing tool** | **Performs real-time, voice-first, multimodal, Kannada-language AI triage at PHC reception while simultaneously generating structured epidemiological surveillance data** |

---

## 2. Proposed Solution

**Healio** is a **multi-agent, multimodal AI triage and disease surveillance system** built entirely on Google's AI stack. It autonomously handles patient intake (voice + image + video), clinical reasoning, doctor handoff, and real-time epidemiological surveillance — from a **single Android tablet at the reception desk**.

- ✅ No new hardware required
- ✅ No app install for patients
- ✅ No English required
- ✅ Works offline with sync

---

## 3. The 3-Agent Pipeline (Google ADK)

### Agent 1: Multimodal Intake Agent
**Tech:** Google Cloud Speech-to-Text (Kannada `kn-IN` + Hindi `hi-IN`) + Gemini 2.5 Flash + Gemini Vision

**What it does:**
- Collects chief complaint via **Kannada/Hindi voice** → transcribed by Google Cloud Speech-to-Text → structured by Gemini
- Accepts image uploads: rash/wound/swelling → Gemini Vision extracts structured clinical observations
- Accepts prescription photos → Gemini Vision reads drug context
- Accepts breathing videos → Gemini Vision flags respiratory distress patterns (wheeze, stridor, retractions)
- Visual findings merged into symptom payload as `clinical_signals` — passed to Agent 2 as additional clinical context, not shown to patient as diagnosis

**Output:** `{ chief_complaint, symptoms[], duration, severity, clinical_signals[], multimodal_findings }`  
**Duration:** Under 3 minutes average

---

### Agent 2: Clinical Reasoning Agent
**Tech:** Gemini 2.5 Flash (Vertex AI)

**Two-Layer Safety Design:**

**Layer A — Confidence Scoring (continuous 0.0–1.0)**
- `score > 0.90` AND 2+ signals → 🔴 Red (escalate immediately)
- `score 0.65–0.90` → 🟡 Yellow ("doctor review suggested")
- `score < 0.65` → 🟢 Green (routine)

**Layer B — Multi-Signal Gating (mirrors NEWS2)**
- Red REQUIRES 2+ independent clinical signals to co-occur
- Single elevated vital NEVER triggers Red alone
- Example: Fever alone → Yellow | Fever + rash → Yellow-High | Fever + rash + Gemini Vision dengue pattern → Red

**Department Allocation (Gemini-based, 12 departments):**

Agent 2 uses clinical reasoning (not keyword matching) to allocate the correct department:

| Department | Typical Symptoms |
|---|---|
| General Medicine | Fever, fatigue, headache, body ache, weakness |
| Cardiology | Chest pain, palpitations, left arm pain, fainting |
| Paediatrics | Child/infant with fever, rash, poor feeding, irritability |
| Respiratory Medicine | Cough, wheezing, chest tightness, difficulty breathing |
| OB&G | Pelvic pain, irregular menstruation, pregnancy concerns |
| Ophthalmology | Eye pain, blurred vision, vision loss |
| Dermatology | Itching, rashes, eczema, blisters |
| General Surgery | Abdominal pain, hernia, lumps, abscess |
| Psychiatry | Anxiety, depression, hallucinations, sleep disturbances |
| ENT | Ear pain, nasal congestion, hearing loss, sinus pressure |
| Orthopaedics | Joint pain, bone pain, fractures, back pain, leg/arm pain |
| Dentistry | Toothache, gum swelling, jaw pain |
| Emergency | Uncontrolled bleeding, unconscious, severe trauma (Red override) |

**Rule:** Red triage always forces `Emergency` regardless of symptoms.

**Output:** `{ risk_score, triage_color, clinical_signals[], red_flags[], reasoning, requires_confirmation, recommended_department, department_reasoning }`

---

### Agent 3: Handoff, Confirmation & Surveillance Agent

**What it does:**

1. **Reads `recommended_department` from Agent 2** → looks up least-busy doctor in that department → assigns
2. **Builds structured patient card:** chief complaint, symptoms, triage color, risk score, red flags, clinical signals, assigned doctor, department, wait time estimate
3. **ANM Confirmation (Red alerts only):** Generates human-in-the-loop message:  
   *"Healio has flagged this patient as HIGH PRIORITY due to: [reasons]. Confirm alert?"*  
   ANM can Confirm or Downgrade to Yellow — no clinical knowledge required
4. **Writes to Firestore** — 4-step canonical sequence:
   - Step 1: Full patient record → `patients/{patient_id}`
   - Step 2: Queue entry → `patient_queue/{queue_id}`  
   - Step 3: Anonymized entry → `outbreak_surveillance/{surveillance_id}`
   - Step 4: Back-link all three IDs onto the master `patients/` doc
5. **Cluster Detection:** After every write, runs outbreak detection on `outbreak_surveillance` — if 3+ patients share a symptom cluster in 48 hours → writes alert to `detected_clusters/`, logs DHO notification
6. **WebSocket Broadcast:** Every patient add/update broadcasts to `/ws/queue` for real-time dashboard updates

**Doctors assigned by department:**

| Department | Doctors |
|---|---|
| General Medicine | Dr. Sharma, Dr. Patel |
| Cardiology | Dr. Mehta, Dr. Iyer |
| Paediatrics | Dr. Reddy, Dr. Rao |
| Respiratory Medicine | Dr. Nambiar |
| OB&G | Dr. Priya, Dr. Lakshmi |
| Ophthalmology | Dr. Srinivas |
| Dermatology | Dr. Rao |
| General Surgery | Dr. Bhat, Dr. Kumar |
| Psychiatry | Dr. Murthy |
| ENT | Dr. Hegde |
| Orthopaedics | Dr. Joshi, Dr. Singh |
| Dentistry | Dr. Pillai |
| Emergency | Dr. Nair, Dr. Krishnan |

---

## 4. Outbreak Surveillance & Cluster Detection

**How it works:**
- Every triage session writes anonymized `{ symptoms_anonymized, severity_category, triage_color, risk_score, symptom_signature, patient_id }` to `outbreak_surveillance/`
- After each write, cluster detection runs: queries all entries within last 48 hours, computes **keyword-level Jaccard similarity** (≥0.25 threshold) between symptom sets
- "High fever + rash + joint pain" and "fever with rash, body pain" correctly match because both tokenize to shared keywords: `fever`, `rash`, `joint/pain`
- **3+ matching cases in 48h** → alert written to `detected_clusters/` (confidence: 0.65, severity: medium)
- **5+ cases** → `action_required: True` (auto-escalate to DHO)
- Collapses IDSP's 7–10 day detection window to **under 2 hours**

**To trigger a test outbreak:**
```powershell
# Send 5 similar-symptom patients — cluster fires after patient 3
Invoke-RestMethod -Uri "http://localhost:8080/triage" -Method POST -ContentType "application/json" -Body '{"text": "high fever since 3 days, red rash on arms and legs, severe joint pain", "name": "Patient Ravi"}'
Invoke-RestMethod -Uri "http://localhost:8080/triage" -Method POST -ContentType "application/json" -Body '{"text": "fever for 2 days, skin rash all over body, joint pain and headache", "name": "Patient Meena"}'
Invoke-RestMethod -Uri "http://localhost:8080/triage" -Method POST -ContentType "application/json" -Body '{"text": "high fever, rash on body, joint pain, feeling very weak", "name": "Patient Suresh"}'
Invoke-RestMethod -Uri "http://localhost:8080/triage" -Method POST -ContentType "application/json" -Body '{"text": "fever with rash and severe body pain and joint pain", "name": "Patient Anita"}'
Invoke-RestMethod -Uri "http://localhost:8080/triage" -Method POST -ContentType "application/json" -Body '{"text": "3 days fever, red rash spreading, joint pain, headache, weakness", "name": "Patient Kiran"}'

# Check cluster results
Invoke-RestMethod -Uri "http://localhost:8080/surveillance/clusters" -Method GET
Invoke-RestMethod -Uri "http://localhost:8080/surveillance/summary" -Method GET
```

---

## 5. API Reference

### Triage Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/triage` | Main triage — text input, runs all 3 agents, writes to 3 Firestore collections |
| `POST` | `/analyze` | Alias for text triage |
| `POST` | `/analyze/with-audio` | Upload audio file → Speech-to-Text → triage |
| `POST` | `/analyze/with-multimodal` | Text + images + videos → full multimodal triage |

**`/triage` Request body:**
```json
{
  "text": "patient symptom description",
  "name": "Patient Name",
  "audio_file_path": "optional/path/to/audio.wav",
  "audio_language": "kannada"
}
```

**`/triage` Response:**
```json
{
  "success": true,
  "pipeline": "ADK_REAL_AGENTS",
  "patient_id": "Firestore ID in patients/",
  "queue_id": "Firestore ID in patient_queue/",
  "surveillance_id": "Firestore ID in outbreak_surveillance/",
  "triage_color": "Red | Yellow | Green",
  "risk_score": 0.95,
  "chief_complaint": "...",
  "assigned_doctor": "Dr. Nair",
  "assigned_department": "Emergency",
  "requires_anm_confirmation": true,
  "agents_executed": ["Agent 1", "Agent 2", "Agent 3"],
  "session_id": "...",
  "timestamp": "..."
}
```

### Queue Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/queue` | Get full patient queue ordered by priority (Red → Yellow → Green) |
| `GET` | `/queue/department/{dept}` | Get queue for a specific department |
| `PATCH` | `/queue/patient/{id}` | Update patient status (waiting → in_consultation → completed) |

### Surveillance Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/surveillance/clusters` | Get all active detected outbreak clusters |
| `GET` | `/surveillance/summary?hours=24` | Symptom distribution summary for last N hours |
| `POST` | `/surveillance/clusters/{id}/escalate` | Escalate cluster to DHO |
| `GET` | `/surveillance` | Raw all surveillance records |

### WebSocket

| Endpoint | Description |
|---|---|
| `ws://localhost:8080/ws/queue` | Real-time queue updates — broadcasts on every patient add/status change |
| `ws://localhost:8080/ws/alerts` | Real-time outbreak cluster alerts |

### Demo / Utility

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | System status |
| `GET` | `/health` | Health check |
| `POST` | `/reset` | Clear all Firestore demo data (patients, queue, surveillance, clusters) |

---

## 6. Firestore Collections

```
Firestore
├── patients/                    ← Full patient records (master)
│   └── {patient_id}
│       ├── chief_complaint
│       ├── symptoms[]
│       ├── triage_color
│       ├── risk_score
│       ├── assigned_doctor
│       ├── assigned_department
│       ├── agent1_gemini_raw_response
│       ├── agent2_gemini_raw_response
│       ├── queue_id             ← links to patient_queue/
│       └── surveillance_id      ← links to outbreak_surveillance/
│
├── patient_queue/               ← Real-time triage queue
│   └── {queue_id}
│       ├── patient_id           ← links back to patients/
│       ├── triage_color
│       ├── assigned_doctor
│       ├── assigned_department
│       ├── status               (waiting | in_consultation | completed)
│       └── urgent_flag
│
├── outbreak_surveillance/       ← Anonymized epidemiological data
│   └── {surveillance_id}
│       ├── patient_id           ← links back to patients/
│       ├── symptoms_anonymized[]
│       ├── symptom_signature
│       ├── severity_category
│       ├── triage_color
│       └── location
│
└── detected_clusters/           ← Outbreak alerts
    └── {cluster_id}
        ├── symptoms[]
        ├── patient_count
        ├── confidence
        ├── severity             (medium | high)
        ├── action_required      (true if 5+ cases)
        ├── status               (pending_verification | escalated_to_dho)
        └── time_window_hours
```

---

## 7. Setup & Installation

```powershell
# Clone / navigate to project
cd "...\Healio\backend"

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Verify key dependencies
.\venv\Scripts\pip show google-cloud-speech    # v2.38.0
.\venv\Scripts\pip show vertexai              # Gemini
.\venv\Scripts\pip show firebase-admin        # Firestore
.\venv\Scripts\pip show Pillow               # Image processing
```

**Requirements (key packages):**
- `fastapi`, `uvicorn` — API server
- `vertexai` — Gemini 2.5 Flash (Agent 1, 2)
- `google-cloud-speech` — Speech-to-Text Kannada/Hindi
- `firebase-admin` — Firestore real-time DB
- `Pillow` — Image preprocessing for Gemini Vision
- `google-cloud-aiplatform` — Vertex AI

---

## 8. Running Tests

```powershell
# Test Gemini Vision (image analysis)
.\venv\Scripts\python test_gemini_vision.py

# Test Speech-to-Text (Kannada/Hindi)
.\venv\Scripts\python test_speech_to_text.py

# Test Firestore connection
.\venv\Scripts\python test_firestore.py

# Test full ADK pipeline (all 3 agents)
.\venv\Scripts\python test_real_adk_agents.py

# Test triage via API
Invoke-RestMethod -Uri "http://localhost:8080/triage" -Method POST -ContentType "application/json" -Body '{"text": "blood is oozing from my wound, not stopping, feeling very weak and dizzy"}'

# Test department routing
Invoke-RestMethod -Uri "http://localhost:8080/triage" -Method POST -ContentType "application/json" -Body '{"text": "chest pain and palpitations since 2 days"}'
# Expected: Cardiology

Invoke-RestMethod -Uri "http://localhost:8080/triage" -Method POST -ContentType "application/json" -Body '{"text": "discomfort in my leg bone, knee pain since few days"}'
# Expected: Orthopaedics

Invoke-RestMethod -Uri "http://localhost:8080/triage" -Method POST -ContentType "application/json" -Body '{"text": "cough and wheezing since 3 days"}'
# Expected: Respiratory Medicine
```

---

## 9. Project Structure

```
Healio/
└── backend/
    ├── agents/
    │   ├── agent1_intake.py        ← Voice + Vision + text intake (Gemini 2.5 Flash)
    │   ├── agent2_reasoning.py     ← Clinical reasoning, risk scoring, dept allocation
    │   └── agent3_handoff.py       ← Patient card, ANM confirmation, Firestore writes
    ├── api/
    │   ├── main.py                 ← FastAPI app, all endpoints, WebSocket
    │   ├── speech_handler.py       ← Google Cloud Speech-to-Text handler
    │   └── file_handler.py         ← Image/video/audio file handling
    ├── firebase/
    │   ├── queue_manager.py        ← Real-time patient queue, Firestore operations
    │   └── surveillance.py         ← Outbreak cluster detection, DHO alerts
    ├── run_adk.py                  ← Pipeline orchestrator (ADK session management)
    ├── requirements.txt
    └── test_*.py                   ← Individual component test scripts
```

---

## 10. Infrastructure (Google Cloud Stack)

| Service | Usage | Status |
|---|---|---|
| **Vertex AI (Gemini 2.5 Flash)** | Agent 1 intake + Agent 2 clinical reasoning | ✅ Live |
| **Google Cloud Speech-to-Text** | Kannada `kn-IN` + Hindi `hi-IN` voice transcription | ✅ Installed & wired |
| **Gemini Vision** | Image/video clinical analysis | ✅ Live |
| **Cloud Firestore** | Real-time patient queue + surveillance + patient records | ✅ Live |
| **Google ADK** | Multi-agent session orchestration | ✅ Live |
| **Cloud Run** | Serverless deployment | 🔲 Ready to containerize |
| **Firebase Auth** | Staff login | 🔲 Planned |
| **Cloud Functions** | SMS to doctors/DHO on escalation | 🔲 Planned |

---

## 11. Expected Impact

### Immediate (Per PHC Per Month)
- **35–40% reduction** in patient wait time through AI-driven priority queuing
- **40–80 minutes** of additional clinical time freed per doctor per day
- **Near elimination** of missed Red flag cases at reception
- Visual symptom data reaching doctor before consultation — first time at any PHC in India

### Systemic (Surveillance Layer)
- Every triage session generates structured, anonymized surveillance data — first PHC-integrated epidemiological early warning system in Karnataka
- Symptom cluster detection triggers DHO alerts **weeks** before outbreak data appears in hospital records
- Collapses IDSP's 7–10 day detection window to **under 2 hours**
- Directly supports Ayushman Bharat Digital Mission: national health intelligence from primary care data

### Scale
- **Bengaluru pilot (10 PHCs):** 3,000–5,000 patients/week
- **Karnataka rollout (2,357 PHCs):** Largest community-level AI triage infrastructure in India
- **National model:** 31,000+ PHCs with regional language swap (Hindi, Tamil, Telugu)
- **SDG 3.4** (reduce NCD mortality by one-third by 2030) + **SDG 3.8** (Universal Health Coverage)

---

*Built with Google ADK · Gemini 2.5 Flash · Vertex AI · Google Cloud Speech-to-Text · Cloud Firestore*
