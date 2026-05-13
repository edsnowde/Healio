#!/bin/bash
# Setup Cloud Logging Alert Policies for Healio
# Alerts on ERROR logs in backend services

set -e

PROJECT_ID="healio-494416"
ALERT_EMAIL="${1:-}"

if [ -z "$ALERT_EMAIL" ]; then
  echo "⚠️  Email address not provided for alerts"
  echo "Usage: ./setup_log_alerts.sh your-email@example.com"
  echo ""
  echo "Continuing without email notifications..."
else
  echo "📧 Using alert email: $ALERT_EMAIL"
fi

echo ""
echo "📋 Creating Log-based Alert Policies..."
echo ""

# ─────────────────────────────────────────────────────
# Alert Policy: Backend Errors
# ─────────────────────────────────────────────────────

echo "✅ Creating Backend Error Alert Policy..."

POLICY=$(cat <<EOF
{
  "displayName": "Healio Backend - Error Alert",
  "conditions": [
    {
      "displayName": "ERROR in backend logs",
      "conditionThreshold": {
        "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"healio-backend\" AND severity=\"ERROR\"",
        "comparison": "COMPARISON_GT",
        "thresholdValue": 0,
        "duration": "60s",
        "aggregations": [
          {
            "alignmentPeriod": "60s",
            "perSeriesAligner": "ALIGN_RATE"
          }
        ]
      }
    }
  ],
  "notificationChannels": [],
  "alertStrategy": {
    "autoClose": "1800s"
  }
}
EOF
)

echo "$POLICY" > /tmp/backend_error_policy.json

gcloud alpha monitoring policies create --policy-from-file=/tmp/backend_error_policy.json \
  --project=$PROJECT_ID || echo "Note: Policy creation via CLI limited; use Cloud Console"

echo ""
echo "✅ Creating Frontend Error Alert Policy..."

FRONTEND_POLICY=$(cat <<EOF
{
  "displayName": "Healio Frontend - Error Alert",
  "conditions": [
    {
      "displayName": "ERROR in frontend logs",
      "conditionThreshold": {
        "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"healio-frontend\" AND severity=\"ERROR\"",
        "comparison": "COMPARISON_GT",
        "thresholdValue": 0,
        "duration": "60s",
        "aggregations": [
          {
            "alignmentPeriod": "60s",
            "perSeriesAligner": "ALIGN_RATE"
          }
        ]
      }
    }
  ],
  "notificationChannels": [],
  "alertStrategy": {
    "autoClose": "1800s"
  }
}
EOF
)

echo "$FRONTEND_POLICY" > /tmp/frontend_error_policy.json

echo ""
echo "⚠️  Alert policies partially configured"
echo ""
echo "📊 Complete setup in Cloud Console:"
echo "https://console.cloud.google.com/monitoring/alerting/policies?project=$PROJECT_ID"
echo ""
echo "To finish:"
echo "1. Go to Monitoring → Alerting Policies"
echo "2. Click 'Create Policy'"
echo "3. Use this filter for backend errors:"
echo '   resource.type="cloud_run_revision" AND resource.labels.service_name="healio-backend" AND severity="ERROR"'
echo "4. Add notification channel with email: $ALERT_EMAIL"
echo ""
