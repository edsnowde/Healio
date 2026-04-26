"""
Agent 1: Multimodal Intake Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PURPOSE:
  - Receives raw patient input (text from voice transcription, images, videos)
  - Uses Gemini 2.5 Flash to extract structured clinical data from that input
  - Returns a standardized JSON payload (chief_complaint, symptoms, duration, severity)
  - Multimodal: can process Gemini Vision findings from image/video uploads

CALLED BY:
  - run_adk.py → HealioAgentOrchestrator.run_pipeline()
  - api/main.py → /analyze, /analyze/with-audio, /analyze/with-multimodal endpoints
  - main_pipeline.py (direct test)

OUTPUT FORMAT:
  {
    "chief_complaint": "...",
    "symptoms": [...],
    "duration": "...",
    "severity": "mild|moderate|severe",
    "additional_info": {...},
    "multimodal_findings": {...}
  }
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import vertexai
from vertexai.generative_models import GenerativeModel
import json
import re
import logging
import asyncio
from typing import Optional, Dict, List
from pathlib import Path

# ─── Logger Setup ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s │ %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("healio.agent1")

# ─── Gemini Initialization ───────────────────────────────────────────────────
logger.info("⚙️  [AGENT 1] Initializing Vertex AI (project=healio-494416, location=us-central1)")
vertexai.init(project="healio-494416", location="us-central1")
model = GenerativeModel("gemini-2.5-flash")
logger.info("✅ [AGENT 1] Gemini 2.5 Flash model loaded and ready")


# ─── Async Wrapper ────────────────────────────────────────────────────────────
async def run_agent1_async(
    symptom_text: Optional[str] = None,
    audio_transcript: Optional[str] = None,
    image_paths: Optional[List[str]] = None,
    video_paths: Optional[List[str]] = None
) -> dict:
    """Async wrapper — runs Agent 1 in thread executor so it doesn't block the event loop"""
    logger.info("🔄 [AGENT 1] Async call received — dispatching to thread executor")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, run_agent1, symptom_text, audio_transcript, image_paths, video_paths)


# ─── Main Agent Function ──────────────────────────────────────────────────────
def run_agent1(
    symptom_text: Optional[str] = None,
    audio_transcript: Optional[str] = None,   # pre-transcribed text (legacy)
    audio_file_path: Optional[str] = None,    # NEW: path to audio file → auto Speech-to-Text
    image_paths: Optional[List[str]] = None,
    video_paths: Optional[List[str]] = None,
    audio_language: str = "kn-IN"             # default Kannada; also accepts hi-IN, en-IN
) -> dict:
    """
    Agent 1: Multimodal Intake Agent

    Accepts:
      - symptom_text      : typed/transcribed text
      - audio_transcript  : already-transcribed text (legacy)
      - audio_file_path   : path to audio file → auto-transcribed via Google Speech-to-Text
      - image_paths       : list of image paths → analyzed via Gemini Vision
      - video_paths       : list of video paths → analyzed via Gemini Vision
      - audio_language    : BCP-47 code for Speech-to-Text (kn-IN / hi-IN / en-IN)
    """
    logger.info("━" * 60)
    logger.info("🟢 [AGENT 1] ▶ Starting Multimodal Intake")
    logger.info(f"   Input received:")
    logger.info(f"   ├─ symptom_text      : {'✓ present' if symptom_text else '✗ not provided'}")
    logger.info(f"   ├─ audio_transcript  : {'✓ present' if audio_transcript else '✗ not provided'}")
    logger.info(f"   ├─ audio_file_path   : {audio_file_path if audio_file_path else '✗ not provided'}")
    logger.info(f"   ├─ image_paths       : {image_paths if image_paths else 'none'}")
    logger.info(f"   └─ video_paths       : {video_paths if video_paths else 'none'}")

    # ── Step 0: Auto-transcribe audio file if provided ───────────────────
    if audio_file_path:
        logger.info(f"   🎙️  [AGENT 1] Audio file detected — calling Google Speech-to-Text...")
        stt_transcript = _transcribe_audio_google_speech(audio_file_path, audio_language)
        if stt_transcript:
            # Prepend Speech-to-Text result to any existing transcript
            audio_transcript = (stt_transcript + " " + audio_transcript) if audio_transcript else stt_transcript
            logger.info(f"   ✅ [AGENT 1] Speech-to-Text transcript: \"{stt_transcript[:100]}...\"")
        else:
            logger.warning(f"   ⚠️  [AGENT 1] Speech-to-Text returned empty — continuing with other inputs")

    # ── Input validation ────────────────────────────────────────────────
    if not symptom_text and not audio_transcript and not image_paths and not video_paths:
        logger.error("❌ [AGENT 1] No input provided — at least one of (text/audio/image/video) is required")
        return {
            "error": "No input provided (text, audio, image, or video required)",
            "chief_complaint": "",
            "symptoms": [],
            "duration": "Unknown",
            "severity": "unknown",
            "multimodal_findings": {}
        }

    # ── Combine text sources ─────────────────────────────────────────────
    combined_text = ""
    if audio_transcript:
        combined_text = audio_transcript
        logger.info(f"   📢 Using audio transcript as primary: \"{audio_transcript[:80]}...\"")
    if symptom_text:
        combined_text += (" " + symptom_text) if combined_text else symptom_text
        logger.info(f"   📝 Appended symptom text: \"{symptom_text[:80]}...\"")

    logger.info(f"   🔗 Combined input text (length={len(combined_text)}): \"{combined_text[:100]}...\"")

    # ── Build Gemini prompt ──────────────────────────────────────────────
    prompt = f"""
You are a clinical intake specialist at a PHC (Primary Health Centre) in Bengaluru.

Patient says (voice transcribed from Kannada/Hindi/English): "{combined_text}"

Extract and return ONLY a valid JSON (no markdown, no extra text) with these fields:
- chief_complaint (string): Main reason they came, in clear clinical language
- symptoms (array of strings): Specific symptoms reported
- duration (string): How long symptoms have been present
- severity (string): one of mild / moderate / severe
- additional_info (object): Other relevant data (allergies, medications, vitals if mentioned)

IMPORTANT: Return ONLY the JSON object. No markdown. No explanations.
"""

    multimodal_findings = {}

    try:
        # ── Call Gemini ──────────────────────────────────────────────────
        logger.info("   🤖 [AGENT 1] Sending prompt to Gemini 2.5 Flash...")
        response = model.generate_content(prompt)
        text = response.text.strip()
        logger.info(f"   📨 [AGENT 1] Gemini responded ({len(text)} chars)")
        logger.debug(f"   Raw response: {text[:300]}")

        # ── Parse JSON ───────────────────────────────────────────────────
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            json_str = match.group()
            result = json.loads(json_str)
            logger.info(f"   ✅ [AGENT 1] JSON parsed successfully")
            logger.info(f"   ├─ chief_complaint : \"{result.get('chief_complaint')}\"")
            logger.info(f"   ├─ symptoms        : {result.get('symptoms')}")
            logger.info(f"   ├─ duration        : \"{result.get('duration')}\"")
            logger.info(f"   └─ severity        : \"{result.get('severity')}\"")
        else:
            logger.warning("   ⚠️  [AGENT 1] Could not parse JSON from Gemini response — using fallback")
            result = {
                "error": "Could not parse JSON response",
                "chief_complaint": combined_text,
                "symptoms": [],
                "duration": "Unknown",
                "severity": "unknown"
            }

        # ── Process images ───────────────────────────────────────────────
        if image_paths:
            logger.info(f"   🖼️  [AGENT 1] Processing {len(image_paths)} image(s) via Gemini Vision")
            image_findings = _process_images_gemini(image_paths)
            multimodal_findings["images"] = image_findings
            if image_findings.get("clinical_observations"):
                result["symptoms"].extend(image_findings["clinical_observations"])
                logger.info(f"   ➕ Added {len(image_findings['clinical_observations'])} visual observations to symptoms")

        # ── Process videos ───────────────────────────────────────────────
        if video_paths:
            logger.info(f"   🎥 [AGENT 1] Processing {len(video_paths)} video(s) via Gemini Vision")
            video_findings = _process_videos_gemini(video_paths)
            multimodal_findings["videos"] = video_findings
            if video_findings.get("clinical_observations"):
                result["symptoms"].extend(video_findings["clinical_observations"])
                logger.info(f"   ➕ Added {len(video_findings['clinical_observations'])} video observations to symptoms")

        result["multimodal_findings"] = multimodal_findings

        # Store raw Gemini text so it can be saved to Firestore
        result["_gemini_raw_response"] = text
        result["_prompt_sent"]         = prompt.strip()
        result["_input_text"]          = combined_text

        logger.info(f"✅ [AGENT 1] ▶ Intake complete — chief_complaint: \"{result.get('chief_complaint')}\"")
        logger.info("━" * 60)
        return result

    except Exception as e:
        logger.error(f"❌ [AGENT 1] Exception during intake: {str(e)}", exc_info=True)
        return {
            "error": str(e),
            "chief_complaint": combined_text,
            "symptoms": [],
            "duration": "Unknown",
            "severity": "unknown",
            "multimodal_findings": multimodal_findings
        }


# ─── Google Speech-to-Text ────────────────────────────────────────────────────
def _transcribe_audio_google_speech(audio_file_path: str, language: str = "kn-IN") -> str:
    """
    Transcribe an audio file using Google Cloud Speech-to-Text.

    Supports:
      - Kannada (kn-IN) — default for Karnataka PHC patients
      - Hindi   (hi-IN)
      - English (en-IN)

    Automatically falls back to other Indian languages if primary fails.

    Args:
        audio_file_path: Path to audio file (WAV, MP3, M4A, FLAC, OGG)
        language: BCP-47 language code

    Returns:
        Transcribed text string, or empty string on failure
    """
    logger.info(f"   🎙️  [SPEECH-TO-TEXT] Starting transcription")
    logger.info(f"      ├─ file     : {audio_file_path}")
    logger.info(f"      ├─ language : {language}")

    p = Path(audio_file_path)
    if not p.exists():
        logger.error(f"      ❌ Audio file not found: {audio_file_path}")
        return ""

    file_size = p.stat().st_size
    logger.info(f"      └─ size     : {file_size} bytes")

    try:
        from google.cloud import speech as gcs
    except ImportError:
        logger.error("      ❌ google-cloud-speech not installed!")
        logger.error("         Run: .\\venv\\Scripts\\pip install google-cloud-speech")
        return ""

    try:
        client = gcs.SpeechClient()
        logger.info("      ✅ Speech client created (using ADC)")

        with open(audio_file_path, "rb") as f:
            audio_content = f.read()

        # Map file extension → encoding
        ext = p.suffix.lower().lstrip(".")
        encoding_map = {
            "wav":  gcs.RecognitionConfig.AudioEncoding.LINEAR16,
            "mp3":  gcs.RecognitionConfig.AudioEncoding.MP3,
            "flac": gcs.RecognitionConfig.AudioEncoding.FLAC,
            "m4a":  gcs.RecognitionConfig.AudioEncoding.MP3,
            "ogg":  gcs.RecognitionConfig.AudioEncoding.OGG_OPUS,
        }
        encoding = encoding_map.get(ext, gcs.RecognitionConfig.AudioEncoding.LINEAR16)
        logger.info(f"      ├─ encoding : {encoding.name}")

        # Alternative languages — patient may mix Kannada, Hindi, English
        alt_languages = {
            "kn-IN": ["hi-IN", "en-IN"],
            "hi-IN": ["en-IN", "kn-IN"],
            "en-IN": ["hi-IN", "kn-IN"],
        }.get(language, ["en-IN"])

        config = gcs.RecognitionConfig(
            encoding=encoding,
            language_code=language,
            alternative_language_codes=alt_languages,
            enable_automatic_punctuation=True,
            model="default",
        )

        audio = gcs.RecognitionAudio(content=audio_content)
        logger.info("      🤖 Sending audio to Google Speech-to-Text API...")
        response = client.recognize(config=config, audio=audio)

        if not response.results:
            logger.warning("      ⚠️  No speech detected in audio file")
            return ""

        # Concatenate all result segments
        transcript = " ".join(
            result.alternatives[0].transcript
            for result in response.results
            if result.alternatives
        )
        confidence = response.results[0].alternatives[0].confidence if response.results else 0

        logger.info(f"      ✅ Transcription complete:")
        logger.info(f"         ├─ transcript  : \"{transcript[:100]}...\"")
        logger.info(f"         └─ confidence  : {confidence:.1%}")

        return transcript.strip()

    except Exception as e:
        logger.error(f"      ❌ Speech-to-Text error: {str(e)}")
        return ""


# ─── Image Processing (wired to Gemini Vision) ─────────────────────────────────
def _process_images_gemini(image_paths: List[str]) -> dict:
    """Analyze clinical images using Gemini Vision — extracts rash patterns, wound characteristics, etc."""
    logger.info(f"   🔍 [AGENT 1 → GEMINI VISION] Analyzing {len(image_paths)} image(s)...")

    # Import vision_agent (same package)
    try:
        from agents.vision_agent import analyze_clinical_image
    except ImportError:
        try:
            from vision_agent import analyze_clinical_image
        except ImportError:
            logger.error("   ❌ [VISION] Cannot import vision_agent — skipping image analysis")
            return {"images_processed": 0, "clinical_observations": [], "red_flags": [], "error": "vision_agent not importable"}

    findings = {
        "images_processed": 0,
        "images_skipped": 0,
        "clinical_observations": [],
        "red_flags": [],
        "individual_results": []
    }

    for i, image_path in enumerate(image_paths, 1):
        p = Path(image_path)
        if not p.exists():
            logger.warning(f"   ⚠️  [VISION] Image {i}/{len(image_paths)} not found: {image_path}")
            findings["images_skipped"] += 1
            continue

        file_size = p.stat().st_size
        if file_size < 500:
            logger.warning(f"   ⚠️  [VISION] Image {i} is too small ({file_size} bytes) — skipping")
            findings["images_skipped"] += 1
            continue

        logger.info(f"   🖼️  [VISION] Analyzing image {i}/{len(image_paths)}: {p.name} ({file_size} bytes)")

        # ── REAL Gemini Vision call ──────────────────────────────────────
        result = analyze_clinical_image(str(image_path))
        findings["individual_results"].append(result)

        if result.get("success"):
            findings["images_processed"] += 1

            # Merge clinical signals → clinical_observations (fed into symptoms)
            signals = result.get("clinical_signals", [])
            flags   = result.get("red_flags", [])
            findings["clinical_observations"].extend(signals)
            findings["red_flags"].extend(flags)

            logger.info(f"   ✅ [VISION] Image {i} analyzed:")
            logger.info(f"      ├─ visual_findings    : {result.get('visual_findings', '')[:80]}")
            logger.info(f"      ├─ possible_conditions: {result.get('possible_conditions', [])}")
            logger.info(f"      ├─ severity           : {result.get('severity_assessment')}")
            logger.info(f"      ├─ clinical_signals   : {signals}")
            logger.info(f"      ├─ red_flags          : {flags}")
            logger.info(f"      └─ confidence         : {result.get('confidence', 0):.0%}")
        else:
            findings["images_skipped"] += 1
            logger.warning(f"   ⚠️  [VISION] Image {i} analysis failed: {result.get('error')}")

    # Deduplicate
    findings["clinical_observations"] = list(set(findings["clinical_observations"]))
    findings["red_flags"]              = list(set(findings["red_flags"]))

    logger.info(
        f"   ✅ [VISION] Done — {findings['images_processed']} analyzed, "
        f"{findings['images_skipped']} skipped, "
        f"{len(findings['clinical_observations'])} observations extracted"
    )
    return findings


# ─── Video Processing (Gemini Vision) ─────────────────────────────────────────
def _process_videos_gemini(video_paths: List[str]) -> dict:
    """Analyze clinical videos via Gemini Vision — detects breathing distress, movement patterns, etc."""
    logger.info(f"   🔍 [AGENT 1 → GEMINI VISION] Analyzing {len(video_paths)} video(s)...")

    try:
        import vertexai as vx
        from vertexai.generative_models import GenerativeModel as GM, Part
    except ImportError:
        logger.error("   ❌ vertexai not available for video analysis")
        return {"videos_processed": 0, "clinical_observations": [], "error": "vertexai unavailable"}

    findings = {
        "videos_processed": 0,
        "videos_skipped": 0,
        "clinical_observations": [],
        "red_flags": []
    }

    vision_model = GM("gemini-2.5-flash")

    for i, video_path in enumerate(video_paths, 1):
        p = Path(video_path)
        if not p.exists():
            logger.warning(f"   ⚠️  [VISION] Video {i}/{len(video_paths)} not found: {video_path}")
            findings["videos_skipped"] += 1
            continue

        file_size = p.stat().st_size
        logger.info(f"   🎥 [VISION] Processing video {i}/{len(video_paths)}: {p.name} ({file_size} bytes)")

        try:
            with open(video_path, "rb") as f:
                video_bytes = f.read()

            ext = p.suffix.lower()
            mime_map = {".mp4": "video/mp4", ".mov": "video/quicktime", ".avi": "video/x-msvideo", ".webm": "video/webm"}
            mime_type = mime_map.get(ext, "video/mp4")

            video_part = Part.from_data(data=video_bytes, mime_type=mime_type)
            prompt = (
                "You are a clinical video analyst for a PHC in Bengaluru. "
                "Analyze this clinical video and return ONLY valid JSON: "
                '{"clinical_observations": [list of observed symptoms/signs], '
                '"red_flags": [list of emergency warning signs], '
                '"severity": "mild/moderate/severe", '
                '"breathing_pattern": "normal/labored/absent", '
                '"movement_pattern": "normal/restricted/absent"}'
            )

            response = vision_model.generate_content([video_part, prompt])
            text = response.text.strip()

            import re as _re, json as _json
            match = _re.search(r'\{.*\}', text, _re.DOTALL)
            if match:
                vr = _json.loads(match.group())
                findings["clinical_observations"].extend(vr.get("clinical_observations", []))
                findings["red_flags"].extend(vr.get("red_flags", []))
                findings["videos_processed"] += 1
                logger.info(f"   ✅ [VISION] Video {i} analyzed: {vr.get('clinical_observations', [])}")
            else:
                findings["videos_skipped"] += 1
                logger.warning(f"   ⚠️  [VISION] Could not parse video analysis response")

        except Exception as e:
            findings["videos_skipped"] += 1
            logger.error(f"   ❌ [VISION] Video {i} analysis error: {str(e)}")

    findings["clinical_observations"] = list(set(findings["clinical_observations"]))
    findings["red_flags"]              = list(set(findings["red_flags"]))
    logger.info(f"   ✅ [VISION] Video analysis done — {findings['videos_processed']} processed")
    return findings


# ─── CLI Test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  HEALIO — Agent 1 Direct Test")
    print("=" * 60)
    test_input = "I have high fever since 2 days and red rash on my arms and legs. My joints are aching."
    print(f"  Test Input: \"{test_input}\"\n")

    result = run_agent1(symptom_text=test_input)
    print("\n  ── Agent 1 Output ──")
    print(json.dumps(result, indent=2))
    print("=" * 60)
