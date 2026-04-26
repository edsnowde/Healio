# Phase 1: STOP — Python Installation Required

## Issue
```
Python was not found; run without arguments to install from the Microsoft Store
```

Python is not installed on your system.

---

## Solution: Install Python

### Option 1: Microsoft Store (Easiest)
```powershell
# Windows will offer to install Python from Microsoft Store
# Just type:
python
# OR
python3

# Follow the Microsoft Store prompt
```

### Option 2: Direct Download
1. Go to **https://www.python.org/downloads/**
2. Download **Python 3.11 or later** for Windows
3. **IMPORTANT:** During installation, check:
   - ☑️ **"Add Python to PATH"** (critical!)
   - ☑️ "Install pip"
4. Click **Install Now**
5. Wait for completion
6. **Restart PowerShell/Terminal**

### Option 3: Verify Installation
After installing, restart PowerShell and check:
```powershell
python --version
python -m pip --version
```

Should show:
```
Python 3.11.x (or higher)
pip 24.x
```

---

## After Python Installation, Resume with:

```powershell
cd C:\Users\User\Desktop\activities_ABULANCE\Build For Bengaluru Hackathon_Reva university_roactract\Healio\backend

# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Test Gemini
python test_gemini.py

# Test Firestore
python test_firestore.py
```

---

## Timeline Fix
- **Install Python:** 5 minutes
- **Restart PowerShell:** 1 minute
- **Python setup:** 2-3 minutes

**Total:** ~10 minutes

Install Python now, then come back! 🐍
