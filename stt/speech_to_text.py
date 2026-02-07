
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


def transcribe_audio(
    audio_file_path: str,
    model: str = "scribe_v2"
) -> Dict:
    """
    Transcribe audio file using Eleven Labs Speech-to-Text API

    Args:
        audio_file_path: Path to the audio file to transcribe
        model: Model to use for transcription (default: scribe_v2)

    Returns:
        dict: Transcription result containing text and metadata

    Raises:
        FileNotFoundError: If audio file doesn't exist
        Exception: If API request fails
    """
    url = "https://api.elevenlabs.io/v1/speech-to-text"

    headers = {
        "xi-api-key": ELEVEN_LABS_API_KEY
    }

    # Check if file exists
    if not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

    # Open and send the audio file
    with open(audio_file_path, 'rb') as audio_file:
        files = {
            'file': (os.path.basename(audio_file_path), audio_file, 'audio/mpeg')
        }

        data = {
            'model_id': model
        }

        response = requests.post(url, headers=headers, files=files, data=data)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(
            f"API request failed with status {response.status_code}: {response.text}"
        )


def transcribe_with_timestamps(audio_file_path: str) -> Dict:
    """
    Transcribe audio with word-level timestamps

    Args:
        audio_file_path: Path to the audio file

    Returns:
        dict: Transcription with timestamps

    Raises:
        FileNotFoundError: If audio file doesn't exist
        Exception: If API request fails
    """
    url = "https://api.elevenlabs.io/v1/speech-to-text"

    headers = {
        "xi-api-key": ELEVEN_LABS_API_KEY
    }

    if not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

    with open(audio_file_path, 'rb') as audio_file:
        files = {
            'file': (os.path.basename(audio_file_path), audio_file, 'audio/mpeg')
        }

        data = {
            'model_id': 'scribe_v2',
            'timestamp_granularities': 'word'
        }

        response = requests.post(url, headers=headers, files=files, data=data)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API request failed: {response.text}")


def batch_transcribe(audio_files: List[str], verbose: bool = True) -> Dict[str, Dict]:
    """
    Transcribe multiple audio files

    Args:
        audio_files: List of audio file paths
        verbose: Print progress messages

    Returns:
        dict: Dictionary mapping file paths to transcription results
    """
    results = {}

    for i, audio_file in enumerate(audio_files, 1):
        try:
            if verbose:
                print(f"[{i}/{len(audio_files)}] Transcribing: {audio_file}")

            result = transcribe_audio(audio_file)
            results[audio_file] = result

            if verbose:
                text_preview = result.get('text', '')[:100]
                print(f"✓ Success: {text_preview}{'...' if len(result.get('text', '')) > 100 else ''}")

        except Exception as e:
            if verbose:
                print(f"✗ Error transcribing {audio_file}: {e}")
            results[audio_file] = {"error": str(e)}

    return results


def save_transcription(result: Dict, output_file: str) -> None:
    """
    Save transcription result to a text file

    Args:
        result: Transcription result dictionary
        output_file: Path to output file
    """
    text = result.get('text', '')

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(text)

    print(f"Transcription saved to: {output_file}")


def main():
    """
    Main function for CLI usage
    """
    if len(sys.argv) < 2:
        print("Usage: python speech_to_text.py <audio_file> [output_file]")
        print("\nExample:")
        print("  python speech_to_text.py recording.mp3")
        print("  python speech_to_text.py recording.mp3 transcription.txt")
        sys.exit(1)

    audio_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        print(f"Transcribing: {audio_file}")
        result = transcribe_audio(audio_file)

        text = result.get('text', '')
        print("\n" + "="*60)
        print("TRANSCRIPTION:")
        print("="*60)
        print(text)
        print("="*60)

        # Save to file if specified
        if output_file:
            save_transcription(result, output_file)

        # Print metadata if available
        if 'metadata' in result:
            print(f"\nMetadata: {result['metadata']}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
