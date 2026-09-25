"""Text to Speech Service using Google Cloud Text-to-Speech."""

import os
from typing import Optional

try:
    from google.cloud import texttospeech
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False


class TTSService:
    def __init__(self, voice_name: Optional[str] = None):
        self.voice_name = voice_name or os.environ.get("TTS_VOICE_NAME", "en-US-Journey-F")
        self.client = None
        if TTS_AVAILABLE:
            try:
                self.client = texttospeech.TextToSpeechClient()
            except Exception as e:
                print(f"[TTSService] Warning: Could not initialize TextToSpeechClient: {e}")

    def synthesize(self, text: str) -> Optional[bytes]:
        """Synthesize text to MP3 audio bytes using Google Cloud TTS."""
        if not self.client or not text.strip():
            return None

        try:
            synthesis_input = texttospeech.SynthesisInput(text=text.strip())
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name=self.voice_name,
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.05,
                pitch=0.0,
            )
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config,
            )
            return response.audio_content
        except Exception as e:
            print(f"[TTSService] Speech synthesis error: {e}")
            return None
