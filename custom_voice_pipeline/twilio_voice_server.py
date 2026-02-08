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
import subprocess
import tempfile
import wave
from datetime import datetime
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
from tts.text_to_speech import text_to_speech_pcm
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

INPUT_PROMPT = """
You are an AI-powered voice agent James from Tangerine Bank for debt collection and customer engagement. Your responsibility is to conduct clear, ethical, and empathetic phone conversations that aim to resolve outstanding balances while preserving customer dignity and long-term trust.

Speak in a natural, calm, and human voice. Adapt your tone, pacing, and language to the customer’s emotional state and level of understanding. Listen carefully, acknowledge concerns without judgment, and respond with patience and clarity.

Clearly identify yourself, your organization, and the purpose of the call. Communicate account information honestly and in plain language. Avoid blame, pressure, or confrontational behavior at all times.

When discussing repayment, work collaboratively with the customer to explore realistic and appropriate options. Encourage resolution without coercion, respect financial hardship, and clearly summarize any agreements, next steps, and expectations before ending the call.

Always comply with all applicable laws and regulations. Respect customer boundaries and requests to pause, reschedule, or stop the conversation. Maintain professionalism even in tense situations and actively de-escalate frustration or distress.


Success is measured not only by payment outcomes, but by ethical conduct, customer trust, reduced conflict, and positive, human-centered experiences.
"""

# Configuration
TWILIO_SAMPLE_RATE = 8000  # Twilio uses 8kHz μ-law
VAD_SAMPLE_RATE = 16000    # VAD works better at 16kHz
WEBSOCKET_PORT = 5001


class TwilioVoiceServer:
    """WebSocket server for Twilio Media Streams integration"""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        system_prompt: str = None,
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",
        vad_method: str = 'silero',
        vad_threshold: float = 0.5,
        vad_min_silence_ms: int = 400,
        enable_transcription: bool = True,
        enable_recording: bool = True,
        tts_model: str = "eleven_turbo_v2"
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
            enable_transcription: Save conversation transcript to file
            enable_recording: Save call recording as MP4
            tts_model: 11Labs TTS model ID
        """
        self.model = model
        self.voice_id = voice_id
        self.tts_model = tts_model
        self.vad_method = vad_method
        self.vad_threshold = vad_threshold
        self.vad_min_silence_ms = vad_min_silence_ms
        self.enable_transcription = enable_transcription
        self.enable_recording = enable_recording

        # Default system prompt
        if system_prompt is None:
            system_prompt = (INPUT_PROMPT)
        self.system_prompt = system_prompt

        # Audio processor
        self.audio_processor = AudioProcessor()

        print(f"   Twilio Voice Server initialized")
        print(f"   Model: {model}")
        print(f"   Voice: {voice_id}")
        print(f"   TTS model: {tts_model}")
        print(f"   VAD: {vad_method} (threshold: {vad_threshold})")
        print(f"   Transcription: {'enabled' if enable_transcription else 'disabled'}")
        print(f"   Recording: {'enabled' if enable_recording else 'disabled'}")

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
        vad_chunk_buffer = np.array([], dtype=np.int16)  # Buffer to accumulate 512 samples for Silero VAD
        call_recording = []  # Full call recording (list of np.int16 arrays at RECORDING_SAMPLE_RATE)
        RECORDING_SAMPLE_RATE = VAD_SAMPLE_RATE  # 16kHz for recording
        vad = None
        conversation_history = [
            {"role": "system", "content": self.system_prompt}
        ]
        turn_counter = 0
        frame_counter = 0
        transcript_path = None

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

                    # Create transcription file
                    if self.enable_transcription or self.enable_recording:
                        transcription_dir = Path(__file__).parent.parent / 'transcription'
                        transcription_dir.mkdir(exist_ok=True)
                    if self.enable_transcription:
                        transcript_path = transcription_dir / f'transcription_{call_sid}.txt'
                        with open(transcript_path, 'w') as f:
                            f.write(f"Call ID: {call_sid}\n")
                            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                            f.write(f"{'='*60}\n\n")
                        print(f"  Transcript: {transcript_path}")

                    # Initialize VAD for this call
                    vad = VoiceActivityDetector(
                        method=self.vad_method,
                        threshold=self.vad_threshold,
                        min_silence_duration_ms=self.vad_min_silence_ms,
                        sample_rate=VAD_SAMPLE_RATE
                    )
                    audio_buffer = []

                    # Send welcome message
                    welcome_text, welcome_audio = await self._send_welcome_message(websocket, stream_sid)
                    if welcome_text and transcript_path:
                        with open(transcript_path, 'a') as f:
                            f.write(f"Agent: {welcome_text}\n\n")
                    if self.enable_recording and welcome_audio is not None:
                        call_recording.append(welcome_audio)

                elif event == 'media':
                    # Audio data from Twilio
                    if vad is None:
                        continue

                    try:
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

                        # Add to main audio buffer (for STT later)
                        audio_buffer.extend(pcm_audio)

                        # Accumulate into VAD chunk buffer (Silero needs 512 samples at 16kHz)
                        vad_chunk_buffer = np.concatenate([vad_chunk_buffer, pcm_audio])

                        # Process VAD in 512-sample chunks
                        VAD_CHUNK_SIZE = 512
                        while len(vad_chunk_buffer) >= VAD_CHUNK_SIZE:
                            vad_chunk = vad_chunk_buffer[:VAD_CHUNK_SIZE]
                            vad_chunk_buffer = vad_chunk_buffer[VAD_CHUNK_SIZE:]

                            speech_prob = vad.process_audio_chunk(
                                vad_chunk,
                                VAD_SAMPLE_RATE
                            )

                            frame_counter += 1
                            if frame_counter % 50 == 0:
                                state = vad.get_state_info()
                                print(f"   VAD frame {frame_counter}: prob={speech_prob:.2f} started={state['speech_started']}")

                        # Check if speech ended
                        if vad.is_speech_ended():
                            print(f"\n🔵 Turn {turn_counter + 1}: Processing speech...")

                            # Process the conversation turn
                            await self._process_turn(
                                websocket,
                                stream_sid,
                                audio_buffer,
                                conversation_history,
                                VAD_SAMPLE_RATE,
                                transcript_path if self.enable_transcription else None,
                                call_recording if self.enable_recording else None
                            )

                            # Reset for next turn
                            vad.reset()
                            audio_buffer = []
                            vad_chunk_buffer = np.array([], dtype=np.int16)
                            turn_counter += 1

                    except Exception as e:
                        print(f"⚠️  Error processing media frame: {e}")
                        import traceback
                        traceback.print_exc()

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
        finally:
            # Save call recording as MP4
            if self.enable_recording and call_recording and call_sid:
                await self._save_call_recording(call_recording, call_sid, RECORDING_SAMPLE_RATE)

    async def _send_welcome_message(self, websocket, stream_sid):
        """Send initial greeting to caller. Returns (welcome_text, audio_data_16khz) on success."""
        try:
            welcome_text = "Hello! I'm calling on behalf of Tangerine Bank about your outstanding balance. Do you have a moment to speak?"
            print(f"🤖 Sending welcome: \"{welcome_text}\"")

            # Generate welcome audio as raw PCM (skip MP3/ffmpeg conversion)
            pcm_bytes = await asyncio.to_thread(
                text_to_speech_pcm, welcome_text, self.voice_id, self.tts_model, VAD_SAMPLE_RATE
            )
            audio_data = np.frombuffer(pcm_bytes, dtype=np.int16)

            # Audio is already at VAD_SAMPLE_RATE (16kHz)
            recording_audio = audio_data.copy()

            # Send to Twilio
            await self._send_audio_to_twilio(
                websocket,
                stream_sid,
                audio_data,
                VAD_SAMPLE_RATE
            )

            return welcome_text, recording_audio

        except Exception as e:
            print(f"⚠️  Failed to send welcome: {e}")
            import traceback
            traceback.print_exc()
            return None, None

    async def _process_turn(
        self,
        websocket,
        stream_sid: str,
        audio_buffer: list,
        conversation_history: list,
        sample_rate: int,
        transcript_path: Path = None,
        call_recording: list = None
    ):
        """
        Process one conversation turn

        Args:
            websocket: WebSocket connection
            stream_sid: Twilio stream SID
            audio_buffer: Buffered audio data
            conversation_history: Conversation history
            sample_rate: Audio sample rate
            transcript_path: Path to transcript file
            call_recording: List to append audio segments for full call recording
        """
        try:
            # 1. Save audio to temporary file
            audio_array = np.array(audio_buffer, dtype=np.int16)

            # Add caller audio to call recording
            if call_recording is not None:
                call_recording.append(audio_array.copy())

            temp_wav = tempfile.NamedTemporaryFile(
                delete=False,
                suffix='.wav',
                prefix='caller_'
            )
            temp_wav.close()

            await asyncio.to_thread(
                self.audio_processor.save_wav,
                audio_array,
                temp_wav.name,
                sample_rate
            )

            # 2. Transcribe with 11Labs STT
            print("   🔄 Transcribing...")
            result = await asyncio.to_thread(transcribe_audio, temp_wav.name)
            user_text = result.get('text', '').strip()

            os.unlink(temp_wav.name)

            if not user_text:
                print("   ⚠️  No speech detected")
                return

            print(f"   📝 Caller: \"{user_text}\"")

            # Log user text to transcript
            if transcript_path:
                with open(transcript_path, 'a') as f:
                    f.write(f"User: {user_text}\n\n")

            # 3. Get LLM response
            conversation_history.append({
                "role": "user",
                "content": user_text
            })

            print("   🤖 Generating response...")
            response = await asyncio.to_thread(
                openai_client.chat.completions.create,
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

            # Log agent response to transcript
            if transcript_path:
                with open(transcript_path, 'a') as f:
                    f.write(f"Agent: {agent_text}\n\n")

            # 4. Generate speech with 11Labs TTS (raw PCM, no MP3/ffmpeg)
            print("   🔊 Generating speech...")
            pcm_bytes = await asyncio.to_thread(
                text_to_speech_pcm, agent_text, self.voice_id, self.tts_model, VAD_SAMPLE_RATE
            )
            audio_data = np.frombuffer(pcm_bytes, dtype=np.int16)

            # Add agent audio to call recording (already at 16kHz)
            if call_recording is not None:
                call_recording.append(audio_data.copy())

            # 5. Send to Twilio
            await self._send_audio_to_twilio(
                websocket,
                stream_sid,
                audio_data,
                VAD_SAMPLE_RATE
            )

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

    async def _save_call_recording(self, call_recording: list, call_sid: str, sample_rate: int):
        """Save the full call recording as MP4"""
        try:
            recording_dir = Path(__file__).parent.parent / 'transcription'
            recording_dir.mkdir(exist_ok=True)

            # Concatenate all audio segments
            full_audio = np.concatenate(call_recording)
            print(f"\n🎵 Saving call recording ({len(full_audio) / sample_rate:.1f}s)...")

            # Save as WAV first
            wav_path = recording_dir / f'recording_{call_sid}.wav'
            self.audio_processor.save_wav(full_audio, str(wav_path), sample_rate)

            # Convert WAV to MP4 (AAC) using ffmpeg
            mp4_path = recording_dir / f'recording_{call_sid}.mp4'
            result = await asyncio.to_thread(
                subprocess.run,
                ['ffmpeg', '-y', '-i', str(wav_path), '-c:a', 'aac', '-b:a', '128k', str(mp4_path)],
                capture_output=True, text=True
            )

            if result.returncode == 0:
                os.unlink(wav_path)  # Remove WAV, keep MP4
                print(f"   ✓ Recording saved: {mp4_path}")
            else:
                print(f"   ⚠️  FFmpeg conversion failed, keeping WAV: {wav_path}")
                print(f"      {result.stderr[:200]}")

        except Exception as e:
            print(f"   ❌ Failed to save recording: {e}")

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

        async with websockets.serve(self.handle_call, host, port):
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
        default='gpt-4o-mini',
        help='OpenAI model to use (default: gpt-4o-mini)'
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
        default=400,
        help='Silence duration in ms to end speech (default: 400)'
    )
    parser.add_argument(
        '--tts-model',
        default='eleven_turbo_v2',
        help='11Labs TTS model (default: eleven_turbo_v2). Options: eleven_turbo_v2, eleven_turbo_v2_5, eleven_multilingual_v2'
    )
    parser.add_argument(
        '--no-transcription',
        action='store_true',
        help='Disable saving conversation transcript'
    )
    parser.add_argument(
        '--no-recording',
        action='store_true',
        help='Disable saving call recording as MP4'
    )

    args = parser.parse_args()

    try:
        # Create and start server
        server = TwilioVoiceServer(
            model=args.model,
            system_prompt=args.system_prompt,
            voice_id=args.voice,
            tts_model=args.tts_model,
            vad_method=args.vad_method,
            vad_threshold=args.vad_threshold,
            vad_min_silence_ms=args.vad_silence_ms,
            enable_transcription=not args.no_transcription,
            enable_recording=not args.no_recording
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
