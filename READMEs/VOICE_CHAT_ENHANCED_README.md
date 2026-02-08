# Voice Chat Enhanced - Automatic Speech Detection & Mobile Call Integration

Complete implementation of automatic speech detection and Twilio phone call integration for the voice chat system.

## 🎯 What's New

### ✅ Automatic Speech Detection (VAD)
- **No more manual Enter key presses** - System automatically detects when you stop speaking
- **Multiple VAD backends**: Silero (ML-based), WebRTC (lightweight), Energy-based (simple)
- **Configurable sensitivity**: Adjust thresholds for different environments

### ✅ Mobile Phone Call Integration
- **Twilio Media Streams**: Real-time bidirectional audio streaming
- **WebSocket server**: Handles incoming and outgoing calls
- **Automatic audio processing**: G.711 μ-law codec conversion for telephony

### ✅ Backward Compatible
- Original `voice_chat.py` remains unchanged
- Enhanced version supports both VAD and manual modes
- Gradual migration path

## 📁 Project Structure

```
cxc_hackathon/
├── vad/
│   ├── __init__.py
│   └── voice_activity_detector.py        # VAD with Silero/WebRTC/Energy
├── audio/
│   ├── __init__.py
│   └── audio_processor.py                 # Audio format conversion utilities
├── twilio/
│   ├── __init__.py
│   ├── twilio_voice_server.py             # WebSocket server for calls
│   ├── twilio_server_simple.py            # TwiML configuration server
│   └── outbound_call.py                   # Outbound call manager
├── stt/
│   └── speech_to_text.py                  # 11Labs STT (existing)
├── tts/
│   └── text_to_speech.py                  # 11Labs TTS (existing)
├── voice_chat.py                          # Original (unchanged)
├── voice_chat_enhanced.py                 # Enhanced with VAD
├── requirements.txt                        # Updated dependencies
└── .env.example                           # Updated configuration
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Activate virtual environment
source .venv/bin/activate

# Install new dependencies
pip install -r requirements.txt
```

**Note**: First run will download the Silero VAD model (~5MB) from torch.hub.

### 2. Configure Environment

```bash
# Copy example env file if you haven't already
cp .env.example .env

# Edit .env and add your API keys:
# - OPENAI_API_KEY
# - ELEVEN_LABS_API_KEY
# - TWILIO_ACCOUNT_SID (for phone calls)
# - TWILIO_AUTH_TOKEN (for phone calls)
# - TWILIO_PHONE_NUMBER (for phone calls)
```

### 3. Test Local VAD (No Twilio Required)

```bash
# Test with automatic VAD (recommended)
python voice_chat_enhanced.py --use-vad --vad-method silero

# Test with manual mode (original behavior)
python voice_chat_enhanced.py --no-vad

# Test different VAD methods
python voice_chat_enhanced.py --vad-method webrtc
python voice_chat_enhanced.py --vad-method energy
```

### 4. Test Twilio Integration (Requires Twilio Account)

**Step 1: Start WebSocket Server**
```bash
python twilio/twilio_voice_server.py
```

**Step 2: Expose Server (in new terminal)**
```bash
# Using Cloudflare Tunnel (recommended)
cloudflared tunnel --url http://localhost:5001

# Or using ngrok
ngrok http 5001
```

**Step 3: Start TwiML Server (in new terminal)**
```bash
# Set your public WebSocket URL
export WEBSOCKET_URL="xxx.trycloudflare.com"  # From step 2

python twilio/twilio_server_simple.py
```

**Step 4: Configure Twilio Phone Number**
1. Go to Twilio Console → Phone Numbers
2. Select your phone number
3. Under "Voice Configuration" → "A Call Comes In"
4. Set webhook URL to: `https://YOUR_TUNNEL_URL/voice`
5. Save

**Step 5: Make a Test Call**
Call your Twilio number and have a conversation!

## 📖 Usage Examples

### Local Testing with VAD

```bash
# Basic automatic mode
python voice_chat_enhanced.py

# With custom settings
python voice_chat_enhanced.py \
  --model gpt-4o \
  --vad-method silero \
  --vad-threshold 0.5 \
  --vad-silence-ms 700 \
  --turns 5

# Manual mode (like original voice_chat.py)
python voice_chat_enhanced.py --no-vad
```

### Twilio WebSocket Server

```bash
# Basic server
python twilio/twilio_voice_server.py

# With custom settings
python twilio/twilio_voice_server.py \
  --model gpt-4o \
  --voice 21m00Tcm4TlvDq8ikWAM \
  --vad-method silero \
  --vad-threshold 0.5 \
  --system-prompt "You are a helpful assistant"
```

### TwiML Configuration Server

```bash
# Basic server
python twilio/twilio_server_simple.py

# Custom port and WebSocket URL
python twilio/twilio_server_simple.py \
  --port 5000 \
  --websocket-url wss://your-domain.com/media-stream
```

### Outbound Calls

```bash
# Make a call
python twilio/outbound_call.py call \
  --to +1234567890 \
  --webhook https://your-domain.com/voice

# Check call status
python twilio/outbound_call.py status CALL_SID

# Hang up a call
python twilio/outbound_call.py hangup CALL_SID

# List active calls
python twilio/outbound_call.py list
```

## 🎛️ Configuration Options

### VAD Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `--vad-method` | `silero` | VAD method: `silero`, `webrtc`, or `energy` |
| `--vad-threshold` | `0.5` | Detection sensitivity (0.0-1.0) |
| `--vad-silence-ms` | `500` | Silence duration to end speech (ms) |

**Recommendations**:
- **Quiet environments**: Use `silero` with threshold `0.5`
- **Noisy environments**: Use `silero` with threshold `0.6-0.7`
- **Low latency needed**: Use `webrtc` with threshold `0.5`
- **No dependencies**: Use `energy` with threshold `0.3-0.5`

### Audio Configuration

Audio settings are defined in the scripts:
- **Sample rate**: 16kHz (local), 8kHz (Twilio)
- **Channels**: Mono
- **Format**: PCM (local), G.711 μ-law (Twilio)

## 🧪 Testing

### Test VAD Module

```bash
# Test VAD with microphone
python vad/voice_activity_detector.py
```

### Test Audio Processor

```bash
# Test audio format conversions
python audio/audio_processor.py
```

### Test Audio Devices

```bash
# List available audio devices
python voice_chat_enhanced.py --help  # Will show device info
```

## 📊 Architecture Details

### Local Mode Flow
```
1. Microphone → Audio Capture (sounddevice)
2. Audio Chunks → VAD Processing (Silero/WebRTC/Energy)
3. Speech End Detection → Trigger Transcription
4. Audio → 11Labs STT → Text
5. Text → OpenAI GPT → Response
6. Response → 11Labs TTS → Audio File
```

### Twilio Mode Flow
```
1. Phone Call → Twilio → WebSocket (G.711 μ-law, base64)
2. Audio Decode → μ-law to PCM → Resample to 16kHz
3. Audio Chunks → VAD Processing
4. Speech End Detection → Trigger Processing
5. Audio → 11Labs STT → Text
6. Text → OpenAI GPT → Response
7. Response → 11Labs TTS → MP3
8. MP3 → WAV → PCM → μ-law → base64
9. WebSocket → Twilio → Phone
```

### VAD Methods

**1. Silero VAD (Recommended)**
- Deep learning model from PyTorch Hub
- Best accuracy and noise handling
- ~5MB model download on first use
- CPU: ~10ms per 30ms chunk
- GPU: ~2ms per 30ms chunk

**2. WebRTC VAD**
- Google WebRTC algorithm
- Lightweight, no model download
- Good for clean audio
- Fast: <1ms per chunk

**3. Energy-based VAD**
- Simple RMS energy threshold
- No dependencies
- Works everywhere
- Good for controlled environments

## 🔧 Troubleshooting

### VAD Issues

**Problem**: Speech not detected
- **Solution**: Lower threshold (`--vad-threshold 0.3`)
- **Solution**: Check microphone is working
- **Solution**: Try different VAD method

**Problem**: Too sensitive (detects noise as speech)
- **Solution**: Raise threshold (`--vad-threshold 0.7`)
- **Solution**: Increase silence duration (`--vad-silence-ms 800`)

**Problem**: Silero VAD fails to load
- **Solution**: Check internet connection (needs to download model)
- **Solution**: Falls back to energy-based automatically

### Twilio Issues

**Problem**: WebSocket connection fails
- **Solution**: Check WebSocket server is running
- **Solution**: Verify WEBSOCKET_URL in .env
- **Solution**: Check firewall allows port 5001

**Problem**: Audio quality poor
- **Solution**: Check sample rate conversion
- **Solution**: Verify G.711 μ-law encoding
- **Solution**: Test with different VAD settings

**Problem**: High latency
- **Solution**: Use faster OpenAI model (`gpt-4o-mini`)
- **Solution**: Reduce `--vad-silence-ms` (e.g., 400ms)
- **Solution**: Use WebRTC VAD instead of Silero

### API Issues

**Problem**: 11Labs STT fails
- **Solution**: Check API key and quota
- **Solution**: Verify audio file format
- **Solution**: Test with simple audio file

**Problem**: OpenAI timeout
- **Solution**: Reduce max_tokens in code
- **Solution**: Check API status
- **Solution**: Use faster model

## 📈 Performance

### Expected Latency (per turn)

| Component | Latency | Notes |
|-----------|---------|-------|
| VAD Detection | 100-300ms | After speech ends |
| 11Labs STT | 500-1500ms | Depends on audio length |
| OpenAI GPT-4o | 1000-3000ms | Depends on response length |
| 11Labs TTS | 500-1500ms | Depends on text length |
| **Total** | **2-6 seconds** | Acceptable for phone calls |

### Optimization Tips

1. **Use GPT-4o-mini**: 50% faster, 75% cheaper
2. **Shorter system prompts**: Reduce token usage
3. **Limit response length**: Set max_tokens=200-300
4. **Use WebRTC VAD**: 5-10x faster than Silero
5. **Streaming TTS**: Use 11Labs streaming API (future)

## 🔐 Security Notes

- **API Keys**: Never commit `.env` file
- **WebSocket**: Use WSS (TLS) in production
- **Audio Storage**: Temporary files are deleted after use
- **Rate Limiting**: Implement per-user limits
- **Input Validation**: All user inputs are sanitized

## 💰 Cost Estimation

**Per 5-minute call (10 turns, 30 sec each)**:

| Service | Cost | Notes |
|---------|------|-------|
| 11Labs STT | ~$0.50 | ~$0.10/minute |
| OpenAI GPT-4o | ~$0.025 | 500 tokens/turn |
| 11Labs TTS | ~$0.18 | 100 chars/turn |
| Twilio | ~$0.07 | ~$0.014/minute |
| **Total** | **~$0.78** | Per 5-min call |

**Optimization**: Use GPT-4o-mini → ~$0.25 per call (68% savings)

## 🚀 Next Steps

### Short Term
- [ ] Test with real phone calls
- [ ] Optimize latency
- [ ] Add error recovery
- [ ] Implement call recording (optional)

### Medium Term
- [ ] Streaming TTS for lower latency
- [ ] Interrupt handling (user can interrupt AI)
- [ ] Multi-language support
- [ ] Background noise cancellation

### Long Term
- [ ] WebRTC browser support
- [ ] Mobile SDK integration
- [ ] Analytics dashboard
- [ ] Call routing based on intent

## 📚 Additional Resources

- [Plan Document](/.claude/plans/ancient-shimmying-volcano.md) - Full implementation plan
- [Silero VAD](https://github.com/snakers4/silero-vad) - VAD model documentation
- [Twilio Media Streams](https://www.twilio.com/docs/voice/twiml/stream) - Twilio WebSocket docs
- [11Labs API](https://elevenlabs.io/docs) - STT/TTS API documentation
- [OpenAI API](https://platform.openai.com/docs) - LLM API documentation

## 🤝 Contributing

When adding features:
1. Maintain backward compatibility
2. Add comprehensive tests
3. Update documentation
4. Follow existing code style

## 📝 License

Same as parent project.
