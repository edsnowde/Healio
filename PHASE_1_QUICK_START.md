# Phase 1 Quick Start Guide

## TL;DR - Do This Now

You're in: `C:\Users\User\Desktop\activities_ABULANCE\Build For Bengaluru Hackathon_Reva university_roactract\Healio`

### Step 1: Create GCP Project (5 min)
```powershell
# Set your project name (replace healio-phc with your preference)
$PROJECT_ID = "healio-phc"

# Create project
gcloud projects create $PROJECT_ID --name="Healio PHC Triage"
gcloud config set project $PROJECT_ID

# Enable APIs
gcloud services enable aiplatform.googleapis.com cloudrun.googleapis.com speech.googleapis.com firestore.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

### Step 2: Create Service Account & Get Credentials (5 min)
```powershell
# Create service account
gcloud iam service-accounts create healio-sa --display-name="Healio Service Account"

# Get service account email
$SA_EMAIL = $(gcloud iam service-accounts list --filter="displayName:Healio" --format='value(email)')

# Grant roles
gcloud projects add-iam-policy-binding $PROJECT_ID --member=serviceAccount:$SA_EMAIL --role=roles/aiplatform.user
gcloud projects add-iam-policy-binding $PROJECT_ID --member=serviceAccount:$SA_EMAIL --role=roles/speech.client
gcloud projects add-iam-policy-binding $PROJECT_ID --member=serviceAccount:$SA_EMAIL --role=roles/datastore.user
gcloud projects add-iam-policy-binding $PROJECT_ID --member=serviceAccount:$SA_EMAIL --role=roles/run.admin

# Download credentials
gcloud iam service-accounts keys create credentials.json --iam-account=$SA_EMAIL

# Move to backend folder
Move-Item credentials.json backend\credentials.json

# Set default credentials
gcloud auth application-default login
```

### Step 3: Setup Firebase (5 min)
- Go to `firebase.google.com`
- Add existing project → select `healio-phc`
- Firestore → Create Database → Test mode → Region: `asia-south1`
- Authentication → Enable Email/Password

### Step 4: Setup Python Environment (5 min)
```powershell
cd backend

# Run setup script (PowerShell)
.\setup_phase1.ps1

# OR manual setup:
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 5: Test Everything (5 min)
```powershell
# Test Gemini
python test_gemini.py

# Test Firestore
python test_firestore.py
```

---

## Detailed Setup: PHASE_1_SETUP.md

For step-by-step instructions with explanations, see: `PHASE_1_SETUP.md`

---

## Files Created

```
Healio/
├── backend/
│   ├── requirements.txt           ← Python dependencies
│   ├── test_gemini.py             ← Test Gemini connection
│   ├── test_firestore.py          ← Test Firestore connection
│   ├── setup_phase1.bat           ← Setup script (Command Prompt)
│   ├── setup_phase1.ps1           ← Setup script (PowerShell)
│   ├── credentials.json           ← ⚠️ ADD THIS (from GCP)
│   └── venv/                      ← Created by setup
│
└── PHASE_1_SETUP.md               ← Detailed guide

```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `gcloud: command not found` | Install Google Cloud SDK from https://cloud.google.com/sdk/docs/install-sdk |
| `credentials.json not found` | Download from GCP → Service Account → Keys |
| `ModuleNotFoundError: google-cloud-aiplatform` | Activate venv: `venv\Scripts\Activate.ps1` |
| `Permission denied` in Firestore test | Make sure Firestore is in Test mode, not Production |
| `GOOGLE_APPLICATION_CREDENTIALS` error | Move credentials.json to backend/ folder |

---

## Project IDs

Replace these in your environment:
- **Project ID:** `healio-phc` (or your chosen name)
- **Service Account:** `healio-sa`
- **Region:** `us-central1` (Vertex AI), `asia-south1` (Firestore/Firebase)

---

## What's Next?

Once Phase 1 tests pass ✅:
- Phase 2: FastAPI backend scaffolding
- Phase 3: Agent 1 implementation (Intake)
- Phase 4: Agent 2 implementation (Triage)
- Phase 5: Agent 3 implementation (Handoff)
- Phase 6: Frontend (Next.js)

---

**Last Updated:** April 25, 2026  
**Status:** Ready for Implementation
