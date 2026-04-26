# Phase 1: Foundation Setup (Hours 1–3)

## Overview
This phase sets up Google Cloud, Firebase, GitHub, and Python environment for Healio development.

---

## Step 1: Google Cloud Project Setup (Person 1)

### 1.1 Create GCP Project
```bash
# Open console.cloud.google.com in browser
# OR use CLI:
gcloud projects create healio-phc --name="Healio PHC Triage"
gcloud config set project healio-phc
```

### 1.2 Enable Required APIs
```bash
gcloud services enable \
  aiplatform.googleapis.com \
  cloudrun.googleapis.com \
  speech.googleapis.com \
  firestore.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com
```

### 1.3 Create Service Account
```bash
# Create service account
gcloud iam service-accounts create healio-sa \
  --display-name="Healio Service Account"

# Get the service account email
gcloud iam service-accounts list --filter="displayName:Healio"
# Copy the EMAIL address for next step

# Grant roles (replace SERVICE_ACCOUNT_EMAIL with actual email)
gcloud projects add-iam-policy-binding healio-phc \
  --member=serviceAccount:SERVICE_ACCOUNT_EMAIL \
  --role=roles/aiplatform.user

gcloud projects add-iam-policy-binding healio-phc \
  --member=serviceAccount:SERVICE_ACCOUNT_EMAIL \
  --role=roles/speech.client

gcloud projects add-iam-policy-binding healio-phc \
  --member=serviceAccount:SERVICE_ACCOUNT_EMAIL \
  --role=roles/datastore.user

gcloud projects add-iam-policy-binding healio-phc \
  --member=serviceAccount:SERVICE_ACCOUNT_EMAIL \
  --role=roles/run.admin
```

### 1.4 Create and Download Service Account Key
```bash
# Replace SERVICE_ACCOUNT_EMAIL
gcloud iam service-accounts keys create credentials.json \
  --iam-account=SERVICE_ACCOUNT_EMAIL

# Move it to backend folder
move credentials.json backend\credentials.json
```

### 1.5 Set Default Credentials
```bash
gcloud auth application-default login
# Follow browser prompt to authenticate
```

✅ **Person 1 Checklist:**
- [ ] GCP project created (`healio-phc`)
- [ ] All 6 APIs enabled
- [ ] Service account `healio-sa` created
- [ ] `credentials.json` downloaded & moved to `backend/`
- [ ] Application default credentials set

---

## Step 2: Firebase Setup (Person 4)

### 2.1 Create Firebase Project
```bash
# Go to firebase.google.com
# Sign in with same Google account
# Click "Add project"
# Select existing project: healio-phc
# Enable Google Analytics (optional)
# Create project
```

### 2.2 Initialize Firestore
- In Firebase Console → **Firestore Database**
- Click **Create Database**
- Select **Test mode** (for development)
- Choose region: `asia-south1` (India - closest to Bengaluru)
- Click **Create**

### 2.3 Enable Email/Password Auth
- In Firebase Console → **Authentication**
- Click **Get Started**
- Enable **Email/Password** provider
- Save

### 2.4 Download Firebase Config
```bash
# In Firebase Console → Project Settings (gear icon)
# Copy the config object
# Create backend/firebase_config.py:
```

✅ **Person 4 Checklist:**
- [ ] Firebase project linked to `healio-phc`
- [ ] Firestore Database created in Test mode
- [ ] Email/Password Authentication enabled
- [ ] Firebase config saved

---

## Step 3: GitHub Repository (Person 1)

```bash
# Create repo on github.com named 'healio'
# Clone it
git clone https://github.com/YOUR_USERNAME/healio.git
cd healio

# Add folders
mkdir backend frontend dashboard

# Initialize git
git init
git add .
git commit -m "Initial project structure"
git push origin main
```

✅ **Person 1 Checklist:**
- [ ] GitHub repo created
- [ ] All folders committed
- [ ] Link shared with team

---

## Step 4: Python Environment Setup (Person 1 + 2)

### 4.1 Create Virtual Environment (in `backend/` folder)
```bash
cd backend

# Create venv
python -m venv venv

# Activate venv
venv\Scripts\activate

# Verify activation (should show (venv) prefix)
```

### 4.2 Install Dependencies
```bash
# With venv activated:
pip install --upgrade pip

pip install \
  google-cloud-aiplatform \
  google-cloud-speech \
  google-api-core \
  fastapi \
  uvicorn \
  firebase-admin \
  python-dotenv \
  pydantic

# Verify installation
pip list
```

### 4.3 Create requirements.txt
```bash
# Generate requirements file
pip freeze > requirements.txt

# Others can install with:
# pip install -r requirements.txt
```

✅ **Person 1 + 2 Checklist:**
- [ ] venv created & activated
- [ ] All dependencies installed
- [ ] requirements.txt generated
- [ ] `pip list` shows all packages

---

## Step 5: Test Gemini Connection (Person 2)

### 5.1 Create Test File
File: `backend/test_gemini.py`

```python
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"

import vertexai
from vertexai.generative_models import GenerativeModel

# Initialize Vertex AI
vertexai.init(project="healio-phc", location="us-central1")

# Create model instance
model = GenerativeModel("gemini-2.0-flash")

# Test call
print("🔄 Testing Gemini 2.0 Flash connection...")
response = model.generate_content(
    "Patient has fever and rash. Give triage priority (Red/Yellow/Green)."
)

print("✅ Gemini Response:")
print(response.text)
```

### 5.2 Run Test
```bash
# Make sure venv is activated
python test_gemini.py
```

**Expected Output:**
```
🔄 Testing Gemini 2.0 Flash connection...
✅ Gemini Response:
Based on the symptoms presented, this patient should be triaged as **RED** priority...
```

✅ **Person 2 Checklist:**
- [ ] test_gemini.py created in backend/
- [ ] Script runs without errors
- [ ] Gemini response printed successfully
- [ ] Output shows Red/Yellow/Green priority

---

## Step 6: Test Firestore Connection (Person 4)

### 6.1 Create Test File
File: `backend/test_firestore.py`

```python
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

print("🔄 Initializing Firebase...")

# Initialize Firebase
try:
    cred = credentials.Certificate("credentials.json")
    firebase_admin.initialize_app(cred)
    print("✅ Firebase initialized")
except ValueError:
    # Already initialized
    print("⚠️ Firebase already initialized (skipping)")

# Get Firestore client
db = firestore.client()

print("📝 Testing Firestore write...")

# Test write
test_doc = {
    "test": "Phase 1 connection test",
    "timestamp": datetime.now().isoformat(),
    "status": "connected"
}

doc_ref = db.collection("test_collection").add(test_doc)
print(f"✅ Document written: {doc_ref}")

print("📖 Reading from Firestore...")

# Test read
docs = db.collection("test_collection").stream()
for doc in docs:
    print(f"Document ID: {doc.id}, Data: {doc.to_dict()}")

print("✅ Firestore connection working!")
```

### 6.2 Run Test
```bash
python test_firestore.py
```

**Expected Output:**
```
🔄 Initializing Firebase...
✅ Firebase initialized
📝 Testing Firestore write...
✅ Document written: (...)
📖 Reading from Firestore...
Document ID: xxx, Data: {'test': 'Phase 1 connection test', ...}
✅ Firestore connection working!
```

✅ **Person 4 Checklist:**
- [ ] test_firestore.py created in backend/
- [ ] Script runs without errors
- [ ] Document written to Firestore
- [ ] Document read back successfully
- [ ] Firebase Console shows test_collection

---

## Phase 1 Verification Checklist

| Task | Owner | Status |
|------|-------|--------|
| GCP project created + APIs enabled | Person 1 | ⬜ |
| Service account + credentials.json | Person 1 | ⬜ |
| Application default login complete | Person 1 | ⬜ |
| Firebase project initialized | Person 4 | ⬜ |
| Firestore Database created | Person 4 | ⬜ |
| Email/Password Auth enabled | Person 4 | ⬜ |
| GitHub repo created + cloned | Person 1 | ⬜ |
| Python venv created | Person 1+2 | ⬜ |
| Dependencies installed | Person 1+2 | ⬜ |
| Gemini connection test PASS ✅ | Person 2 | ⬜ |
| Firestore connection test PASS ✅ | Person 4 | ⬜ |

---

## Troubleshooting

### Error: `gcloud: command not found`
```bash
# Install Google Cloud SDK
# Download from: https://cloud.google.com/sdk/docs/install-sdk
# Then restart PowerShell/terminal
```

### Error: `credentials.json not found`
```bash
# Make sure you're in the backend/ folder
# And credentials.json is there:
ls credentials.json
```

### Error: `GOOGLE_APPLICATION_CREDENTIALS` not set
```bash
# The test files set it automatically, but you can also:
$env:GOOGLE_APPLICATION_CREDENTIALS = "credentials.json"
```

### Error: `ModuleNotFoundError: No module named 'vertexai'`
```bash
# Make sure venv is activated
venv\Scripts\activate

# Then reinstall
pip install google-cloud-aiplatform
```

### Firestore: Permission Denied
```bash
# Make sure you're using Test mode (not Production)
# And service account has correct roles
# Check Firebase Console → Firestore → Rules (should allow reads/writes)
```

---

## Next Steps (After Phase 1)

Once all checks pass ✅:
- Phase 2: Backend API scaffolding (FastAPI routes)
- Phase 3: Agent 1 (Intake) implementation
- Phase 4: Agent 2 (Triage) implementation
- Phase 5: Agent 3 (Handoff) implementation
- Phase 6: Frontend (Next.js) setup

---

**Phase 1 Status:** Not Started  
**Estimated Time:** 2–3 hours  
**Last Updated:** April 25, 2026
