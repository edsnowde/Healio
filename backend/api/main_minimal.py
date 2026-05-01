"""
Healio FastAPI Backend - MINIMAL VERSION
Just get it running first
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Healio PHC Triage API",
    version="2.0",
)

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - system status"""
    return {
        "status": "operational",
        "service": "Healio PHC Triage API",
        "version": "2.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/analyze", tags=["Triage"])
async def analyze_patient(text_input: str = None):
    """
    Main triage endpoint - minimal version
    """
    try:
        if not text_input or not text_input.strip():
            return JSONResponse(
                status_code=400,
                content={"error": "text_input required"}
            )
        
        logger.info(f"[ANALYZE] Input: {text_input[:50]}...")
        
        return {
            "status": "success",
            "message": "Analysis in progress",
            "input": text_input[:100]
        }
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
