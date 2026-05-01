# 🚀 STEP-BY-STEP DEPLOYMENT GUIDE

## ⚠️ VERY IMPORTANT: DO THIS FIRST BEFORE ANY DEPLOYMENT

from claude chat When i got error

Read everything. Here's the full picture of what's broken:

**Problem 1 (Critical) — Frontend API URL is `undefined`:**
From the browser log: `POST https://healio-frontend-322299516577.us-central1.run.app/undefined/triage`

`API_BASE` is `undefined` because `NEXT_PUBLIC_API_URL` env variable isn't being baked into the Docker image at build time. The `.env.local` file isn't being picked up during Cloud Build.

**Problem 2 — Backend Firestore permission (403):**
`ERROR: 403 Missing or insufficient permissions` when writing to patients collection. The `roles/datastore.user` grant may not have propagated or wasn't applied correctly.

**Fix both — run these in order:**

**Step 1: Fix the env variable — set it at Cloud Run level (most reliable way):**
```powershell
gcloud run services update healio-frontend `
  --region us-central1 `
  --set-env-vars NEXT_PUBLIC_API_URL=https://healio-backend-322299516577.us-central1.run.app
```

**Step 2: Rebuild and redeploy frontend:**
```powershell
cd "c:\Users\User\Desktop\activities_ABULANCE\Build For Bengaluru Hackathon_Reva university_roactract\Healio"
gcloud builds submit --config cloudbuild-frontend.yaml .
gcloud run deploy healio-frontend `
  --image us-central1-docker.pkg.dev/healio-494416/cloud-run-source-deploy/healio-frontend:latest `
  --platform managed --region us-central1 --allow-unauthenticated `
  --port 3000 --memory 512Mi --cpu 1 `
  --set-env-vars NEXT_PUBLIC_API_URL=https://healio-backend-322299516577.us-central1.run.app
```

**Step 3: Fix Firestore permission on backend:**
```powershell
gcloud projects add-iam-policy-binding healio-494416 `
  --member="serviceAccount:322299516577-compute@developer.gserviceaccount.com" `
  --role="roles/datastore.owner"
```

Run all 3 and paste the output here.

-----------------------------------

Here are the exact changes needed:

**1. Replace your `frontend/Dockerfile` with this:**

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

**2. Replace your `cloudbuild-frontend.yaml` with this:**

```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '--build-arg'
      - 'NEXT_PUBLIC_API_URL=https://healio-backend-322299516577.us-central1.run.app'
      - '-t'
      - 'us-central1-docker.pkg.dev/healio-494416/cloud-run-source-deploy/healio-frontend:latest'
      - '-f'
      - 'frontend/Dockerfile'
      - 'frontend/'

  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - 'us-central1-docker.pkg.dev/healio-494416/cloud-run-source-deploy/healio-frontend:latest'

images:
  - 'us-central1-docker.pkg.dev/healio-494416/cloud-run-source-deploy/healio-frontend:latest'

options:
  machineType: 'N1_HIGHCPU_8'
  logging: CLOUD_LOGGING_ONLY

timeout: '1800s'
```

**3. Then run these commands:**

```powershell
# Fix Firestore permission first
gcloud projects add-iam-policy-binding healio-494416 `
  --member="serviceAccount:322299516577-compute@developer.gserviceaccount.com" `
  --role="roles/datastore.owner"

# Rebuild and redeploy frontend
cd "c:\Users\User\Desktop\activities_ABULANCE\Build For Bengaluru Hackathon_Reva university_roactract\Healio"
gcloud builds submit --config cloudbuild-frontend.yaml .
gcloud run deploy healio-frontend `
  --image us-central1-docker.pkg.dev/healio-494416/cloud-run-source-deploy/healio-frontend:latest `
  --platform managed --region us-central1 --allow-unauthenticated `
  --port 3000 --memory 512Mi --cpu 1
```

Paste output here when done.


-------------------------------

### PRE-DEPLOYMENT SETUP (1 MINUTE)

You need to edit ONE file to connect frontend to backend:

**File to Edit:** `frontend/.env.local`

**Location:** 
```
c:\Users\User\Desktop\activities_ABULANCE\Build For Bengaluru Hackathon_Reva university_roactract\Healio\frontend\.env.local
```

**Current Content:**
```env
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=AIzaSyBRy_riN5meM-iasdyEXc3c6NadgbQMLVA
```

**Change To:**
```env
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=AIzaSyBRy_riN5meM-iasdyEXc3c6NadgbQMLVA
NEXT_PUBLIC_API_URL=https://healio-backend-322299516577.us-central1.run.app
```

**✅ Save the file and come back here!**

---

## 📋 DEPLOYMENT STEPS (COPY & PASTE EACH ONE)

### PHASE 1: BUILD & DEPLOY FRONTEND

---

#### STEP 1: Navigate to Root Directory
```bash
cd c:\Users\User\Desktop\activities_ABULANCE\Build For Bengaluru Hackathon_Reva university_roactract\Healio
```

**Expected:** You should see folder contents including `frontend/`, `backend/`, `cloudbuild-frontend.yaml`

---

#### STEP 2: Install Frontend Dependencies
```bash
cd frontend
npm install
```

**Expected Output:**
- See "added X packages"
- Completes without errors

**⏱️ Time:** 2-3 minutes

---

#### STEP 3: Build Frontend (Local)
```bash
npm run build
```

**Expected Output:**
```
✓ Compiled successfully
✓ All checks passed

Routes (prerendered):
/
/dashboard
/intake
/kn/dashboard
/kn/intake
/surveillance
... etc
```

**✅ Success if:** No errors, all routes compiled

**❌ If you see errors:** Let me know the error message

**⏱️ Time:** 2-3 minutes

---

#### STEP 4: Go Back to Root
```bash
cd ..
```

**Expected:** You're back in the Healio root folder

---

#### STEP 5: Build Docker Image & Push to Cloud Registry
```bash
gcloud builds submit --config cloudbuild-frontend.yaml .
```

**Expected Output:**
```
BUILD
id: 2ae4f912-4ff2-4236-a6a5-3a63996e9184
...
IMAGES
us-central1-docker.pkg.dev/healio-494416/cloud-run-source-deploy/healio-frontend:latest
BUILD SUCCESS
```

**✅ Success if:** You see "BUILD SUCCESS" at the end

**⏱️ Time:** 3-5 minutes (it downloads dependencies and builds)

---

#### STEP 6: Deploy Frontend to Cloud Run
```bash
gcloud run deploy healio-frontend `
  --image us-central1-docker.pkg.dev/healio-494416/cloud-run-source-deploy/healio-frontend:latest `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --port 3000 `
  --memory 512Mi `
  --cpu 1
```

**Expected Output:**
```
Service [healio-frontend] revision [healio-frontend-00002-xxx] has been deployed 
and is serving 100 percent of traffic.

Service URL: https://healio-frontend-322299516577.us-central1.run.app
```

**✅ Success if:** You see the Service URL

**⏱️ Time:** 1-2 minutes

---

### PHASE 2: DEPLOY BACKEND

---

#### STEP 7: Go to Backend Folder
```bash
cd backend
```

**Expected:** You're inside the backend directory

---

#### STEP 8: Deploy Backend to Cloud Run
```bash
gcloud run deploy healio-backend `
  --source . `
  --project healio-494416 `
  --region us-central1 `
  --platform managed `
  --allow-unauthenticated `
  --memory 2Gi `
  --cpu 2 `
  --timeout 300 `
  --port 8080 `
  --set-env-vars GOOGLE_CLOUD_PROJECT=healio-494416
```

**Expected Output:**
```
Service [healio-backend] revision [healio-backend-00002-xxx] has been deployed 
and is serving 100 percent of traffic.

Service URL: https://healio-backend-322299516577.us-central1.run.app
```

**✅ Success if:** You see the Service URL

**⏱️ Time:** 3-5 minutes (it downloads dependencies and builds)

---

#### STEP 9: Go Back to Root
```bash
cd ..
```

---

### PHASE 3: VERIFY DEPLOYMENT

---

#### STEP 10: Check Both Services Are Running
```bash
gcloud run services list --region us-central1
```

**Expected Output:**
```
SERVICE          REGION         URL                                             STATUS
healio-backend   us-central1    https://healio-backend-322299516577...         Ready
healio-frontend  us-central1    https://healio-frontend-322299516577...        Ready
```

**✅ Success if:** Both show "Ready" status

---

#### STEP 11: Test Frontend Works
```bash
curl https://healio-frontend-322299516577.us-central1.run.app
```

**Expected Output:** HTML code (page content) - not an error

---

#### STEP 12: Test Backend Works
```bash
curl https://healio-backend-322299516577.us-central1.run.app/health
```

**Expected Output:** JSON response like:
```json
{"status":"ok"}
```

or similar response (not an error)

---

## ✅ YOU'RE DONE!

If all steps above completed successfully, your app is **LIVE** and ready!

---

## 🌐 YOUR LIVE URLS

- **Frontend:** https://healio-frontend-322299516577.us-central1.run.app
- **Backend:** https://healio-backend-322299516577.us-central1.run.app

---

## 🧪 TEST YOUR DEPLOYMENT

### From Your Browser:

1. **Open Frontend:**
   ```
   https://healio-frontend-322299516577.us-central1.run.app
   ```
   ✅ You should see the Healio landing page

2. **Go to Intake:**
   ```
   https://healio-frontend-322299516577.us-central1.run.app/intake
   ```
   ✅ You should see the patient intake form

3. **Test Submission:**
   - Enter name
   - Enter symptoms
   - Click submit
   ✅ Should show triage result (Red/Yellow/Green)

4. **Check Dashboard:**
   ```
   https://healio-frontend-322299516577.us-central1.run.app/dashboard
   ```
   ✅ Should show queue with your submitted patient

5. **Check Surveillance:**
   ```
   https://healio-frontend-322299516577.us-central1.run.app/surveillance
   ```
   ✅ Should show interactive Google Map

---

## ❌ TROUBLESHOOTING

### If Step 3 (npm run build) Fails:
```bash
cd frontend
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
npm run build
cd ..
```

### If Step 5 (gcloud builds submit) Fails:
Check the build logs:
```bash
gcloud builds log --region=us-central1 --limit=100
```

### If Step 6 (gcloud run deploy frontend) Fails:
Check if image exists:
```bash
gcloud artifacts docker images list us-central1-docker.pkg.dev/healio-494416/cloud-run-source-deploy/
```

### If Step 8 (gcloud run deploy backend) Fails:
View backend logs:
```bash
gcloud run services logs read healio-backend --region us-central1 --limit 50
```

### If Frontend Shows "Cannot Connect to API":
1. Check `.env.local` has `NEXT_PUBLIC_API_URL` set
2. Verify backend URL is correct
3. Run Steps 2-6 again to rebuild frontend with correct URL

### If Google Map Not Showing:
1. Check browser console (F12) for errors
2. Verify API key in `frontend/.env.local`
3. Rebuild frontend

---

## 📊 WHAT EACH STEP DOES

| Step | Action | Time | Purpose |
|------|--------|------|---------|
| 1-4 | Setup | 1 min | Prepare environment |
| 2 | npm install | 2 min | Install dependencies |
| 3 | npm run build | 3 min | Compile frontend code |
| 5 | gcloud build | 5 min | Build Docker image |
| 6 | deploy frontend | 2 min | Upload to Cloud Run |
| 7-9 | deploy backend | 5 min | Upload to Cloud Run |
| 10 | verify | 1 min | Check both running |
| 11-12 | test | 1 min | Confirm working |

**Total Time:** ~20-25 minutes

---

## 🎯 SUMMARY

**What you're doing:**
1. Installing latest packages ✅
2. Building frontend code ✅
3. Creating Docker image ✅
4. Uploading to Google Cloud ✅
5. Deploying backend ✅
6. Testing everything works ✅

**What happens after deployment:**
- Users visit your frontend URL
- Frontend connects to backend using `NEXT_PUBLIC_API_URL`
- Backend processes requests, talks to Firebase + AI
- Results show in real-time
- Google Maps shows outbreak clusters
- Everything is LIVE! 🎉

---

## ⚠️ IMPORTANT NOTES

- **Do NOT skip the `.env.local` edit** - this is critical!
- Each `gcloud` command waits for completion before moving to next
- If any step fails, stop and let me know the error
- After deployment, changes to frontend require rebuilding
- After deployment, changes to backend require redeploying
- Google Maps API key is already configured ✅

---

**Questions? Let me know which step you're on and I can help!** 🚀
