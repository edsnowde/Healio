"""
Speech-to-Text Handler with Kannada Support
Integrates Google Cloud Speech-to-Text API for real-time audio transcription
"""

from google.cloud import speech_v1
import io
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpeechToTextHandler:
    """Handles real-time audio transcription with Kannada/Hindi language support"""
    
    def __init__(self):
        self.client = speech_v1.SpeechClient()
        self.language_codes = {
            "kannada": "kn-IN",
            "hindi": "hi-IN",
            "english": "en-IN",
            "tamil": "ta-IN",
            "telugu": "te-IN",
        }
    
    def transcribe_audio(
        self, 
        audio_bytes: bytes, 
        language: str = "kannada",
        sample_rate_hertz: int = 16000,
        audio_encoding: str = "LINEAR16"
    ) -> dict:
        """
        Transcribe audio bytes to text
        
        Args:
            audio_bytes: Raw audio data (typically 16-bit PCM WAV or MP3)
            language: Language code ("kannada", "hindi", "english", etc.)
            sample_rate_hertz: Sample rate of audio (default 16000 Hz)
            audio_encoding: Audio encoding type ("LINEAR16" for WAV, "MP3" for MP3)
        
        Returns:
            {
                "success": bool,
                "transcript": str (full transcript),
                "confidence": float (0.0-1.0),
                "language": str,
                "words": [{"word": str, "confidence": float, "start_ms": int}]
            }
        """
        
        try:
            language_code = self.language_codes.get(language.lower(), "kn-IN")
            
            # Prepare audio
            audio = speech_v1.RecognitionAudio(content=audio_bytes)
            
            # Speech recognition config with Kannada support
            config = speech_v1.RecognitionConfig(
                encoding=speech_v1.RecognitionConfig.AudioEncoding[audio_encoding],
                sample_rate_hertz=sample_rate_hertz,
                language_code=language_code,
                enable_automatic_punctuation=True,
                enable_word_time_offsets=True,
                model="latest_long",  # Best model for longer audio
            )
            
            # Call Speech-to-Text API
            response = self.client.recognize(config=config, audio=audio)
            
            if not response.results:
                return {
                    "success": False,
                    "transcript": "",
                    "confidence": 0.0,
                    "language": language,
                    "error": "No speech detected in audio"
                }
            
            # Process results
            transcript = ""
            total_confidence = 0.0
            word_results = []
            result_count = 0
            
            for result in response.results:
                if result.alternatives:
                    alternative = result.alternatives[0]
                    transcript += alternative.transcript + " "
                    total_confidence += alternative.confidence
                    result_count += 1
                    
                    # Extract word-level details
                    if hasattr(alternative, 'words') and alternative.words:
                        for word_info in alternative.words:
                            word_results.append({
                                "word": word_info.word,
                                "confidence": word_info.confidence,
                                "start_ms": int(word_info.start_time.seconds * 1000 + 
                                               word_info.start_time.microseconds / 1000),
                                "end_ms": int(word_info.end_time.seconds * 1000 + 
                                             word_info.end_time.microseconds / 1000),
                            })
            
            avg_confidence = total_confidence / result_count if result_count > 0 else 0.0
            
            return {
                "success": True,
                "transcript": transcript.strip(),
                "confidence": round(avg_confidence, 3),
                "language": language,
                "words": word_results,
                "full_response": {
                    "results_count": len(response.results),
                    "is_final": response.results[-1].is_final if response.results else False
                }
            }
        
        except Exception as e:
            logger.error(f"Speech-to-Text error: {str(e)}")
            return {
                "success": False,
                "transcript": "",
                "confidence": 0.0,
                "language": language,
                "error": str(e)
            }
    
    def stream_transcribe_audio(self, audio_stream, language: str = "kannada"):
        """
        Stream audio transcription (for real-time audio streaming)
        
        Args:
            audio_stream: Generator yielding audio chunks
            language: Language code
        
        Yields:
            Partial transcription results as they arrive
        """
        language_code = self.language_codes.get(language.lower(), "kn-IN")
        
        requests = self._create_stream_requests(
            audio_stream, language_code
        )
        
        config = speech_v1.StreamingRecognitionConfig(
            config=speech_v1.RecognitionConfig(
                encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=language_code,
                enable_automatic_punctuation=True,
                model="latest_long",
            ),
            interim_results=True,
        )
        
        try:
            responses = self.client.streaming_recognize(config, requests)
            
            for response in responses:
                if response.results:
                    result = response.results[0]
                    
                    yield {
                        "transcript": result.alternatives[0].transcript if result.alternatives else "",
                        "confidence": result.alternatives[0].confidence if result.alternatives else 0.0,
                        "is_final": result.is_final,
                        "language": language,
                    }
        
        except Exception as e:
            logger.error(f"Stream transcription error: {str(e)}")
            yield {
                "error": str(e),
                "transcript": "",
                "confidence": 0.0
            }
    
    def _create_stream_requests(self, audio_stream, language_code):
        """Helper to create streaming requests"""
        
        # Send config first
        config = speech_v1.StreamingRecognitionConfig(
            config=speech_v1.RecognitionConfig(
                encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=language_code,
                enable_automatic_punctuation=True,
            ),
            interim_results=True,
        )
        
        yield speech_v1.StreamingRecognizeRequest(streaming_config=config)
        
        # Send audio chunks
        for audio_chunk in audio_stream:
            yield speech_v1.StreamingRecognizeRequest(audio_content=audio_chunk)


# Singleton instance
_speech_handler = None

def get_speech_handler() -> SpeechToTextHandler:
    """Get or create Speech-to-Text handler singleton"""
    global _speech_handler
    if _speech_handler is None:
        _speech_handler = SpeechToTextHandler()
    return _speech_handler
