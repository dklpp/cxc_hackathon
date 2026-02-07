#!/usr/bin/env python3
"""
Voice Chat Simulation between User and AI Agent

Flow:
1. User speaks (microphone) -> STT (11Labs) -> Text
2. Text -> LLM (OpenAI GPT) -> Response text
3. Response text -> TTS (11Labs) -> Speech audio file
"""

import os
import sys
import wave
import tempfile
from pathlib import Path
from dotenv import load_dotenv
import sounddevice as sd
import numpy as np
from openai import OpenAI
from typing import List, Dict

# Import our STT and TTS modules
from stt.speech_to_text import transcribe_audio
from tts.text_to_speech import text_to_speech

# Load environment variables
load_dotenv()

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env file")

openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Configuration
SAMPLE_RATE = 16000  # 16kHz is standard for speech
CHANNELS = 1  # Mono
RECORDING_DEVICE = None  # None = default device
OUTPUT_DIR = "chat_outputs"  # Directory to save audio files

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)


class VoiceChat:
    """Manages voice chat conversation between user and AI agent"""

    def __init__(
        self,
        model: str = "gpt-4o",
        system_prompt: str = None,
        voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
    ):
        """
        Initialize voice chat

        Args:
            model: OpenAI model to use (gpt-4o, gpt-4, gpt-3.5-turbo, etc.)
            system_prompt: System prompt for the AI agent
            voice_id: 11Labs voice ID for TTS
        """
        self.model = model
        self.voice_id = voice_id
        self.conversation_history: List[Dict] = []
        self.turn_counter = 0

        # Default system prompt
        if system_prompt is None:
            system_prompt = (
                "You are a helpful AI assistant in a voice conversation. "
                "Keep your responses concise and natural, as they will be "
                "converted to speech. Avoid using special characters or "
                "formatting that doesn't translate well to speech."
            )

        self.conversation_history.append({
            "role": "system",
            "content": system_prompt
        })

    def record_audio(self, duration: float = None) -> str:
        """
        Record audio from microphone

        Args:
            duration: Recording duration in seconds. If None, records until Enter is pressed.

        Returns:
            str: Path to temporary audio file
        """
        print("\n🎤 Recording... ", end='', flush=True)

        if duration:
            print(f"(for {duration} seconds)")
            recording = sd.rec(
                int(duration * SAMPLE_RATE),
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=np.int16,
                device=RECORDING_DEVICE
            )
            sd.wait()
        else:
            print("(Press Enter to stop)")
            recording = []

            def callback(indata, frames, time, status):
                if status:
                    print(f"Status: {status}")
                recording.append(indata.copy())

            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=np.int16,
                callback=callback,
                device=RECORDING_DEVICE
            ):
                input()  # Wait for Enter key

            recording = np.concatenate(recording, axis=0)

        print("✓ Recording complete")

        # Save to temporary WAV file
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix='.wav',
            prefix='user_recording_'
        )
        temp_path = temp_file.name
        temp_file.close()

        with wave.open(temp_path, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(recording.tobytes())

        return temp_path

    def speech_to_text(self, audio_path: str) -> str:
        """
        Convert speech to text using 11Labs STT

        Args:
            audio_path: Path to audio file

        Returns:
            str: Transcribed text
        """
        print("🔄 Transcribing audio...")
        result = transcribe_audio(audio_path)
        text = result.get('text', '').strip()
        print(f"📝 User said: \"{text}\"")
        return text

    def get_llm_response(self, user_text: str) -> str:
        """
        Get response from OpenAI LLM

        Args:
            user_text: User's transcribed text

        Returns:
            str: AI agent's response
        """
        # Add user message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_text
        })

        print("🤖 Generating AI response...")

        # Get completion from OpenAI
        response = openai_client.chat.completions.create(
            model=self.model,
            messages=self.conversation_history,
            temperature=0.7,
            max_tokens=500
        )

        assistant_text = response.choices[0].message.content.strip()

        # Add assistant response to conversation history
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_text
        })

        print(f"💬 Agent says: \"{assistant_text}\"")
        return assistant_text

    def text_to_speech(self, text: str) -> str:
        """
        Convert text to speech using 11Labs TTS

        Args:
            text: Text to convert

        Returns:
            str: Path to generated audio file
        """
        self.turn_counter += 1
        output_path = os.path.join(
            OUTPUT_DIR,
            f"agent_response_{self.turn_counter:03d}.mp3"
        )

        print("🔊 Generating speech...")
        text_to_speech(text, output_path, voice_id=self.voice_id)
        print(f"💾 Audio saved to: {output_path}")

        return output_path

    def process_turn(self, duration: float = None) -> tuple:
        """
        Process one complete conversation turn

        Args:
            duration: Recording duration. If None, user presses Enter to stop.

        Returns:
            tuple: (user_text, agent_text, audio_path)
        """
        print("\n" + "="*70)
        print(f"TURN {self.turn_counter + 1}")
        print("="*70)

        # Step 1: Record user audio
        audio_path = self.record_audio(duration)

        try:
            # Step 2: Transcribe to text
            user_text = self.speech_to_text(audio_path)

            if not user_text:
                print("⚠️  No speech detected. Please try again.")
                return None, None, None

            # Step 3: Get LLM response
            agent_text = self.get_llm_response(user_text)

            # Step 4: Convert response to speech
            agent_audio_path = self.text_to_speech(agent_text)

            return user_text, agent_text, agent_audio_path

        finally:
            # Clean up temporary recording file
            if os.path.exists(audio_path):
                os.unlink(audio_path)

    def run_interactive(self, max_turns: int = None):
        """
        Run interactive voice chat session

        Args:
            max_turns: Maximum number of turns. None = unlimited.
        """
        print("\n" + "🎙️  VOICE CHAT STARTED ".center(70, "="))
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

            # Wait for user to be ready
            print("\n📢 Press Enter when ready to speak (or type 'quit' to exit)...")
            user_input = input()

            if user_input.lower() in ['quit', 'exit', 'q']:
                break

            # Process one conversation turn
            result = self.process_turn(duration=None)

            if result[0] is None:  # No speech detected
                continue

            turn += 1

        print("\n" + "🎙️  VOICE CHAT ENDED ".center(70, "="))
        print(f"\nTotal turns: {turn}")
        print(f"Audio files saved in: {OUTPUT_DIR}/")
        print("\nConversation history:")
        self._print_history()

    def _print_history(self):
        """Print conversation history (excluding system prompt)"""
        print("\n" + "-"*70)
        for msg in self.conversation_history[1:]:  # Skip system prompt
            role = "👤 User" if msg["role"] == "user" else "🤖 Agent"
            print(f"{role}: {msg['content']}")
            print("-"*70)


def test_audio_devices():
    """Test and list available audio devices"""
    print("\n🎧 Available Audio Devices:")
    print("="*70)
    devices = sd.query_devices()

    if isinstance(devices, list):
        for i, device in enumerate(devices):
            print(f"{i}: {device['name']}")
            print(f"   Input channels: {device['max_input_channels']}")
            print(f"   Output channels: {device['max_output_channels']}")
            print(f"   Default sample rate: {device['default_samplerate']}")
            print("-"*70)
    else:
        print(devices)

    print("\nDefault input device:", sd.query_devices(kind='input')['name'])
    print("Default output device:", sd.query_devices(kind='output')['name'])


def main():
    """Main CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Voice chat simulation with STT, LLM, and TTS"
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
    parser.add_argument(
        '--test-devices',
        action='store_true',
        help='List available audio devices and exit'
    )

    args = parser.parse_args()

    # Test devices and exit
    if args.test_devices:
        test_audio_devices()
        return

    # Create and run voice chat
    try:
        chat = VoiceChat(
            model=args.model,
            system_prompt=args.system_prompt,
            voice_id=args.voice
        )
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
