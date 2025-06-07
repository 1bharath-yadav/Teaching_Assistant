#!/bin/bash

# ******************** Next.js Frontend Startup Script ********************#
# Start the Teaching Assistant frontend (separate deployment)

echo "🌐 Starting Teaching Assistant Frontend (Separate Deployment)"

# ******************** Environment Setup ********************#
# Change to the frontend directory
cd "$(dirname "$0")/frontend"

# Load frontend environment variables
if [ -f .env.production ]; then
    echo "📄 Loading frontend environment variables..."
    set -a
    source .env.production
    set +a
else
    echo "⚠️  Warning: .env.production file not found. Using defaults."
fi

# ******************** Environment Verification ********************#
echo "🔧 Environment Configuration:"
echo "NEXT_PUBLIC_API_BASE_URL: ${NEXT_PUBLIC_API_BASE_URL:-http://localhost:8000}"
echo "NEXT_PUBLIC_API_ENDPOINT: ${NEXT_PUBLIC_API_ENDPOINT:-/api/v1/ask}"
echo "PORT: ${PORT:-3000}"
echo "NODE_ENV: ${NODE_ENV:-production}"

# ******************** Dependency Check ********************#
echo "📦 Checking Node.js and dependencies..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

# Check if npm/yarn is available
if command -v yarn &> /dev/null; then
    PACKAGE_MANAGER="yarn"
elif command -v npm &> /dev/null; then
    PACKAGE_MANAGER="npm"
else
    echo "❌ Neither npm nor yarn is available. Please install one."
    exit 1
fi

echo "📦 Using package manager: $PACKAGE_MANAGER"

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📥 Installing dependencies..."
    $PACKAGE_MANAGER install
fi

# ******************** Build Process ********************#
echo "🔨 Building frontend for production..."

# Clean previous builds
if [ -d ".next" ]; then
    echo "🧹 Cleaning previous build..."
    rm -rf .next
fi

# Build the application
if ! $PACKAGE_MANAGER run build; then
    echo "❌ Build failed. Please check the errors above."
    exit 1
fi

# ******************** Health Checks ********************#
echo "🏥 Performing pre-startup health checks..."

# Check if port is available
if lsof -Pi :${PORT:-3000} -sTCP:LISTEN -t >/dev/null; then
    echo "⚠️  Warning: Port ${PORT:-3000} is already in use."
    echo "Please stop the existing service or change the PORT."
    exit 1
fi

# Check if backend is accessible (optional)
echo "🔗 Checking backend connectivity..."
if curl -f "${NEXT_PUBLIC_API_BASE_URL:-http://localhost:8000}/health" >/dev/null 2>&1; then
    echo "✅ Backend is accessible"
else
    echo "⚠️  Warning: Backend is not accessible at ${NEXT_PUBLIC_API_BASE_URL:-http://localhost:8000}"
    echo "Make sure the backend is running before starting the frontend."
fi

# ******************** Start Server ********************#
echo "🎯 Starting Next.js frontend server..."
echo "📍 Frontend will be available at: http://localhost:${PORT:-3000}"
echo "🔗 Backend API: ${NEXT_PUBLIC_API_BASE_URL:-http://localhost:8000}"

# Start the Next.js production server
$PACKAGE_MANAGER start

echo "🛑 Frontend server stopped."
