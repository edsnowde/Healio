# ✅ HOW TO RUN BACKEND - COMPLETE GUIDE

## 🔴 PROBLEM YOU'RE FACING
```
.\venv\Scripts\python : The term '.\venv\Scripts\python' is not recognized
```

**Why?**
1. ❌ Virtual environment NOT activated
2. ❌ Dependencies NOT installed
3. ❌ Created `myenv` but need to activate it first

---

## ✅ CORRECT STEPS TO RUN BACKEND

### Step 1: Navigate to Backend Folder
```powershell
cd "c:\Users\User\Desktop\activities_ABULANCE\Build For Bengaluru Hackathon_Reva university_roactract\Healio\backend"
```

### Step 2: Activate Virtual Environment (you already have `myenv` created)
```powershell
.\myenv\Scripts\Activate.ps1
```

**After this, your terminal prompt will show `(myenv)` like:**
```
(myenv) PS C:\...\Healio\backend>
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

**This will install all required packages:**
- fastapi, uvicorn
- vertexai (Gemini)
- google-cloud-speech
- firebase-admin
- Pillow
- And others...

**Wait for it to complete.** You'll see `Successfully installed X packages`

### Step 4: Run the Backend Server
```powershell
python -m uvicorn api.main:app --port 8080 --log-level info
```

**Success! You should see:**
```
INFO:     Uvicorn running on http://127.0.0.1:8080
INFO:     Application startup complete
```

---

## 🧪 TEST THE BACKEND (New Terminal)

**While backend is running, open a NEW PowerShell terminal and test:**

```powershell
$body = @{
    text = "high fever since 3 days, red rash on arms and legs, severe joint pain"
    name = "Test Patient"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8080/triage" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

**Expected response:**
```json
{
  "success": true,
  "triage_color": "Red",
  "risk_score": 0.95,
  "assigned_doctor": "Dr. Nair",
  "assigned_department": "Emergency",
  ...
}
```

---

## 🚀 QUICK REFERENCE COMMANDS

**In backend folder:**

```powershell
# 1. Activate virtual environment
.\myenv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run backend
python -m uvicorn api.main:app --port 8080 --log-level info

# 4. Stop backend (in terminal running backend)
Ctrl + C

# 5. Deactivate virtual environment (when done)
deactivate
```

---

## ⚡ COMMON ISSUES & FIXES

### Issue 1: "ExecutionPolicy" Error on Activation
```
File cannot be loaded because running scripts is disabled
```
**Fix:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Then try again: `.\myenv\Scripts\Activate.ps1`

---

### Issue 2: "requirements.txt not found"
**Cause:** You're not in the backend folder

**Fix:**
```powershell
cd "c:\Users\User\Desktop\activities_ABULANCE\Build For Bengaluru Hackathon_Reva university_roactract\Healio\backend"
pip install -r requirements.txt
```

---

### Issue 3: "ModuleNotFoundError: No module named 'uvicorn'"
**Cause:** Dependencies not installed

**Fix:**
```powershell
# Verify venv is activated (should see (myenv) in prompt)
# Then reinstall:
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Issue 4: "Address already in use" (port 8080)
**Cause:** Backend already running on port 8080

**Fix:**
```powershell
# Either:
# 1. Stop existing backend (Ctrl + C in other terminal)
# 2. Or use different port:
python -m uvicorn api.main:app --port 8081 --log-level info
```

---

## 📋 STEP-BY-STEP COPY-PASTE COMMANDS

**Run these commands in order in PowerShell:**

```powershell
# Navigate to backend
cd "c:\Users\User\Desktop\activities_ABULANCE\Build For Bengaluru Hackathon_Reva university_roactract\Healio\backend"

# Activate virtual environment
.\myenv\Scripts\Activate.ps1

# Install all dependencies
pip install -r requirements.txt

# Run the backend server
python -m uvicorn api.main:app --port 8080 --log-level info
```

**That's it!** Backend will start on `http://localhost:8080`

---

## 🎯 VERIFYING BACKEND IS RUNNING

**Check these endpoints in a NEW terminal:**

```powershell
# Health check
Invoke-WebRequest -Uri "http://localhost:8080/health" -Method GET

# Get queue (empty initially)
Invoke-WebRequest -Uri "http://localhost:8080/queue" -Method GET

# Get surveillance
Invoke-WebRequest -Uri "http://localhost:8080/surveillance" -Method GET
```

All should return 200 status code.

---

## 📚 REQUIREMENTS.TXT (What gets installed)

Current dependencies (from requirements.txt):
```
fastapi
uvicorn
google-cloud-speech
google-cloud-aiplatform
vertexai
firebase-admin
Pillow
pydantic
python-multipart
```

---

**Status:** Backend ready to run! ✅  
**Next:** Follow the step-by-step commands above to start it.
