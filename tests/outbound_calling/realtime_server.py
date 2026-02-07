import asyncio
import base64
import json
import os
import websockets
from websockets.server import serve
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SYSTEM_MESSAGE = "You are a bank collector. Inform user about their dept of 100000$ and ask kindly to pay the money back."

class TwilioOpenAIBridge:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        self.openai_ws = None

    async def handle_twilio_connection(self, websocket):
        """Handle incoming WebSocket connection from Twilio"""
        print("Twilio connected")
        stream_sid = None

        try:
            async with websockets.connect(
                'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01',
                extra_headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "OpenAI-Beta": "realtime=v1"
                }
            ) as openai_ws:
                self.openai_ws = openai_ws
                print("Connected to OpenAI Realtime API")

                session_update = {
                    "type": "session.update",
                    "session": {
                        "modalities": ["text", "audio"],
                        "instructions": SYSTEM_MESSAGE,
                        "voice": "alloy",
                        "input_audio_format": "g711_ulaw",
                        "output_audio_format": "g711_ulaw",
                        "turn_detection": {
                            "type": "server_vad",
                            "threshold": 0.5,
                            "prefix_padding_ms": 300,
                            "silence_duration_ms": 500
                        }
                    }
                }
                await openai_ws.send(json.dumps(session_update))

                async def twilio_to_openai():
                    """Forward audio from Twilio to OpenAI"""
                    async for message in websocket:
                        data = json.loads(message)

                        if data['event'] == 'start':
                            nonlocal stream_sid
                            stream_sid = data['start']['streamSid']
                            print(f"Stream started: {stream_sid}")

                        elif data['event'] == 'media':
                            audio_append = {
                                "type": "input_audio_buffer.append",
                                "audio": data['media']['payload']
                            }
                            await openai_ws.send(json.dumps(audio_append))

                        elif data['event'] == 'stop':
                            print("Stream stopped")
                            break

                async def openai_to_twilio():
                    """Forward audio from OpenAI to Twilio"""
                    async for message in openai_ws:
                        response = json.loads(message)

                        if response['type'] == 'response.audio.delta':
                            audio_data = {
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {
                                    "payload": response['delta']
                                }
                            }
                            await websocket.send(json.dumps(audio_data))

                        elif response['type'] == 'response.audio_transcript.done':
                            print(f"AI said: {response.get('transcript', '')}")

                        elif response['type'] == 'conversation.item.input_audio_transcription.completed':
                            print(f"User said: {response.get('transcript', '')}")

                await asyncio.gather(
                    twilio_to_openai(),
                    openai_to_twilio()
                )

        except Exception as e:
            print(f"Error: {e}")
        finally:
            print("Connection closed")

async def main():
    bridge = TwilioOpenAIBridge()

    async with serve(bridge.handle_twilio_connection, "0.0.0.0", 5001):
        print("WebSocket server started on ws://0.0.0.0:5001")
        print("Waiting for Twilio connections...")
        await asyncio.Future()  

if __name__ == "__main__":
    asyncio.run(main())
