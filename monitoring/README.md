# 📊 Healio Monitoring & Alerting

Production monitoring for Healio using Google Cloud Monitoring and Cloud Logging.

## 📋 What's Monitored

### Uptime Checks
- ✅ **Backend Health Endpoint** — `/health` endpoint (HTTPS)
- ✅ **Frontend Availability** — Main page load (HTTPS)
- ✅ Multi-region checks (USA, Europe, Asia-Pacific)
- ✅ 60-second check interval
- ✅ 10-second timeout

### Log-Based Alerts
- ✅ **Backend Errors** — Alert on ERROR severity logs
- ✅ **Frontend Errors** — Alert on application errors
- ✅ **Auto-close** after 30 minutes of normal operations
- ✅ Email notifications

### Metrics Collected
- ✅ Request latency (p50, p95, p99)
- ✅ Error rates
- ✅ CPU & memory usage
- ✅ Container restart counts
- ✅ Network I/O

---

## 🚀 Quick Start

### Prerequisites
```bash
gcloud auth login
gcloud config set project healio-494416
```

### Setup Monitoring

```bash
# Make scripts executable
chmod +x monitoring/*.sh

# Option 1: Full setup with email alerts
./monitoring/setup_all_monitoring.sh your-email@example.com

# Option 2: Individual components
./monitoring/setup_uptime_checks.sh
./monitoring/setup_log_alerts.sh
```

---

## 📁 File Structure

```
monitoring/
├── setup_uptime_checks.sh     ← HTTP/HTTPS endpoint monitoring
├── setup_log_alerts.sh        ← Error log-based alerts
├── setup_all_monitoring.sh    ← Orchestrates full setup
└── README.md                  ← This file
```

---

## 🔍 Detailed Setup

### 1. Uptime Checks (`setup_uptime_checks.sh`)

Monitors service availability by making periodic HTTP requests.

**What it checks:**
```
Backend:  https://healio-backend-322299516577.us-central1.run.app/health
Frontend: https://healio-frontend-322299516577.us-central1.run.app/
```

**Configuration:**
- Interval: 60 seconds
- Timeout: 10 seconds  
- Regions: USA, Europe, Asia-Pacific (global coverage)
- Alerts trigger if service unreachable for 2+ checks

**View results:**
https://console.cloud.google.com/monitoring/uptime

---

### 2. Log Alerts (`setup_log_alerts.sh`)

Monitors application logs and triggers alerts on errors.

**What it watches:**
```
Filter: resource.type="cloud_run_revision" 
        AND severity="ERROR"
```

**Alerts trigger on:**
- Backend service errors (Python exceptions, failures)
- Frontend deployment errors
- API timeouts or 5xx responses

**View alerts:**
https://console.cloud.google.com/monitoring/alerting/policies

**Manual setup (if script fails):**
1. Go to Cloud Console → Monitoring → Alerting Policies
2. Click "Create Policy"
3. Name: "Healio Backend - Error Alert"
4. Condition: Log filter
   ```
   resource.type="cloud_run_revision"
   AND resource.labels.service_name="healio-backend"
   AND severity="ERROR"
   ```
5. Duration: 60 seconds
6. Threshold: 0 (alert on first error)
7. Add notification channel (email)

---

### 3. Complete Setup (`setup_all_monitoring.sh`)

Orchestrates both uptime checks and log alerts.

```bash
./monitoring/setup_all_monitoring.sh admin@example.com
```

---

## 📊 View Monitoring Data

### Cloud Monitoring Console
https://console.cloud.google.com/monitoring?project=healio-494416

Shows:
- Resource list
- Active uptime checks
- Alert policies
- Custom metrics

### Cloud Logging Console
https://console.cloud.google.com/logs?project=healio-494416

View application logs:
```
# Backend errors
resource.type="cloud_run_revision"
resource.labels.service_name="healio-backend"
severity="ERROR"

# Frontend errors
resource.type="cloud_run_revision"
resource.labels.service_name="healio-frontend"
severity="ERROR"

# All logs with timestamps
resource.type="cloud_run_revision"
```

### Dashboards
https://console.cloud.google.com/monitoring/dashboards?project=healio-494416

Pre-built dashboards show:
- Service latency
- Error rates
- Uptime status
- Resource usage

---

## 🔔 Alert Notifications

### Email Alerts
Alerts are sent to configured email addresses when:
- ✅ Uptime check fails (service down)
- ✅ ERROR appears in logs
- ✅ Multiple errors in 60 seconds

### Create Notification Channel

1. Go to: **Monitoring → Alerting → Notification Channels**
2. Click **"Create Channel"**
3. Select **"Email"**
4. Enter your email address
5. Click **"Create"**
6. Verify email link sent to you

### Add Channel to Alert Policy

1. Open alert policy in Cloud Console
2. Click **"Edit"**
3. Under "Notification channels": **Add channel**
4. Select your email channel
5. Click **"Save Policy"**

---

## 📈 Recommended Alerts

Beyond what's configured, consider adding:

### 1. High Error Rate
```
Alert if error_rate > 5% for 5 minutes
```

### 2. Slow Response Times
```
Alert if p95_latency > 5 seconds
```

### 3. Memory Usage
```
Alert if memory_usage > 80% for 10 minutes
```

### 4. Frequent Restarts
```
Alert if restart_count > 3 in 1 hour
```

---

## 🐛 Troubleshooting

### Uptime check shows red
```bash
# Test backend manually
curl https://healio-backend-322299516577.us-central1.run.app/health

# Check backend logs
gcloud run services describe healio-backend \
  --region us-central1 --project healio-494416

# View recent logs
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=healio-backend" \
  --limit 50 --format json --project healio-494416
```

### Alerts not sending
1. Verify notification channel created
2. Verify email address confirmed
3. Check alert policy has channel assigned
4. Manually trigger test alert from policy page

### Can't run scripts
```bash
# Make executable
chmod +x monitoring/*.sh

# Or run with bash explicitly
bash monitoring/setup_all_monitoring.sh your-email@example.com
```

---

## 📝 Best Practices

1. **Monitor actively**
   - Review uptime trends weekly
   - Archive alert history monthly

2. **Alert appropriately**
   - Don't over-alert (leads to alert fatigue)
   - Set thresholds based on SLO/SLA

3. **Escalate strategically**
   - Page on-call for critical issues (30s downtime)
   - Email for warnings (performance degradation)

4. **Document incidents**
   - Keep runbooks for common alerts
   - Update alert conditions based on false positives

5. **Test alerts**
   - Monthly alert system tests
   - Verify email notifications work
   - Test escalation procedures

---

## 📚 Resources

- [Cloud Monitoring Documentation](https://cloud.google.com/monitoring/docs)
- [Cloud Logging Documentation](https://cloud.google.com/logging/docs)
- [Alert Policy Best Practices](https://cloud.google.com/monitoring/alert-policies)
- [SLO Best Practices](https://cloud.google.com/blog/products/management-tools/sre-fundamentals-slis-slos-slas)

---

**Created:** May 13, 2026  
**Project:** Healio PHC Triage System  
**Status:** Production Monitoring Ready
