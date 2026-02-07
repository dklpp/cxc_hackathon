"""
Voice Activity Detection (VAD) module with multiple backends

Supports:
- Silero VAD (primary): ML-based, robust, handles noise well
- WebRTC VAD (fallback): Lightweight, good for clean audio
- Energy-based (simple fallback): No dependencies, always works
"""

import numpy as np
import torch
from typing import Literal, Optional
import time


class VoiceActivityDetector:
    """
    Voice Activity Detection with multiple backend options

    Detects when speech starts and ends based on audio analysis.
    """

    def __init__(
        self,
        method: Literal['silero', 'webrtc', 'energy'] = 'silero',
        threshold: float = 0.5,
        min_speech_duration_ms: int = 250,
        min_silence_duration_ms: int = 500,
        sample_rate: int = 16000
    ):
        """
        Initialize Voice Activity Detector

        Args:
            method: Detection method ('silero', 'webrtc', 'energy')
            threshold: Detection sensitivity (0.0-1.0)
            min_speech_duration_ms: Minimum speech duration to start detection
            min_silence_duration_ms: Silence duration to end speech
            sample_rate: Audio sample rate in Hz
        """
        self.method = method
        self.threshold = threshold
        self.min_speech_duration_ms = min_speech_duration_ms
        self.min_silence_duration_ms = min_silence_duration_ms
        self.sample_rate = sample_rate

        # State tracking
        self._speech_started = False
        self._speech_start_time = None
        self._last_speech_time = None
        self._silence_start_time = None

        # Initialize backend
        self._init_backend()

    def _init_backend(self):
        """Initialize the selected VAD backend"""
        if self.method == 'silero':
            self._init_silero()
        elif self.method == 'webrtc':
            self._init_webrtc()
        elif self.method == 'energy':
            self._init_energy()
        else:
            raise ValueError(f"Unknown VAD method: {self.method}")

    def _init_silero(self):
        """Initialize Silero VAD"""
        try:
            import torch
            # Load Silero VAD model
            self.model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False
            )
            self.model.eval()
            (self.get_speech_timestamps,
             self.save_audio,
             self.read_audio,
             self.VADIterator,
             self.collect_chunks) = utils
            print(f"✓ Silero VAD initialized (threshold: {self.threshold})")
        except Exception as e:
            print(f"⚠️  Failed to initialize Silero VAD: {e}")
            print("   Falling back to energy-based VAD")
            self.method = 'energy'
            self._init_energy()

    def _init_webrtc(self):
        """Initialize WebRTC VAD"""
        try:
            import webrtcvad
            # WebRTC VAD modes: 0 (least aggressive) to 3 (most aggressive)
            # Map our 0.0-1.0 threshold to 0-3 mode
            mode = int(self.threshold * 3)
            self.vad = webrtcvad.Vad(mode)
            print(f"✓ WebRTC VAD initialized (mode: {mode})")
        except ImportError:
            print("⚠️  WebRTC VAD not available (install: pip install webrtcvad)")
            print("   Falling back to energy-based VAD")
            self.method = 'energy'
            self._init_energy()

    def _init_energy(self):
        """Initialize energy-based VAD (no dependencies)"""
        # Energy threshold will be calculated dynamically
        self.energy_threshold = None
        self.energy_history = []
        self.energy_history_size = 50  # frames for baseline
        print(f"✓ Energy-based VAD initialized (threshold: {self.threshold})")

    def process_audio_chunk(
        self,
        audio_chunk: np.ndarray,
        sample_rate: Optional[int] = None
    ) -> float:
        """
        Process audio chunk and return speech probability

        Args:
            audio_chunk: Audio data as numpy array (int16)
            sample_rate: Sample rate (uses default if None)

        Returns:
            float: Speech probability (0.0 = silence, 1.0 = speech)
        """
        if sample_rate is None:
            sample_rate = self.sample_rate

        if self.method == 'silero':
            return self._process_silero(audio_chunk, sample_rate)
        elif self.method == 'webrtc':
            return self._process_webrtc(audio_chunk, sample_rate)
        elif self.method == 'energy':
            return self._process_energy(audio_chunk, sample_rate)

    def _process_silero(
        self,
        audio_chunk: np.ndarray,
        sample_rate: int
    ) -> float:
        """Process audio with Silero VAD"""
        # Convert to float32 and normalize
        if audio_chunk.dtype == np.int16:
            audio_float = audio_chunk.astype(np.float32) / 32768.0
        else:
            audio_float = audio_chunk.astype(np.float32)

        # Convert to torch tensor
        audio_tensor = torch.from_numpy(audio_float)

        # Get speech probability
        with torch.no_grad():
            speech_prob = self.model(audio_tensor, sample_rate).item()

        # Update state based on speech probability
        self._update_state(speech_prob)

        return speech_prob

    def _process_webrtc(
        self,
        audio_chunk: np.ndarray,
        sample_rate: int
    ) -> float:
        """Process audio with WebRTC VAD"""
        # WebRTC VAD requires specific frame sizes (10, 20, or 30ms)
        # and sample rates (8000, 16000, 32000, 48000)

        # Convert to bytes
        if audio_chunk.dtype != np.int16:
            audio_chunk = audio_chunk.astype(np.int16)
        audio_bytes = audio_chunk.tobytes()

        # WebRTC VAD returns boolean
        try:
            is_speech = self.vad.is_speech(audio_bytes, sample_rate)
            speech_prob = 1.0 if is_speech else 0.0
        except Exception as e:
            # If frame size is wrong, return 0.5 (uncertain)
            speech_prob = 0.5

        # Update state
        self._update_state(speech_prob)

        return speech_prob

    def _process_energy(
        self,
        audio_chunk: np.ndarray,
        sample_rate: int
    ) -> float:
        """Process audio with energy-based VAD"""
        # Calculate RMS energy
        if audio_chunk.dtype == np.int16:
            audio_float = audio_chunk.astype(np.float32) / 32768.0
        else:
            audio_float = audio_chunk.astype(np.float32)

        rms_energy = np.sqrt(np.mean(audio_float ** 2))

        # Build energy baseline
        self.energy_history.append(rms_energy)
        if len(self.energy_history) > self.energy_history_size:
            self.energy_history.pop(0)

        # Calculate dynamic threshold
        if len(self.energy_history) >= 10:
            baseline = np.median(self.energy_history)
            # Threshold is baseline + (threshold * range)
            energy_range = np.max(self.energy_history) - np.min(self.energy_history)
            self.energy_threshold = baseline + (self.threshold * energy_range)
        else:
            # Not enough history, use fixed threshold
            self.energy_threshold = 0.01

        # Determine if speech based on energy
        is_speech = rms_energy > self.energy_threshold
        speech_prob = 1.0 if is_speech else 0.0

        # Update state
        self._update_state(speech_prob)

        return speech_prob

    def _update_state(self, speech_prob: float):
        """Update internal state based on speech probability"""
        current_time = time.time()
        is_speech = speech_prob >= self.threshold

        if is_speech:
            # Speech detected
            self._last_speech_time = current_time
            self._silence_start_time = None

            if not self._speech_started:
                if self._speech_start_time is None:
                    self._speech_start_time = current_time
                else:
                    # Check if minimum speech duration met
                    duration_ms = (current_time - self._speech_start_time) * 1000
                    if duration_ms >= self.min_speech_duration_ms:
                        self._speech_started = True
        else:
            # Silence detected
            if self._speech_started:
                if self._silence_start_time is None:
                    self._silence_start_time = current_time

    def is_speech_started(self) -> bool:
        """
        Check if speech has been detected

        Returns:
            bool: True if speech started and minimum duration met
        """
        return self._speech_started

    def is_speech_ended(self) -> bool:
        """
        Check if speech has ended (silence detected after speech)

        Returns:
            bool: True if silence duration threshold met after speech
        """
        if not self._speech_started:
            return False

        if self._silence_start_time is None:
            return False

        current_time = time.time()
        silence_duration_ms = (current_time - self._silence_start_time) * 1000

        return silence_duration_ms >= self.min_silence_duration_ms

    def reset(self):
        """Reset VAD state for new detection"""
        self._speech_started = False
        self._speech_start_time = None
        self._last_speech_time = None
        self._silence_start_time = None

        # Reset energy history for energy-based VAD
        if self.method == 'energy':
            self.energy_history = []
            self.energy_threshold = None

    def get_state_info(self) -> dict:
        """
        Get current VAD state information for debugging

        Returns:
            dict: State information
        """
        current_time = time.time()

        info = {
            'method': self.method,
            'threshold': self.threshold,
            'speech_started': self._speech_started,
        }

        if self._speech_start_time:
            info['speech_duration_ms'] = (current_time - self._speech_start_time) * 1000

        if self._silence_start_time:
            info['silence_duration_ms'] = (current_time - self._silence_start_time) * 1000

        if self.method == 'energy' and self.energy_threshold:
            info['energy_threshold'] = self.energy_threshold

        return info


def test_vad():
    """Test VAD with sample audio"""
    import sounddevice as sd

    print("\n=== VAD Test ===")
    print("Testing different VAD methods...")

    for method in ['silero', 'webrtc', 'energy']:
        print(f"\nTesting {method} VAD:")
        try:
            vad = VoiceActivityDetector(
                method=method,
                threshold=0.5,
                min_silence_duration_ms=500
            )

            # Record 3 seconds of audio
            print("Recording 3 seconds... Speak something!")
            duration = 3
            sample_rate = 16000
            recording = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype=np.int16
            )
            sd.wait()

            # Process in chunks
            chunk_size = int(sample_rate * 0.03)  # 30ms chunks
            num_chunks = len(recording) // chunk_size

            print(f"Processing {num_chunks} chunks...")
            for i in range(num_chunks):
                start = i * chunk_size
                end = start + chunk_size
                chunk = recording[start:end].flatten()

                prob = vad.process_audio_chunk(chunk, sample_rate)

                if vad.is_speech_started() and not vad.is_speech_ended():
                    status = "🔴 SPEAKING"
                elif vad.is_speech_ended():
                    status = "⚪ ENDED"
                else:
                    status = "⚫ SILENCE"

                if i % 10 == 0:  # Print every 300ms
                    print(f"  Chunk {i}: {status} (prob: {prob:.2f})")

            print(f"✓ {method} VAD test complete")

        except Exception as e:
            print(f"✗ {method} VAD test failed: {e}")

    print("\n=== VAD Test Complete ===")


if __name__ == "__main__":
    test_vad()
