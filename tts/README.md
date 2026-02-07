# Text-to-Speech (TTS) with Eleven Labs

Convert text to natural-sounding speech using the Eleven Labs Text-to-Speech API.

## Features

- 🗣️ High-quality voice synthesis
- 🎭 Multiple voice options
- 🌍 Multilingual support
- 🎚️ Customizable voice settings
- 📦 Batch processing
- 💾 File and streaming support
- 🔧 CLI and Python module support

## Installation

1. Install required dependencies:
```bash
pip install python-dotenv requests
```

2. Set up your API key in `.env`:
```bash
ELEVEN_LABS_API_KEY=your_api_key_here
```

## Usage

### Command Line

**List available voices:**
```bash
python text_to_speech.py --list-voices
```

**Convert text to speech:**
```bash
python text_to_speech.py "Hello world" output.mp3
```

**Use specific voice:**
```bash
python text_to_speech.py "Hello" output.mp3 21m00Tcm4TlvDq8ikWAM
```

**Convert from text file:**
```bash
python text_to_speech.py --file input.txt output.mp3
```

### As a Python Module

**Simple conversion:**
```python
from text_to_speech import text_to_speech

text_to_speech("Hello world", "output.mp3")
```

**Use specific voice:**
```python
from text_to_speech import text_to_speech

text_to_speech(
    text="Hello world",
    output_file="output.mp3",
    voice_id="21m00Tcm4TlvDq8ikWAM"  # Rachel
)
```

**Custom voice settings:**
```python
from text_to_speech import text_to_speech

text_to_speech(
    text="Hello world",
    output_file="output.mp3",
    voice_id="21m00Tcm4TlvDq8ikWAM",
    voice_settings={
        "stability": 0.5,
        "similarity_boost": 0.75,
        "style": 0.0,
        "use_speaker_boost": True
    }
)
```

**Batch conversion:**
```python
from text_to_speech import batch_text_to_speech

texts = [
    "First sentence",
    "Second sentence",
    "Third sentence"
]

batch_text_to_speech(
    texts=texts,
    output_dir="audio_files/",
    prefix="speech"
)
# Creates: audio_files/speech_001.mp3, speech_002.mp3, etc.
```

**Get audio bytes for streaming:**
```python
from text_to_speech import text_to_speech_stream

audio_bytes = text_to_speech_stream("Hello world")
# Use audio_bytes for streaming or further processing
```

## API Reference

### `text_to_speech(text, output_file, voice_id, model, voice_settings)`

Convert text to speech and save as MP3 file.

**Parameters:**
- `text` (str): Text to convert
- `output_file` (str): Path to save audio file
- `voice_id` (str, optional): Voice ID (default: Rachel)
- `model` (str, optional): Model name (default: "eleven_multilingual_v2")
- `voice_settings` (dict, optional): Voice configuration

**Voice Settings:**
- `stability` (0-1): Lower = more expressive, Higher = more stable
- `similarity_boost` (0-1): How closely to match the voice
- `style` (0-1): Exaggeration of the speaking style
- `use_speaker_boost` (bool): Enhanced voice clarity

### `get_voices()`

Get all available voices from the API.

**Returns:**
- `dict`: Dictionary containing all available voices

### `list_voices()`

Print formatted list of all available voices with details.

### `text_to_speech_stream(text, voice_id, model)`

Get audio bytes for streaming without saving to file.

**Parameters:**
- `text` (str): Text to convert
- `voice_id` (str, optional): Voice ID
- `model` (str, optional): Model name

**Returns:**
- `bytes`: Audio data in MP3 format

### `batch_text_to_speech(texts, output_dir, voice_id, prefix, verbose)`

Convert multiple texts to audio files.

**Parameters:**
- `texts` (list): List of text strings
- `output_dir` (str): Directory to save files
- `voice_id` (str, optional): Voice ID
- `prefix` (str, optional): Filename prefix (default: "audio")
- `verbose` (bool, optional): Show progress (default: True)

**Returns:**
- `list`: List of generated file paths

### `text_file_to_speech(input_file, output_file, voice_id, model)`

Convert text file contents to speech.

**Parameters:**
- `input_file` (str): Path to text file
- `output_file` (str): Path to save audio
- `voice_id` (str, optional): Voice ID
- `model` (str, optional): Model name

## Popular Voices

| Name | Voice ID | Gender | Accent |
|------|----------|--------|--------|
| Rachel | `21m00Tcm4TlvDq8ikWAM` | Female | American |
| Adam | `pNInz6obpgDQGcFmaJgB` | Male | American |
| Bella | `EXAVITQu4vr4xnSDxMaL` | Female | American |
| Antoni | `ErXwobaYiN019PkySvjV` | Male | American |

Run `--list-voices` to see all available voices in your account.

## Examples

### Example 1: Simple Text-to-Speech
```python
from text_to_speech import text_to_speech

text_to_speech(
    "Welcome to our application!",
    "welcome.mp3"
)
```

### Example 2: Multiple Voices
```python
from text_to_speech import text_to_speech

voices = {
    "Rachel": "21m00Tcm4TlvDq8ikWAM",
    "Adam": "pNInz6obpgDQGcFmaJgB"
}

text = "Hello, how are you today?"

for name, voice_id in voices.items():
    text_to_speech(
        text,
        f"greeting_{name.lower()}.mp3",
        voice_id=voice_id
    )
```

### Example 3: Convert Book Chapter
```python
from text_to_speech import text_file_to_speech

text_file_to_speech(
    input_file="chapter1.txt",
    output_file="chapter1_audio.mp3",
    voice_id="21m00Tcm4TlvDq8ikWAM"
)
```

### Example 4: Custom Voice Settings
```python
from text_to_speech import text_to_speech

# More stable, less expressive (good for narration)
text_to_speech(
    "This is a professional narration.",
    "narration.mp3",
    voice_settings={
        "stability": 0.8,
        "similarity_boost": 0.5,
        "style": 0.0,
        "use_speaker_boost": True
    }
)

# More expressive (good for dialogue)
text_to_speech(
    "Wow! That's amazing!",
    "excited.mp3",
    voice_settings={
        "stability": 0.3,
        "similarity_boost": 0.75,
        "style": 0.5,
        "use_speaker_boost": True
    }
)
```

### Example 5: Batch Processing
```python
from text_to_speech import batch_text_to_speech

# Convert dialogue lines
dialogue = [
    "Hello, welcome to the store.",
    "How can I help you today?",
    "We have a special promotion.",
    "Thank you for visiting!"
]

files = batch_text_to_speech(
    texts=dialogue,
    output_dir="store_audio/",
    prefix="line",
    voice_id="21m00Tcm4TlvDq8ikWAM"
)

print(f"Generated {len(files)} audio files")
```

### Example 6: List and Choose Voice
```python
from text_to_speech import get_voices, text_to_speech

# Get all voices
voices_data = get_voices()
voices = voices_data['voices']

# Filter female voices
female_voices = [
    v for v in voices
    if v.get('labels', {}).get('gender') == 'female'
]

# Use the first female voice
if female_voices:
    voice = female_voices[0]
    print(f"Using voice: {voice['name']}")

    text_to_speech(
        "Hello from a female voice",
        "female_voice.mp3",
        voice_id=voice['voice_id']
    )
```

## Voice Settings Guide

### Stability (0.0 - 1.0)
- **Low (0.0-0.3)**: Very expressive, emotional, may have more variation
- **Medium (0.4-0.6)**: Balanced between expression and consistency
- **High (0.7-1.0)**: Stable, consistent, good for long-form content

### Similarity Boost (0.0 - 1.0)
- **Low (0.0-0.3)**: More creative interpretation
- **Medium (0.4-0.6)**: Balanced
- **High (0.7-1.0)**: Closely matches original voice characteristics

### Style (0.0 - 1.0)
- **Low (0.0)**: Neutral delivery
- **High (1.0)**: Exaggerated speaking style

### Speaker Boost
- **True**: Enhanced clarity (recommended for most cases)
- **False**: Natural voice without enhancement

## Troubleshooting

**Error: "ELEVEN_LABS_API_KEY not found in .env file"**
- Ensure `.env` file exists in project root
- Verify the key is named exactly `ELEVEN_LABS_API_KEY`

**Error: "API request failed"**
- Check API key validity
- Verify sufficient API credits
- Check internet connection
- Verify voice ID is correct

**Audio quality issues:**
- Try adjusting voice settings
- Use `use_speaker_boost: True`
- Increase `similarity_boost` value

**Voice not found:**
- Run `--list-voices` to see available voices
- Some voices may be account-specific

## API Documentation

For more details:
- [Eleven Labs TTS Documentation](https://elevenlabs.io/docs/api-reference/text-to-speech)
- [Voice Lab](https://elevenlabs.io/voice-lab) - Create custom voices

## License

This project uses the Eleven Labs API. Please refer to their terms of service.
