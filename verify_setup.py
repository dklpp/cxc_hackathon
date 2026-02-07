#!/usr/bin/env python3
"""
Setup verification script for Voice Chatbot
Checks if all dependencies and configuration are correct
"""

import sys
import os


def check_python_version():
    """Check Python version"""
    print("1. Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print(f"   ✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ✗ Python {version.major}.{version.minor}.{version.micro} (needs 3.9+)")
        return False


def check_dependencies():
    """Check if required packages are installed"""
    print("\n2. Checking dependencies...")
    required = [
        'sounddevice',
        'numpy',
        'torch',
        'pydub',
        'aiohttp',
        'google.generativeai',
        'dotenv'
    ]

    missing = []
    for package in required:
        try:
            __import__(package.replace('.', '_') if '.' in package else package)
            print(f"   ✓ {package}")
        except ImportError:
            print(f"   ✗ {package} (missing)")
            missing.append(package)

    if missing:
        print(f"\n   Install missing packages: pip install -r requirements.txt")
        return False
    return True


def check_audio_devices():
    """Check audio devices"""
    print("\n3. Checking audio devices...")
    try:
        import sounddevice as sd
        devices = sd.query_devices()

        # Check for input device
        default_input = sd.default.device[0]
        if default_input is not None:
            input_device = sd.query_devices(default_input, 'input')
            print(f"   ✓ Microphone: {input_device['name']}")
        else:
            print("   ✗ No microphone detected")
            return False

        # Check for output device
        default_output = sd.default.device[1]
        if default_output is not None:
            output_device = sd.query_devices(default_output, 'output')
            print(f"   ✓ Speakers: {output_device['name']}")
        else:
            print("   ✗ No speakers detected")
            return False

        return True

    except Exception as e:
        print(f"   ✗ Error checking audio devices: {e}")
        return False


def check_env_file():
    """Check .env configuration"""
    print("\n4. Checking .env configuration...")

    if not os.path.exists('.env'):
        print("   ✗ .env file not found")
        print("   → Copy .env.example to .env and add your API keys")
        return False

    from dotenv import load_dotenv
    load_dotenv()

    checks = {
        'ELEVEN_LABS_API_KEY': os.getenv('ELEVEN_LABS_API_KEY'),
        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
    }

    all_good = True
    for key, value in checks.items():
        if value and value != f"your_{key.lower()}_here":
            print(f"   ✓ {key} is set")
        else:
            print(f"   ✗ {key} is missing or not configured")
            all_good = False

    if not all_good:
        print("\n   Get API keys:")
        print("   • ElevenLabs: https://elevenlabs.io/")
        print("   • Gemini: https://makersuite.google.com/app/apikey")

    return all_good


def check_vad_model():
    """Check if Silero VAD model can be loaded"""
    print("\n5. Checking Silero VAD model...")
    try:
        import torch
        print("   → Loading VAD model (this may take a moment)...")
        model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=False
        )
        print("   ✓ Silero VAD model loaded successfully")
        return True
    except Exception as e:
        print(f"   ✗ Failed to load VAD model: {e}")
        return False


def main():
    """Run all checks"""
    print("=" * 60)
    print("Voice Chatbot - Setup Verification")
    print("=" * 60)

    checks = [
        check_python_version(),
        check_dependencies(),
        check_audio_devices(),
        check_env_file(),
        check_vad_model()
    ]

    print("\n" + "=" * 60)
    if all(checks):
        print("✓ All checks passed! You're ready to run the chatbot.")
        print("\nRun: python main.py")
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        print("\nSee README.md for setup instructions.")
    print("=" * 60)

    return 0 if all(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
