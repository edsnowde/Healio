# 🔧 Healio Deployment Scripts

Automated bash scripts for deploying Healio infrastructure to Google Cloud Run.

## Prerequisites

- Google Cloud SDK installed (`gcloud`)
- Authenticated to GCP project (`gcloud auth login`)
- Bash 3.2+
- Execute permissions on scripts

## 📋 Available Scripts

### 1. `setup_iam.sh` — IAM Configuration
Grants required Google Cloud roles to the service account:
- ✅ Vertex AI User (for Gemini AI models)
- ✅ Firestore User (for real-time database)
- ✅ Cloud Speech-to-Text Client (for audio transcription)
- ✅ Enables all required APIs

```bash
./scripts/setup_iam.sh
```

**Run first!** Must complete before deploying services.

---

### 2. `deploy_backend.sh` — Backend Deployment
Deploys FastAPI backend to Cloud Run with:
- 2 CPU cores, 2GB memory
- 300-second timeout for long-running agent pipelines
- Port 8080 exposed
- Environment variables configured

```bash
./scripts/deploy_backend.sh
```

**Requirements:** IAM setup complete

---

### 3. `deploy_frontend.sh` — Frontend Deployment
Builds Next.js frontend and deploys to Cloud Run with:
- Cloud Build automated Docker image build
- 512MB memory, 1 CPU
- Frontend → Backend API connectivity
- Environment variables for Google Maps API

```bash
./scripts/deploy_frontend.sh
```

**Requirements:** IAM setup complete, Backend deployed

---

### 4. `full_deployment.sh` — Complete Pipeline
Orchestrates the full deployment in correct order:
1. IAM setup (if not done)
2. Backend deployment
3. Frontend deployment

```bash
./scripts/full_deployment.sh
```

**One-command deployment** — runs everything!

---

## 🚀 Quick Start

### First-time setup:
```bash
chmod +x scripts/*.sh
./scripts/full_deployment.sh
```

### Redeployment only:
```bash
./scripts/deploy_backend.sh
./scripts/deploy_frontend.sh
```

---

## 📊 Configuration

Edit these files to customize:
- `deploy_backend.sh` — Change `MEMORY`, `CPU`, `TIMEOUT`
- `deploy_frontend.sh` — Change `PORT`, `MEMORY`, `API_URL`
- `setup_iam.sh` — Add/remove IAM roles

---

## ✅ Verification

After deployment, verify services are running:

```bash
# Check Cloud Run services
gcloud run services list --project healio-494416 --region us-central1

# Test backend health
curl https://healio-backend-322299516577.us-central1.run.app/health

# Check deployment logs
gcloud run services describe healio-backend --region us-central1 --project healio-494416
```

---

## 🐛 Troubleshooting

**Permission denied errors:**
```bash
chmod +x scripts/*.sh
```

**gcloud not found:**
```bash
# Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install
```

**Deployment timeout:**
- Increase `TIMEOUT` in `deploy_backend.sh`
- Check Cloud Build logs for build failures

**IAM permission errors:**
- Run `setup_iam.sh` again
- Ensure service account has correct roles

---

## 📝 Production Notes

- Scripts use `set -e` to fail fast on errors
- All commands run with `--quiet` flag to reduce noise
- Deployment logs are automatically captured in Cloud Logging
- Monitor deployments in Cloud Console: https://console.cloud.google.com/run

---

**Created:** May 13, 2026  
**Used for:** Healio PHC Triage System
