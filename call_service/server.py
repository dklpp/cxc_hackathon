import os
import time
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

app = Flask(__name__)

API_KEY = os.getenv("ELEVEN_LABS_API_KEY")
AGENT_ID = os.getenv("ELEVEN_LABS_AGENT_ID")
PHONE_NUMBER_ID = os.getenv("ELEVEN_LABS_AGENT_PHONE_NUMBER_ID")

ELEVENLABS_URL = "https://api.elevenlabs.io/v1/convai/twilio/outbound-call"
ELEVENLABS_CONV_URL = "https://api.elevenlabs.io/v1/convai/conversations"


@app.route("/")
def index():
    return {"status": "ok"}

@app.route("/make_call", methods=["POST"])
def make_call():
    body = request.get_json()
    if not body or not all(k in body for k in ("username", "userdata", "phone")):
        return jsonify({"error": "username, userdata, and phone are required"}), 400

    username = body["username"]
    userdata = body["userdata"]
    phone = body["phone"]

    first_message = f"Hi {username} — I'm calling about your outstanding balance."
    prompt = f"{username} owes {userdata}. Ask them politely to arrange payment."

    payload = {
        "agent_id": AGENT_ID,
        "agent_phone_number_id": PHONE_NUMBER_ID,
        "to_number": phone,
        "conversation_initiation_client_data": {
            "conversation_config_override": {
                "agent": {
                    "first_message": first_message,
                    "prompt": {"prompt": prompt},
                }
            }
        },
    }

    response = requests.post(
        ELEVENLABS_URL,
        headers={"Content-Type": "application/json", "xi-api-key": API_KEY},
        json=payload,
    )

    if response.status_code != 200:
        return jsonify({"error": "Failed to initiate call", "details": response.text}), response.status_code

    conversation_id = response.json()["conversation_id"]

    while True:
        time.sleep(5)
        conv_response = requests.get(
            f"{ELEVENLABS_CONV_URL}/{conversation_id}",
            headers={"xi-api-key": API_KEY},
        )
        status = conv_response.json().get("status")
        if status in ("done", "failed"):
            break

    conv_data = conv_response.json()
    transcript = [
        {"role": turn["role"], "message": turn["message"]}
        for turn in conv_data.get("transcript", [])
    ]

    return jsonify({
        "conversation_id": conversation_id,
        "status": conv_data["status"],
        "transcript": transcript,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
