#!/usr/bin/env python3
"""
Enhanced Voice Chat with Automatic Speech Detection

Extends the original voice_chat.py with:
- Automatic speech detection using VAD (no manual Enter key)
- Support for multiple VAD backends (Silero, WebRTC, Energy)
- Backward compatible with manual mode

Usage:
    # Automatic mode with VAD (default)
    python voice_chat_enhanced.py --use-vad

    # Manual mode (original behavior)
    python voice_chat_enhanced.py --no-vad

    # Specific VAD method
    python voice_chat_enhanced.py --vad-method silero
"""

import os
import sys
import wave
import tempfile
import numpy as np
from pathlib import Path

# Import VAD and audio processor
from vad.voice_activity_detector import VoiceActivityDetector
from audio.audio_processor import AudioProcessor

# Import original VoiceChat
from voice_chat import VoiceChat, SAMPLE_RATE, CHANNELS, RECORDING_DEVICE
import sounddevice as sd


class VoiceChatEnhanced(VoiceChat):
    """Enhanced VoiceChat with automatic speech detection"""

    def __init__(
        self,
        model: str = "gpt-4o",
        system_prompt: str = None,
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",
        use_vad: bool = True,
        vad_method: str = 'silero',
        vad_threshold: float = 0.5,
        vad_min_silence_ms: int = 500,
        vad_min_speech_ms: int = 250
    ):
        """
        Initialize enhanced voice chat

        Args:
            model: OpenAI model to use
            system_prompt: System prompt for AI
            voice_id: 11Labs voice ID
            use_vad: Use automatic VAD (True) or manual mode (False)
            vad_method: VAD method ('silero', 'webrtc', 'energy')
            vad_threshold: VAD sensitivity (0.0-1.0)
            vad_min_silence_ms: Silence duration to end speech
            vad_min_speech_ms: Minimum speech duration to start
        """
        # Initialize parent class
        super().__init__(model, system_prompt, voice_id)

        # VAD configuration
        self.use_vad = use_vad
        self.vad = None

        if use_vad:
            print(f"\n🎯 Initializing VAD ({vad_method})...")
            self.vad = VoiceActivityDetector(
                method=vad_method,
                threshold=vad_threshold,
                min_speech_duration_ms=vad_min_speech_ms,
                min_silence_duration_ms=vad_min_silence_ms,
                sample_rate=SAMPLE_RATE
            )
            print(f"   ✓ VAD ready (silence threshold: {vad_min_silence_ms}ms)")

    def record_audio_with_vad(self) -> str:
        """
        Record audio with automatic speech detection

        Automatically detects:
        - When user starts speaking
        - When user stops speaking (silence)

        Returns:
            str: Path to temporary audio file
        """
        print("\n🎤 Listening... (start speaking)")

        recording_chunks = []
        chunk_size = int(SAMPLE_RATE * 0.03)  # 30ms chunks
        is_recording = False
        speech_detected = False

        def callback(indata, frames, time, status):
            """Audio callback for real-time processing"""
            nonlocal is_recording, speech_detected

            if status:
                print(f"Audio status: {status}")

            # Process audio chunk with VAD
            audio_chunk = indata.copy().flatten()
            speech_prob = self.vad.process_audio_chunk(audio_chunk, SAMPLE_RATE)

            # Check speech state
            if self.vad.is_speech_started():
                if not speech_detected:
                    speech_detected = True
                    print("🗣️  Speech detected!")
                is_recording = True

            # Add chunk to recording if we're recording
            if is_recording:
                recording_chunks.append(audio_chunk)

            # Check if speech ended
            if self.vad.is_speech_ended() and is_recording:
                print("⏸️  Speech ended (silence detected)")
                raise sd.CallbackStop

        try:
            # Start streaming audio input
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=np.int16,
                callback=callback,
                device=RECORDING_DEVICE,
                blocksize=chunk_size
            ):
                # Wait until callback stops (speech ended)
                while True:
                    sd.sleep(100)

        except sd.CallbackStop:
            pass

        # Reset VAD for next turn
        self.vad.reset()

        if not recording_chunks:
            print("⚠️  No speech detected")
            return None

        # Concatenate all recorded chunks
        recording = np.concatenate(recording_chunks)
        duration = len(recording) / SAMPLE_RATE
        print(f"✓ Recorded {duration:.1f} seconds")

        # Save to temporary WAV file
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix='.wav',
            prefix='user_recording_vad_'
        )
        temp_path = temp_file.name
        temp_file.close()

        with wave.open(temp_path, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(recording.tobytes())

        return temp_path

    def record_audio_manual(self, duration: float = None) -> str:
        """
        Record audio manually (original behavior)

        Args:
            duration: Recording duration. If None, user presses Enter to stop.

        Returns:
            str: Path to temporary audio file
        """
        # Use parent class method
        return super().record_audio(duration)

    def record_audio(self, duration: float = None) -> str:
        """
        Record audio (VAD or manual based on configuration)

        Args:
            duration: Recording duration (manual mode only)

        Returns:
            str: Path to temporary audio file
        """
        if self.use_vad:
            return self.record_audio_with_vad()
        else:
            return self.record_audio_manual(duration)

    def process_turn_vad(self) -> tuple:
        """
        Process one conversation turn with VAD

        Returns:
            tuple: (user_text, agent_text, audio_path)
        """
        print("\n" + "="*70)
        print(f"TURN {self.turn_counter + 1}")
        print("="*70)

        # Record with automatic VAD
        audio_path = self.record_audio_with_vad()

        if audio_path is None:
            return None, None, None

        try:
            # Transcribe to text
            user_text = self.speech_to_text(audio_path)

            if not user_text:
                print("⚠️  No speech detected. Please try again.")
                return None, None, None

            # Get LLM response
            agent_text = self.get_llm_response(user_text)

            # Convert response to speech
            agent_audio_path = self.text_to_speech(agent_text)

            return user_text, agent_text, agent_audio_path

        finally:
            # Clean up temporary recording file
            if os.path.exists(audio_path):
                os.unlink(audio_path)

    def process_turn(self, duration: float = None) -> tuple:
        """
        Process one conversation turn (VAD or manual)

        Args:
            duration: Recording duration (manual mode only)

        Returns:
            tuple: (user_text, agent_text, audio_path)
        """
        if self.use_vad:
            return self.process_turn_vad()
        else:
            return super().process_turn(duration)

    def run_interactive(self, max_turns: int = None):
        """
        Run interactive voice chat session

        Args:
            max_turns: Maximum number of turns. None = unlimited.
        """
        mode_str = "VAD (Automatic)" if self.use_vad else "Manual"
        print("\n" + f"🎙️  VOICE CHAT STARTED ({mode_str}) ".center(70, "="))

        if self.use_vad:
            print("\nInstructions:")
            print("  - Speak when ready (speech will be detected automatically)")
            print("  - Stop speaking when done (silence will be detected)")
            print("  - Press Ctrl+C to exit")
        else:
            print("\nInstructions:")
            print("  - Press Enter when ready to speak")
            print("  - Speak your message")
            print("  - Press Enter again to stop recording")
            print("  - Type 'quit' or 'exit' at any prompt to end the session")

        print("\n" + "="*70)

        turn = 0
        while True:
            if max_turns and turn >= max_turns:
                print(f"\n✓ Reached maximum turns ({max_turns})")
                break

            try:
                if not self.use_vad:
                    # Manual mode: wait for user to be ready
                    print("\n📢 Press Enter when ready to speak (or type 'quit' to exit)...")
                    user_input = input()

                    if user_input.lower() in ['quit', 'exit', 'q']:
                        break

                # Process one conversation turn
                result = self.process_turn(duration=None)

                if result[0] is None:  # No speech detected
                    continue

                turn += 1

            except KeyboardInterrupt:
                print("\n\n⚠️  Interrupted by user")
                break

        print("\n" + "🎙️  VOICE CHAT ENDED ".center(70, "="))
        print(f"\nTotal turns: {turn}")
        print(f"Audio files saved in: {self.output_dir if hasattr(self, 'output_dir') else 'chat_outputs'}/")
        print("\nConversation history:")
        self._print_history()


def main():
    """Main CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Enhanced voice chat with automatic speech detection"
    )
    parser.add_argument(
        '--model',
        default='gpt-4o',
        help='OpenAI model to use (default: gpt-4o)'
    )
    parser.add_argument(
        '--voice',
        default='21m00Tcm4TlvDq8ikWAM',
        help='11Labs voice ID (default: Rachel)'
    )
    parser.add_argument(
        '--turns',
        type=int,
        default=None,
        help='Maximum number of conversation turns (default: unlimited)'
    )
    parser.add_argument(
        '--system-prompt',
        help='Custom system prompt for the AI agent'
    )

    # VAD options
    vad_group = parser.add_mutually_exclusive_group()
    vad_group.add_argument(
        '--use-vad',
        action='store_true',
        default=True,
        help='Use automatic VAD (default)'
    )
    vad_group.add_argument(
        '--no-vad',
        action='store_true',
        help='Use manual mode (press Enter to start/stop)'
    )

    parser.add_argument(
        '--vad-method',
        choices=['silero', 'webrtc', 'energy'],
        default='silero',
        help='VAD method to use (default: silero)'
    )
    parser.add_argument(
        '--vad-threshold',
        type=float,
        default=0.5,
        help='VAD sensitivity threshold 0.0-1.0 (default: 0.5)'
    )
    parser.add_argument(
        '--vad-silence-ms',
        type=int,
        default=500,
        help='Silence duration in ms to end speech (default: 500)'
    )

    args = parser.parse_args()

    # Determine VAD mode
    use_vad = not args.no_vad

    try:
        # Create enhanced voice chat
        chat = VoiceChatEnhanced(
            model=args.model,
            system_prompt=args.system_prompt,
            voice_id=args.voice,
            use_vad=use_vad,
            vad_method=args.vad_method,
            vad_threshold=args.vad_threshold,
            vad_min_silence_ms=args.vad_silence_ms
        )

        # Run interactive session
        chat.run_interactive(max_turns=args.turns)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
