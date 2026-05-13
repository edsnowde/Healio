#!/bin/bash
# Full Healio Deployment Pipeline
# Runs: IAM setup → Backend deploy → Frontend deploy
# Usage: ./scripts/full_deployment.sh

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ID="healio-494416"

echo "🚀 ========================================="
echo "   HEALIO FULL DEPLOYMENT PIPELINE"
echo "   Project: $PROJECT_ID"
echo "=========================================="
echo ""

# Step 1: IAM Setup
echo "STEP 1️⃣  — Configuring IAM Roles..."
echo "---"
bash "$SCRIPT_DIR/setup_iam.sh"
echo ""

# Step 2: Backend Deployment
echo ""
echo "STEP 2️⃣  — Deploying Backend..."
echo "---"
bash "$SCRIPT_DIR/deploy_backend.sh"
echo ""

# Step 3: Frontend Deployment
echo ""
echo "STEP 3️⃣  — Deploying Frontend..."
echo "---"
bash "$SCRIPT_DIR/deploy_frontend.sh"
echo ""

echo "✅ ========================================="
echo "   ALL DEPLOYMENTS COMPLETE!"
echo "=========================================="
echo ""
echo "🎉 Your Healio services are now live:"
echo "   Frontend: https://healio-frontend-322299516577.us-central1.run.app"
echo "   Backend:  https://healio-backend-322299516577.us-central1.run.app"
echo ""
