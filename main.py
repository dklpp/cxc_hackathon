#!/usr/bin/env python3
"""
Voice Chatbot - Conversational AI with Real-time Voice Interaction

A local conversational voice chatbot that uses:
- ElevenLabs Speech-to-Text
- Google Gemini LLM
- ElevenLabs Text-to-Speech
- Silero VAD for automatic speech detection
"""

import asyncio
import sys
from voice_chatbot.conversation_controller import ConversationController
from voice_chatbot.config import Config


def print_banner():
    """Print welcome banner"""
    print()
    print("=" * 60)
    print("          Voice Chatbot - Bank Collector Demo")
    print("=" * 60)
    print()
    print("This is an AI voice assistant that will have a conversation")
    print("with you about your bank account debt.")
    print()
    print("Features:")
    print("  • Real-time speech detection (Silero VAD)")
    print("  • Speech-to-Text (ElevenLabs)")
    print("  • Conversation AI (Google Gemini)")
    print("  • Text-to-Speech (ElevenLabs)")
    print()
    print("Controls:")
    print("  • Speak naturally - the system will detect when you're done")
    print("  • Press Ctrl+C to exit")
    print()
    print("=" * 60)
    print()


async def main():
    """Main entry point"""
    try:
        # Print banner
        print_banner()

        # Load configuration
        print("Loading configuration...")
        try:
            config = Config.from_env()
        except ValueError as e:
            print(f"\n❌ Configuration Error: {e}")
            print("\nPlease ensure your .env file contains:")
            print("  - ELEVEN_LABS_API_KEY")
            print("  - GEMINI_API_KEY")
            print("\nTo get API keys:")
            print("  • ElevenLabs: https://elevenlabs.io/")
            print("  • Gemini: https://makersuite.google.com/app/apikey")
            return 1

        # Create controller
        try:
            controller = ConversationController(config)
        except Exception as e:
            print(f"\n❌ Initialization Error: {e}")
            print("\nTroubleshooting:")
            print("  • Check if microphone is connected")
            print("  • Check microphone permissions")
            print("  • Ensure audio drivers are installed")
            return 1

        # Run conversation loop
        try:
            await controller.run()
        except KeyboardInterrupt:
            print("\n\n✓ Shutting down gracefully...")
            controller.stop()

        return 0

    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)
