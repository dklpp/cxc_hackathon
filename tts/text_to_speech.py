import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests
from typing import Optional, List, Dict

# Load environment variables from .env file
load_dotenv()

# Get API key
ELEVEN_LABS_API_KEY = os.getenv('ELEVEN_LABS_API_KEY')

if not ELEVEN_LABS_API_KEY:
    raise ValueError("ELEVEN_LABS_API_KEY not found in .env file")

# Default voice ID (Rachel - a popular voice)
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"


def get_voices() -> Dict:
    """
    Get available voices from Eleven Labs API

    Returns:
        dict: Dictionary containing available voices

    Raises:
        Exception: If API request fails
    """
    url = "https://api.elevenlabs.io/v1/voices"

    headers = {
        "xi-api-key": ELEVEN_LABS_API_KEY
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(
            f"Failed to get voices: {response.status_code} - {response.text}"
        )


def list_voices() -> None:
    """
    List all available voices with their IDs and names
    """
    try:
        voices_data = get_voices()
        voices = voices_data.get('voices', [])

        print(f"\nAvailable Voices ({len(voices)}):")
        print("=" * 60)

        for voice in voices:
            voice_id = voice.get('voice_id')
            name = voice.get('name')
            category = voice.get('category', 'N/A')
            labels = voice.get('labels', {})

            print(f"Name: {name}")
            print(f"ID: {voice_id}")
            print(f"Category: {category}")
            if labels:
                print(f"Labels: {labels}")
            print("-" * 60)

    except Exception as e:
        print(f"Error listing voices: {e}", file=sys.stderr)


def text_to_speech(
    text: str,
    output_file: str,
    voice_id: str = DEFAULT_VOICE_ID,
    model: str = "eleven_multilingual_v2",
    voice_settings: Optional[Dict] = None
) -> None:
    """
    Convert text to speech and save to file

    Args:
        text: Text to convert to speech
        output_file: Path to save the audio file (e.g., output.mp3)
        voice_id: Voice ID to use (default: Rachel)
        model: Model to use (default: eleven_multilingual_v2)
        voice_settings: Optional voice settings (stability, similarity_boost, etc.)

    Raises:
        Exception: If API request fails
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVEN_LABS_API_KEY
    }

    # Default voice settings if not provided
    if voice_settings is None:
        voice_settings = {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }

    data = {
        "text": text,
        "model_id": model,
        "voice_settings": voice_settings
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        # Save audio to file
        with open(output_file, 'wb') as f:
            f.write(response.content)
        print(f"Audio saved to: {output_file}")
    else:
        raise Exception(
            f"API request failed with status {response.status_code}: {response.text}"
        )


def text_to_speech_pcm(
    text: str,
    voice_id: str = DEFAULT_VOICE_ID,
    model: str = "eleven_multilingual_v2",
    sample_rate: int = 16000,
    voice_settings: Optional[Dict] = None
) -> bytes:
    """
    Convert text to speech and return raw PCM audio bytes (no MP3/ffmpeg needed).

    Args:
        text: Text to convert to speech
        voice_id: Voice ID to use
        model: Model to use
        sample_rate: Output sample rate (default: 16000)
        voice_settings: Optional voice settings

    Returns:
        bytes: Raw PCM audio data (signed 16-bit little-endian)
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "Accept": "audio/pcm",
        "Content-Type": "application/json",
        "xi-api-key": ELEVEN_LABS_API_KEY
    }

    if voice_settings is None:
        voice_settings = {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }

    data = {
        "text": text,
        "model_id": model,
        "voice_settings": voice_settings,
        "output_format": f"pcm_{sample_rate}"
    }

    response = requests.post(
        url,
        json=data,
        headers=headers,
        params={"output_format": f"pcm_{sample_rate}"}
    )

    if response.status_code == 200:
        return response.content
    else:
        raise Exception(
            f"API request failed with status {response.status_code}: {response.text}"
        )


def text_to_speech_stream(
    text: str,
    voice_id: str = DEFAULT_VOICE_ID,
    model: str = "eleven_multilingual_v2"
) -> bytes:
    """
    Convert text to speech and return audio bytes (for streaming)

    Args:
        text: Text to convert to speech
        voice_id: Voice ID to use
        model: Model to use

    Returns:
        bytes: Audio data in MP3 format

    Raises:
        Exception: If API request fails
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVEN_LABS_API_KEY
    }

    data = {
        "text": text,
        "model_id": model,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    response = requests.post(url, json=data, headers=headers, stream=True)

    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"API request failed: {response.text}")


def batch_text_to_speech(
    texts: List[str],
    output_dir: str,
    voice_id: str = DEFAULT_VOICE_ID,
    prefix: str = "audio",
    verbose: bool = True
) -> List[str]:
    """
    Convert multiple texts to speech files

    Args:
        texts: List of text strings to convert
        output_dir: Directory to save audio files
        voice_id: Voice ID to use
        prefix: Prefix for output files (default: "audio")
        verbose: Print progress messages

    Returns:
        list: List of generated file paths
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    output_files = []

    for i, text in enumerate(texts, 1):
        try:
            output_file = os.path.join(output_dir, f"{prefix}_{i:03d}.mp3")

            if verbose:
                text_preview = text[:50] + "..." if len(text) > 50 else text
                print(f"[{i}/{len(texts)}] Converting: {text_preview}")

            text_to_speech(text, output_file, voice_id)
            output_files.append(output_file)

            if verbose:
                print(f"✓ Saved: {output_file}")

        except Exception as e:
            if verbose:
                print(f"✗ Error converting text {i}: {e}")

    return output_files


def text_file_to_speech(
    input_file: str,
    output_file: str,
    voice_id: str = DEFAULT_VOICE_ID,
    model: str = "eleven_multilingual_v2"
) -> None:
    """
    Read text from file and convert to speech

    Args:
        input_file: Path to text file
        output_file: Path to save audio file
        voice_id: Voice ID to use
        model: Model to use

    Raises:
        FileNotFoundError: If input file doesn't exist
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    text_to_speech(text, output_file, voice_id, model)


def main():
    """
    Main function for CLI usage
    """
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python text_to_speech.py <text> [output_file] [voice_id]")
        print("  python text_to_speech.py --list-voices")
        print("  python text_to_speech.py --file <input.txt> <output.mp3> [voice_id]")
        print("\nExamples:")
        print('  python text_to_speech.py "Hello world" output.mp3')
        print('  python text_to_speech.py "Hello" output.mp3 21m00Tcm4TlvDq8ikWAM')
        print("  python text_to_speech.py --list-voices")
        print("  python text_to_speech.py --file input.txt output.mp3")
        sys.exit(1)

    # List voices
    if sys.argv[1] == "--list-voices":
        list_voices()
        return

    # Convert from file
    if sys.argv[1] == "--file":
        if len(sys.argv) < 4:
            print("Error: --file requires input and output file paths")
            sys.exit(1)

        input_file = sys.argv[2]
        output_file = sys.argv[3]
        voice_id = sys.argv[4] if len(sys.argv) > 4 else DEFAULT_VOICE_ID

        try:
            print(f"Reading text from: {input_file}")
            text_file_to_speech(input_file, output_file, voice_id)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # Convert direct text
    text = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "output.mp3"
    voice_id = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_VOICE_ID

    try:
        print(f"Converting text to speech...")
        print(f"Text: {text}")
        print(f"Voice ID: {voice_id}")

        text_to_speech(text, output_file, voice_id)

        print(f"\n✓ Success! Audio saved to: {output_file}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
