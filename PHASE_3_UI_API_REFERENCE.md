# 🎯 PHASE 3 - BACKEND API REFERENCE FOR UI

**Server Status**: ✅ Running on `http://localhost:8000`

---

## 📱 Main Endpoint for UI (Simple & Fast)

### **POST `/triage`** - Phase 3 UI Endpoint

**Purpose**: Get triage result from patient symptoms

**Request**:
```json
{
  "text": "I have high fever since 2 days and red rash on my arms and legs"
}
```

**Response**:
```json
{
  "success": true,
  "patient_id": "d4882561-ddf",
  "triage_color": "Yellow",
  "risk_score": 0.82,
  "chief_complaint": "High fever and red rash",
  "assigned_doctor": "Dr. Sharma",
  "assigned_department": "General",
  "requires_anm_confirmation": false,
  "anm_message": ""
}
```

**Triage Colors**:
- 🟢 **Green**: Low risk (Score 0.0-0.65) - Send to queue
- 🟡 **Yellow**: Medium risk (Score 0.65-0.90) - Urgent attention
- 🔴 **Red**: High risk (Score 0.90-1.0) - Emergency + ANM confirmation

---

## 🔗 Other Useful Endpoints

### **POST `/analyze/with-audio`** - With Voice Recording
```json
{
  "text": "symptoms in kannada",
  "audio": "base64_encoded_audio_file"
}
```
Returns triage with speech-to-text transcription

### **POST `/analyze/with-multimodal`** - With Images/Videos
```json
{
  "text": "patient symptoms",
  "images": ["base64_image1", "base64_image2"]
}
```
Returns triage with vision analysis of images

### **GET `/queue`** - Live Queue Status
Returns all patients in queue ordered by priority (Red → Yellow → Green)

### **GET `/health`** - Server Health Check
```bash
curl http://localhost:8000/health
```
Returns: `{"status": "ok"}`

---

## 💻 How to Call from Tablet UI

### Using JavaScript/React
```javascript
// Post to triage endpoint
async function getTriage(symptomText) {
  const response = await fetch('http://localhost:8000/triage', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: symptomText })
  });
  
  const result = await response.json();
  
  // Display triage color
  console.log(result.triage_color);  // "Yellow"
  console.log(result.risk_score);    // 0.82
  
  return result;
}

// Example usage
getTriage("I have high fever and red rash").then(result => {
  // Show result to user
  document.getElementById('triage-color').textContent = result.triage_color;
});
```

### Using Python
```python
import requests

response = requests.post('http://localhost:8000/triage', json={
    'text': 'I have high fever and red rash'
})

result = response.json()
print(result['triage_color'])   # Yellow
print(result['risk_score'])     # 0.82
```

### Using cURL
```bash
curl -X POST http://localhost:8000/triage \
  -H "Content-Type: application/json" \
  -d '{"text": "I have high fever and red rash"}'
```

---

## 📊 UI Components to Display

### Triage Result Screen
```
┌─────────────────────────────────┐
│   TRIAGE RESULT                 │
├─────────────────────────────────┤
│                                 │
│   Chief Complaint:              │
│   High fever and red rash       │
│                                 │
│   Risk Level: 🟡 YELLOW         │
│   Score: 0.82/1.0              │
│                                 │
│   Doctor: Dr. Sharma           │
│   Department: General          │
│   Queue Position: #4           │
│                                 │
│   [✓ Confirm] [✗ Cancel]       │
│                                 │
└─────────────────────────────────┘
```

### If Red Alert (requires ANM confirmation)
```
┌─────────────────────────────────┐
│   ⚠️ EMERGENCY ALERT             │
├─────────────────────────────────┤
│   Risk Level: 🔴 RED (0.95)    │
│                                 │
│   Confirm alert with ANM:       │
│   [Text: "ANM - Red Alert"]    │
│                                 │
│   [✓ Confirm] [✗ Cancel]       │
│                                 │
└─────────────────────────────────┘
```

---

## 🎤 Voice Recording Flow

1. **Record Audio** → `audio_blob`
2. **Convert to Base64** → `base64_string`
3. **Send to `/analyze/with-audio`**:
   ```javascript
   const formData = new FormData();
   formData.append('text', 'symptoms heard');
   formData.append('audio', audioFile);
   
   fetch('http://localhost:8000/analyze/with-audio', {
     method: 'POST',
     body: formData
   }).then(r => r.json())
   ```

---

## 📸 Image Upload Flow

1. **Upload Image** → `image_file`
2. **Send to `/analyze/with-multimodal`**:
   ```javascript
   const formData = new FormData();
   formData.append('text', 'patient symptoms');
   formData.append('images', imageFile);
   
   fetch('http://localhost:8000/analyze/with-multimodal', {
     method: 'POST',
     body: formData
   }).then(r => r.json())
   ```

---

## 👨‍⚕️ Doctor Dashboard Flow

1. **Connect WebSocket** → `ws://localhost:8000/ws/queue`
2. **Receive Live Updates**:
   ```javascript
   const ws = new WebSocket('ws://localhost:8000/ws/queue');
   
   ws.onmessage = (event) => {
     const data = JSON.parse(event.data);
     console.log('New patient:', data.patient_id);
     console.log('Triage Color:', data.triage_color);
     
     // Update dashboard
     updateQueueDisplay(data);
   };
   ```

---

## 🚨 DHO Dashboard (Outbreak Alerts)

**Connect to**: `ws://localhost:8000/ws/alerts`

**Receives Alerts When**:
- 3+ patients have similar symptoms within 48 hours
- Jaccard similarity > 60%

**Alert Format**:
```json
{
  "type": "outbreak_alert",
  "cluster_id": "cls-fever-rash-001",
  "symptoms": ["fever", "rash"],
  "patient_count": 3,
  "severity": "high",
  "action_required": true
}
```

---

## ✅ Test the API

### Quick Test
```bash
# Health check
curl http://localhost:8000/health

# Simple triage
curl -X POST http://localhost:8000/triage \
  -H "Content-Type: application/json" \
  -d '{"text":"fever and cough"}'

# See all docs
# Visit: http://localhost:8000/docs (Swagger UI)
```

---

## 🔗 All Available Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Welcome message |
| `/health` | GET | Health check |
| `/triage` | POST | **UI Main Endpoint** |
| `/analyze` | POST | Text triage |
| `/analyze/with-audio` | POST | Audio + text triage |
| `/analyze/with-multimodal` | POST | Files + text triage |
| `/queue` | GET | Live queue status |
| `/queue/department/{dept}` | GET | Queue by department |
| `/queue/patient/{id}` | PATCH | Update patient status |
| `/surveillance/clusters` | GET | Active outbreak clusters |
| `/surveillance/summary` | GET | Surveillance stats |
| `/surveillance/clusters/{id}/escalate` | POST | Escalate cluster to DHO |
| `/ws/queue` | WebSocket | Queue live updates |
| `/ws/alerts` | WebSocket | Outbreak alerts |

---

## 📖 Full Documentation

Visit: **http://localhost:8000/docs**

This shows interactive Swagger UI with all endpoints and test capability.

---

## ⚡ Quick Start for UI Team

1. **Show Voice Record Button** → Click to record Kannada symptoms
2. **Send to `/triage`** → POST with text from speech-to-text
3. **Display Triage Card** → Show color (Red/Yellow/Green) + risk score
4. **If Red** → Show "ANM Confirmation" dialog
5. **Update Live Queue** → Connect to `ws://localhost:8000/ws/queue`
6. **Show Doctor List** → Assign to doctor from response

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Connection refused" | Ensure server running: `python -m uvicorn api.main:app --port 8000` |
| "No module named api" | Run from backend directory: `cd backend/` |
| "CORS error" | Server allows all origins (production: restrict to your UI domain) |
| "Empty response" | Check text is not empty: `text` must be >0 characters |

---

## 📞 Support

- **Server Logs**: Check terminal output for request logs
- **API Docs**: http://localhost:8000/docs
- **Backend Code**: `backend/api/main.py`
- **Agent Code**: `backend/agents/agent{1,2,3}.py`

---

**Server Running**: ✅ http://localhost:8000  
**Ready for UI Integration**: ✅ YES  
**Main Endpoint**: ✅ POST /triage

**Your UI team can start building immediately!** 🚀
