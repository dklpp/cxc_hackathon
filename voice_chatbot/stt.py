"""
Speech-to-Text module using ElevenLabs API

Adapted from existing implementation in tts_stt_11labs branch
"""

import os
import tempfile
import wave
from pathlib import Path
from typing import Dict
import requests
import numpy as np
import aiohttp
import asyncio


class SpeechToText:
    """ElevenLabs Speech-to-Text client"""

    def __init__(self, api_key: str, model: str = "scribe_v2"):
        """
        Initialize STT client

        Args:
            api_key: ElevenLabs API key
            model: Model to use for transcription (default: scribe_v2)
        """
        self.api_key = api_key
        self.model = model
        self.url = "https://api.elevenlabs.io/v1/speech-to-text"

    async def transcribe_audio_chunk(self, audio_data: np.ndarray, sample_rate: int) -> str:
        """
        Transcribe audio chunk to text

        Args:
            audio_data: Audio data as NumPy array (int16)
            sample_rate: Sample rate of audio

        Returns:
            Transcribed text string

        Raises:
            Exception: If transcription fails
        """
        # Create temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_path = tmp_file.name

            try:
                # Write audio to WAV file
                with wave.open(tmp_path, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(audio_data.tobytes())

                # Transcribe file
                result = await self._transcribe_file(tmp_path)

                return result.get('text', '').strip()

            finally:
                # Clean up temp file
                try:
                    Path(tmp_path).unlink()
                except Exception:
                    pass

    async def _transcribe_file(self, audio_file_path: str) -> Dict:
        """
        Transcribe audio file using ElevenLabs API

        Args:
            audio_file_path: Path to audio file

        Returns:
            dict: Transcription result

        Raises:
            Exception: If API request fails
        """
        headers = {
            "xi-api-key": self.api_key
        }

        data = aiohttp.FormData()
        data.add_field('model_id', self.model)

        # Read file and add to form data
        with open(audio_file_path, 'rb') as audio_file:
            file_content = audio_file.read()
            data.add_field(
                'file',
                file_content,
                filename=os.path.basename(audio_file_path),
                content_type='audio/wav'
            )

        # Make async API request
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, headers=headers, data=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(
                        f"STT API request failed with status {response.status}: {error_text}"
                    )

    def transcribe_audio(self, audio_file_path: str) -> Dict:
        """
        Synchronous transcription method (for compatibility)

        Args:
            audio_file_path: Path to audio file

        Returns:
            dict: Transcription result

        Raises:
            FileNotFoundError: If audio file doesn't exist
            Exception: If API request fails
        """
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

        headers = {
            "xi-api-key": self.api_key
        }

        with open(audio_file_path, 'rb') as audio_file:
            files = {
                'file': (os.path.basename(audio_file_path), audio_file, 'audio/mpeg')
            }

            data = {
                'model_id': self.model
            }

            response = requests.post(self.url, headers=headers, files=files, data=data)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                f"API request failed with status {response.status_code}: {response.text}"
            )
