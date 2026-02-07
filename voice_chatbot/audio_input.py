"""
Audio input module with Voice Activity Detection (VAD)
"""

import asyncio
import numpy as np
import sounddevice as sd
import torch
from typing import Optional
import threading
from queue import Queue


class MicrophoneRecorder:
    """Records audio from microphone with automatic speech detection using Silero VAD"""

    def __init__(self, sample_rate: int = 16000, channels: int = 1, chunk_duration: float = 0.1):
        """
        Initialize microphone recorder

        Args:
            sample_rate: Audio sample rate (default: 16kHz)
            channels: Number of audio channels (default: 1 for mono)
            chunk_duration: Duration of each audio chunk in seconds (default: 0.1s = 100ms)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)

        # Audio buffers
        self.audio_buffer = []
        self.speech_segments = Queue()

        # Speech detection state
        self.is_speaking = False
        self.silence_counter = 0
        self.silence_threshold = 5  # Number of silent chunks to end speech (0.5 seconds)
        self.speech_threshold = 0.5  # VAD probability threshold

        # Stream and threading
        self.stream = None
        self.is_recording = False

        # Load Silero VAD model
        print("Loading Silero VAD model...")
        self.vad_model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=False
        )
        self.get_speech_timestamps = utils[0]
        print("VAD model loaded successfully")

    def _audio_callback(self, indata, frames, time_info, status):
        """
        Callback function called by sounddevice for each audio chunk

        Args:
            indata: Input audio data as numpy array
            frames: Number of frames
            time_info: Time information
            status: Stream status
        """
        if status:
            print(f"Audio callback status: {status}")

        # Copy audio data
        audio_chunk = indata.copy().flatten()

        # Run VAD on audio chunk
        try:
            audio_tensor = torch.FloatTensor(audio_chunk)

            # Get speech probability
            speech_prob = self.vad_model(audio_tensor, self.sample_rate).item()

            if speech_prob > self.speech_threshold:
                # Speech detected
                if not self.is_speaking:
                    self.is_speaking = True
                    print("\n[Speech detected]", end=" ", flush=True)

                self.audio_buffer.append(audio_chunk)
                self.silence_counter = 0

            elif self.is_speaking:
                # In speech segment but current chunk is silent
                self.audio_buffer.append(audio_chunk)
                self.silence_counter += 1

                # Check if speech has ended
                if self.silence_counter >= self.silence_threshold:
                    # Speech segment complete
                    print("[Speech ended]", flush=True)
                    self._process_speech_segment()

        except Exception as e:
            print(f"\nError in VAD processing: {e}")

    def _process_speech_segment(self):
        """Process complete speech segment and add to queue"""
        if len(self.audio_buffer) > 0:
            # Concatenate all audio chunks
            speech_segment = np.concatenate(self.audio_buffer)

            # Convert float32 to int16 for better compatibility
            speech_segment_int16 = (speech_segment * 32767).astype(np.int16)

            # Add to queue
            self.speech_segments.put(speech_segment_int16)

            # Reset state
            self.audio_buffer = []
            self.is_speaking = False
            self.silence_counter = 0

    def start(self):
        """Start recording from microphone"""
        if self.is_recording:
            print("Already recording")
            return

        self.is_recording = True

        try:
            self.stream = sd.InputStream(
                callback=self._audio_callback,
                channels=self.channels,
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                dtype=np.float32
            )
            self.stream.start()
            print(f"Microphone recording started (Sample rate: {self.sample_rate}Hz)")

        except Exception as e:
            print(f"Error starting microphone: {e}")
            print("\nTroubleshooting tips:")
            print("1. Check if microphone is connected")
            print("2. Check microphone permissions")
            print("3. Try: python -c 'import sounddevice as sd; print(sd.query_devices())'")
            raise

    def stop(self):
        """Stop recording from microphone"""
        if not self.is_recording:
            return

        self.is_recording = False

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        # Process any remaining audio
        if len(self.audio_buffer) > 0:
            self._process_speech_segment()

        print("Microphone recording stopped")

    async def get_speech_segment(self) -> Optional[np.ndarray]:
        """
        Get the next speech segment from the queue (async)

        Returns:
            NumPy array containing speech audio, or None if queue is empty
        """
        try:
            # Non-blocking check
            if not self.speech_segments.empty():
                return self.speech_segments.get_nowait()
            return None
        except Exception:
            return None

    def has_speech_segments(self) -> bool:
        """Check if there are speech segments available"""
        return not self.speech_segments.empty()
