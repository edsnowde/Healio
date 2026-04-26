@echo off
REM Phase 1 Setup Script for Healio
REM Run this from backend/ folder after GCP credentials are ready

echo.
echo ============================================================
echo Phase 1: Healio Foundation Setup
echo ============================================================
echo.

REM Check if venv exists
if exist venv\ (
    echo [✓] Virtual environment already exists
) else (
    echo [•] Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [✗] Failed to create venv
        exit /b 1
    )
    echo [✓] Virtual environment created
)

echo.
echo [•] Activating virtual environment...
call venv\Scripts\activate.bat

echo [✓] Virtual environment activated

echo.
echo [•] Installing dependencies from requirements.txt...
pip install --upgrade pip > nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo [✗] Failed to install dependencies
    exit /b 1
)
echo [✓] Dependencies installed

echo.
echo [•] Verifying installation...
pip list | findstr google-cloud-aiplatform > nul
if errorlevel 1 (
    echo [✗] Installation verification failed
    exit /b 1
)
echo [✓] All packages verified

echo.
echo ============================================================
echo Phase 1 Setup Complete!
echo ============================================================
echo.
echo Next steps:
echo 1. Make sure credentials.json is in this folder
echo 2. Run: python test_gemini.py
echo 3. Run: python test_firestore.py
echo.
echo To deactivate venv later, type: deactivate
echo.
