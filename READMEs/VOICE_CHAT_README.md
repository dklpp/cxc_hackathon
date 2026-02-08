# Voice Chat Simulation

A voice-based chat system that simulates a conversation between a user and an AI agent using Speech-to-Text (STT), Large Language Model (LLM), and Text-to-Speech (TTS).

## Architecture

```
User speaks → [Microphone] → STT (11Labs) → Text
                                              ↓
                                         LLM (OpenAI GPT)
                                              ↓
                                         Response Text
                                              ↓
                              TTS (11Labs) → Audio File → Saved
```

## Features

- **Live microphone recording** - Record user voice input in real-time
- **Speech-to-Text** - Convert audio to text using 11Labs API
- **LLM Agent** - Generate intelligent responses using OpenAI GPT
- **Text-to-Speech** - Convert agent responses to natural speech
- **Conversation history** - Maintain context throughout the chat
- **Audio file output** - Save all agent responses as MP3 files

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your `.env` file with API keys:
```bash
cp .env.example .env
# Edit .env and add your API keys:
# - OPENAI_API_KEY
# - ELEVEN_LABS_API_KEY
```

## Usage

### Basic Usage

Run an interactive voice chat session:

```bash
python voice_chat.py
```

This will:
1. Wait for you to press Enter to start recording
2. Record your voice (press Enter again to stop)
3. Transcribe your speech to text
4. Generate an AI response
5. Convert the response to speech and save it
6. Repeat for multiple turns

### Command Line Options

```bash
# Use a specific OpenAI model
python voice_chat.py --model gpt-4

# Use a different voice (see 11Labs API for voice IDs)
python voice_chat.py --voice 21m00Tcm4TlvDq8ikWAM

# Limit to a specific number of turns
python voice_chat.py --turns 3

# Custom system prompt
python voice_chat.py --system-prompt "You are a helpful coding assistant"

# Test audio devices
python voice_chat.py --test-devices

# Combine options
python voice_chat.py --model gpt-4o --turns 5 --voice 21m00Tcm4TlvDq8ikWAM
```

### Example Session

```
🎙️  VOICE CHAT STARTED ================================================

Instructions:
  - Press Enter when ready to speak
  - Speak your message
  - Press Enter again to stop recording
  - Type 'quit' or 'exit' at any prompt to end the session

======================================================================

📢 Press Enter when ready to speak (or type 'quit' to exit)...
[Press Enter]

======================================================================
TURN 1
======================================================================

🎤 Recording... (Press Enter to stop)
[Speak your message]
[Press Enter]
✓ Recording complete
🔄 Transcribing audio...
📝 User said: "Hello, how are you today?"
🤖 Generating AI response...
💬 Agent says: "I'm doing well, thank you for asking! How can I help you today?"
🔊 Generating speech...
💾 Audio saved to: chat_outputs/agent_response_001.mp3

📢 Press Enter when ready to speak (or type 'quit' to exit)...
```

### Output Files

All agent audio responses are saved in the `chat_outputs/` directory with sequential numbering:
- `agent_response_001.mp3`
- `agent_response_002.mp3`
- `agent_response_003.mp3`
- etc.

You can play these files with any audio player to hear the agent's responses.

## Configuration

### Environment Variables

Required in `.env`:
- `OPENAI_API_KEY` - Your OpenAI API key
- `ELEVEN_LABS_API_KEY` - Your 11Labs API key

### Audio Settings

In `voice_chat.py`, you can modify:
- `SAMPLE_RATE` - Recording sample rate (default: 16000 Hz)
- `CHANNELS` - Audio channels (default: 1 for mono)
- `RECORDING_DEVICE` - Specific device ID (default: None for system default)

### OpenAI Models

Supported models (via `--model` flag):
- `gpt-4o` (default) - Latest GPT-4 Optimized
- `gpt-4` - GPT-4
- `gpt-4-turbo` - GPT-4 Turbo
- `gpt-3.5-turbo` - GPT-3.5 Turbo

### 11Labs Voices

Default voice: Rachel (`21m00Tcm4TlvDq8ikWAM`)

To list available voices:
```bash
python tts/text_to_speech.py --list-voices
```

To use a different voice:
```bash
python voice_chat.py --voice YOUR_VOICE_ID
```

## Programmatic Usage

You can also use the `VoiceChat` class in your own code:

```python
from voice_chat import VoiceChat

# Create a chat instance
chat = VoiceChat(
    model="gpt-4o",
    system_prompt="You are a friendly assistant",
    voice_id="21m00Tcm4TlvDq8ikWAM"
)

# Run interactive session
chat.run_interactive(max_turns=5)

# Or process individual turns
user_text, agent_text, audio_path = chat.process_turn()
```

## Troubleshooting

### Audio Device Issues

If you're having trouble with audio recording:

1. List available devices:
```bash
python voice_chat.py --test-devices
```

2. Check your system's default input device
3. Ensure your microphone permissions are enabled
4. Try specifying a specific device in `voice_chat.py` by setting `RECORDING_DEVICE`

### API Errors

- **OpenAI API errors**: Check your API key and billing status
- **11Labs API errors**: Verify your API key and check your character quota
- **Rate limiting**: Add delays between requests if hitting rate limits

### No Speech Detected

If STT returns empty text:
- Speak louder and closer to the microphone
- Check that your microphone is working
- Increase recording duration
- Reduce background noise

## Dependencies

- `elevenlabs` - 11Labs API client
- `openai` - OpenAI API client
- `sounddevice` - Audio recording
- `numpy` - Audio data processing
- `python-dotenv` - Environment variable management
- `requests` - HTTP requests

## License

MIT License - see LICENSE file for details.
