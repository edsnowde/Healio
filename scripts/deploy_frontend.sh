#!/bin/bash
# Deploy Healio Frontend to Google Cloud Run
# Usage: ./scripts/deploy_frontend.sh

set -e

PROJECT_ID="healio-494416"
SERVICE_NAME="healio-frontend"
REGION="us-central1"
PORT="3000"
MEMORY="512Mi"
CPU="1"
API_URL="https://healio-backend-322299516577.us-central1.run.app"

echo "🎨 Deploying Healio Frontend to Cloud Run..."
echo "   Project: $PROJECT_ID"
echo "   Service: $SERVICE_NAME"
echo "   Region: $REGION"
echo "   Backend API: $API_URL"
echo ""

# Build Docker image via Cloud Build
echo "📦 Building Docker image via Cloud Build..."
gcloud builds submit --config cloudbuild-frontend.yaml . \
  --project $PROJECT_ID

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image us-central1-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/$SERVICE_NAME:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port $PORT \
  --memory $MEMORY \
  --cpu $CPU \
  --project $PROJECT_ID \
  --set-env-vars NEXT_PUBLIC_API_URL=$API_URL

echo ""
echo "✅ Frontend deployment complete!"
echo "   URL: https://$SERVICE_NAME-322299516577.$REGION.run.app"
