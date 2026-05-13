#!/bin/bash
# Setup Cloud Monitoring Uptime Checks for Healio
# Monitors backend and frontend health endpoints

set -e

PROJECT_ID="healio-494416"
BACKEND_URL="https://healio-backend-322299516577.us-central1.run.app/health"
FRONTEND_URL="https://healio-frontend-322299516577.us-central1.run.app"

echo "📊 Creating Cloud Monitoring Uptime Checks..."
echo ""

# ─────────────────────────────────────────────────────
# Backend Uptime Check
# ─────────────────────────────────────────────────────

echo "✅ Creating Backend Health Check..."
gcloud monitoring uptime create backend-health \
  --display-name="Healio Backend - Health Check" \
  --resource-type="uptime-url" \
  --monitored-resource-path="monitored_resource.labels.host=$BACKEND_URL" \
  --tcp-check-port=443 \
  --period=60 \
  --timeout=10 \
  --regions="USA","EUROPE","ASIA_PACIFIC" \
  --project=$PROJECT_ID || echo "Note: Backend check may already exist"

echo ""
echo "✅ Creating Frontend Availability Check..."
gcloud monitoring uptime create frontend-health \
  --display-name="Healio Frontend - Availability Check" \
  --resource-type="uptime-url" \
  --monitored-resource-path="monitored_resource.labels.host=$FRONTEND_URL" \
  --http-check-path="/" \
  --period=60 \
  --timeout=10 \
  --regions="USA","EUROPE","ASIA_PACIFIC" \
  --project=$PROJECT_ID || echo "Note: Frontend check may already exist"

echo ""
echo "✅ Uptime checks created!"
echo ""
echo "View in Cloud Console:"
echo "https://console.cloud.google.com/monitoring/uptime?project=$PROJECT_ID"
echo ""
