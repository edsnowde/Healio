"""
TEST 2: Gemini Vision - Clinical Image Analysis
===============================================
FIXED VERSION - Downloads a real medical image for testing

HOW TO RUN:
  cd backend
  .\\venv\\Scripts\\python test_gemini_vision.py
"""

import sys
import os
import json
import urllib.request

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def download_test_image(save_path: str = "test_rash_real.jpg") -> str:
    """
    Downloads a real public-domain skin image for testing.
    This is a proper JPEG that Gemini can analyze.
    """
    print(f"  Downloading a real test image...")

    # A proper public domain medical/skin image (from Wikimedia Commons)
    # This is an image of a skin rash (measles-like rash - public domain)
    url = "https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/Rash_on_arm_of_unknown_origin.jpg/320px-Rash_on_arm_of_unknown_origin.jpg"

    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            image_data = response.read()

        with open(save_path, "wb") as f:
            f.write(image_data)

        size_kb = len(image_data) // 1024
        print(f"  Downloaded: {save_path} ({size_kb} KB)")
        return save_path

    except Exception as e:
        print(f"  Could not download image ({e})")
        print(f"  Creating a synthetic test image using Pillow instead...")
        return create_synthetic_image(save_path.replace(".jpg", ".png"))


def create_synthetic_image(save_path: str = "test_rash_synthetic.png") -> str:
    """
    Creates a proper synthetic image using PIL that Gemini will accept.
    Draws a red-spotted pattern on skin-tone background (simulates a rash).
    """
    try:
        from PIL import Image, ImageDraw
        import random

        # Create a skin-tone background (300x300 pixels - big enough for Gemini)
        img = Image.new("RGB", (300, 300), color=(210, 170, 120))  # skin tone
        draw = ImageDraw.Draw(img)

        # Draw red spots (simulate rash)
        random.seed(42)
        for _ in range(25):
            x = random.randint(20, 280)
            y = random.randint(20, 280)
            r = random.randint(5, 18)
            # Red spots with slight variation
            red   = random.randint(180, 220)
            green = random.randint(30, 60)
            blue  = random.randint(30, 60)
            draw.ellipse([x-r, y-r, x+r, y+r], fill=(red, green, blue))

        img.save(save_path)
        size = os.path.getsize(save_path)
        print(f"  Created synthetic rash image: {save_path} ({size} bytes)")
        return save_path

    except ImportError:
        print("  Pillow not installed. Installing...")
        os.system(".\\venv\\Scripts\\pip install Pillow -q")
        return create_synthetic_image(save_path)


def test_vision_with_image(image_path: str):
    """
    Test Gemini Vision with a real clinical image file.
    """
    print(f"\n{'='*60}")
    print(f"  GEMINI VISION TEST")
    print(f"{'='*60}")
    print(f"  Image: {image_path}")

    # Check file is valid
    if not os.path.exists(image_path):
        print(f"  ERROR: File not found: {image_path}")
        return None

    size = os.path.getsize(image_path)
    print(f"  File size: {size} bytes")

    if size < 500:
        print(f"  ERROR: File is too small ({size} bytes) — not a real image!")
        print(f"  Gemini needs a proper image, at least several KB.")
        print(f"  The file at '{image_path}' is probably a dummy/corrupted file.")
        print(f"  Delete it and put a real photo there.")
        return None

    print(f"  File size OK ({size // 1024} KB)")
    print(f"{'='*60}\n")

    print(f"  [1] Loading Gemini Vision model...")
    from agents.vision_agent import analyze_clinical_image
    print(f"      Model loaded OK")

    print(f"  [2] Sending image to Gemini Vision...")
    result = analyze_clinical_image(image_path)

    print(f"\n  [3] GEMINI VISION RESPONSE:")
    print(f"{'='*60}")

    if not result.get("success"):
        print(f"  FAILED: {result.get('error')}")

        # Give helpful error-specific advice
        error_msg = str(result.get("error", ""))
        if "400" in error_msg and "not valid" in error_msg:
            print(f"\n  WHY: Gemini rejected the image. Common reasons:")
            print(f"    - Image is too small (Gemini needs at least ~50x50 pixels)")
            print(f"    - File is corrupted or not a real image")
            print(f"    - MIME type mismatch (file says .png but is actually something else)")
            print(f"\n  FIX: Use a real photo from your phone/camera")
        return result

    print(f"  Visual Findings  : {result.get('visual_findings', 'N/A')}")
    print(f"  Conditions       : {result.get('possible_conditions', [])}")
    print(f"  Severity         : {result.get('severity_assessment', 'N/A')}")
    print(f"  Clinical Signals : {result.get('clinical_signals', [])}")
    print(f"  Red Flags        : {result.get('red_flags', [])}")
    print(f"  Confidence       : {result.get('confidence', 0):.0%}")
    print(f"  Recommendations  : {result.get('recommendations', 'N/A')}")

    print(f"\n{'='*60}")
    print(f"  SUCCESS: Gemini Vision is working!")
    print(f"  These findings merge with Agent 1 text intake -> Agent 2 triage")
    print(f"{'='*60}")

    return result


if __name__ == "__main__":
    print("\nGEMINI VISION TEST")
    print("=" * 60)

    # ----------------------------------------------------------------
    # YOUR IMAGE PATH — change this to your own photo if you have one
    # (phone photo of a rash/wound/injury saved to the backend folder)
    YOUR_IMAGE = "test_rash.png"
    # ----------------------------------------------------------------

    size = os.path.getsize(YOUR_IMAGE) if os.path.exists(YOUR_IMAGE) else 0

    if os.path.exists(YOUR_IMAGE) and size > 1000:
        # Good file — use it
        print(f"  Using your image: {YOUR_IMAGE} ({size} bytes)")
        test_vision_with_image(YOUR_IMAGE)

    else:
        if os.path.exists(YOUR_IMAGE):
            print(f"  Found '{YOUR_IMAGE}' but it's only {size} bytes — too small, not a real image.")
        else:
            print(f"  No image found at '{YOUR_IMAGE}'")

        print(f"\n  OPTIONS:")
        print(f"  1. Download a real medical image from internet")
        print(f"  2. Create a synthetic rash image using Python (no internet)")
        print(f"\n  Which do you want? (auto-selecting based on internet access...)\n")

        # Try downloading first, fall back to synthetic
        image_path = download_test_image("test_rash_real.jpg")
        test_vision_with_image(image_path)

    print(f"\n  HOW TO USE YOUR OWN IMAGE:")
    print(f"  1. Take a photo on your phone (any skin condition, wound, rash)")
    print(f"  2. Transfer it to this folder:")
    print(f"     {os.path.abspath('.')}\\")
    print(f"  3. Rename it to 'test_rash.jpg'")
    print(f"  4. Run this script again")
