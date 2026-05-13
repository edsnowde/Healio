output "backend_url" {
  description = "URL of the deployed backend service"
  value       = google_cloud_run_service.healio_backend.status[0].url
}

output "frontend_url" {
  description = "URL of the deployed frontend service"
  value       = google_cloud_run_service.healio_frontend.status[0].url
}

output "backend_service_account" {
  description = "Backend service account email"
  value       = google_service_account.healio_backend.email
}

output "frontend_service_account" {
  description = "Frontend service account email"
  value       = google_service_account.healio_frontend.email
}

output "firestore_database" {
  description = "Firestore database ID"
  value       = google_firestore_database.healio.name
}

output "project_id" {
  description = "Google Cloud Project ID"
  value       = var.project_id
}

output "region" {
  description = "Deployment region"
  value       = var.region
}
