"""
Text-to-Speech module using ElevenLabs API

Adapted from existing implementation in tts_stt_11labs branch
"""

from typing import Optional, Dict
import aiohttp


class TextToSpeech:
    """ElevenLabs Text-to-Speech client"""

    def __init__(
        self,
        api_key: str,
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",
        model: str = "eleven_multilingual_v2"
    ):
        """
        Initialize TTS client

        Args:
            api_key: ElevenLabs API key
            voice_id: Voice ID to use (default: Rachel)
            model: Model to use (default: eleven_multilingual_v2)
        """
        self.api_key = api_key
        self.voice_id = voice_id
        self.model = model

        # Default voice settings
        self.voice_settings = {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }

    async def synthesize(self, text: str) -> bytes:
        """
        Convert text to speech and return MP3 audio bytes

        Args:
            text: Text to convert to speech

        Returns:
            bytes: MP3 audio data

        Raises:
            Exception: If TTS API request fails
        """
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }

        data = {
            "text": text,
            "model_id": self.model,
            "voice_settings": self.voice_settings
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        error_text = await response.text()
                        raise Exception(
                            f"TTS API request failed with status {response.status}: {error_text}"
                        )

        except Exception as e:
            raise Exception(f"TTS error: {e}")

    def set_voice_settings(
        self,
        stability: Optional[float] = None,
        similarity_boost: Optional[float] = None,
        style: Optional[float] = None,
        use_speaker_boost: Optional[bool] = None
    ):
        """
        Update voice settings

        Args:
            stability: Voice stability (0-1). Lower = more expressive, higher = more consistent
            similarity_boost: Voice similarity (0-1). Higher = more similar to original voice
            style: Style exaggeration (0-1). Higher = more exaggerated
            use_speaker_boost: Enable speaker boost for clarity
        """
        if stability is not None:
            self.voice_settings["stability"] = max(0.0, min(1.0, stability))
        if similarity_boost is not None:
            self.voice_settings["similarity_boost"] = max(0.0, min(1.0, similarity_boost))
        if style is not None:
            self.voice_settings["style"] = max(0.0, min(1.0, style))
        if use_speaker_boost is not None:
            self.voice_settings["use_speaker_boost"] = use_speaker_boost

    def get_voice_settings(self) -> Dict:
        """Get current voice settings"""
        return self.voice_settings.copy()
