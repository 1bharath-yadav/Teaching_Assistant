#!/usr/bin/env bash

# Project structure optimizer for TDS Teaching Assistant
# Run this script to organize and clean up the project structure

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

echo "🧹 Starting project structure optimization..."

# Create necessary directories if they don't exist
mkdir -p "$PROJECT_ROOT"/{scripts,logs,docker,docs,tests/{unit,integration}}

# Move scripts to scripts directory
echo "📁 Organizing script files..."
find "$PROJECT_ROOT" -maxdepth 1 -name "*.sh" -exec mv {} "$PROJECT_ROOT/scripts/" \;

# Move Docker files to docker directory
echo "🐳 Organizing Docker files..."
find "$PROJECT_ROOT" -maxdepth 1 -name "Dockerfile*" -exec mv {} "$PROJECT_ROOT/docker/" \;
find "$PROJECT_ROOT" -maxdepth 1 -name "docker-compose*" -exec mv {} "$PROJECT_ROOT/docker/" \;
[ -f "$PROJECT_ROOT/nginx.conf" ] && mv "$PROJECT_ROOT/nginx.conf" "$PROJECT_ROOT/docker/"

# Move documentation to docs directory
echo "📚 Organizing documentation files..."
find "$PROJECT_ROOT" -maxdepth 1 -name "*.md" -not -name "README.md" -not -name "LICENSE.md" -exec mv {} "$PROJECT_ROOT/docs/" \;

# Move log files to logs directory
echo "📝 Organizing log files..."
find "$PROJECT_ROOT" -maxdepth 1 -name "*.log" -exec mv {} "$PROJECT_ROOT/logs/" \;

# Remove empty directories
echo "🗑️ Cleaning up empty directories..."
find "$PROJECT_ROOT" -type d -empty -delete

# Create .env.example if it doesn't exist
if [ ! -f "$PROJECT_ROOT/.env.example" ] && [ -f "$PROJECT_ROOT/.env" ]; then
    echo "📄 Creating .env.example from .env..."
    cat "$PROJECT_ROOT/.env" | sed 's/=.*/=your_value_here/g' > "$PROJECT_ROOT/.env.example"
fi

echo "✨ Project structure optimization complete!"
echo "Project structure is now clean and organized."
