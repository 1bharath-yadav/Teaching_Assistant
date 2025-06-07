#!/usr/bin/env zsh

# setup.sh - Complete setup script for TDS Teaching Assistant
# Run this script to set up the entire project from scratch

set -e  # Exit on error

# Get the project root directory
PROJECT_ROOT=$(pwd)

# Print colored output
print_green() {
  echo "\033[0;32m$1\033[0m"
}

print_blue() {
  echo "\033[0;34m$1\033[0m"
}

print_yellow() {
  echo "\033[0;33m$1\033[0m"
}

# Welcome message
print_blue "============================================================"
print_blue "🎓 TDS Teaching Assistant - Complete Setup"
print_blue "============================================================"
echo

# Check for required tools
print_yellow "Checking for required tools..."

# Check for Python
if ! command -v python3 &> /dev/null; then
  echo "❌ Python 3 not found. Please install Python 3.9 or higher."
  exit 1
fi
print_green "✓ Python 3 found: $(python3 --version)"

# Check for uv
if ! command -v uv &> /dev/null; then
  echo "❌ UV package manager not found. Installing..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
else
  print_green "✓ UV package manager found: $(uv --version)"
fi

# Check for Node.js
if ! command -v node &> /dev/null; then
  echo "❌ Node.js not found. Please install Node.js 16 or higher."
  exit 1
fi
print_green "✓ Node.js found: $(node --version)"

# Check for npm
if ! command -v npm &> /dev/null; then
  echo "❌ npm not found. Please install npm."
  exit 1
fi
print_green "✓ npm found: $(npm --version)"

# Check for Docker
if ! command -v docker &> /dev/null; then
  echo "⚠️ Docker not found. Docker deployment won't be available."
else
  print_green "✓ Docker found: $(docker --version)"
fi

# Setup environment files
print_yellow "\nSetting up environment files..."

if [ ! -f "$PROJECT_ROOT/.env" ]; then
  if [ -f "$PROJECT_ROOT/.env.example" ]; then
    cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
    print_green "✓ Created .env file from template"
    print_yellow "⚠️ Please edit .env file with your own values"
  elif [ -f "$PROJECT_ROOT/.env.unified" ]; then
    cp "$PROJECT_ROOT/.env.unified" "$PROJECT_ROOT/.env"
    print_green "✓ Created .env file from unified template"
    print_yellow "⚠️ Please edit .env file with your own values"
  else
    echo "❌ No environment template file found"
  fi
else
  print_green "✓ .env file already exists"
fi

# Install Python dependencies
print_yellow "\nInstalling Python dependencies..."
uv pip install -e .
print_green "✓ Python dependencies installed"

# Install frontend dependencies
print_yellow "\nInstalling frontend dependencies..."
(cd "$PROJECT_ROOT/frontend" && npm install)
print_green "✓ Frontend dependencies installed"

# Start Typesense
print_yellow "\nStarting Typesense service..."
"$PROJECT_ROOT/scripts/start_typesense.sh" &
TYPESENSE_PID=$!
sleep 5  # Give Typesense some time to start
print_green "✓ Typesense started"

# Run initial setup
print_yellow "\nRunning initial setup..."
"$PROJECT_ROOT/scripts/manage_separate.sh" setup
print_green "✓ Initial setup completed"

print_blue "\n============================================================"
print_blue "🎉 Setup completed successfully!"
print_blue "============================================================"
echo
print_green "To start the development server:"
echo "  ./scripts/manage_separate.sh dev"
echo
print_green "To start the production server:"
echo "  ./scripts/manage_separate.sh start"
echo
print_green "To deploy with Docker:"
echo "  docker-compose -f docker/docker-compose.separate.yml up"
echo
print_green "To run tests:"
echo "  pytest"
echo
print_yellow "For more information, see the README.md file."
echo
