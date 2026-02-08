#!/usr/bin/env python3
"""
Simple TwiML Configuration Server

Serves TwiML XML that routes incoming Twilio calls to the WebSocket server.

Usage:
    python twilio/twilio_server_simple.py

Environment Variables:
    WEBSOCKET_URL - Public URL for WebSocket server (e.g., from cloudflare tunnel)
"""

import os
import sys
from pathlib import Path
from flask import Flask, Response, request
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

app = Flask(__name__)

# Get WebSocket URL from environment
WEBSOCKET_URL = os.getenv('WEBSOCKET_URL', 'localhost:5001')

# Ensure proper protocol
if not WEBSOCKET_URL.startswith('ws://') and not WEBSOCKET_URL.startswith('wss://'):
    # Use wss:// for HTTPS domains, ws:// for localhost
    if 'localhost' in WEBSOCKET_URL or '127.0.0.1' in WEBSOCKET_URL:
        WEBSOCKET_URL = f'ws://{WEBSOCKET_URL}'
    else:
        WEBSOCKET_URL = f'wss://{WEBSOCKET_URL}'

# Ensure path
if not WEBSOCKET_URL.endswith('/media-stream'):
    WEBSOCKET_URL = f'{WEBSOCKET_URL}/media-stream'


@app.route('/voice', methods=['POST', 'GET'])
def voice():
    """
    TwiML endpoint for incoming calls

    Returns TwiML that connects the call to WebSocket server
    """
    print(f"\n📞 Incoming call from: {request.values.get('From', 'Unknown')}")
    print(f"   To: {request.values.get('To', 'Unknown')}")
    print(f"   Routing to: {WEBSOCKET_URL}")

    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{WEBSOCKET_URL}" />
    </Connect>
</Response>'''

    return Response(twiml, mimetype='text/xml')


@app.route('/voice.xml', methods=['GET'])
def voice_xml():
    """Alternative endpoint (static XML)"""
    return voice()


@app.route('/status', methods=['POST'])
def status():
    """
    Status callback endpoint

    Twilio sends status updates here
    """
    call_sid = request.values.get('CallSid')
    call_status = request.values.get('CallStatus')

    print(f"📊 Call status: {call_sid} - {call_status}")

    return Response('OK', mimetype='text/plain')


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'websocket_url': WEBSOCKET_URL
    }


@app.route('/', methods=['GET'])
def index():
    """Root endpoint with information"""
    return f'''
    <html>
        <head><title>Twilio Voice Server</title></head>
        <body>
            <h1>Twilio Voice Server</h1>
            <p><strong>Status:</strong> Running</p>
            <p><strong>WebSocket URL:</strong> {WEBSOCKET_URL}</p>
            <h2>Endpoints:</h2>
            <ul>
                <li><code>/voice</code> - TwiML endpoint for calls</li>
                <li><code>/voice.xml</code> - Alternative TwiML endpoint</li>
                <li><code>/status</code> - Call status callback</li>
                <li><code>/health</code> - Health check</li>
            </ul>
            <h2>Setup Instructions:</h2>
            <ol>
                <li>Ensure WebSocket server is running on {WEBSOCKET_URL}</li>
                <li>Expose this server with ngrok/cloudflare: <code>cloudflared tunnel --url http://localhost:5050</code></li>
                <li>Configure Twilio phone number webhook to: <code>https://YOUR-DOMAIN/voice</code></li>
            </ol>
        </body>
    </html>
    '''


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="TwiML Configuration Server"
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host to bind to (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5050,
        help='Port to listen on (default: 5050)'
    )
    parser.add_argument(
        '--websocket-url',
        help='Override WebSocket URL (default: from WEBSOCKET_URL env var)'
    )

    args = parser.parse_args()

    # Override WebSocket URL if provided
    if args.websocket_url:
        global WEBSOCKET_URL
        WEBSOCKET_URL = args.websocket_url
        if not WEBSOCKET_URL.endswith('/media-stream'):
            WEBSOCKET_URL = f'{WEBSOCKET_URL}/media-stream'

    print("\n" + "="*70)
    print("🌐 TwiML Configuration Server")
    print("="*70)
    print(f"\nServer URL: http://{args.host}:{args.port}")
    print(f"WebSocket URL: {WEBSOCKET_URL}")
    print(f"\nEndpoints:")
    print(f"  - http://{args.host}:{args.port}/voice (TwiML)")
    print(f"  - http://{args.host}:{args.port}/health (Health check)")
    print(f"\nSetup:")
    print(f"  1. Start WebSocket server: python twilio/twilio_voice_server.py")
    print(f"  2. Expose with tunnel: cloudflared tunnel --url http://localhost:5050")
    print(f"  3. Configure Twilio webhook to tunnel URL + /voice")
    print(f"\nPress Ctrl+C to stop\n")

    try:
        app.run(host=args.host, port=args.port, debug=False)
    except KeyboardInterrupt:
        print("\n\n⚠️  Server stopped by user")


if __name__ == '__main__':
    main()
