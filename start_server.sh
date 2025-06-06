#!/bin/bash

# ******************** Teaching Assistant API Server Startup ********************#
# Start the Teaching Assistant API server with Ollama configuration
echo "Starting Teaching Assistant API server with Ollama configuration..."

# ******************** environment setup ********************#
# Unset any existing environment variables that might conflict
unset OPENAI_BASE_URL
unset OPENAI_API_KEY

# ******************** directory and environment setup ********************#
# Change to the project directory
cd "$(dirname "$0")"

# ******************** environment verification ********************#
echo "Environment check:"
if [ -f .env ]; then
    echo "OPENAI_BASE_URL: $(grep OPENAI_BASE_URL .env | cut -d'=' -f2)"
    echo "OPENAI_API_KEY: $(grep OPENAI_API_KEY .env | cut -d'=' -f2)"
else
    echo "No .env file found - using default configuration"
fi

# ******************** server startup ********************#
# Start the server using UV
echo "Starting server with UV..."
echo "Using Python path modifications for organized API structure..."
PYTHONPATH="$PWD:$PYTHONPATH" uv run uvicorn api.main:app --host 0.0.0.0 --port 8000
