"""
Gemini Vision Agent
Analyzes clinical images (rashes, wounds, swelling, etc.) to extract visual findings
Integrates findings into Agent 2 clinical reasoning

Input: Image file path
Output: JSON with visual findings, possible conditions, severity hints
"""

import vertexai
from vertexai.generative_models import GenerativeModel, Part
import base64
import json
import re
import logging
from pathlib import Path
from typing import Optional, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Vertex AI
vertexai.init(project="healio-494416", location="us-central1")
model = GenerativeModel("gemini-2.5-flash")


def analyze_clinical_image(image_path: str) -> dict:
    """
    Analyze a clinical image using Gemini Vision
    
    Args:
        image_path: Path to image file (JPEG, PNG, WebP, GIF)
    
    Returns:
        {
            "success": bool,
            "visual_findings": str (description),
            "possible_conditions": [list of suspected conditions],
            "severity_assessment": "mild/moderate/severe",
            "clinical_signals": [list of concerning signs],
            "red_flags": [list of emergency warning signs],
            "confidence": float (0.0-1.0),
            "recommendations": str
        }
    """
    
    try:
        # Validate file exists
        if not Path(image_path).exists():
            return {
                "success": False,
                "error": f"Image file not found: {image_path}",
                "visual_findings": "",
                "possible_conditions": []
            }
        
        # Read and encode image
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        # Determine MIME type from file extension
        ext = Path(image_path).suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        mime_type = mime_types.get(ext, 'image/jpeg')
        
        # Create image part
        image_part = Part.from_data(data=image_bytes, mime_type=mime_type)
        
        # Clinical analysis prompt
        prompt = """You are a clinical image analyst assisting a Primary Health Centre in Bengaluru.

Analyze this medical/clinical image and provide ONLY a valid JSON response (no markdown, no extra text):

{
    "visual_findings": "Detailed description of what you observe in the image",
    "possible_conditions": ["condition1", "condition2", "condition3"],
    "severity_assessment": "mild/moderate/severe",
    "clinical_signals": ["signal1", "signal2", "signal3"],
    "red_flags": ["warning1", "warning2"],
    "confidence": 0.0 to 1.0,
    "recommendations": "Brief clinical recommendation"
}

If this is not a clinical/medical image, return:
{"error": "Not a clinical image", "visual_findings": ""}

IMPORTANT: Return ONLY the JSON object. No markdown. No explanations. No code blocks.
"""
        
        # Call Gemini Vision
        response = model.generate_content([image_part, prompt])
        text = response.text.strip()
        
        logger.info(f"Gemini Vision analyzed image: {Path(image_path).name}")
        
        # Parse JSON response
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            json_str = match.group()
            result = json.loads(json_str)
            
            # Check for error in response
            if "error" in result:
                return {
                    "success": False,
                    "error": result.get("error"),
                    "visual_findings": result.get("visual_findings", ""),
                    "possible_conditions": []
                }
            
            # Add success flag
            result["success"] = True
            result["image_path"] = image_path
            
            return result
        else:
            return {
                "success": False,
                "error": "Could not parse Gemini Vision response",
                "visual_findings": text[:200],
                "possible_conditions": [],
                "raw_response": text
            }
    
    except Exception as e:
        logger.error(f"Error analyzing image: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "visual_findings": "",
            "possible_conditions": [],
            "image_path": image_path
        }


def analyze_multiple_images(image_paths: list) -> dict:
    """
    Analyze multiple clinical images
    
    Args:
        image_paths: List of image file paths
    
    Returns:
        Combined analysis of all images
    """
    
    all_findings = {
        "success": True,
        "images_analyzed": 0,
        "images_failed": 0,
        "combined_findings": "",
        "all_conditions": [],
        "all_signals": [],
        "all_red_flags": [],
        "max_severity": "mild",
        "overall_confidence": 0.0,
        "individual_analyses": []
    }
    
    severity_rank = {"mild": 0, "moderate": 1, "severe": 2}
    total_confidence = 0.0
    
    for image_path in image_paths:
        result = analyze_clinical_image(image_path)
        all_findings["individual_analyses"].append(result)
        
        if result.get("success"):
            all_findings["images_analyzed"] += 1
            
            # Aggregate findings
            all_findings["combined_findings"] += f"\n[{Path(image_path).name}] {result.get('visual_findings', '')}"
            all_findings["all_conditions"].extend(result.get("possible_conditions", []))
            all_findings["all_signals"].extend(result.get("clinical_signals", []))
            all_findings["all_red_flags"].extend(result.get("red_flags", []))
            
            # Track maximum severity
            severity = result.get("severity_assessment", "mild")
            if severity_rank.get(severity, 0) > severity_rank.get(all_findings["max_severity"], 0):
                all_findings["max_severity"] = severity
            
            # Average confidence
            total_confidence += result.get("confidence", 0.5)
        else:
            all_findings["images_failed"] += 1
    
    # Calculate average confidence
    if all_findings["images_analyzed"] > 0:
        all_findings["overall_confidence"] = total_confidence / all_findings["images_analyzed"]
    
    # Deduplicate conditions and signals
    all_findings["all_conditions"] = list(set(all_findings["all_conditions"]))
    all_findings["all_signals"] = list(set(all_findings["all_signals"]))
    all_findings["all_red_flags"] = list(set(all_findings["all_red_flags"]))
    
    logger.info(f"Analyzed {all_findings['images_analyzed']} images successfully")
    
    return all_findings


if __name__ == "__main__":
    # Test with a sample image (create a test image first)
    test_image = "test_rash.jpg"
    
    print("🔬 Gemini Vision Agent - Clinical Image Analysis\n")
    
    if Path(test_image).exists():
        result = analyze_clinical_image(test_image)
        print("Analysis Result:")
        print(json.dumps(result, indent=2))
    else:
        print(f"❌ Test image not found: {test_image}")
        print("To test, place a clinical image in the backend directory")
