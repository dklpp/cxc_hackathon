# Outbound Voice Call Server

AI-powered outbound voice calls using Twilio + ElevenLabs (STT/TTS) + OpenAI (LLM) + Silero (VAD).

## Prerequisites

- Python 3.10+ with virtual environment
- `ffmpeg` installed (`brew install ffmpeg`)
- `.env` file with API keys (see `.env.example`)
- Cloudflared installed (`brew install cloudflared`)

### Required API Keys (`.env`)

```
OPENAI_API_KEY=...
ELEVEN_LABS_API_KEY=...
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER='+1...'
```

## Architecture

```
Terminal 1: WebSocket Server (port 5001)
    Handles audio streaming, VAD, STT, LLM, TTS

Terminal 2: Cloudflared tunnel for WebSocket
    Exposes port 5001 publicly so Twilio can reach it

Terminal 3: TwiML HTTP Server (port 5050)
    Serves TwiML XML that tells Twilio to connect via WebSocket
    Needs WEBSOCKET_URL env var pointing to Terminal 2's tunnel

Terminal 4: Cloudflared tunnel for TwiML + trigger outbound call
    Exposes port 5050 publicly, then initiates the call
```

## Step-by-Step Startup

### Terminal 1 — WebSocket Server

```bash
source .venv/bin/activate
python twilio/twilio_voice_server.py
```

Optional flags:
| Flag | Default | Description |
|------|---------|-------------|
| `--model` | `gpt-4o-mini` | OpenAI model (`gpt-4o`, `gpt-4o-mini`) |
| `--tts-model` | `eleven_turbo_v2` | ElevenLabs TTS model |
| `--voice` | `21m00Tcm4TlvDq8ikWAM` | ElevenLabs voice ID (Rachel) |
| `--vad-silence-ms` | `400` | Silence duration (ms) to detect end of speech |
| `--vad-threshold` | `0.5` | VAD sensitivity (0.0–1.0) |
| `--vad-method` | `silero` | VAD backend (`silero`, `webrtc`, `energy`) |
| `--no-transcription` | off | Disable saving transcript to file |
| `--no-recording` | off | Disable saving MP4 recording |
| `--system-prompt` | built-in | Custom system prompt |
| `--port` | `5001` | WebSocket port |

Example with all options:
```bash
python twilio/twilio_voice_server.py \
  --model gpt-4o \
  --tts-model eleven_turbo_v2 \
  --vad-silence-ms 500 \
  --no-recording
```

### Terminal 2 — Cloudflared Tunnel for WebSocket

```bash
cloudflared tunnel --url http://localhost:5001
```

Copy the generated URL (e.g., `abc-xyz.trycloudflare.com`). You'll need just the **hostname** (without `https://`).

### Terminal 3 — TwiML Server

Set `WEBSOCKET_URL` to the hostname from Terminal 2, then start:

```bash
source .venv/bin/activate
export WEBSOCKET_URL=abc-xyz.trycloudflare.com
python twilio/twilio_server_simple.py
```

The server auto-prepends `wss://` and appends `/media-stream` to the URL.

### Terminal 4 — Cloudflared Tunnel for TwiML + Make Call

Start a tunnel for the TwiML server, then trigger the call:

```bash
cloudflared tunnel --url http://localhost:5050
```

Once the tunnel URL appears, trigger the outbound call:

```bash
source .venv/bin/activate
python twilio/outbound_call.py call \
  --to +1XXXXXXXXXX \
  --webhook https://YOUR-TWIML-TUNNEL.trycloudflare.com/voice
```

## Call Flow

```
1. outbound_call.py → Twilio API: "Call this number, use this webhook"
2. Twilio → TwiML server (/voice): Gets XML saying "connect WebSocket"
3. Twilio → WebSocket server: Opens bidirectional audio stream
4. WebSocket server plays welcome message
5. Loop:
   a. Receive audio from Twilio (G.711 μ-law, 8kHz)
   b. Convert to PCM 16kHz, run through Silero VAD
   c. On speech end → ElevenLabs STT → OpenAI LLM → ElevenLabs TTS (PCM)
   d. Convert to μ-law, stream back to Twilio
```

## Outputs

| File | Location | Description |
|------|----------|-------------|
| Transcript | `transcription/transcription_<CALL_SID>.txt` | Full conversation log |
| Recording | `transcription/recording_<CALL_SID>.mp4` | Audio recording of the call |

Disable with `--no-transcription` and `--no-recording`.

## Managing Calls

```bash
# Check call status
python twilio/outbound_call.py status <CALL_SID>

# Hang up a call
python twilio/outbound_call.py hangup <CALL_SID>

# List active calls
python twilio/outbound_call.py list
```

## Killing All Servers

```bash
# Kill all processes on the used ports
lsof -ti:5001 | xargs kill -9 2>/dev/null
lsof -ti:5050 | xargs kill -9 2>/dev/null
pkill -f cloudflared
```

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Call drops after "press any number" | `WEBSOCKET_URL` not set or wrong | Set it to the Terminal 2 tunnel hostname (no `https://`) |
| Call drops after 1 second | `ffmpeg` not installed | `brew install ffmpeg` |
| Call drops after welcome message | Blocking calls on async event loop | Already fixed in code with `asyncio.to_thread()` |
| Agent never responds | VAD buffer mismatch | Already fixed with 512-sample accumulator |
| `wss://https://...` in logs | Double protocol | Pass just hostname, not full URL |
