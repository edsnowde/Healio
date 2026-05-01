# 🚀 REDEPLOYMENT COMMANDS - RUN THESE IN ORDER

## ⚠️ IMPORTANT: DO THIS FIRST

Make sure you're in the root project folder:
```bash
cd c:\Users\User\Desktop\activities_ABULANCE\Build For Bengaluru Hackathon_Reva university_roactract\Healio
```

---

## 🎨 STEP 1: REDEPLOY FRONTEND

### 1A. Build Frontend Locally
```bash
cd frontend
npm install
npm run build
cd ..
```

**Wait for:** "✓ Compiled successfully" message

---

### 1B. Build & Push to Cloud Registry
```bash
gcloud builds submit --config cloudbuild-frontend.yaml .
```

**Wait for:** "BUILD SUCCESS" and image pushed to Artifact Registry  
**Expected time:** 2-3 minutes  

---

### 1C. Deploy to Cloud Run
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

**Expected output:**
```
Service [healio-frontend] revision [healio-frontend-XXXXX] has been deployed and is serving 100 percent of traffic.
Service URL: https://healio-frontend-322299516577.us-central1.run.app
```

---

## ⚙️ STEP 2: REDEPLOY BACKEND

### 2A. Deploy Backend to Cloud Run
```bash
cd backend
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
cd ..
```

**Expected output:**
```
Service [healio-backend] revision [healio-backend-XXXXX] has been deployed and is serving 100 percent of traffic.
Service URL: https://healio-backend-322299516577.us-central1.run.app
```

---

## ✅ STEP 3: VERIFY DEPLOYMENT

### 3A. Check Both Services Are Running
```bash
gcloud run services list --region us-central1
```

**Expected output:** Both services should show "Ready" status

---

### 3B. Test Frontend
```bash
curl https://healio-frontend-322299516577.us-central1.run.app
```

**Expected:** HTML response (not error)

---

### 3C. Test Backend
```bash
curl https://healio-backend-322299516577.us-central1.run.app/health
```

**Expected:** `{"status":"ok"}` or similar response

---

## 📋 COMPLETE ONE-LINER (Copy & Paste)

If you want to deploy everything in sequence:

```powershell
cd "c:\Users\User\Desktop\activities_ABULANCE\Build For Bengaluru Hackathon_Reva university_roactract\Healio" ; `
cd frontend ; npm install ; npm run build ; cd .. ; `
gcloud builds submit --config cloudbuild-frontend.yaml . ; `
gcloud run deploy healio-frontend --image us-central1-docker.pkg.dev/healio-494416/cloud-run-source-deploy/healio-frontend:latest --platform managed --region us-central1 --allow-unauthenticated --port 3000 --memory 512Mi --cpu 1 ; `
cd backend ; `
gcloud run deploy healio-backend --source . --project healio-494416 --region us-central1 --platform managed --allow-unauthenticated --memory 2Gi --cpu 2 --timeout 300 --port 8080 --set-env-vars GOOGLE_CLOUD_PROJECT=healio-494416 ; `
cd .. ; `
gcloud run services list --region us-central1
```

---

## 🎯 LIVE URLS AFTER DEPLOYMENT

- **Frontend:** https://healio-frontend-322299516577.us-central1.run.app
- **Backend:** https://healio-backend-322299516577.us-central1.run.app

---

## 📊 WHAT HAPPENS IN EACH STEP

| Step | Action | Time | Status |
|------|--------|------|--------|
| 1A | Build frontend locally | < 1 min | Should say "✓ Compiled" |
| 1B | Build Docker image & push to registry | 2-3 min | Should say "BUILD SUCCESS" |
| 1C | Deploy to Cloud Run | < 1 min | Should show Service URL |
| 2A | Deploy backend | 1-2 min | Should show Service URL |
| 3A | Verify both running | < 1 min | Both should show "Ready" |

---

## ⚡ IF SOMETHING FAILS

### Frontend won't build?
```bash
cd frontend
npm cache clean --force
rm -r node_modules package-lock.json
npm install
npm run build
```

### Cloud Build failing?
```bash
gcloud builds log --region=us-central1 --limit=100
```
(shows last build errors)

### Backend deployment hanging?
Press `Ctrl+C` to stop, wait 10 seconds, then retry the backend deploy command

---

**Status:** Ready to deploy ✅  
**Project:** healio-494416  
**Region:** us-central1  
**Date:** 2026-05-01
