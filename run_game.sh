#!/bin/bash

# Run script: Starts server and 2 clients for local testing
# Usage: ./run_game.sh

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SERVER_PID=""
CLIENT1_PID=""
CLIENT2_PID=""
SHUTDOWN_REQUESTED=false

cleanup() {
    if [ "$SHUTDOWN_REQUESTED" = true ]; then
        return
    fi
    SHUTDOWN_REQUESTED=true

    echo -e "\n${YELLOW}Shutting down all processes...${NC}"

    safe_kill() {
        local pid=$1
        local name=$2
        if [ ! -z "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo -n "Stopping $name (PID: $pid)... "
            kill -TERM "$pid" 2>/dev/null || true
            for i in {1..30}; do
                if ! kill -0 "$pid" 2>/dev/null; then
                    echo -e "${GREEN}stopped${NC}"
                    return 0
                fi
                sleep 0.1
            done
            if kill -0 "$pid" 2>/dev/null; then
                kill -KILL "$pid" 2>/dev/null || true
                echo -e "${YELLOW}force killed${NC}"
            fi
        fi
    }

    safe_kill "$CLIENT1_PID" "Client 1"
    safe_kill "$CLIENT2_PID" "Client 2"

    safe_kill "$SERVER_PID" "Server"

    echo -e "${GREEN}All processes stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

echo -e "${GREEN}Starting game server and clients...${NC}\n"

# Check for and kill any existing game processes
EXISTING_SERVER=$(ps aux | grep -E "python.*td_server" | grep -v grep | awk '{print $2}')
EXISTING_CLIENTS=$(ps aux | grep -E "python.*td_client" | grep -v grep | awk '{print $2}')

if [ ! -z "$EXISTING_SERVER" ] || [ ! -z "$EXISTING_CLIENTS" ]; then
    echo -e "${YELLOW}Found existing processes, cleaning up...${NC}"
    [ ! -z "$EXISTING_SERVER" ] && echo "$EXISTING_SERVER" | xargs kill -9 2>/dev/null || true
    [ ! -z "$EXISTING_CLIENTS" ] && echo "$EXISTING_CLIENTS" | xargs kill -9 2>/dev/null || true
    sleep 1
fi

if ! command -v python &> /dev/null; then
    echo -e "${RED}Error: python command not found${NC}"
    exit 1
fi

echo -e "${YELLOW}Starting server...${NC}"
python -m server.src.td_server.main &
SERVER_PID=$!
echo "Server started with PID: $SERVER_PID"

echo "Waiting for server to initialize..."
sleep 2

if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo -e "${RED}Error: Server failed to start${NC}"
    exit 1
fi

echo -e "${GREEN}Server is running${NC}\n"

echo -e "${YELLOW}Starting client 1...${NC}"
python -m client.src.td_client.main &
CLIENT1_PID=$!
echo "Client 1 started with PID: $CLIENT1_PID"

sleep 1

echo -e "${YELLOW}Starting client 2...${NC}"
python -m client.src.td_client.main &
CLIENT2_PID=$!
echo "Client 2 started with PID: $CLIENT2_PID"

echo -e "\n${GREEN}All processes started!${NC}"
echo -e "Server PID: $SERVER_PID"
echo -e "Client 1 PID: $CLIENT1_PID"
echo -e "Client 2 PID: $CLIENT2_PID"
echo -e "\nPress Ctrl+C to stop all processes\n"

wait