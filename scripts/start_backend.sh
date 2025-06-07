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
echo "📦 Checking uv and Python dependencies..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source ~/.profile
    
    # Check if uv is now available
    if ! command -v uv &> /dev/null; then
        echo "❌ Failed to install uv. Please install manually:"
        echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    echo "✅ uv installed successfully"
fi

# Check dependencies from pyproject.toml
echo "📦 Verifying dependencies from pyproject.toml..."
uv sync || {
    echo "❌ Failed to sync dependencies. Please check pyproject.toml"
    exit 1
}
echo "✅ Dependencies verified and synced"

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

# Run the API server with uv (automatically manages environment)
# Convert LOG_LEVEL to lowercase for uvicorn compatibility
LOG_LEVEL_LOWER=$(echo "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')

if [ "${DEVELOPMENT:-false}" = "true" ]; then
    uv run -m uvicorn api.main_api_only:app \
        --host "${API_HOST:-0.0.0.0}" \
        --port "${API_PORT:-8000}" \
        --reload \
        --log-level="${LOG_LEVEL_LOWER}" \
        --access-log \
        --use-colors
else
    uv run -m uvicorn api.main_api_only:app \
        --host "${API_HOST:-0.0.0.0}" \
        --port "${API_PORT:-8000}" \
        --log-level="${LOG_LEVEL_LOWER}" \
        --access-log \
        --use-colors
fi

echo "🛑 Backend server stopped."
