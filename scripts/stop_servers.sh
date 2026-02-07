#!/bin/bash
# Stop all running servers

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${RED}Stopping servers...${NC}\n"

# Function to stop a server
stop_server() {
    local name=$1
    local pidfile="logs/${name}.pid"

    if [ -f "$pidfile" ]; then
        local pid=$(cat "$pidfile")
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "Stopping $name (PID: $pid)..."
            kill $pid
            rm "$pidfile"
            echo -e "${GREEN}✓ $name stopped${NC}"
        else
            echo -e "${RED}✗ $name not running${NC}"
            rm "$pidfile"
        fi
    else
        echo -e "${RED}✗ $name PID file not found${NC}"
    fi
}

# Stop servers
stop_server "websocket-server"
stop_server "twiml-server"

echo -e "\n${GREEN}All servers stopped${NC}"
