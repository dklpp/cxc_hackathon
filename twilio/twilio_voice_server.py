#!/usr/bin/env python3
"""
Twilio Voice WebSocket Server

Handles real-time bidirectional audio streaming between Twilio and the voice chat system.

Flow:
1. Receive audio from Twilio (G.711 μ-law, base64-encoded)
2. Detect speech end with VAD
3. Transcribe with 11Labs STT
4. Get LLM response from OpenAI
5. Generate speech with 11Labs TTS
6. Convert to G.711 μ-law and stream back to Twilio

Based on patterns from tests/outbound_calling/realtime_server.py
"""

import os
import sys
import json
import asyncio
import base64
import tempfile
import wave
from pathlib import Path
from dotenv import load_dotenv
import websockets
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import our modules
from vad.voice_activity_detector import VoiceActivityDetector
from audio.audio_processor import AudioProcessor
from stt.speech_to_text import transcribe_audio
from tts.text_to_speech import text_to_speech
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Configuration
TWILIO_SAMPLE_RATE = 8000  # Twilio uses 8kHz μ-law
VAD_SAMPLE_RATE = 16000    # VAD works better at 16kHz
WEBSOCKET_PORT = 5001


class TwilioVoiceServer:
    """WebSocket server for Twilio Media Streams integration"""

    def __init__(
        self,
        model: str = "gpt-4o",
        system_prompt: str = None,
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",
        vad_method: str = 'silero',
        vad_threshold: float = 0.5,
        vad_min_silence_ms: int = 700
    ):
        """
        Initialize Twilio voice server

        Args:
            model: OpenAI model for LLM
            system_prompt: System prompt for AI agent
            voice_id: 11Labs voice ID for TTS
            vad_method: VAD method ('silero', 'webrtc', 'energy')
            vad_threshold: VAD sensitivity
            vad_min_silence_ms: Silence duration to end speech
        """
        self.model = model
        self.voice_id = voice_id
        self.vad_method = vad_method
        self.vad_threshold = vad_threshold
        self.vad_min_silence_ms = vad_min_silence_ms

        # Default system prompt
        if system_prompt is None:
            system_prompt = (
                "You are a helpful AI assistant in a phone conversation. "
                "Keep your responses concise and natural for phone calls. "
                "Avoid special characters or formatting that doesn't "
                "translate well to speech."
            )
        self.system_prompt = system_prompt

        # Audio processor
        self.audio_processor = AudioProcessor()

        print(f"🚀 Twilio Voice Server initialized")
        print(f"   Model: {model}")
        print(f"   Voice: {voice_id}")
        print(f"   VAD: {vad_method} (threshold: {vad_threshold})")

    async def handle_call(self, websocket):
        """
        Handle incoming Twilio WebSocket connection

        Args:
            websocket: WebSocket connection from Twilio
        """
        print("\n📞 Incoming call connection...")

        # Connection state
        stream_sid = None
        call_sid = None
        audio_buffer = []
        vad = None
        conversation_history = [
            {"role": "system", "content": self.system_prompt}
        ]
        turn_counter = 0

        try:
            async for message in websocket:
                data = json.loads(message)
                event = data.get('event')

                if event == 'start':
                    # Call started
                    stream_sid = data['start']['streamSid']
                    call_sid = data['start']['callSid']
                    print(f"✓ Call started: {call_sid}")
                    print(f"  Stream SID: {stream_sid}")

                    # Initialize VAD for this call
                    vad = VoiceActivityDetector(
                        method=self.vad_method,
                        threshold=self.vad_threshold,
                        min_silence_duration_ms=self.vad_min_silence_ms,
                        sample_rate=VAD_SAMPLE_RATE
                    )
                    audio_buffer = []

                    # Send welcome message
                    await self._send_welcome_message(websocket, stream_sid)

                elif event == 'media':
                    # Audio data from Twilio
                    if vad is None:
                        continue

                    # Decode audio payload (base64 G.711 μ-law)
                    payload = data['media']['payload']
                    mulaw_audio = base64.b64decode(payload)

                    # Convert μ-law to PCM
                    pcm_audio = self.audio_processor.convert_from_mulaw(
                        mulaw_audio,
                        TWILIO_SAMPLE_RATE
                    )

                    # Resample to VAD sample rate for better detection
                    if TWILIO_SAMPLE_RATE != VAD_SAMPLE_RATE:
                        pcm_audio = self.audio_processor.resample_audio(
                            pcm_audio,
                            TWILIO_SAMPLE_RATE,
                            VAD_SAMPLE_RATE
                        )

                    # Add to buffer
                    audio_buffer.extend(pcm_audio)

                    # Process with VAD
                    speech_prob = vad.process_audio_chunk(
                        pcm_audio,
                        VAD_SAMPLE_RATE
                    )

                    # Check if speech ended
                    if vad.is_speech_ended():
                        print(f"\n🔵 Turn {turn_counter + 1}: Processing speech...")

                        # Process the conversation turn
                        await self._process_turn(
                            websocket,
                            stream_sid,
                            audio_buffer,
                            conversation_history,
                            VAD_SAMPLE_RATE
                        )

                        # Reset for next turn
                        vad.reset()
                        audio_buffer = []
                        turn_counter += 1

                elif event == 'stop':
                    # Call ended
                    print(f"\n✓ Call ended: {call_sid}")
                    print(f"   Total turns: {turn_counter}")
                    break

        except websockets.exceptions.ConnectionClosed:
            print(f"⚠️  Connection closed: {call_sid if call_sid else 'Unknown'}")
        except Exception as e:
            print(f"❌ Error handling call: {e}")
            import traceback
            traceback.print_exc()

    async def _send_welcome_message(self, websocket, stream_sid):
        """Send initial greeting to caller"""
        try:
            welcome_text = "Hello! I'm your AI assistant. How can I help you today?"
            print(f"🤖 Sending welcome: \"{welcome_text}\"")

            # Generate welcome audio
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix='.mp3',
                prefix='welcome_'
            )
            temp_file.close()

            text_to_speech(welcome_text, temp_file.name, voice_id=self.voice_id)

            # Convert MP3 to WAV, then to μ-law for Twilio
            wav_path = self.audio_processor.convert_mp3_to_wav(temp_file.name)
            audio_data, sample_rate = self.audio_processor.load_wav(wav_path)

            # Send to Twilio
            await self._send_audio_to_twilio(
                websocket,
                stream_sid,
                audio_data,
                sample_rate
            )

            # Cleanup
            os.unlink(temp_file.name)
            os.unlink(wav_path)

        except Exception as e:
            print(f"⚠️  Failed to send welcome: {e}")

    async def _process_turn(
        self,
        websocket,
        stream_sid: str,
        audio_buffer: list,
        conversation_history: list,
        sample_rate: int
    ):
        """
        Process one conversation turn

        Args:
            websocket: WebSocket connection
            stream_sid: Twilio stream SID
            audio_buffer: Buffered audio data
            conversation_history: Conversation history
            sample_rate: Audio sample rate
        """
        try:
            # 1. Save audio to temporary file
            audio_array = np.array(audio_buffer, dtype=np.int16)

            temp_wav = tempfile.NamedTemporaryFile(
                delete=False,
                suffix='.wav',
                prefix='caller_'
            )
            temp_wav.close()

            self.audio_processor.save_wav(
                audio_array,
                temp_wav.name,
                sample_rate
            )

            # 2. Transcribe with 11Labs STT
            print("   🔄 Transcribing...")
            result = transcribe_audio(temp_wav.name)
            user_text = result.get('text', '').strip()

            os.unlink(temp_wav.name)

            if not user_text:
                print("   ⚠️  No speech detected")
                return

            print(f"   📝 Caller: \"{user_text}\"")

            # 3. Get LLM response
            conversation_history.append({
                "role": "user",
                "content": user_text
            })

            print("   🤖 Generating response...")
            response = openai_client.chat.completions.create(
                model=self.model,
                messages=conversation_history,
                temperature=0.7,
                max_tokens=300  # Keep responses concise for phone calls
            )

            agent_text = response.choices[0].message.content.strip()
            conversation_history.append({
                "role": "assistant",
                "content": agent_text
            })

            print(f"   💬 Agent: \"{agent_text}\"")

            # 4. Generate speech with 11Labs TTS
            print("   🔊 Generating speech...")
            temp_mp3 = tempfile.NamedTemporaryFile(
                delete=False,
                suffix='.mp3',
                prefix='agent_'
            )
            temp_mp3.close()

            text_to_speech(agent_text, temp_mp3.name, voice_id=self.voice_id)

            # 5. Convert to WAV, then to μ-law and send to Twilio
            wav_path = self.audio_processor.convert_mp3_to_wav(temp_mp3.name)
            audio_data, audio_sample_rate = self.audio_processor.load_wav(wav_path)

            await self._send_audio_to_twilio(
                websocket,
                stream_sid,
                audio_data,
                audio_sample_rate
            )

            # Cleanup
            os.unlink(temp_mp3.name)
            os.unlink(wav_path)

            print("   ✓ Turn complete")

        except Exception as e:
            print(f"   ❌ Error processing turn: {e}")
            import traceback
            traceback.print_exc()

    async def _send_audio_to_twilio(
        self,
        websocket,
        stream_sid: str,
        audio_data: np.ndarray,
        sample_rate: int
    ):
        """
        Send audio to Twilio via WebSocket

        Args:
            websocket: WebSocket connection
            stream_sid: Twilio stream SID
            audio_data: Audio as numpy array (int16)
            sample_rate: Audio sample rate
        """
        # Convert to G.711 μ-law
        mulaw_audio = self.audio_processor.convert_to_mulaw(
            audio_data,
            sample_rate,
            TWILIO_SAMPLE_RATE
        )

        # Split into chunks (20ms each)
        chunk_size = int(TWILIO_SAMPLE_RATE * 0.02)  # 20ms at 8kHz = 160 bytes

        for i in range(0, len(mulaw_audio), chunk_size):
            chunk = mulaw_audio[i:i + chunk_size]

            # Encode as base64
            payload = base64.b64encode(chunk).decode('utf-8')

            # Send media event to Twilio
            media_event = {
                "event": "media",
                "streamSid": stream_sid,
                "media": {
                    "payload": payload
                }
            }

            await websocket.send(json.dumps(media_event))

            # Small delay to avoid overwhelming Twilio
            await asyncio.sleep(0.02)  # 20ms

    async def start_server(self, host: str = '0.0.0.0', port: int = WEBSOCKET_PORT):
        """
        Start the WebSocket server

        Args:
            host: Host to bind to (default: 0.0.0.0 for all interfaces)
            port: Port to listen on (default: 5001)
        """
        print(f"\n{'='*70}")
        print(f"🎙️  TWILIO VOICE SERVER")
        print(f"{'='*70}")
        print(f"\nListening on: ws://{host}:{port}")
        print(f"WebSocket path: /media-stream")
        print(f"\nWaiting for incoming calls...")
        print(f"Press Ctrl+C to stop\n")

        async with websockets.serve(self.handle_call, host, port, subprotocols=['media-stream']):
            await asyncio.Future()  # Run forever


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Twilio Voice WebSocket Server"
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host to bind to (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=WEBSOCKET_PORT,
        help=f'Port to listen on (default: {WEBSOCKET_PORT})'
    )
    parser.add_argument(
        '--model',
        default='gpt-4o',
        help='OpenAI model to use (default: gpt-4o)'
    )
    parser.add_argument(
        '--voice',
        default='21m00Tcm4TlvDq8ikWAM',
        help='11Labs voice ID (default: Rachel)'
    )
    parser.add_argument(
        '--system-prompt',
        help='Custom system prompt for AI agent'
    )
    parser.add_argument(
        '--vad-method',
        choices=['silero', 'webrtc', 'energy'],
        default='silero',
        help='VAD method (default: silero)'
    )
    parser.add_argument(
        '--vad-threshold',
        type=float,
        default=0.5,
        help='VAD threshold 0.0-1.0 (default: 0.5)'
    )
    parser.add_argument(
        '--vad-silence-ms',
        type=int,
        default=700,
        help='Silence duration in ms to end speech (default: 700)'
    )

    args = parser.parse_args()

    try:
        # Create and start server
        server = TwilioVoiceServer(
            model=args.model,
            system_prompt=args.system_prompt,
            voice_id=args.voice,
            vad_method=args.vad_method,
            vad_threshold=args.vad_threshold,
            vad_min_silence_ms=args.vad_silence_ms
        )

        # Run server
        asyncio.run(server.start_server(args.host, args.port))

    except KeyboardInterrupt:
        print("\n\n⚠️  Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Server error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
