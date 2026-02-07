import asyncio
import audioop
import base64
import json
import os
import traceback

import websockets
from websockets.server import serve
from dotenv import load_dotenv

load_dotenv()

ELEVEN_LABS_API_KEY = os.getenv("ELEVEN_LABS_API_KEY")
ELEVEN_LABS_AGENT_ID = os.getenv("ELEVEN_LABS_AGENT_ID")

class TwilioElevenLabsBridge:
    """Bridges Twilio media streams to ElevenLabs Conversational AI.

    Audio conversion:
      Twilio  -> bridge: μ-law 8 kHz mono  →  PCM16 16 kHz mono  -> ElevenLabs
      Twilio  <- bridge: μ-law 8 kHz mono  ←  PCM16 (sample rate from event) <- ElevenLabs
    """

    async def handle_twilio_connection(self, websocket):
        print("Twilio WebSocket connected")
        stream_sid = None

        try:
            # Connect to ElevenLabs Conversational AI
            url = (
                f"wss://api.elevenlabs.io/v1/convai/conversation"
                f"?agent_id={ELEVEN_LABS_AGENT_ID}"
            )

            async with websockets.connect(
                url, extra_headers={"xi-api-key": ELEVEN_LABS_API_KEY}
            ) as eleven_ws:
                print("Connected to ElevenLabs Conversational AI")

                # Receive conversation initiation metadata
                init_msg = await eleven_ws.recv()
                init_data = json.loads(init_msg)
                conv_id = (
                    init_data.get("conversation_initiation_metadata_event", {})
                    .get("conversation_id", "unknown")
                )
                print(f"Conversation ID: {conv_id}")

                # ── Twilio → ElevenLabs ──────────────────────────────
                async def twilio_to_elevenlabs():
                    nonlocal stream_sid
                    async for message in websocket:
                        data = json.loads(message)

                        if data["event"] == "start":
                            stream_sid = data["start"]["streamSid"]
                            print(f"Twilio stream started: {stream_sid}")

                        elif data["event"] == "media":
                            # μ-law 8 kHz → PCM16 16 kHz
                            mulaw_bytes = base64.b64decode(data["media"]["payload"])
                            pcm_data = audioop.ulaw2lin(mulaw_bytes, 2)
                            pcm_data = audioop.ratecv(
                                pcm_data, 2, 1, 8000, 16000, None
                            )[0]

                            await eleven_ws.send(
                                json.dumps(
                                    {
                                        "user_audio_chunk": base64.b64encode(
                                            pcm_data
                                        ).decode()
                                    }
                                )
                            )

                        elif data["event"] == "stop":
                            print("Twilio stream stopped")
                            break

                # ── ElevenLabs → Twilio ──────────────────────────────
                async def elevenlabs_to_twilio():
                    async for message in eleven_ws:
                        response = json.loads(message)
                        msg_type = response.get("type", "")

                        if msg_type == "audio":
                            audio_event = response.get("audio_event", {})
                            audio_b64 = audio_event.get("audio_base_64", "")
                            sample_rate = audio_event.get("sample_rate", 16000)

                            if audio_b64 and stream_sid:
                                pcm_data = base64.b64decode(audio_b64)
                                # Resample to 8 kHz if needed
                                if sample_rate != 8000:
                                    pcm_data = audioop.ratecv(
                                        pcm_data, 2, 1, sample_rate, 8000, None
                                    )[0]
                                # PCM16 → μ-law
                                mulaw_data = audioop.lin2ulaw(pcm_data, 2)

                                await websocket.send(
                                    json.dumps(
                                        {
                                            "event": "media",
                                            "streamSid": stream_sid,
                                            "media": {
                                                "payload": base64.b64encode(
                                                    mulaw_data
                                                ).decode()
                                            },
                                        }
                                    )
                                )

                        elif msg_type == "ping":
                            event_id = response.get("ping_event", {}).get("event_id")
                            await eleven_ws.send(
                                json.dumps({"type": "pong", "event_id": event_id})
                            )

                        elif msg_type == "agent_response":
                            text = (
                                response.get("agent_response_event", {})
                                .get("agent_response", "")
                            )
                            if text:
                                print(f"Agent: {text}")

                        elif msg_type == "user_transcript":
                            text = (
                                response.get("user_transcription_event", {})
                                .get("user_transcript", "")
                            )
                            if text:
                                print(f"User:  {text}")

                        elif msg_type == "interruption":
                            # Tell Twilio to stop playing current audio
                            if stream_sid:
                                await websocket.send(
                                    json.dumps(
                                        {"event": "clear", "streamSid": stream_sid}
                                    )
                                )

                await asyncio.gather(
                    twilio_to_elevenlabs(),
                    elevenlabs_to_twilio(),
                )

        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()
        finally:
            print("Connection closed")


async def main():
    if not ELEVEN_LABS_AGENT_ID:
        print("ERROR: ELEVEN_LABS_AGENT_ID not set in .env")
        print("Create an agent at https://elevenlabs.io/app/conversational-ai")
        return

    bridge = TwilioElevenLabsBridge()

    async with serve(bridge.handle_twilio_connection, "0.0.0.0", 5001):
        print("ElevenLabs <-> Twilio Bridge")
        print(f"  WebSocket: ws://0.0.0.0:5001")
        print(f"  Agent ID:  {ELEVEN_LABS_AGENT_ID}")
        print("Expose with: cloudflared tunnel --url http://localhost:5001")
        print("Waiting for Twilio connections...")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
