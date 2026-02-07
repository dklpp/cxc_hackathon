"""
Conversation controller - orchestrates the voice chatbot conversation loop
"""

import asyncio
from .audio_input import MicrophoneRecorder
from .stt import SpeechToText
from .llm import ConversationLLM
from .tts import TextToSpeech
from .audio_output import AudioPlayer
from .config import Config


class ConversationController:
    """Main conversation orchestration controller"""

    def __init__(self, config: Config):
        """
        Initialize conversation controller

        Args:
            config: Configuration object
        """
        self.config = config

        # Initialize all components
        print("Initializing components...")

        self.mic = MicrophoneRecorder(sample_rate=config.sample_rate)
        self.stt = SpeechToText(config.elevenlabs_api_key)
        self.llm = ConversationLLM(
            config.gemini_api_key,
            system_prompt=config.system_prompt
        )
        self.tts = TextToSpeech(
            config.elevenlabs_api_key,
            voice_id=config.voice_id
        )
        self.player = AudioPlayer()

        self.is_running = False
        self.retry_count = 0
        self.max_retries = 3

        print("All components initialized successfully")

    async def run(self):
        """Main conversation loop"""
        print("\n" + "=" * 60)
        print("Starting voice chatbot conversation loop...")
        print("=" * 60)

        # Start microphone
        self.mic.start()
        self.is_running = True

        print("\n[Status: LISTENING 🎤]")
        print("Speak to start the conversation...")
        print("Press Ctrl+C to exit\n")

        while self.is_running:
            try:
                # Wait for speech segment from microphone
                audio_segment = await self.mic.get_speech_segment()

                if audio_segment is None:
                    # No speech detected yet, wait a bit
                    await asyncio.sleep(0.1)
                    continue

                print("\n[Status: PROCESSING ⚙️]")

                # Transcribe speech to text
                try:
                    user_text = await self.stt.transcribe_audio_chunk(
                        audio_segment,
                        self.config.sample_rate
                    )
                except Exception as e:
                    print(f"STT error: {e}")
                    print("\n[Status: LISTENING 🎤]")
                    continue

                if not user_text.strip():
                    print("(No speech detected)")
                    print("\n[Status: LISTENING 🎤]")
                    continue

                print(f"\n👤 User: {user_text}")

                # Get LLM response
                try:
                    assistant_text = await self.llm.get_response(user_text)
                except Exception as e:
                    print(f"LLM error: {e}")
                    print("\n[Status: LISTENING 🎤]")
                    continue

                print(f"🤖 Assistant: {assistant_text}")

                # Convert response to speech
                try:
                    print("\n[Status: SPEAKING 🔊]")
                    audio_bytes = await self.tts.synthesize(assistant_text)
                except Exception as e:
                    print(f"TTS error: {e}")
                    print("\n[Status: LISTENING 🎤]")
                    continue

                # Play audio response
                try:
                    self.player.play_mp3(audio_bytes)
                except Exception as e:
                    print(f"Playback error: {e}")

                # Reset retry count on success
                self.retry_count = 0

                # Ready for next input
                print("\n[Status: LISTENING 🎤]")

            except KeyboardInterrupt:
                print("\n\nShutting down...")
                self.is_running = False
                break

            except Exception as e:
                self.retry_count += 1
                print(f"\nError in conversation loop: {e}")

                if self.retry_count >= self.max_retries:
                    print(f"\nToo many errors ({self.max_retries}). Exiting...")
                    self.is_running = False
                    break

                print(f"Retrying... ({self.retry_count}/{self.max_retries})")
                await asyncio.sleep(1)

        # Cleanup
        self.mic.stop()
        print("\n" + "=" * 60)
        print("Conversation ended")
        print("=" * 60)

    def stop(self):
        """Stop the conversation loop"""
        self.is_running = False
        self.mic.stop()

    def reset(self):
        """Reset conversation history"""
        self.llm.reset_conversation()
        print("Conversation history reset")

    def get_stats(self):
        """Get conversation statistics"""
        return {
            "turns": self.llm.get_turn_count(),
            "history": self.llm.get_history()
        }
