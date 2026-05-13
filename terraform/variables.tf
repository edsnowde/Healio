variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
  default     = "healio-494416"
}

variable "region" {
  description = "Google Cloud region for Cloud Run services"
  type        = string
  default     = "us-central1"
}

variable "firestore_region" {
  description = "Firestore multi-region location"
  type        = string
  default     = "us-central"
}

variable "google_maps_api_key" {
  description = "Google Maps API Key for frontend"
  type        = string
  sensitive   = true
  default     = ""
}

variable "backend_memory" {
  description = "Memory allocated to backend Cloud Run service"
  type        = string
  default     = "2Gi"
}

variable "backend_cpu" {
  description = "CPU allocated to backend Cloud Run service"
  type        = string
  default     = "2"
}

variable "frontend_memory" {
  description = "Memory allocated to frontend Cloud Run service"
  type        = string
  default     = "512Mi"
}

variable "frontend_cpu" {
  description = "CPU allocated to frontend Cloud Run service"
  type        = string
  default     = "1"
}

variable "enable_monitoring" {
  description = "Enable Cloud Monitoring and alerting"
  type        = bool
  default     = true
}

variable "alert_email" {
  description = "Email for alert notifications"
  type        = string
  default     = ""
}
