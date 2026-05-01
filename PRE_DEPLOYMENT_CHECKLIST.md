# ✅ PRE-DEPLOYMENT CHECKLIST & SETUP GUIDE

## 📋 WHAT I FOUND AFTER READING ALL FILES

Your project is **98% ready** for deployment. Just a few environment variables need to be configured. Here's what needs to be done:

---

## 🔍 CURRENT STATUS

| Component | Status | Details |
|-----------|--------|---------|
| Frontend Build | ✅ OK | All packages installed, Google Maps library added |
| Backend Setup | ✅ OK | FastAPI properly configured with CORS |
| Firebase | ✅ OK | Already configured in `frontend/lib/firebase.ts` |
| Google Maps API Key | ✅ SET | Found in `frontend/.env.local` |
| Backend API URL | ❌ MISSING | Needs to be added to frontend/.env.local |
| Docker Images | ✅ OK | Both Frontend & Backend Dockerfiles are correct |

---

## 🎯 WHAT YOU NEED TO DO BEFORE DEPLOYMENT

### STEP 1: Update Frontend Environment Variables

**Edit:** `frontend/.env.local`

**Current Content:**
```env
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=AIzaSyBRy_riN5meM-iasdyEXc3c6NadgbQMLVA
```

**Change To:**
```env
# Google Maps API Key (for interactive map display)
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=AIzaSyBRy_riN5meM-iasdyEXc3c6NadgbQMLVA

# Backend API URL (change this for production)
NEXT_PUBLIC_API_URL=https://healio-backend-322299516577.us-central1.run.app
```

**⚠️ IMPORTANT:** After you deploy the backend, you'll know the exact URL. The format is:
```
https://healio-backend-[PROJECT_NUMBER].us-central1.run.app
```

---

### STEP 2: Understand Frontend-Backend Connectivity

**Frontend Code** (`frontend/lib/api.ts`):
```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8080'
```

**What This Means:**
- **Locally (dev):** Uses `http://127.0.0.1:8080` (your local backend)
- **Production:** Uses `NEXT_PUBLIC_API_URL` env var (Cloud Run backend URL)

**Backend CORS Config** (`backend/api/main.py`):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ✅ Already set to allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**✅ This is correct for now** (but in production, you should change `["*"]` to specific frontend URL)

---

## 🗺️ GOOGLE MAPS API SETUP

### ✅ ALREADY DONE IN YOUR PROJECT

Your `.env.local` already has the Google Maps API key:
```
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=AIzaSyBRy_riN5meM-iasdyEXc3c6NadgbQMLVA
```

### What This Key Does:
- Enables the interactive map on `/surveillance` page
- Shows outbreak cluster locations in Bengaluru
- Allows zoom, pan, and marker clicks

### How It Works:
1. Frontend loads Google Maps library using this key
2. `ClusterMap.tsx` component renders interactive map
3. Cluster markers appear automatically from Firestore data
4. Each marker shows patient count + symptoms on hover

**✅ No additional setup needed for Google Maps!**

---

## 🔧 DEPLOYMENT WORKFLOW

### BEFORE YOU RUN DEPLOY COMMANDS:

**Local Testing** (Optional):
```bash
cd frontend
npm run dev
# Visit http://localhost:3001
# Check if everything works locally
```

### THEN FOLLOW THESE EXACT STEPS:

**Step 1:** Update `frontend/.env.local` with backend URL ⚠️ (CRITICAL!)

**Step 2:** Build & Deploy Frontend:
```bash
cd frontend && npm install && npm run build && cd ..
gcloud builds submit --config cloudbuild-frontend.yaml .
gcloud run deploy healio-frontend --image us-central1-docker.pkg.dev/healio-494416/cloud-run-source-deploy/healio-frontend:latest --platform managed --region us-central1 --allow-unauthenticated --port 3000 --memory 512Mi --cpu 1
```

**Step 3:** Deploy Backend:
```bash
cd backend && gcloud run deploy healio-backend --source . --project healio-494416 --region us-central1 --platform managed --allow-unauthenticated --memory 2Gi --cpu 2 --timeout 300 --port 8080 --set-env-vars GOOGLE_CLOUD_PROJECT=healio-494416 && cd ..
```

**Step 4:** Check Deployment:
```bash
gcloud run services list --region us-central1
```

---

## 🔗 API ENDPOINTS AVAILABLE

Your backend has these endpoints ready:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/triage` | POST | Submit symptom text (text or voice transcribed) |
| `/analyze/with-multimodal` | POST | Submit text + images/videos |
| `/queue` | GET | Fetch all patients in queue |
| `/queue/department/{dept}` | GET | Get queue by department |
| `/surveillance/clusters` | GET | Get outbreak alerts |
| `/surveillance/summary` | GET | Get outbreak statistics |
| `/health` | GET | Check backend status |

**Frontend connects to all these via** `frontend/lib/api.ts`

---

## 📱 HOW EVERYTHING CONNECTS

```
┌─────────────────────────────────────────────────────────────┐
│                   User's Browser                             │
│  (https://healio-frontend-...-us-central1.run.app)          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTP Requests
                     │ (fetch API calls)
                     │
         ┌───────────▼──────────────┐
         │  NEXT_PUBLIC_API_URL     │
         │  Environment Variable    │
         │  Points to Backend URL   │
         └───────────┬──────────────┘
                     │
                     │ HTTPS
                     │
    ┌────────────────▼─────────────────┐
    │  Healio Backend (FastAPI)         │
    │  https://healio-backend-...      │
    │  :us-central1.run.app            │
    │                                   │
    │  - /triage (POST)                │
    │  - /queue (GET)                  │
    │  - /surveillance (GET)           │
    │  - Connected to Firestore        │
    │  - Connected to Vertex AI        │
    │  - Connected to Google Speech    │
    └────────────────┬──────────────────┘
                     │
                     │ API Calls
                     │
    ┌────────────────▼──────────────────┐
    │  Firebase Firestore               │
    │  (Database + Real-time sync)     │
    │                                   │
    │  Collections:                    │
    │  - patients/                     │
    │  - patient_queue/                │
    │  - detected_clusters/            │
    │  - outbreak_surveillance/        │
    └───────────────────────────────────┘
```

---

## ⚠️ CRITICAL: WHAT YOU MUST DO BEFORE DEPLOYING

### 1️⃣ EDIT `.env.local` - ADD BACKEND URL

**File:** `frontend/.env.local`

**Add this line** (after you deploy backend, replace with actual URL):
```env
NEXT_PUBLIC_API_URL=https://healio-backend-322299516577.us-central1.run.app
```

**Why?** Without this, frontend won't know where to send API requests!

### 2️⃣ REBUILD FRONTEND IMAGE

After changing `.env.local`, the Docker image needs to rebuild so these variables are baked in:

```bash
cd frontend && npm run build && cd ..
gcloud builds submit --config cloudbuild-frontend.yaml .
```

### 3️⃣ DEPLOY BOTH SERVICES

Then follow the standard deployment commands.

---

## 🚀 FINAL DEPLOYMENT CHECKLIST

Before you run deploy commands:

- [ ] Read this guide completely
- [ ] Edit `frontend/.env.local` with `NEXT_PUBLIC_API_URL`
- [ ] Frontend builds without errors (`npm run build`)
- [ ] No console errors when visiting `http://localhost:3001` (optional)
- [ ] Ready to run deployment commands

---

## 📊 EXPECTED OUTCOMES

### After Frontend Deployment:
✅ Frontend loads at: `https://healio-frontend-322299516577.us-central1.run.app`  
✅ Google Maps displays on `/surveillance` page  
✅ Form submits to backend at URL in `NEXT_PUBLIC_API_URL`  

### After Backend Deployment:
✅ Backend responds at: `https://healio-backend-322299516577.us-central1.run.app/health`  
✅ `/triage` endpoint accepts POST requests  
✅ Real-time data flows to Firestore  
✅ Queue updates visible in frontend  

### End Result:
✅ Users can:
1. Submit intake forms (text/voice/images)
2. See real-time triage queue
3. View patient details
4. See outbreak clusters on interactive Google Map
5. Get clinical decision support from 3-agent AI pipeline

---

## 🆘 TROUBLESHOOTING

### "Frontend shows 'Cannot connect to API'"
**Solution:** 
1. Check `NEXT_PUBLIC_API_URL` is set in `.env.local`
2. Verify backend URL is correct
3. Rebuild and redeploy frontend

### "Backend not responding"
**Solution:**
1. Check service is running: `gcloud run services describe healio-backend --region us-central1`
2. View logs: `gcloud run services logs read healio-backend --region us-central1 --limit 50`
3. Check Firebase credentials are set up

### "Google Map not showing"
**Solution:**
1. Check API key in `.env.local`
2. Verify Maps JavaScript API is enabled in GCP console
3. Check browser console for errors

### "CORS errors"
**Solution:**
1. Backend already allows all origins (for now)
2. Check request headers match

---

## ✅ SUMMARY

**What's Required:**
1. ✅ Add `NEXT_PUBLIC_API_URL` to `frontend/.env.local`
2. ✅ Google Maps API key already set
3. ✅ Firebase already configured
4. ✅ CORS already enabled

**All other components are ready to deploy!**

Once you add the backend URL to `.env.local`, you can proceed with the deployment commands.

---

**Ready to deploy?** Let me know and I'll confirm the exact URLs to use! 🚀
