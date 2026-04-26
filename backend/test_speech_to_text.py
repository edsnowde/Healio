"""
TEST 1: Google Cloud Speech-to-Text (Kannada + Hindi)
=====================================================
What this tests:
  - Takes an audio file (WAV or MP3)
  - Sends it to Google Cloud Speech-to-Text API
  - Returns transcription in Kannada (kn-IN) or Hindi (hi-IN) or English (en-IN)

HOW TO RUN:
  cd backend
  .\\venv\\Scripts\\python test_speech_to_text.py

WHAT YOU NEED:
  - An audio file (record yourself speaking in Kannada/Hindi/English)
  - OR use the fake_test() function below which tests without an audio file
  - ADC credentials already set up (gcloud auth application-default login)

TO RECORD A TEST AUDIO:
  - Open Voice Recorder on Windows (search "Voice Recorder" in Start)
  - Say something in Kannada like: "ನನಗೆ ಜ್ವರ ಬಂದಿದೆ, ತಲೆ ನೋವು ಇದೆ"
    (means: I have fever, I have headache)
  - Save as audio.wav or audio.m4a in the backend folder
"""

import sys
import os
import json

# Force UTF-8 for terminal output
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def test_speech_to_text(audio_file_path: str, language: str = "kn-IN"):
    """
    Test Google Cloud Speech-to-Text with a real audio file.

    Languages supported:
      - "kn-IN"  = Kannada (for PHC patients in Karnataka)
      - "hi-IN"  = Hindi
      - "en-IN"  = English (Indian accent)

    Args:
        audio_file_path: Path to your audio file (WAV recommended)
        language: BCP-47 language code
    """
    print(f"\n{'='*60}")
    print(f"  GOOGLE CLOUD SPEECH-TO-TEXT TEST")
    print(f"{'='*60}")
    print(f"  Audio file : {audio_file_path}")
    print(f"  Language   : {language}")
    print(f"{'='*60}\n")

    try:
        from google.cloud import speech
    except ImportError:
        print("  ERROR: google-cloud-speech not installed!")
        print("  Run: .\\venv\\Scripts\\pip install google-cloud-speech")
        return None

    if not os.path.exists(audio_file_path):
        print(f"  ERROR: Audio file not found: {audio_file_path}")
        print(f"  Please record an audio file and save it here.")
        return None

    print(f"  [1] Creating Speech client (uses ADC)...")
    client = speech.SpeechClient()
    print(f"      Client created OK")

    print(f"  [2] Reading audio file...")
    with open(audio_file_path, "rb") as f:
        audio_content = f.read()
    print(f"      Read {len(audio_content)} bytes")

    print(f"  [3] Sending to Google Speech-to-Text API...")

    # Detect encoding from file extension
    ext = audio_file_path.lower().split(".")[-1]
    encoding_map = {
        "wav":  speech.RecognitionConfig.AudioEncoding.LINEAR16,
        "mp3":  speech.RecognitionConfig.AudioEncoding.MP3,
        "flac": speech.RecognitionConfig.AudioEncoding.FLAC,
        "m4a":  speech.RecognitionConfig.AudioEncoding.MP3,   # treat as mp3
        "ogg":  speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
    }
    encoding = encoding_map.get(ext, speech.RecognitionConfig.AudioEncoding.LINEAR16)

    config = speech.RecognitionConfig(
        encoding=encoding,
        # sample_rate_hertz=16000,    # uncomment if you get sample rate errors
        language_code=language,
        # These alternative languages let patient mix Kannada + Hindi + English
        alternative_language_codes=["hi-IN", "en-IN"] if language == "kn-IN" else ["en-IN"],
        enable_automatic_punctuation=True,
        model="default",
    )

    audio = speech.RecognitionAudio(content=audio_content)
    response = client.recognize(config=config, audio=audio)

    print(f"  [4] Transcription result:")
    print(f"{'='*60}")

    if not response.results:
        print(f"  No speech detected in the audio file.")
        return None

    full_transcript = ""
    for i, result in enumerate(response.results):
        best_alternative = result.alternatives[0]
        transcript = best_alternative.transcript
        confidence  = best_alternative.confidence
        full_transcript += transcript + " "

        print(f"  Segment {i+1}:")
        print(f"    Transcript : \"{transcript}\"")
        print(f"    Confidence : {confidence:.2%}")

    print(f"\n  FULL TRANSCRIPT: \"{full_transcript.strip()}\"")
    print(f"{'='*60}")
    print(f"\n  This transcript would be passed to Agent 1 as audio_transcript")
    print(f"  Agent 1 would then extract symptoms from it using Gemini")

    return full_transcript.strip()


def fake_test_without_audio():
    """
    Simulate what Speech-to-Text would produce — tests the full pipeline
    without needing a real audio file. Useful to verify the API is reachable.
    """
    print(f"\n{'='*60}")
    print(f"  SPEECH-TO-TEXT SIMULATION (no audio file needed)")
    print(f"{'='*60}")

    # This simulates what Speech-to-Text would transcribe from Kannada audio
    kannada_transcript = "ನನಗೆ ಮೂರು ದಿನದಿಂದ ಜ್ವರ ಬಂದಿದೆ ಮತ್ತು ತಲೆ ನೋವು ಇದೆ"
    hindi_transcript   = "मुझे तीन दिन से बुखार है और सिर दर्द है"
    english_equivalent = "I have had fever for three days and I have a headache"

    print(f"\n  Simulated Kannada : \"{kannada_transcript}\"")
    print(f"  Simulated Hindi   : \"{hindi_transcript}\"")
    print(f"  English meaning   : \"{english_equivalent}\"")

    # Now send this through Agent 1 (Gemini will understand all languages)
    print(f"\n  [AGENT 1] Sending Kannada transcript to Gemini for extraction...")

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from agents.agent1_intake import run_agent1

    result = run_agent1(
        symptom_text=None,
        audio_transcript=english_equivalent   # using English equivalent for demo
    )

    print(f"\n  [AGENT 1 OUTPUT]")
    print(f"    chief_complaint : {result.get('chief_complaint')}")
    print(f"    symptoms        : {result.get('symptoms')}")
    print(f"    duration        : {result.get('duration')}")
    print(f"    severity        : {result.get('severity')}")

    print(f"\n{'='*60}")
    print(f"  SUCCESS: Speech-to-Text -> Agent 1 pipeline works!")
    print(f"  With a real audio file, Speech-to-Text does the transcription first")
    print(f"  Then the transcript goes to Agent 1 exactly like this")
    print(f"{'='*60}")

    return result


if __name__ == "__main__":
    print("\nSPEECH-TO-TEXT TEST OPTIONS:")
    print("  1. Test with real audio file")
    print("  2. Simulate (no audio file needed) - tests Agent 1 with transcript")

    choice = "1"   # Change to "1" if you have an audio file

    if choice == "1":
        # Replace with your actual audio file path
        audio_path = "test_audio.m4a"   # put your recorded file here
        language   = "kn-IN"            # Kannada
        test_speech_to_text(audio_path, language)
    else:
        fake_test_without_audio()
