#!/bin/bash

# ******************** FastAPI Backend Startup Script ********************#
# Start the Teaching Assistant API backend (API-only mode)

echo "🚀 Starting Teaching Assistant API Backend (Separate Deployment)"

# ******************** Environment Setup ********************#
# Change to the project directory
cd "$(dirname "$0")/.."

# Load backend environment variables
if [ -f .env.backend ]; then
    echo "📄 Loading backend environment variables..."
    set -a
    source .env.backend
    set +a
else
    echo "⚠️  Warning: .env.backend file not found. Using defaults."
fi

# ******************** Environment Verification ********************#
echo "🔧 Environment Configuration:"
echo "API_HOST: ${API_HOST:-0.0.0.0}"
echo "API_PORT: ${API_PORT:-8000}"
echo "DEVELOPMENT: ${DEVELOPMENT:-false}"
echo "LOG_LEVEL: ${LOG_LEVEL:-INFO}"

# ******************** Virtual Environment Setup ********************#
if [ -d ".venv" ]; then
    echo "🐍 Activating virtual environment..."
    source .venv/bin/activate
else
    echo "⚠️  Warning: Virtual environment not found. Make sure dependencies are installed."
fi

# ******************** Dependency Check ********************#
echo "📦 Checking Python dependencies..."
python -c "import fastapi, uvicorn" 2>/dev/null || {
    echo "❌ Missing required dependencies. Please install them:"
    echo "   pip install fastapi uvicorn"
    exit 1
}

# ******************** Health Checks ********************#
echo "🏥 Performing pre-startup health checks..."

# Check if port is available
if lsof -Pi :${API_PORT:-8000} -sTCP:LISTEN -t >/dev/null; then
    echo "⚠️  Warning: Port ${API_PORT:-8000} is already in use."
    echo "Please stop the existing service or change the API_PORT."
    exit 1
fi

# ******************** Start Server ********************#
echo "🎯 Starting FastAPI backend server..."
echo "📍 API will be available at: http://${API_HOST:-0.0.0.0}:${API_PORT:-8000}"
echo "📚 API Documentation: http://${API_HOST:-0.0.0.0}:${API_PORT:-8000}/docs"
echo "🔍 Health Check: http://${API_HOST:-0.0.0.0}:${API_PORT:-8000}/health"

# Run the API server
python -m uvicorn api.main_api_only:app \
    --host "${API_HOST:-0.0.0.0}" \
    --port "${API_PORT:-8000}" \
    --reload="${DEVELOPMENT:-false}" \
    --log-level="${LOG_LEVEL:-info}" \
    --access-log \
    --use-colors

echo "🛑 Backend server stopped."
