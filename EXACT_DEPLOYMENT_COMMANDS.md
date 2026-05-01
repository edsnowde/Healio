# 🎯 EXACT DEPLOYMENT COMMANDS USED

## ✅ BOTH BACKEND & FRONTEND DEPLOYMENT

---

## 🔧 BACKEND DEPLOYMENT COMMAND

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

**Status:** ✅ LIVE  
**URL:** https://healio-backend-322299516577.us-central1.run.app  
**Deployed:** 2026-04-28 08:00:30 UTC  
**Region:** us-central1  

---

## 🎨 FRONTEND DEPLOYMENT COMMANDS

### Command 1: Build Frontend Locally
```bash
cd frontend
npm run build
```
**Result:** ✅ 12 routes compiled, 0 errors

---

### Command 2: Build Docker Image via Cloud Build
```bash
cd ..
gcloud builds submit --config cloudbuild-frontend.yaml .
```
**Build Details:**
- Build ID: `2ae4f912-4ff2-4236-a6a5-3a63996e9184`
- Duration: 2 min 35 sec
- Status: ✅ SUCCESS
- Image URI: `us-central1-docker.pkg.dev/healio-494416/cloud-run-source-deploy/healio-frontend:latest`

---

### Command 3: Deploy to Cloud Run
```bash
gcloud run deploy healio-frontend \
  --image us-central1-docker.pkg.dev/healio-494416/cloud-run-source-deploy/healio-frontend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 3000
```


gcloud run deploy healio-backend `
  --source . `
  --project healio-494416 `
  --region us-central1 `
  --platform managed `
  --allow-unauthenticated `
  --memory 2Gi `
  --port 8080 `
  --set-env-vars GOOGLE_CLOUD_PROJECT=healio-494416

**Deployment Result:**
```
Service [healio-frontend] revision [healio-frontend-00001-bqm] has been deployed and is serving 100 percent of traffic.
Service URL: https://healio-frontend-322299516577.us-central1.run.app
```

**Status:** ✅ LIVE  
**URL:** https://healio-frontend-322299516577.us-central1.run.app  
**Deployed:** 2026-04-30 15:22:55 UTC  
**Region:** us-central1  
**Revision:** healio-frontend-00001-bqm  
**Traffic:** 100%  

---

## ✅ VERIFY BOTH SERVICES

### Command: List All Services
```bash
gcloud run services list --region us-central1
```

### Output (Both Services Running):
```
SERVICE: healio-backend
REGION: us-central1
URL: https://healio-backend-322299516577.us-central1.run.app
LAST DEPLOYED BY: chotullas@gmail.com
LAST DEPLOYED AT: 2026-04-28T08:00:30.247809Z

SERVICE: healio-frontend
REGION: us-central1
URL: https://healio-frontend-322299516577.us-central1.run.app
LAST DEPLOYED BY: chotullas@gmail.com
LAST DEPLOYED AT: 2026-04-30T15:22:55.280685Z
```

---

## 📊 DEPLOYMENT SUMMARY

| Service | Command | Duration | Status | URL |
|---------|---------|----------|--------|-----|
| **Backend** | `gcloud run deploy healio-backend --source . --project healio-494416 ...` | N/A | ✅ LIVE | https://healio-backend-322299516577.us-central1.run.app |
| **Frontend Build** | `npm run build` | < 1 min | ✅ SUCCESS | N/A |
| **Frontend Cloud Build** | `gcloud builds submit --config cloudbuild-frontend.yaml .` | 2m 35s | ✅ SUCCESS | Artifact Registry |
| **Frontend Deploy** | `gcloud run deploy healio-frontend --image ... --platform managed ...` | < 1 min | ✅ LIVE | https://healio-frontend-322299516577.us-central1.run.app |

---

## 🎯 QUICK REFERENCE

**To redeploy backend:**
```bash
gcloud run deploy healio-backend --source . --project healio-494416 --region us-central1 --platform managed --allow-unauthenticated --memory 2Gi --cpu 2 --timeout 300 --port 8080 --set-env-vars GOOGLE_CLOUD_PROJECT=healio-494416
```

**To redeploy frontend:**
```bash
gcloud builds submit --config cloudbuild-frontend.yaml .
gcloud run deploy healio-frontend --image us-central1-docker.pkg.dev/healio-494416/cloud-run-source-deploy/healio-frontend:latest --platform managed --region us-central1 --allow-unauthenticated --port 3000
```

**To check service status:**
```bash
gcloud run services list --region us-central1
```

---

**Date:** 2026-04-30  
**Status:** ✅ BOTH SERVICES LIVE & OPERATIONAL
