#!/bin/bash
# Configure IAM roles for Healio Cloud Run services
# Usage: ./scripts/setup_iam.sh

set -e

PROJECT_ID="healio-494416"
SERVICE_ACCOUNT_EMAIL="322299516577-compute@developer.gserviceaccount.com"

echo "🔐 Configuring IAM Roles for Healio..."
echo "   Project: $PROJECT_ID"
echo "   Service Account: $SERVICE_ACCOUNT_EMAIL"
echo ""

# Enable required APIs
echo "📡 Enabling required Google Cloud APIs..."
gcloud services enable \
  aiplatform.googleapis.com \
  firestore.googleapis.com \
  speech.googleapis.com \
  cloudbuild.googleapis.com \
  cloudrun.googleapis.com \
  --project $PROJECT_ID

# Grant Vertex AI User role
echo "🤖 Granting Vertex AI User role..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/aiplatform.user" \
  --quiet

# Grant Firestore User role
echo "📊 Granting Firestore User role..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/datastore.user" \
  --quiet

# Grant Cloud Speech-to-Text User role
echo "🎤 Granting Cloud Speech-to-Text User role..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/speech.client" \
  --quiet

echo ""
echo "✅ IAM configuration complete!"
echo "   All required roles have been assigned."
