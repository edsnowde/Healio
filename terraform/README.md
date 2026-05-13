# 🏗️ Healio Infrastructure as Code (Terraform)

Production-grade Infrastructure-as-Code for Healio using HashiCorp Terraform.

## 📋 What's Managed

### Cloud Run Services
- ✅ **Backend Service** — FastAPI with Gemini AI agents
- ✅ **Frontend Service** — Next.js web application
- ✅ Auto-scaling configuration
- ✅ Service account management
- ✅ Public access (IAM bindings)

### Identity & Access Management
- ✅ Dedicated service accounts per service
- ✅ Role-based access control (RBAC)
- ✅ Vertex AI permissions
- ✅ Firestore database permissions
- ✅ Cloud Speech-to-Text permissions

### Google Cloud APIs
- ✅ Vertex AI Platform
- ✅ Firestore
- ✅ Cloud Speech-to-Text
- ✅ Cloud Run
- ✅ Cloud Build
- ✅ Artifact Registry

### Database
- ✅ Firestore database creation
- ✅ Firestore indexes for query optimization
- ✅ Default security rules

---

## 🚀 Quick Start

### Prerequisites
```bash
# Install Terraform (https://www.terraform.io/downloads)
terraform version

# Authenticate to GCP
gcloud auth application-default login

# Set your project
gcloud config set project healio-494416
```

### Deploy Infrastructure

```bash
cd terraform

# 1. Initialize Terraform (downloads providers)
terraform init

# 2. Plan deployment (shows what will be created)
terraform plan

# 3. Apply changes (creates infrastructure)
terraform apply

# 4. View outputs (service URLs)
terraform output
```

### Destroy Infrastructure (when done)
```bash
terraform destroy
```

---

## 📁 File Structure

```
terraform/
├── main.tf              ← Cloud Run, IAM, Firestore, APIs
├── variables.tf         ← Input variables
├── outputs.tf          ← Exported values
├── terraform.tfvars    ← Your configuration values
└── README.md           ← This file
```

### `main.tf` — Main Configuration
Defines:
- `google_cloud_run_service` — Backend & Frontend
- `google_service_account` — Service account creation
- `google_project_service` — API enablement
- `google_firestore_database` — Real-time database
- `google_firestore_index` — Query optimization

### `variables.tf` — Input Variables
- `project_id` — GCP project
- `region` — Deployment region (default: us-central1)
- `firestore_region` — Firestore location (default: us-central)
- `google_maps_api_key` — Maps integration
- Resource limits (memory, CPU)
- Monitoring configuration

### `terraform.tfvars` — Your Values
Edit this to customize:
- Project ID
- Region
- API keys
- Resource sizes
- Email for alerts

### `outputs.tf` — Exported Values
After deployment, outputs:
- Backend URL
- Frontend URL
- Service account emails
- Firestore database name

---

## 🔧 Configuration

### Before First Deploy
Edit `terraform.tfvars`:

```hcl
project_id           = "healio-494416"
region               = "us-central1"
google_maps_api_key  = "YOUR_KEY_HERE"  # Get from Cloud Console
alert_email          = "you@example.com"
```

### Resource Sizing
Adjust in `terraform.tfvars`:

```hcl
# Backend (AI pipeline — needs more resources)
backend_memory = "2Gi"    # 2GB RAM
backend_cpu    = "2"      # 2 CPUs

# Frontend (React app — lightweight)
frontend_memory = "512Mi"  # 512MB RAM
frontend_cpu    = "1"      # 1 CPU
```

---

## 📊 Service Accounts

Terraform creates two dedicated service accounts:

### 1. Backend Service Account
- Has: Vertex AI User, Firestore User, Speech-to-Text Client
- Runs backend Cloud Run service
- Calls AI models and database

### 2. Frontend Service Account
- Has: Basic Cloud Run permissions
- Runs frontend Cloud Run service
- No sensitive API access

---

## 🔍 Verification

After successful deployment:

```bash
# Show all outputs
terraform output

# Check backend is running
curl $(terraform output -raw backend_url)/health

# View created resources in Cloud Console
gcloud run services list --project healio-494416 --region us-central1
```

---

## 🔄 Updating Infrastructure

To update resources:

```bash
# Edit terraform.tfvars with new values
# Example: increase backend memory

terraform plan    # Review changes
terraform apply   # Apply changes
```

Terraform updates only changed resources, leaving others untouched.

---

## 🐛 Troubleshooting

### Terraform init fails
```bash
terraform init -upgrade
```

### Permission denied
```bash
gcloud auth application-default login
gcloud projects add-iam-policy-binding healio-494416 \
  --member="user:YOUR_EMAIL" \
  --role="roles/editor"
```

### Firestore already exists
If error about existing Firestore, remove from state:
```bash
terraform state rm google_firestore_database.healio
terraform apply
```

### Services not accessible
Check IAM bindings:
```bash
gcloud run services get-iam-policy healio-backend \
  --region us-central1 --project healio-494416
```

---

## 📝 Best Practices

1. **Always plan before apply**
   ```bash
   terraform plan -out=tfplan
   terraform apply tfplan
   ```

2. **Store state remotely** (for teams)
   ```bash
   terraform init -reconfigure \
     -backend-config="bucket=healio-tf-state" \
     -backend-config="prefix=prod"
   ```

3. **Use terraform.tfvars.example**
   ```bash
   cp terraform.tfvars terraform.tfvars.example
   git add terraform.tfvars.example
   # (don't commit terraform.tfvars with secrets)
   ```

4. **Tag resources**
   Add to main.tf:
   ```hcl
   labels = {
     project = "healio"
     env     = "prod"
     team    = "dev"
   }
   ```

---

## 📚 Resources

- [Terraform Google Provider Docs](https://registry.terraform.io/providers/hashicorp/google/latest)
- [Cloud Run Terraform Resource](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_run_v2_service)
- [Terraform Best Practices](https://cloud.google.com/docs/terraform)

---

**Created:** May 13, 2026  
**Project:** Healio PHC Triage System  
**Status:** Production-Ready Infrastructure-as-Code
