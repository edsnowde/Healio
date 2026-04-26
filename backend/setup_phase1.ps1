# Phase 1 Setup Script for Healio (PowerShell)
# Run this from backend/ folder after GCP credentials are ready

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Phase 1: Healio Foundation Setup (PowerShell)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if venv exists
if (Test-Path "venv") {
    Write-Host "[✓] Virtual environment already exists" -ForegroundColor Green
} else {
    Write-Host "[•] Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[✗] Failed to create venv" -ForegroundColor Red
        exit 1
    }
    Write-Host "[✓] Virtual environment created" -ForegroundColor Green
}

Write-Host ""
Write-Host "[•] Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "[✗] Failed to activate venv" -ForegroundColor Red
    exit 1
}
Write-Host "[✓] Virtual environment activated" -ForegroundColor Green

Write-Host ""
Write-Host "[•] Installing dependencies from requirements.txt..." -ForegroundColor Yellow
pip install --upgrade pip | Out-Null
pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "[✗] Failed to install dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "[✓] Dependencies installed" -ForegroundColor Green

Write-Host ""
Write-Host "[•] Verifying installation..." -ForegroundColor Yellow
$installed = pip list | Select-String "google-cloud-aiplatform"
if ($installed) {
    Write-Host "[✓] All packages verified" -ForegroundColor Green
} else {
    Write-Host "[✗] Installation verification failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Phase 1 Setup Complete!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Make sure credentials.json is in this folder" -ForegroundColor White
Write-Host "2. Run: python test_gemini.py" -ForegroundColor White
Write-Host "3. Run: python test_firestore.py" -ForegroundColor White
Write-Host ""
Write-Host "To deactivate venv later, type: deactivate" -ForegroundColor Cyan
Write-Host ""
