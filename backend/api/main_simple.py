"""
Healio FastAPI Backend - ULTRA-MINIMAL TEST
Just basic endpoints - no external dependencies
"""

from fastapi import FastAPI
from datetime import datetime
import json

app = FastAPI(
    title="Healio Triage API",
    description="Minimal test version",
    version="1.0",
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "status": "operational",
        "service": "Healio PHC Triage API",
        "version": "1.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/analyze")
async def analyze_patient(text_input: str = "test"):
    """Simple analyze endpoint"""
    return {
        "success": True,
        "input": text_input[:50],
        "triage_color": "YELLOW",
        "risk_score": 0.5,
        "message": "System online",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
