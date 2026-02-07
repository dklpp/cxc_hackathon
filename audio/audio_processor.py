"""
Audio Processing Utilities

Provides format conversion, resampling, and codec handling for:
- PCM audio
- G.711 μ-law (Twilio standard)
- MP3 (11Labs standard)
- WAV files
"""

import numpy as np
import audioop
import wave
import base64
from scipy import signal
from typing import Union, Tuple
import tempfile
import os


class AudioProcessor:
    """Audio format conversion and processing utilities"""

    # Standard sample rates
    RATE_8KHZ = 8000    # Telephony standard
    RATE_16KHZ = 16000  # Speech recognition standard
    RATE_44KHZ = 44100  # CD quality
    RATE_48KHZ = 48000  # Professional audio

    @staticmethod
    def convert_to_mulaw(
        audio_data: np.ndarray,
        sample_rate: int,
        target_rate: int = 8000
    ) -> bytes:
        """
        Convert PCM audio to G.711 μ-law format (Twilio standard)

        Args:
            audio_data: Audio as numpy array (float32 or int16)
            sample_rate: Current sample rate
            target_rate: Target sample rate (default: 8000 for Twilio)

        Returns:
            bytes: G.711 μ-law encoded audio
        """
        # Convert to int16 if needed
        if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
            audio_data = (audio_data * 32767).astype(np.int16)
        elif audio_data.dtype != np.int16:
            audio_data = audio_data.astype(np.int16)

        # Convert to bytes
        pcm_bytes = audio_data.tobytes()

        # Resample if needed
        if sample_rate != target_rate:
            pcm_bytes = audioop.ratecv(
                pcm_bytes,
                2,  # sample width (2 bytes = 16 bit)
                1,  # channels (mono)
                sample_rate,
                target_rate,
                None
            )[0]

        # Convert to μ-law
        mulaw_bytes = audioop.lin2ulaw(pcm_bytes, 2)

        return mulaw_bytes

    @staticmethod
    def convert_from_mulaw(
        mulaw_data: bytes,
        sample_rate: int = 8000
    ) -> np.ndarray:
        """
        Convert G.711 μ-law to PCM audio

        Args:
            mulaw_data: G.711 μ-law encoded audio bytes
            sample_rate: Sample rate (default: 8000)

        Returns:
            np.ndarray: PCM audio as int16 array
        """
        # Convert μ-law to linear PCM
        pcm_bytes = audioop.ulaw2lin(mulaw_data, 2)

        # Convert bytes to numpy array
        audio_data = np.frombuffer(pcm_bytes, dtype=np.int16)

        return audio_data

    @staticmethod
    def resample_audio(
        audio_data: np.ndarray,
        from_rate: int,
        to_rate: int
    ) -> np.ndarray:
        """
        Resample audio to different sample rate

        Args:
            audio_data: Audio as numpy array
            from_rate: Current sample rate
            to_rate: Target sample rate

        Returns:
            np.ndarray: Resampled audio
        """
        if from_rate == to_rate:
            return audio_data

        # Calculate resampling ratio
        num_samples = int(len(audio_data) * to_rate / from_rate)

        # Use scipy for high-quality resampling
        resampled = signal.resample(audio_data, num_samples)

        return resampled.astype(audio_data.dtype)

    @staticmethod
    def chunk_audio(
        audio_data: np.ndarray,
        chunk_size_ms: int,
        sample_rate: int
    ) -> list:
        """
        Split audio into chunks for streaming

        Args:
            audio_data: Audio as numpy array
            chunk_size_ms: Chunk size in milliseconds
            sample_rate: Sample rate

        Returns:
            list: List of audio chunks
        """
        chunk_size_samples = int(sample_rate * chunk_size_ms / 1000)
        chunks = []

        for i in range(0, len(audio_data), chunk_size_samples):
            chunk = audio_data[i:i + chunk_size_samples]
            chunks.append(chunk)

        return chunks

    @staticmethod
    def encode_mulaw_base64(mulaw_data: bytes) -> str:
        """
        Encode G.711 μ-law audio as base64 (for Twilio WebSocket)

        Args:
            mulaw_data: G.711 μ-law encoded audio bytes

        Returns:
            str: Base64-encoded string
        """
        return base64.b64encode(mulaw_data).decode('utf-8')

    @staticmethod
    def decode_mulaw_base64(base64_str: str) -> bytes:
        """
        Decode base64 string to G.711 μ-law audio (from Twilio WebSocket)

        Args:
            base64_str: Base64-encoded string

        Returns:
            bytes: G.711 μ-law encoded audio bytes
        """
        return base64.b64decode(base64_str)

    @staticmethod
    def save_wav(
        audio_data: np.ndarray,
        output_path: str,
        sample_rate: int,
        channels: int = 1
    ):
        """
        Save audio as WAV file

        Args:
            audio_data: Audio as numpy array (int16)
            output_path: Path to save WAV file
            sample_rate: Sample rate
            channels: Number of channels (default: 1 for mono)
        """
        # Convert to int16 if needed
        if audio_data.dtype != np.int16:
            if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
                audio_data = (audio_data * 32767).astype(np.int16)
            else:
                audio_data = audio_data.astype(np.int16)

        with wave.open(output_path, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)  # 2 bytes = 16 bit
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data.tobytes())

    @staticmethod
    def load_wav(wav_path: str) -> Tuple[np.ndarray, int]:
        """
        Load audio from WAV file

        Args:
            wav_path: Path to WAV file

        Returns:
            tuple: (audio_data as np.ndarray, sample_rate)
        """
        with wave.open(wav_path, 'rb') as wf:
            sample_rate = wf.getframerate()
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            frames = wf.readframes(wf.getnframes())

            # Convert to numpy array
            if sample_width == 1:  # 8-bit
                audio_data = np.frombuffer(frames, dtype=np.uint8)
            elif sample_width == 2:  # 16-bit
                audio_data = np.frombuffer(frames, dtype=np.int16)
            else:
                raise ValueError(f"Unsupported sample width: {sample_width}")

            # Convert stereo to mono if needed
            if channels == 2:
                audio_data = audio_data.reshape(-1, 2).mean(axis=1).astype(audio_data.dtype)

            return audio_data, sample_rate

    @staticmethod
    def normalize_audio(audio_data: np.ndarray) -> np.ndarray:
        """
        Normalize audio to [-1.0, 1.0] range

        Args:
            audio_data: Audio as numpy array

        Returns:
            np.ndarray: Normalized audio (float32)
        """
        if audio_data.dtype == np.int16:
            return audio_data.astype(np.float32) / 32768.0
        elif audio_data.dtype == np.int32:
            return audio_data.astype(np.float32) / 2147483648.0
        else:
            # Already float, just ensure range
            max_val = np.abs(audio_data).max()
            if max_val > 1.0:
                return audio_data / max_val
            return audio_data.astype(np.float32)

    @staticmethod
    def denormalize_audio(audio_data: np.ndarray, dtype=np.int16) -> np.ndarray:
        """
        Convert normalized audio back to integer format

        Args:
            audio_data: Normalized audio (float32, range [-1.0, 1.0])
            dtype: Target dtype (default: np.int16)

        Returns:
            np.ndarray: Audio in target dtype
        """
        if dtype == np.int16:
            return (audio_data * 32767).astype(np.int16)
        elif dtype == np.int32:
            return (audio_data * 2147483647).astype(np.int32)
        else:
            return audio_data.astype(dtype)

    @staticmethod
    def get_duration_ms(audio_data: np.ndarray, sample_rate: int) -> float:
        """
        Get audio duration in milliseconds

        Args:
            audio_data: Audio as numpy array
            sample_rate: Sample rate

        Returns:
            float: Duration in milliseconds
        """
        return (len(audio_data) / sample_rate) * 1000

    @staticmethod
    def convert_mp3_to_wav(mp3_path: str, wav_path: str = None) -> str:
        """
        Convert MP3 to WAV file

        Args:
            mp3_path: Path to MP3 file
            wav_path: Path to save WAV file (optional, generates temp file if None)

        Returns:
            str: Path to WAV file
        """
        try:
            from pydub import AudioSegment

            # Load MP3
            audio = AudioSegment.from_mp3(mp3_path)

            # Generate output path if not provided
            if wav_path is None:
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix='.wav',
                    prefix='converted_'
                )
                wav_path = temp_file.name
                temp_file.close()

            # Export as WAV
            audio.export(wav_path, format='wav')

            return wav_path

        except ImportError:
            raise ImportError(
                "pydub is required for MP3 conversion. "
                "Install with: pip install pydub"
            )

    @staticmethod
    def create_silence(duration_ms: int, sample_rate: int) -> np.ndarray:
        """
        Create silent audio

        Args:
            duration_ms: Duration in milliseconds
            sample_rate: Sample rate

        Returns:
            np.ndarray: Silent audio (int16)
        """
        num_samples = int(sample_rate * duration_ms / 1000)
        return np.zeros(num_samples, dtype=np.int16)


def test_audio_processor():
    """Test audio processor functions"""
    print("\n=== Audio Processor Test ===")

    # Create test audio (1 second, 440 Hz sine wave)
    sample_rate = 16000
    duration = 1.0
    frequency = 440.0

    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.sin(2 * np.pi * frequency * t)
    audio_data = (audio_data * 32767).astype(np.int16)

    print(f"Generated test audio: {len(audio_data)} samples @ {sample_rate}Hz")

    # Test 1: Convert to μ-law and back
    print("\n1. Testing μ-law conversion...")
    mulaw = AudioProcessor.convert_to_mulaw(audio_data, sample_rate, 8000)
    print(f"   μ-law size: {len(mulaw)} bytes")

    recovered = AudioProcessor.convert_from_mulaw(mulaw, 8000)
    print(f"   Recovered size: {len(recovered)} samples")

    # Test 2: Base64 encoding
    print("\n2. Testing base64 encoding...")
    base64_str = AudioProcessor.encode_mulaw_base64(mulaw)
    print(f"   Base64 length: {len(base64_str)} chars")

    decoded = AudioProcessor.decode_mulaw_base64(base64_str)
    print(f"   Decoded matches original: {decoded == mulaw}")

    # Test 3: Resampling
    print("\n3. Testing resampling...")
    resampled = AudioProcessor.resample_audio(audio_data, sample_rate, 8000)
    print(f"   Original: {len(audio_data)} samples @ {sample_rate}Hz")
    print(f"   Resampled: {len(resampled)} samples @ 8000Hz")

    # Test 4: Chunking
    print("\n4. Testing audio chunking...")
    chunks = AudioProcessor.chunk_audio(audio_data, 20, sample_rate)  # 20ms chunks
    print(f"   Created {len(chunks)} chunks of ~20ms each")

    # Test 5: WAV file operations
    print("\n5. Testing WAV file operations...")
    temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    temp_wav.close()

    AudioProcessor.save_wav(audio_data, temp_wav.name, sample_rate)
    print(f"   Saved WAV: {temp_wav.name}")

    loaded_audio, loaded_rate = AudioProcessor.load_wav(temp_wav.name)
    print(f"   Loaded: {len(loaded_audio)} samples @ {loaded_rate}Hz")
    print(f"   Data matches: {np.array_equal(audio_data, loaded_audio)}")

    # Cleanup
    os.unlink(temp_wav.name)

    # Test 6: Normalization
    print("\n6. Testing normalization...")
    normalized = AudioProcessor.normalize_audio(audio_data)
    print(f"   Normalized range: [{normalized.min():.3f}, {normalized.max():.3f}]")

    denormalized = AudioProcessor.denormalize_audio(normalized)
    print(f"   Denormalized matches: {np.allclose(audio_data, denormalized)}")

    # Test 7: Duration calculation
    print("\n7. Testing duration calculation...")
    duration_ms = AudioProcessor.get_duration_ms(audio_data, sample_rate)
    print(f"   Duration: {duration_ms:.1f}ms (expected: 1000ms)")

    # Test 8: Silence generation
    print("\n8. Testing silence generation...")
    silence = AudioProcessor.create_silence(500, sample_rate)
    print(f"   Created {len(silence)} samples of silence")
    print(f"   All zeros: {np.all(silence == 0)}")

    print("\n=== Audio Processor Test Complete ===")


if __name__ == "__main__":
    test_audio_processor()
