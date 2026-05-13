terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ─────────────────────────────────────────────────────────
# Cloud Run — Backend Service
# ─────────────────────────────────────────────────────────

resource "google_cloud_run_service" "healio_backend" {
  name            = "healio-backend"
  location        = var.region
  project         = var.project_id
  
  template {
    spec {
      service_account_name = google_service_account.healio_backend.email
      
      containers {
        image = "us-central1-docker.pkg.dev/${var.project_id}/cloud-run-source-deploy/healio-backend:latest"
        
        ports {
          container_port = 8080
        }
        
        env {
          name  = "GOOGLE_CLOUD_PROJECT"
          value = var.project_id
        }
        
        env {
          name  = "PORT"
          value = "8080"
        }
        
        resources {
          limits = {
            memory = "2Gi"
            cpu    = "2"
          }
        }
      }
      
      timeout_seconds = 300
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale"       = "100"
        "autoscaling.knative.dev/minScale"       = "1"
        "run.googleapis.com/cpu-throttling"      = "false"
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  depends_on = [
    google_service_account_iam_member.backend_vertex_ai,
    google_service_account_iam_member.backend_firestore,
    google_service_account_iam_member.backend_speech,
  ]
}

# Allow public access to backend
resource "google_cloud_run_service_iam_member" "backend_public" {
  service  = google_cloud_run_service.healio_backend.name
  location = google_cloud_run_service.healio_backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ─────────────────────────────────────────────────────────
# Cloud Run — Frontend Service
# ─────────────────────────────────────────────────────────

resource "google_cloud_run_service" "healio_frontend" {
  name            = "healio-frontend"
  location        = var.region
  project         = var.project_id
  
  template {
    spec {
      service_account_name = google_service_account.healio_frontend.email
      
      containers {
        image = "us-central1-docker.pkg.dev/${var.project_id}/cloud-run-source-deploy/healio-frontend:latest"
        
        ports {
          container_port = 3000
        }
        
        env {
          name  = "NEXT_PUBLIC_API_URL"
          value = google_cloud_run_service.healio_backend.status[0].url
        }
        
        env {
          name  = "NEXT_PUBLIC_GOOGLE_MAPS_API_KEY"
          value = var.google_maps_api_key
        }
        
        resources {
          limits = {
            memory = "512Mi"
            cpu    = "1"
          }
        }
      }
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "50"
        "autoscaling.knative.dev/minScale" = "1"
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  depends_on = [google_service_account_iam_member.frontend_basic]
}

# Allow public access to frontend
resource "google_cloud_run_service_iam_member" "frontend_public" {
  service  = google_cloud_run_service.healio_frontend.name
  location = google_cloud_run_service.healio_frontend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ─────────────────────────────────────────────────────────
# Service Accounts
# ─────────────────────────────────────────────────────────

resource "google_service_account" "healio_backend" {
  account_id   = "healio-backend"
  display_name = "Healio Backend Service Account"
  project      = var.project_id
}

resource "google_service_account" "healio_frontend" {
  account_id   = "healio-frontend"
  display_name = "Healio Frontend Service Account"
  project      = var.project_id
}

# ─────────────────────────────────────────────────────────
# IAM Bindings — Backend
# ─────────────────────────────────────────────────────────

resource "google_service_account_iam_member" "backend_vertex_ai" {
  service_account_id = google_service_account.healio_backend.name
  role               = "roles/aiplatform.user"
  member             = "serviceAccount:${google_service_account.healio_backend.email}"
}

resource "google_service_account_iam_member" "backend_firestore" {
  service_account_id = google_service_account.healio_backend.name
  role               = "roles/datastore.user"
  member             = "serviceAccount:${google_service_account.healio_backend.email}"
}

resource "google_service_account_iam_member" "backend_speech" {
  service_account_id = google_service_account.healio_backend.name
  role               = "roles/speech.client"
  member             = "serviceAccount:${google_service_account.healio_backend.email}"
}

# ─────────────────────────────────────────────────────────
# IAM Bindings — Frontend
# ─────────────────────────────────────────────────────────

resource "google_service_account_iam_member" "frontend_basic" {
  service_account_id = google_service_account.healio_frontend.name
  role               = "roles/editor"
  member             = "serviceAccount:${google_service_account.healio_frontend.email}"
}

# ─────────────────────────────────────────────────────────
# Google APIs — Enable Required Services
# ─────────────────────────────────────────────────────────

resource "google_project_service" "required_apis" {
  for_each = toset([
    "aiplatform.googleapis.com",
    "firestore.googleapis.com",
    "speech.googleapis.com",
    "cloudrun.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "containerregistry.googleapis.com",
  ])

  project = var.project_id
  service = each.value
  
  disable_on_destroy = false
}

# ─────────────────────────────────────────────────────────
# Firestore Database (if not already created)
# ─────────────────────────────────────────────────────────

resource "google_firestore_database" "healio" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.firestore_region
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.required_apis]
}

# ─────────────────────────────────────────────────────────
# Firestore Indexes (for efficient querying)
# ─────────────────────────────────────────────────────────

resource "google_firestore_index" "patient_queue_triage" {
  collection = "patient_queue"
  database   = google_firestore_database.healio.name
  project    = var.project_id

  fields {
    field_path = "triage_color"
    order      = "ASCENDING"
  }

  fields {
    field_path = "__name__"
    order      = "DESCENDING"
  }
}

resource "google_firestore_index" "outbreak_timestamp" {
  collection = "outbreak_surveillance"
  database   = google_firestore_database.healio.name
  project    = var.project_id

  fields {
    field_path = "timestamp"
    order      = "DESCENDING"
  }

  fields {
    field_path = "severity_category"
    order      = "ASCENDING"
  }
}
