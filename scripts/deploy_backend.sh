#!/bin/bash
# Deploy Healio Backend to Google Cloud Run
# Usage: ./scripts/deploy_backend.sh

set -e

PROJECT_ID="healio-494416"
SERVICE_NAME="healio-backend"
REGION="us-central1"
MEMORY="2Gi"
CPU="2"
TIMEOUT="300"
PORT="8080"

echo "🚀 Deploying Healio Backend to Cloud Run..."
echo "   Project: $PROJECT_ID"
echo "   Service: $SERVICE_NAME"
echo "   Region: $REGION"
echo ""

cd backend

gcloud run deploy $SERVICE_NAME \
  --source . \
  --project $PROJECT_ID \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory $MEMORY \
  --cpu $CPU \
  --timeout $TIMEOUT \
  --port $PORT \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID

echo ""
echo "✅ Backend deployment complete!"
echo "   URL: https://$SERVICE_NAME-322299516577.$REGION.run.app"
