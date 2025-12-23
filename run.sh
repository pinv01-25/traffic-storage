#!/bin/bash

# Kill any existing process on port 8000
echo "Stopping any existing traffic-storage service..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Wait a moment for cleanup
sleep 2

echo "Starting traffic-storage service..."
echo "Press Ctrl+C to stop the service gracefully"

# Start the service with proper signal handling
trap 'echo "Received interrupt signal, shutting down..."; exit 0' INT TERM

uv run uvicorn api.server:app --reload --port 8000
