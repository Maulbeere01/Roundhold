#!/bin/bash

# Removes Python cache and kills any leftover game processes

echo "Cleaning up Python cache..."
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true

echo "Checking for leftover game processes..."
SERVER_PIDS=$(ps aux | grep -E "python.*td_server" | grep -v grep | awk '{print $2}')
CLIENT_PIDS=$(ps aux | grep -E "python.*td_client" | grep -v grep | awk '{print $2}')

if [ ! -z "$SERVER_PIDS" ] || [ ! -z "$CLIENT_PIDS" ]; then
    echo "Found leftover processes:"
    [ ! -z "$SERVER_PIDS" ] && echo "  Server PIDs: $SERVER_PIDS"
    [ ! -z "$CLIENT_PIDS" ] && echo "  Client PIDs: $CLIENT_PIDS"
    echo "Killing them..."
    [ ! -z "$SERVER_PIDS" ] && echo "$SERVER_PIDS" | xargs kill -9 2>/dev/null || true
    [ ! -z "$CLIENT_PIDS" ] && echo "$CLIENT_PIDS" | xargs kill -9 2>/dev/null || true
    echo "Done."
else
    echo "No leftover processes found."
fi

echo "Cleanup complete!"
