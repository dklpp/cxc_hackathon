"""
Audio output module for playback
"""

import io
import numpy as np
import sounddevice as sd
from pydub import AudioSegment


class AudioPlayer:
    """Audio playback using sounddevice"""

    def __init__(self):
        """Initialize audio player"""
        pass

    def play_mp3(self, mp3_bytes: bytes):
        """
        Play MP3 audio through speakers

        Args:
            mp3_bytes: MP3 audio data as bytes

        Raises:
            Exception: If playback fails
        """
        try:
            # Convert MP3 to AudioSegment
            audio_segment = AudioSegment.from_mp3(io.BytesIO(mp3_bytes))

            # Convert to numpy array
            samples = np.array(audio_segment.get_array_of_samples())

            # Normalize to float32 (-1.0 to 1.0)
            if audio_segment.sample_width == 2:  # 16-bit audio
                samples = samples.astype(np.float32) / 32768.0
            elif audio_segment.sample_width == 4:  # 32-bit audio
                samples = samples.astype(np.float32) / 2147483648.0
            else:
                samples = samples.astype(np.float32)

            # Handle stereo vs mono
            if audio_segment.channels == 2:
                # Reshape for stereo
                samples = samples.reshape((-1, 2))

            # Play audio (blocking - waits until playback completes)
            sd.play(samples, samplerate=audio_segment.frame_rate)
            sd.wait()

        except Exception as e:
            raise Exception(f"Audio playback error: {e}")

    def play_wav(self, wav_data: np.ndarray, sample_rate: int):
        """
        Play WAV audio from numpy array

        Args:
            wav_data: Audio data as numpy array
            sample_rate: Sample rate of audio

        Raises:
            Exception: If playback fails
        """
        try:
            # Normalize if needed
            if wav_data.dtype == np.int16:
                audio = wav_data.astype(np.float32) / 32768.0
            else:
                audio = wav_data.astype(np.float32)

            # Play audio (blocking)
            sd.play(audio, samplerate=sample_rate)
            sd.wait()

        except Exception as e:
            raise Exception(f"Audio playback error: {e}")

    def stop(self):
        """Stop current playback"""
        sd.stop()

    def test_audio_device(self):
        """Test if audio device is working"""
        try:
            # Get default output device
            device_info = sd.query_devices(sd.default.device[1], 'output')
            print(f"Audio output device: {device_info['name']}")
            print(f"Sample rate: {device_info['default_samplerate']} Hz")
            print(f"Channels: {device_info['max_output_channels']}")
            return True
        except Exception as e:
            print(f"Audio device error: {e}")
            return False
