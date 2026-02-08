from dotenv import load_dotenv
from flask import Flask, request, jsonify
import os
import requests

load_dotenv()

app = Flask(__name__)

ELEVEN_LABS_API_KEY = os.getenv("ELEVEN_LABS_API_KEY")
ELEVEN_LABS_AGENT_ID = os.getenv("ELEVEN_LABS_AGENT_ID")
ELEVEN_LABS_AGENT_PHONE_NUMBER_ID = os.getenv("ELEVEN_LABS_AGENT_PHONE_NUMBER_ID")


@app.route('/call', methods=['POST'])
def make_call():
    """Initiate an outbound call via ElevenLabs Conversational AI + Twilio"""
    data = request.json or {}
    to_number = data.get('phone_number', os.getenv('ALINA_PHONE_NUMBER'))

    response = requests.post(
        "https://api.elevenlabs.io/v1/convai/twilio/outbound-call",
        headers={
            "Content-Type": "application/json",
            "xi-api-key": ELEVEN_LABS_API_KEY,
        },
        json={
            "agent_id": ELEVEN_LABS_AGENT_ID,
            "agent_phone_number_id": ELEVEN_LABS_AGENT_PHONE_NUMBER_ID,
            "to_number": to_number,
        },
    )

    if response.ok:
        return jsonify(response.json())
    else:
        return jsonify({"error": response.text}), response.status_code


if __name__ == '__main__':
    print("Starting Flask server on http://localhost:5000")
    print(f"  Agent ID:       {ELEVEN_LABS_AGENT_ID}")
    print(f"  Phone Number ID: {ELEVEN_LABS_AGENT_PHONE_NUMBER_ID}")
    print("  POST /call — Initiate outbound call via ElevenLabs")
    app.run(host='0.0.0.0', port=5000, debug=True)
