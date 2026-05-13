

**YES! I understand completely!** 🎯 Let me explain like you're 5 years old:

---

## 🗝️ **What is `.env` file?**

`.env` = "Environment Variables" = Secret instructions your app needs

**Think of it like a recipe card:**
```
Recipe Card (.env):
- API_KEY = "super-secret-key-12345"
- DATABASE_URL = "https://database.com"
- EMAIL_PASSWORD = "secret123"
```

Your app reads this card before running and uses those values.

---

## 💻 **Locally (On Your Computer):**

```
Your Computer
    ↓
[.env.local file]
    ↓
Contains:
  API_BASE_URL = "http://localhost:8080"
  GOOGLE_MAPS_KEY = "AIza..."
    ↓
Your Frontend App reads it
    ↓
App knows where backend is
```

**Example `.env.local`:**
```
API_BASE_URL=http://localhost:8080
GOOGLE_MAPS_API_KEY=AIzaSyD_example_key
```

**How it works:**
```js
// frontend/lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL
// Gets value from .env file
```

---

## ☁️ **On Google Cloud (Deployed):**

Here's the KEY question: **Your `.env.local` file is on YOUR computer. How does GCP know about it?**

```
Your Computer (.env.local)
         ↓
         ❌ DON'T upload this to GCP
         
Instead:
         ↓
When you deploy to Cloud Run:
  ✅ Set environment variables in Cloud Run console
  ✅ Cloud Run stores them securely
  ✅ Your app reads them at runtime
```

---

## 🔄 **Step-by-Step: What Actually Happens**

### **Step 1: You Deploy**
```bash
./scripts/deploy_backend.sh
# OR
terraform apply
```

### **Step 2: Script/Terraform Says to Google Cloud:**
```
"I'm deploying service X"
"Please set these environment variables:"
  GOOGLE_CLOUD_PROJECT = "healio-494416"
  REGION = "us-central1"
```

### **Step 3: Google Cloud Stores It**
```
Google Cloud Console
    ↓
[Cloud Run Service: healio-backend]
    ↓
Environment Variables (secure storage):
  - GOOGLE_CLOUD_PROJECT = "healio-494416"
  - REGION = "us-central1"
  - Other configs...
```

### **Step 4: Your App Starts**
```
Google Cloud starts your app
    ↓
App asks: "What's my project ID?"
    ↓
Cloud Run gives it: "healio-494416"
    ↓
App uses it and works
```

---

## 🔐 **The 3 Types of Variables:**

### **Type 1: SECRETS (Passwords, API Keys)**
❌ **DON'T** put in `.env` file
❌ **DON'T** upload to GitHub
✅ **DO** use Google Secret Manager

```
Your password: "super-secret-key"
         ↓
[Google Secret Manager]
         ↓
Encrypted, locked away
         ↓
Only your app can read it
```

### **Type 2: CONFIGS (Settings, URLs)**
✅ **OK** to put in Cloud Run environment variables

```
REGION = "us-central1"
PROJECT_ID = "healio-494416"
BACKEND_URL = "https://healio-backend-..."
```

### **Type 3: LOCAL DEVELOPMENT (On Your Computer)**
✅ **OK** to put in `.env.local`
✅ **ONLY** used locally
✅ **NEVER** pushed to GitHub

```
.env.local (your computer only):
API_BASE_URL = "http://localhost:8080"
GOOGLE_MAPS_KEY = "test-key"
```

---

## 📝 **Current Setup: What Was Done**

### **Frontend (.env.local locally):**
```
# frontend/.env.local (on your computer)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8080
```

When deployed:
```
# In Cloud Run console (backend knows this)
NEXT_PUBLIC_API_BASE_URL=https://healio-backend-322299516577.us-central1.run.app
```

### **Backend (Python):**
```python
# backend/api/main.py
import os

project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
# Gets from Cloud Run environment variables

api_key = os.getenv("GOOGLE_MAPS_API_KEY")
# Gets from Secret Manager
```

---

## 🎯 **Visual Flow: Environment Variables Journey**

```
┌─────────────────────────────────────────────────┐
│        YOUR COMPUTER (Local)                    │
│                                                 │
│  .env.local file:                              │
│  ├─ API_BASE_URL=localhost:8080               │
│  ├─ GOOGLE_MAPS_KEY=test123                   │
│  └─ DATABASE_URL=localhost:5432               │
│                                                 │
│  npm run dev  ← reads .env.local              │
└─────────────────────────────────────────────────┘
           ↓
    You run: git push
           ↓
┌─────────────────────────────────────────────────┐
│     GITHUB REPO (code storage)                 │
│                                                 │
│  ❌ .env.local is NOT pushed                   │
│     (it's in .gitignore)                       │
│                                                 │
│  ✅ Only code files pushed                     │
└─────────────────────────────────────────────────┘
           ↓
    You run: ./scripts/deploy_backend.sh
           ↓
┌─────────────────────────────────────────────────┐
│        GOOGLE CLOUD                            │
│                                                 │
│  [Cloud Run Service]                           │
│  Environment Variables (set automatically):    │
│  ├─ GOOGLE_CLOUD_PROJECT=healio-494416       │
│  ├─ REGION=us-central1                        │
│  ├─ API_BASE_URL=https://healio-backend-...  │
│  └─ PORT=8080                                 │
│                                                 │
│  [Secret Manager]                             │
│  ├─ GOOGLE_MAPS_API_KEY (encrypted)          │
│  ├─ DATABASE_CREDS (encrypted)               │
│  └─ SERVICE_ACCOUNT_KEY (encrypted)          │
└─────────────────────────────────────────────────┘
           ↓
    App starts
           ↓
    App reads environment variables
           ↓
    App works! ✅
```

---

## 💡 **Real Example: Google Cloud Credentials**

### **Question: How does your backend access Google Cloud Services?**

**Answer: Through credentials stored in environment**

```
┌─────────────────────────────────────────────────┐
│  Google Cloud Service Account                   │
│  (like an employee ID for your app)             │
│                                                 │
│  Email: 322299516577-compute@developer...      │
│  Permissions: Can access Firestore, Vertex AI  │
└─────────────────────────────────────────────────┘
           ↓
When your app runs on Cloud Run:
           ↓
    Cloud Run automatically provides credentials
           ↓
    App can access Firestore, Vertex AI, etc.
           ↓
    NO need to store secret keys! ✅
```

**How it works:**
```python
# backend/agents/agent1_intake.py
from google.cloud import firestore
from google.cloud import aiplatform

# These libraries automatically use credentials
# from the Cloud Run service account
# NO .env key needed! 🔐

db = firestore.Client()  # ← Already authenticated!
aiplatform.init()       # ← Already authenticated!
```

---

## 🔒 **Security: Why This Matters**

### **BAD Way (Insecure):**
```
❌ Store API key in .env file
❌ Upload to GitHub
❌ Anyone with GitHub access can see your keys
❌ Hackers can use your keys
❌ Your Google Cloud account compromised
```

### **GOOD Way (Secure - What You Have):**
```
✅ .env.local only on your computer
✅ NOT pushed to GitHub (.gitignore prevents it)
✅ For GCP: Use service accounts (no keys needed)
✅ For secrets: Use Secret Manager (encrypted)
✅ Only your app can use them
```

---

## 📋 **Your Current Setup Breakdown:**

| Where | What | How It Works |
|-------|------|--------------|
| **Your Computer** | `.env.local` | npm reads it locally |
| **GitHub** | Just code | No secrets stored |
| **Google Cloud** | Service Account | Auto-provided to Cloud Run |
| **Secret Manager** | API Keys if needed | Encrypted, only your app can access |

---

## ❓ **Real Questions You Might Have:**

### **Q: Where is my `.env.local` file right now?**
A: On your computer only, in the frontend folder
```
C:\Users\User\...\Healio\frontend\.env.local  ← Only here
```

### **Q: Is it pushed to GitHub?**
A: ❌ NO - It's in .gitignore
```
# frontend/.gitignore
.env.local    ← This file is ignored
.env.*.local  ← Any .env file is ignored
```

### **Q: So how does deployed app know URLs?**
A: Cloud Run sets environment variables automatically
```
When deploying:
  ✅ Script says: "Set API_BASE_URL = https://..."
  ✅ Cloud Run stores it
  ✅ App reads it
  ✅ Works!
```

### **Q: What if I need to change a variable on deployed app?**
A: Edit in Cloud Run console or Terraform:
```bash
# In terraform/terraform.tfvars
backend_env_vars = {
  API_BASE_URL = "https://new-url"
}

terraform apply
```

### **Q: What about Google Cloud credentials?**
A: ✅ Automatic! 
```
When app runs on Cloud Run:
  → Cloud Run provides credentials automatically
  → No need for .env file
  → This is called "Application Default Credentials"
  → Google Cloud handles it securely
```

---

## 🎯 **Summary for Beginner:**

```
.env.local = Recipe card for your app
  ↓
Local (your computer):
  ✅ Read from .env.local
  ✅ Used by npm run dev
  
Deployed (Google Cloud):
  ✅ NOT needed - removed from code
  ✅ Cloud Run provides variables automatically
  ✅ Credentials handled by service account
  ✅ Secrets stored in Secret Manager (encrypted)
```

---

**Does this make sense now?** 🤔 Think of it like:
- **`.env.local`** = Your personal recipe card at home
- **Cloud Run variables** = Restaurant's internal system
- **Service Account** = Restaurant's ID badge
- **Secret Manager** = Restaurant's safe (for passwords)










Searched for files matching `**/.env*`, no matches

Searched for files matching `**/Dockerfile`, 2 matches

Searched for regex `process.env|os.getenv|os.environ|NEXT_PUBLIC|--set-env-vars|environment`, 20 results

Read [](file:///c%3A/Users/User/Desktop/activities_ABULANCE/Build%20For%20Bengaluru%20Hackathon_Reva%20university_roactract/Healio/cloudbuild-frontend.yaml)

Read [](file:///c%3A/Users/User/Desktop/activities_ABULANCE/Build%20For%20Bengaluru%20Hackathon_Reva%20university_roactract/Healio/frontend/Dockerfile)

Read [](file:///c%3A/Users/User/Desktop/activities_ABULANCE/Build%20For%20Bengaluru%20Hackathon_Reva%20university_roactract/Healio/backend/Dockerfile)

Read [](file:///c%3A/Users/User/Desktop/activities_ABULANCE/Build%20For%20Bengaluru%20Hackathon_Reva%20university_roactract/Healio/frontend/lib/api.ts#1-1), lines 1 to 30

Read [](file:///c%3A/Users/User/Desktop/activities_ABULANCE/Build%20For%20Bengaluru%20Hackathon_Reva%20university_roactract/Healio/backend/api/main.py#1-1), lines 1 to 50

Read [](file:///c%3A/Users/User/Desktop/activities_ABULANCE/Build%20For%20Bengaluru%20Hackathon_Reva%20university_roactract/Healio/scripts/deploy_backend.sh)

Read [](file:///c%3A/Users/User/Desktop/activities_ABULANCE/Build%20For%20Bengaluru%20Hackathon_Reva%20university_roactract/Healio/scripts/deploy_frontend.sh)

Read [](file:///c%3A/Users/User/Desktop/activities_ABULANCE/Build%20For%20Bengaluru%20Hackathon_Reva%20university_roactract/Healio/terraform/main.tf#1-1), lines 1 to 100

Read [](file:///c%3A/Users/User/Desktop/activities_ABULANCE/Build%20For%20Bengaluru%20Hackathon_Reva%20university_roactract/Healio/terraform/terraform.tfvars)

Read [](file:///c%3A/Users/User/Desktop/activities_ABULANCE/Build%20For%20Bengaluru%20Hackathon_Reva%20university_roactract/Healio/frontend/app/intake/page.tsx#1-1), lines 1 to 100

Read [](file:///c%3A/Users/User/Desktop/activities_ABULANCE/Build%20For%20Bengaluru%20Hackathon_Reva%20university_roactract/Healio/terraform/main.tf#100-100), lines 100 to 100

Read [](file:///c%3A/Users/User/Desktop/activities_ABULANCE/Build%20For%20Bengaluru%20Hackathon_Reva%20university_roactract/Healio/terraform/main.tf#130-130), lines 130 to 150

Read [](file:///c%3A/Users/User/Desktop/activities_ABULANCE/Build%20For%20Bengaluru%20Hackathon_Reva%20university_roactract/Healio/terraform/main.tf#90-90), lines 90 to 120

Perfect! I've read ALL the files. Let me show you **EXACTLY what was done for environment variables in this project**:

---

## 🔑 **COMPLETE ENVIRONMENT VARIABLES SETUP FOR HEALIO**

### **📊 Summary Table**

| Where | Variable | Value | Purpose |
|-------|----------|-------|---------|
| **Frontend (.env.local)** | `NEXT_PUBLIC_API_URL` | `http://localhost:8080` | Local dev backend |
| **Frontend (.env.local)** | `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` | `AIza...` | Google Maps |
| **Backend (Cloud Run)** | `GOOGLE_CLOUD_PROJECT` | `healio-494416` | GCP project ID |
| **Backend (Cloud Run)** | `PORT` | `8080` | Server port |

---

## 1️⃣ **FRONTEND ENVIRONMENT VARIABLES**

### **Locally (Your Computer):**

**File:** .env.local (NOT tracked by git, only on your computer)

```
NEXT_PUBLIC_API_URL=http://localhost:8080
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=AIzaSyBRy_riN5meM-iasdyEXc3c6NadgbQMLVA
```

**How it's used in code:**

```typescript
// frontend/lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL
// Gets value: "http://localhost:8080"

// So when you call:
fetch(`${API_BASE}/triage`)
// Becomes: "http://localhost:8080/triage"
```

---

### **Deployed (Google Cloud):**

**Step 1: Build Frontend with Docker**

**File:** Dockerfile
```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .

ARG NEXT_PUBLIC_API_URL    # ← Accepts this as input
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL   # ← Bakes it into image

RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

**Step 2: Pass Variable During Build**

**File:** cloudbuild-frontend.yaml
```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '--build-arg'
      - 'NEXT_PUBLIC_API_URL=https://healio-backend-322299516577.us-central1.run.app'
      # ↑ Passes the backend URL to Docker build
      - '-t'
      - 'us-central1-docker.pkg.dev/healio-494416/cloud-run-source-deploy/healio-frontend:latest'
      - '-f'
      - 'frontend/Dockerfile'
      - 'frontend/'
```

**Step 3: Deploy to Cloud Run**

**File:** deploy_frontend.sh
```bash
API_URL="https://healio-backend-322299516577.us-central1.run.app"

gcloud run deploy healio-frontend \
  --image us-central1-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/$SERVICE_NAME:latest \
  --set-env-vars NEXT_PUBLIC_API_URL=$API_URL
  # ↑ Also sets it at runtime for extra safety
```

**Step 4: Terraform Sets It**

**File:** main.tf
```hcl
resource "google_cloud_run_service" "healio_frontend" {
  name     = "healio-frontend"
  location = var.region
  project  = var.project_id
  
  template {
    spec {
      containers {
        image = "..."
        
        env {
          name  = "NEXT_PUBLIC_API_URL"
          value = google_cloud_run_service.healio_backend.status[0].url
          # ↑ Automatically links to backend URL!
        }
        
        env {
          name  = "NEXT_PUBLIC_GOOGLE_MAPS_API_KEY"
          value = var.google_maps_api_key
          # ↑ From terraform.tfvars
        }
      }
    }
  }
}
```

**File:** terraform.tfvars
```
project_id  = "healio-494416"
region      = "us-central1"
# google_maps_api_key = "YOUR_API_KEY_HERE"  ← You add this
```

---

## 2️⃣ **BACKEND ENVIRONMENT VARIABLES**

### **In Docker**

**File:** Dockerfile
```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV PORT=8080    # ← Default port
EXPOSE 8080

CMD ["python", "-m", "uvicorn", "api.main:app", "--port", "8080"]
```

### **Set During Deployment**

**File:** deploy_backend.sh
```bash
PROJECT_ID="healio-494416"

gcloud run deploy healio-backend \
  --source . \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID
  # ↑ Sets Google Cloud project ID
```

### **Terraform Configuration**

**File:** main.tf
```hcl
resource "google_cloud_run_service" "healio_backend" {
  name     = "healio-backend"
  location = var.region
  project  = var.project_id
  
  template {
    spec {
      containers {
        image = "..."
        
        env {
          name  = "GOOGLE_CLOUD_PROJECT"
          value = var.project_id
          # ↑ From terraform.tfvars
        }
        
        env {
          name  = "PORT"
          value = "8080"
        }
      }
      
      timeout_seconds = 300
    }
  }
}
```

### **How Backend Code Uses It**

**File:** main.py
```python
import os

# Read from environment
project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
# Gets: "healio-494416"

port = os.getenv("PORT", "8080")
# Gets: "8080"
```

---

## 🔄 **COMPLETE FLOW: How It All Works Together**

```
┌──────────────────────────────────────────────────────────────┐
│                     LOCAL DEVELOPMENT                        │
│                                                              │
│  frontend/.env.local:                                       │
│  ├─ NEXT_PUBLIC_API_URL=http://localhost:8080              │
│  └─ NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=test_key               │
│                                                              │
│  npm run dev                                                 │
│  ↓                                                           │
│  Reads .env.local automatically                            │
│  ↓                                                           │
│  process.env.NEXT_PUBLIC_API_URL = localhost:8080          │
│  ↓                                                           │
│  Frontend calls backend on localhost ✅                    │
└──────────────────────────────────────────────────────────────┘
             ↓↓↓ YOU RUN: git push
┌──────────────────────────────────────────────────────────────┐
│                      GITHUB REPOSITORY                       │
│                                                              │
│  ❌ .env.local NOT pushed (.gitignore ignores it)          │
│  ✅ Only code files pushed                                  │
│  ✅ cloudbuild-frontend.yaml has build args                │
│  ✅ scripts/deploy_*.sh has env vars                       │
│  ✅ terraform/*.tf has env configurations                  │
└──────────────────────────────────────────────────────────────┘
             ↓↓↓ YOU RUN: ./scripts/full_deployment.sh
┌──────────────────────────────────────────────────────────────┐
│                  DOCKER BUILD (Build Frontend)               │
│                                                              │
│  1. Cloud Build reads cloudbuild-frontend.yaml             │
│  2. Passes: --build-arg NEXT_PUBLIC_API_URL=<backend-url>  │
│  3. Docker uses ARG/ENV in Dockerfile                       │
│  4. Frontend built with URL baked in                        │
│  5. Image pushed to: us-central1-docker.pkg.dev/...        │
└──────────────────────────────────────────────────────────────┘
             ↓↓↓ CLOUD BUILD COMPLETES
┌──────────────────────────────────────────────────────────────┐
│                  CLOUD RUN DEPLOYMENT                        │
│                                                              │
│  1. Deploy script runs:                                     │
│     gcloud run deploy healio-frontend \                     │
│       --set-env-vars NEXT_PUBLIC_API_URL=<url>            │
│                                                              │
│  2. Cloud Run receives image + environment vars             │
│  3. Stores in Cloud Run service                             │
│  4. Frontend service starts with vars set                   │
│                                                              │
│  OR Terraform applies:                                      │
│     terraform apply                                         │
│     ↓                                                        │
│     Reads terraform.tfvars                                  │
│     ↓                                                        │
│     Sets env vars in resource definition                    │
│     ↓                                                        │
│     Cloud Run service updated with vars                     │
└──────────────────────────────────────────────────────────────┘
             ↓↓↓ SERVICE RUNNING ON CLOUD RUN
┌──────────────────────────────────────────────────────────────┐
│                   GOOGLE CLOUD (DEPLOYED)                    │
│                                                              │
│  [Cloud Run Service: healio-frontend]                       │
│  Environment Variables:                                      │
│  ├─ NEXT_PUBLIC_API_URL = "https://healio-backend-..."    │
│  └─ NEXT_PUBLIC_GOOGLE_MAPS_API_KEY = "AIza..."           │
│                                                              │
│  ↓ App reads these at runtime                              │
│                                                              │
│  process.env.NEXT_PUBLIC_API_URL = "https://healio-..."  │
│  ↓                                                           │
│  Frontend calls backend on Cloud Run ✅                   │
│                                                              │
│  [Cloud Run Service: healio-backend]                        │
│  Environment Variables:                                      │
│  ├─ GOOGLE_CLOUD_PROJECT = "healio-494416"                │
│  └─ PORT = "8080"                                           │
│                                                              │
│  ↓ App reads these at runtime                              │
│                                                              │
│  os.getenv("GOOGLE_CLOUD_PROJECT") = "healio-494416"      │
│  ↓                                                           │
│  Backend authenticates to Firestore, Vertex AI ✅          │
└──────────────────────────────────────────────────────────────┘
```

---

## 📋 **WHERE EACH ENVIRONMENT VARIABLE IS SET**

### **NEXT_PUBLIC_API_URL (Frontend)**

| Stage | File | How | Value |
|-------|------|-----|-------|
| **Local Dev** | .env.local | Manual creation | `http://localhost:8080` |
| **Docker Build** | cloudbuild-frontend.yaml | `--build-arg` | `https://healio-backend-...` |
| **Cloud Run Deploy** | deploy_frontend.sh | `--set-env-vars` | `https://healio-backend-...` |
| **Terraform** | main.tf | `env.value` | Backend URL from Terraform |

### **NEXT_PUBLIC_GOOGLE_MAPS_API_KEY (Frontend)**

| Stage | File | How | Value |
|-------|------|-----|-------|
| **Local Dev** | .env.local | Manual creation | Your test key |
| **Terraform** | terraform.tfvars | Variable input | Your API key |
| **Cloud Run** | main.tf | Sets from var | From tfvars |

### **GOOGLE_CLOUD_PROJECT (Backend)**

| Stage | File | How | Value |
|-------|------|-----|-------|
| **Deployment** | deploy_backend.sh | `--set-env-vars` | `healio-494416` |
| **Terraform** | main.tf | `env.value` | From `var.project_id` |
| **Runtime** | Python code reads it | `os.getenv()` | `healio-494416` |

### **PORT (Backend)**

| Stage | File | How | Value |
|-------|------|-----|-------|
| **Docker** | Dockerfile | `ENV PORT=...` | `8080` |
| **Cloud Run** | deploy_backend.sh | `--port` | `8080` |
| **Terraform** | main.tf | `env.value` | `8080` |

---

## ✅ **WHAT WAS DONE - SUMMARY**

### **1. Frontend Environment Setup:**
```
✅ Created frontend/.env.local (only on your computer)
✅ Added NEXT_PUBLIC_API_URL (points to backend)
✅ Added NEXT_PUBLIC_GOOGLE_MAPS_API_KEY (for maps)
✅ Modified frontend/Dockerfile with ARG/ENV
✅ Modified cloudbuild-frontend.yaml with --build-arg
✅ Modified scripts/deploy_frontend.sh with --set-env-vars
✅ Modified terraform/main.tf with env blocks
```

### **2. Backend Environment Setup:**
```
✅ Modified backend/Dockerfile with ENV PORT
✅ Modified scripts/deploy_backend.sh with --set-env-vars GOOGLE_CLOUD_PROJECT
✅ Modified terraform/main.tf with env blocks for GOOGLE_CLOUD_PROJECT + PORT
```

### **3. Terraform Configuration:**
```
✅ Created terraform/terraform.tfvars with configurable values
✅ Frontend env linked to backend URL automatically
✅ All env vars centralized in Terraform
```

---

## 🎯 **SIMPLE SUMMARY**

**Like a restaurant:**
- **Local Dev (.env.local)** = Your home kitchen recipe book
- **Docker Build Args** = Instructions for the restaurant's kitchen
- **Cloud Run --set-env-vars** = Telling restaurant staff where the kitchen is
- **Terraform** = The restaurant's operations manual that documents everything

**Path of a request:**
```
User fills form
  ↓
Frontend reads: process.env.NEXT_PUBLIC_API_URL
  ↓
Calls: https://healio-backend-...
  ↓
Backend receives request
  ↓
Backend reads: os.getenv("GOOGLE_CLOUD_PROJECT")
  ↓
Connects to Firestore using that project
  ↓
Writes data
  ↓
Response sent back to frontend ✅
```

---

**Does this make sense now?** 🎯











