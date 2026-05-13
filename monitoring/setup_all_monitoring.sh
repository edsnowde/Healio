#!/bin/bash
# Complete Monitoring Setup for Healio
# Configures uptime checks, log alerts, and dashboards

set -e

PROJECT_ID="healio-494416"
ALERT_EMAIL="${1:-}"

echo "🔧 ========================================"
echo "   HEALIO MONITORING SETUP"
echo "   Project: $PROJECT_ID"
echo "========================================"
echo ""

# Step 1: Uptime Checks
echo "STEP 1️⃣  — Creating Uptime Checks..."
echo "---"
bash "$(dirname "$0")/setup_uptime_checks.sh"

# Step 2: Log Alerts
echo ""
echo "STEP 2️⃣  — Setting Up Log Alerts..."
echo "---"
if [ -n "$ALERT_EMAIL" ]; then
  bash "$(dirname "$0")/setup_log_alerts.sh" "$ALERT_EMAIL"
else
  bash "$(dirname "$0")/setup_log_alerts.sh"
fi

echo ""
echo "✅ ========================================"
echo "   MONITORING SETUP COMPLETE!"
echo "========================================"
echo ""
echo "📊 Cloud Monitoring Console:"
echo "https://console.cloud.google.com/monitoring?project=$PROJECT_ID"
echo ""
echo "📈 View Dashboard:"
echo "https://console.cloud.google.com/monitoring/dashboards?project=$PROJECT_ID"
echo ""
echo "🚨 Alert Policies:"
echo "https://console.cloud.google.com/monitoring/alerting/policies?project=$PROJECT_ID"
echo ""
echo "📋 Logs:"
echo "https://console.cloud.google.com/logs?project=$PROJECT_ID"
echo ""
