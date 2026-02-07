# Speech-to-Text (STT) with Eleven Labs

Convert audio files to text using the Eleven Labs Speech-to-Text API.

## Features

- 🎤 Convert audio files to text
- ⏱️ Word-level timestamps
- 🌍 Multilingual support
- 📦 Batch processing
- 💾 Save transcriptions to files
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

**Basic transcription:**
```bash
python speech_to_text.py recording.mp3
```

**Save to file:**
```bash
python speech_to_text.py recording.mp3 transcription.txt
```

### As a Python Module

**Simple transcription:**
```python
from speech_to_text import transcribe_audio

result = transcribe_audio("recording.mp3")
print(result['text'])
```

**With timestamps:**
```python
from speech_to_text import transcribe_with_timestamps

result = transcribe_with_timestamps("recording.mp3")
print(result)
```

**Batch processing:**
```python
from speech_to_text import batch_transcribe

audio_files = ["file1.mp3", "file2.mp3", "file3.mp3"]
results = batch_transcribe(audio_files)

for file_path, result in results.items():
    if 'error' not in result:
        print(f"{file_path}: {result['text']}")
```

**Save transcription:**
```python
from speech_to_text import transcribe_audio, save_transcription

result = transcribe_audio("recording.mp3")
save_transcription(result, "output.txt")
```

## API Reference

### `transcribe_audio(audio_file_path, model="eleven_multilingual_v2")`

Transcribe an audio file to text.

**Parameters:**
- `audio_file_path` (str): Path to the audio file
- `model` (str): Model to use (default: "eleven_multilingual_v2")

**Returns:**
- `dict`: Transcription result with 'text' and metadata

**Raises:**
- `FileNotFoundError`: If audio file doesn't exist
- `Exception`: If API request fails

### `transcribe_with_timestamps(audio_file_path)`

Transcribe audio with word-level timestamps.

**Parameters:**
- `audio_file_path` (str): Path to the audio file

**Returns:**
- `dict`: Transcription with timestamps

### `batch_transcribe(audio_files, verbose=True)`

Transcribe multiple audio files.

**Parameters:**
- `audio_files` (list): List of audio file paths
- `verbose` (bool): Print progress messages

**Returns:**
- `dict`: Dictionary mapping file paths to results

### `save_transcription(result, output_file)`

Save transcription to a text file.

**Parameters:**
- `result` (dict): Transcription result
- `output_file` (str): Path to output file

## Supported Audio Formats

- MP3
- WAV
- FLAC
- OGG
- M4A
- And more...

## Models

- `eleven_multilingual_v2` (default): Supports multiple languages with high accuracy
- `eleven_english_v1`: Optimized for English

## Examples

### Example 1: Quick Transcription
```python
from speech_to_text import transcribe_audio

result = transcribe_audio("interview.mp3")
print(result['text'])
```

### Example 2: Batch Process with Error Handling
```python
from speech_to_text import batch_transcribe
import os

audio_dir = "recordings/"
audio_files = [
    os.path.join(audio_dir, f)
    for f in os.listdir(audio_dir)
    if f.endswith('.mp3')
]

results = batch_transcribe(audio_files)

# Save successful transcriptions
for file_path, result in results.items():
    if 'error' not in result:
        output_file = file_path.replace('.mp3', '.txt')
        with open(output_file, 'w') as f:
            f.write(result['text'])
```

### Example 3: Transcription with Timestamps
```python
from speech_to_text import transcribe_with_timestamps
import json

result = transcribe_with_timestamps("meeting.mp3")

# Save as JSON with timestamps
with open("meeting_transcript.json", 'w') as f:
    json.dump(result, f, indent=2)
```

## Troubleshooting

**Error: "ELEVEN_LABS_API_KEY not found in .env file"**
- Make sure you have a `.env` file in the project root
- Check that the key is named exactly `ELEVEN_LABS_API_KEY`

**Error: "Audio file not found"**
- Verify the file path is correct
- Use absolute paths or ensure you're in the right directory

**Error: "API request failed"**
- Check your API key is valid
- Verify you have sufficient API credits
- Check your internet connection

## API Documentation

For more details on the Eleven Labs API:
- [Eleven Labs STT Documentation](https://elevenlabs.io/docs/api-reference/text-to-speech)

## License

This project uses the Eleven Labs API. Please refer to their terms of service.
