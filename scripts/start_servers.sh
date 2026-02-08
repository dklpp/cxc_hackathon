#!/bin/bash
# Start all servers for Twilio voice chat integration

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Starting Twilio Voice Chat Servers${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not activated${NC}"
    echo "Activating .venv..."
    source .venv/bin/activate
fi

# Check environment variables
if [ -z "$OPENAI_API_KEY" ] || [ -z "$ELEVEN_LABS_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  API keys not set in environment${NC}"
    echo "Loading from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Function to start a server in background
start_server() {
    local name=$1
    local command=$2
    local port=$3

    echo -e "${GREEN}Starting $name on port $port...${NC}"
    $command > logs/${name}.log 2>&1 &
    local pid=$!
    echo $pid > logs/${name}.pid
    echo -e "  PID: $pid"
    echo -e "  Logs: logs/${name}.log\n"
}

# Create logs directory
mkdir -p logs

# Start WebSocket server (port 5001)
start_server "websocket-server" "python twilio/twilio_voice_server.py" "5001"

# Wait a bit for WebSocket server to start
sleep 2

# Start TwiML server (port 5000)
start_server "twiml-server" "python twilio/twilio_server_simple.py" "5050"

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ All servers started!${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo "Next steps:"
echo "1. Expose servers with cloudflare tunnel:"
echo "   ${YELLOW}cloudflared tunnel --url http://localhost:5050${NC}"
echo ""
echo "2. Configure Twilio webhook to tunnel URL + /voice"
echo ""
echo "3. Make a test call or check server status:"
echo "   ${YELLOW}curl http://localhost:5050/health${NC}"
echo ""
echo "To stop servers:"
echo "   ${YELLOW}./scripts/stop_servers.sh${NC}"
echo ""
echo "View logs:"
echo "   ${YELLOW}tail -f logs/websocket-server.log${NC}"
echo "   ${YELLOW}tail -f logs/twiml-server.log${NC}"
