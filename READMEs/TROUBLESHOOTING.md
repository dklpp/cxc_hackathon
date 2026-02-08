# Troubleshooting Guide

## Import Errors

### Problem: `ModuleNotFoundError: No module named 'vad'`

**Cause**: Python can't find the project modules.

**Solution**: Run scripts from the project root directory:

```bash
# Wrong - running from twilio directory
cd twilio
python twilio_voice_server.py  # ❌ Will fail

# Correct - running from project root
cd /path/to/cxc_hackathon
python twilio/twilio_voice_server.py  # ✅ Works
```

Or use the `-m` flag:
```bash
python -m twilio.twilio_voice_server
```

### Problem: `DeprecationWarning: websockets.server.serve is deprecated`

**Cause**: Using deprecated websockets API.

**Status**: ✅ Fixed - Now uses `websockets.serve()` instead.

## Running the Servers

### Correct Way to Run

```bash
# 1. Make sure you're in the project root
cd /path/to/cxc_hackathon

# 2. Activate virtual environment
source .venv/bin/activate  # On Linux/macOS
# OR
.venv\Scripts\activate     # On Windows

# 3. Run the server
python twilio/twilio_voice_server.py
```

### Using Helper Scripts

The helper scripts handle paths correctly:

```bash
# From project root
./scripts/start_servers.sh   # ✅ Works
```

## Dependency Issues

### Problem: `torch` or `silero-vad` not found

**Solution**:
```bash
pip install torch torchaudio
# Silero VAD will be downloaded automatically on first use via torch.hub
```

### Problem: `webrtcvad` not installing

**Solution**:
```bash
# On macOS
brew install portaudio
pip install webrtcvad

# On Linux
sudo apt-get install portaudio19-dev
pip install webrtcvad

# On Windows
pip install webrtcvad
```

### Problem: `sounddevice` audio errors

**Solution**:
```bash
# List available audio devices
python -c "import sounddevice as sd; print(sd.query_devices())"

# Test audio
python voice_chat_enhanced.py --help
```

## VAD Issues

### Problem: Silero VAD fails to download

**Solution**:
```bash
# Manually download Silero VAD
python -c "import torch; torch.hub.load('snakers4/silero-vad', 'silero_vad')"
```

### Problem: VAD not detecting speech

**Solutions**:
1. Lower threshold: `--vad-threshold 0.3`
2. Try different method: `--vad-method webrtc`
3. Check microphone: `python -c "import sounddevice as sd; print(sd.query_devices())"`

### Problem: VAD too sensitive

**Solutions**:
1. Raise threshold: `--vad-threshold 0.7`
2. Increase silence duration: `--vad-silence-ms 800`
3. Use energy method: `--vad-method energy`

## Twilio Issues

### Problem: WebSocket connection refused

**Solutions**:
1. Check WebSocket server is running: `ps aux | grep twilio_voice_server`
2. Check port is not blocked: `netstat -an | grep 5001`
3. Verify firewall settings

### Problem: Twilio can't connect to webhook

**Solutions**:
1. Ensure tunnel is running: `cloudflared tunnel --url http://localhost:5000`
2. Check WEBSOCKET_URL in .env: `echo $WEBSOCKET_URL`
3. Test webhook: `curl http://localhost:5000/health`
4. Verify Twilio webhook URL is correct in console

### Problem: Audio quality poor on calls

**Solutions**:
1. Check sample rate conversion
2. Verify G.711 encoding: `python audio/audio_processor.py` (run tests)
3. Reduce background noise
4. Try different VAD settings

## API Issues

### Problem: 11Labs API errors

**Solutions**:
1. Check API key: `echo $ELEVEN_LABS_API_KEY`
2. Verify quota: Check 11Labs dashboard
3. Test API: `python stt/speech_to_text.py test_audio.mp3`

### Problem: OpenAI API timeout

**Solutions**:
1. Check API key: `echo $OPENAI_API_KEY`
2. Use faster model: `--model gpt-4o-mini`
3. Reduce max_tokens in code
4. Check OpenAI status: https://status.openai.com

### Problem: Twilio API errors

**Solutions**:
1. Check credentials: `echo $TWILIO_ACCOUNT_SID`
2. Verify phone number: `echo $TWILIO_PHONE_NUMBER`
3. Test with CLI: `twilio phone-numbers:list`

## Performance Issues

### Problem: High latency (>10 seconds)

**Solutions**:
1. Use faster model: `--model gpt-4o-mini`
2. Reduce VAD silence: `--vad-silence-ms 400`
3. Use WebRTC VAD: `--vad-method webrtc`
4. Check network connection
5. Monitor with: `time python twilio/twilio_voice_server.py`

### Problem: High CPU usage

**Solutions**:
1. Use WebRTC instead of Silero: `--vad-method webrtc`
2. Reduce sample rate (if possible)
3. Limit concurrent calls

### Problem: Memory leaks

**Solutions**:
1. Check audio buffers are cleared
2. Verify temp files are deleted
3. Monitor with: `top` or `htop`
4. Restart servers periodically

## Testing

### Test VAD
```bash
cd /path/to/cxc_hackathon
python vad/voice_activity_detector.py
```

### Test Audio Processor
```bash
cd /path/to/cxc_hackathon
python audio/audio_processor.py
```

### Test Voice Chat
```bash
cd /path/to/cxc_hackathon
python voice_chat_enhanced.py --use-vad --turns 1
```

### Test Twilio Server
```bash
# Terminal 1: WebSocket server
cd /path/to/cxc_hackathon
python twilio/twilio_voice_server.py

# Terminal 2: TwiML server
cd /path/to/cxc_hackathon
python twilio/twilio_server_simple.py

# Terminal 3: Check health
curl http://localhost:5000/health
```

## Logs

### View Server Logs
```bash
# If using helper scripts
tail -f logs/websocket-server.log
tail -f logs/twiml-server.log

# If running manually, redirect output
python twilio/twilio_voice_server.py > server.log 2>&1 &
tail -f server.log
```

### Debug Mode
Add debug prints in code or use logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Environment Variables

### Check All Variables
```bash
# Load and display
source .env
env | grep -E "(OPENAI|ELEVEN|TWILIO|VAD|WEBSOCKET)"
```

### Reset Configuration
```bash
cp .env.example .env
# Edit .env with your values
nano .env
```

## Clean Installation

If nothing works, try clean reinstall:

```bash
# 1. Remove virtual environment
rm -rf .venv

# 2. Create new virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Upgrade pip
pip install --upgrade pip

# 4. Install dependencies
pip install -r requirements.txt

# 5. Test imports
python -c "from vad.voice_activity_detector import VoiceActivityDetector; print('✓ OK')"
python -c "from audio.audio_processor import AudioProcessor; print('✓ OK')"

# 6. Run test
python voice_chat_enhanced.py --help
```

## Getting Help

1. Check logs for detailed error messages
2. Verify all dependencies installed: `pip list`
3. Check Python version: `python --version` (should be 3.9+)
4. Review the main README: [VOICE_CHAT_ENHANCED_README.md](VOICE_CHAT_ENHANCED_README.md)
5. Check the implementation summary: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

## Quick Checklist

Before running, verify:
- [ ] In project root directory
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file configured with API keys
- [ ] Audio device available (for local testing)
- [ ] Twilio credentials set (for phone testing)
- [ ] Ports 5000 and 5001 available
