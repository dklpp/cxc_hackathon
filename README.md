# Voice Chatbot - Conversational AI System

A real-time conversational voice chatbot that simulates phone call interactions using:
- **ElevenLabs Speech-to-Text** - Audio transcription
- **Google Gemini LLM** - Conversational intelligence
- **ElevenLabs Text-to-Speech** - Natural voice synthesis
- **Silero VAD** - Automatic speech detection

## Features

- ✅ Real-time microphone capture
- ✅ Automatic voice activity detection
- ✅ Continuous conversation loop
- ✅ Conversation history management
- ✅ Natural voice synthesis
- ✅ Low-latency processing
- ✅ Modular architecture

## Demo Persona

The current implementation features a **bank collector** persona that:
- Informs users about their debt
- Asks professionally to arrange payment
- Maintains conversation context

## Quick Start

### 1. Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

### 2. Configure API Keys

Create or update your `.env` file:

```bash
ELEVEN_LABS_API_KEY=your_elevenlabs_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
VOICE_ID=21m00Tcm4TlvDq8ikWAM
```

**Get API Keys:**
- **ElevenLabs**: https://elevenlabs.io/ (Sign up for free tier)
- **Gemini**: https://makersuite.google.com/app/apikey (Free with Google account)

### 3. Test Audio Setup

```bash
# Check if microphone and speakers are detected
python -c "import sounddevice as sd; print(sd.query_devices())"
```

### 4. Run the Chatbot

```bash
python main.py
```

## Usage

1. **Start the chatbot**: Run `python main.py`
2. **Speak naturally**: The system automatically detects when you start and stop speaking
3. **Wait for response**: The AI will respond verbally
4. **Continue conversation**: Keep talking - the system maintains context
5. **Exit**: Press `Ctrl+C` to exit gracefully

## Architecture

```
Microphone → Audio Input (VAD) → STT → LLM (Gemini) → TTS → Audio Output
                ↑                                                      ↓
                └────────────── Conversation Loop ──────────────────┘
```

### Module Structure

```
voice_chatbot/
├── __init__.py                 # Package initialization
├── config.py                   # Configuration management
├── audio_input.py              # Microphone capture with Silero VAD
├── stt.py                      # Speech-to-Text (ElevenLabs)
├── llm.py                      # LLM integration (Gemini)
├── tts.py                      # Text-to-Speech (ElevenLabs)
├── audio_output.py             # Audio playback
└── conversation_controller.py  # Main orchestration loop
```

## System Requirements

- **Python**: 3.9+
- **OS**: Linux, macOS, or Windows
- **Hardware**:
  - Microphone (built-in or external)
  - Speakers or headphones
  - 2GB RAM minimum
  - Internet connection (for APIs)

## Configuration

### Voice Settings

Customize the voice in [voice_chatbot/config.py](voice_chatbot/config.py):

```python
voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice (default)
```

**Available voices**: Use ElevenLabs dashboard to explore voices

### System Prompt

Customize the chatbot personality in [voice_chatbot/config.py](voice_chatbot/config.py):

```python
system_prompt: str = "You are a helpful assistant..."
```

### VAD Sensitivity

Adjust speech detection in [voice_chatbot/audio_input.py](voice_chatbot/audio_input.py):

```python
self.speech_threshold = 0.5  # Higher = more strict (less sensitive)
self.silence_threshold = 5    # Chunks of silence to end speech
```

## Troubleshooting

### Microphone Not Detected

```bash
# List audio devices
python -c "import sounddevice as sd; print(sd.query_devices())"

# Set default device
export SD_DEFAULT_DEVICE=<device_id>
```

### API Errors

- Check API keys in `.env` file
- Verify internet connection
- Check API rate limits:
  - ElevenLabs: 10,000 characters/month (free tier)
  - Gemini: 60 requests/minute (free tier)

### Audio Quality Issues

- Ensure quiet environment
- Use external microphone for better quality
- Adjust VAD sensitivity if speech is cut off

### High Latency

- Use faster internet connection
- Consider using lower-quality voice models
- Reduce `max_output_tokens` in LLM config

## Development

### Running Tests

```bash
# Test audio input
python -m voice_chatbot.audio_input

# Test STT with existing audio file
python -c "
from voice_chatbot.stt import SpeechToText
from voice_chatbot.config import Config
import asyncio

async def test():
    config = Config.from_env()
    stt = SpeechToText(config.elevenlabs_api_key)
    result = stt.transcribe_audio('output.mp3')
    print(result)

asyncio.run(test())
"
```

### Project Structure

```
cxc_hackathon/
├── voice_chatbot/          # Main package
├── tests/                  # Test files
│   └── outbound_calling/   # Twilio integration tests
├── main.py                 # CLI entry point
├── requirements.txt        # Dependencies
├── .env                    # Configuration (not in git)
├── .env.example            # Configuration template
└── README.md              # This file
```

## Future Enhancements

- [ ] WebSocket streaming for lower latency
- [ ] Voice interruption support
- [ ] Custom wake word activation
- [ ] Web UI with waveform visualization
- [ ] Multi-language support
- [ ] Conversation transcript export
- [ ] Voice cloning capabilities
- [ ] Integration with CRM systems

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Credits

Built with:
- [ElevenLabs](https://elevenlabs.io/) - Voice AI
- [Google Gemini](https://ai.google.dev/) - LLM
- [Silero VAD](https://github.com/snakers4/silero-vad) - Voice Activity Detection
- [sounddevice](https://python-sounddevice.readthedocs.io/) - Audio I/O