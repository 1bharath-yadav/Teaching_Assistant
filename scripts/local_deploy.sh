#!/bin/bash

# ******************** Teaching Assistant Full Stack Local Runner ********************#
# Comprehensive script for building and running the full stack on Arch Linux
# Author: GitHub Copilot
# Date: $(date)

set -e  # Exit on any error
source "$(dirname "${BASH_SOURCE[0]}")/../.env" 2>/dev/null || true  # Load environment variables if available
# ******************** Configuration ********************#
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
API_PORT=${API_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-3000}
TYPESENSE_PORT=${TYPESENSE_PORT:-8108}
LOG_FILE="$PROJECT_ROOT/fullstack.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ******************** Utility Functions ********************#
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

# ******************** System Requirements Check ********************#
check_system_requirements() {
    log "🔍 Checking system requirements..."
    
    # Check if running on Arch Linux
    if ! grep -q "Arch Linux" /etc/os-release 2>/dev/null; then
        warn "This script is optimized for Arch Linux but will try to continue..."
    fi
    
    # Check required commands
    local missing_deps=()
    
    for cmd in node npm yarn python uv lsof pkill; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        error "Missing required dependencies: ${missing_deps[*]}
Please install them using: sudo pacman -S nodejs npm python python-pip
And install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    fi
    
    success "✅ System requirements check passed"
}

# ******************** Port Management ********************#
check_ports() {
    log "🔌 Checking port availability..."
    
    local ports=($API_PORT $FRONTEND_PORT $TYPESENSE_PORT)
    local occupied_ports=()
    
    for port in "${ports[@]}"; do
        if lsof -Pi ":$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
            occupied_ports+=("$port")
        fi
    done
    
    if [ ${#occupied_ports[@]} -ne 0 ]; then
        warn "The following ports are occupied: ${occupied_ports[*]}"
        read -p "Do you want to kill processes on these ports? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            for port in "${occupied_ports[@]}"; do
                info "Killing processes on port $port..."
                lsof -ti ":$port" | xargs kill -9 2>/dev/null || true
            done
        else
            error "Cannot proceed with occupied ports. Please free them manually or change port configuration."
        fi
    fi
    
    success "✅ Port availability check passed"
}

# ******************** Environment Setup ********************#
setup_environment() {
    log "🔧 Setting up environment..."
    
    cd "$PROJECT_ROOT"
    
    # Create log file
    touch "$LOG_FILE"
    
    # Check if .env files exist, create minimal ones if not
    if [ ! -f ".env" ]; then
        info "Creating basic .env file..."
        cat > .env << EOF
# Backend Configuration
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Typesense Configuration
TYPESENSE_API_KEY=conscious-field
TYPESENSE_HOST=localhost
TYPESENSE_PORT=8108
TYPESENSE_PROTOCOL=http

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEVELOPMENT=true
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite:///./teaching_assistant.db
EOF
        warn "Created basic .env file. Please update it with your API keys."
    fi
    
    # Frontend environment
    if [ ! -f "$FRONTEND_DIR/.env.local" ]; then
        info "Creating frontend environment file..."
        cat > "$FRONTEND_DIR/.env.local" << EOF
# TDS Teaching Assistant API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_API_ENDPOINT=/api/v1/ask

# Development Configuration
NODE_ENV=development
PORT=3000
EOF
    fi
    
    success "✅ Environment setup completed"
}

# ******************** Backend Setup ********************#
setup_backend() {
    log "🐍 Setting up Python backend..."
    
    cd "$PROJECT_ROOT"
    
    # Check if uv environment exists and is working
    if ! uv --version &> /dev/null; then
        error "uv is not installed or not in PATH. Please install it first."
    fi
    
    # Install/sync dependencies
    info "Installing Python dependencies with uv..."
    uv sync --all-extras || error "Failed to sync Python dependencies"
    
    # Verify key dependencies
    info "Verifying Python dependencies..."
    uv run python -c "
import fastapi
import uvicorn
import typesense
print('✅ All core dependencies available')
" || error "Missing critical Python dependencies"
    
    success "✅ Backend setup completed"
}

# ******************** Frontend Setup ********************#
setup_frontend() {
    log "🌐 Setting up Next.js frontend..."
    
    cd "$FRONTEND_DIR"
    
    # Check if node_modules exists and package.json is newer
    if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules" ]; then
        info "Installing Node.js dependencies..."
        yarn install || error "Failed to install frontend dependencies"
    else
        info "Node.js dependencies are up to date"
    fi
    
    # Check if Next.js build exists
    if [ ! -d ".next" ] || [ "package.json" -nt ".next" ]; then
        info "Building Next.js application..."
        yarn build || error "Failed to build frontend"
    else
        info "Next.js build is up to date"
    fi
    
    success "✅ Frontend setup completed"
}

# ******************** Typesense Check ********************#
check_typesense() {
    log "🔍 Checking Typesense server..."
    
    # Check if Typesense is running
    if curl -s "http://localhost:$TYPESENSE_PORT/health" > /dev/null 2>&1; then
        success "✅ Typesense server is running"
        return 0
    fi
    
    # Try to start Typesense if available
    if command -v typesense-server &> /dev/null; then
        info "Starting Typesense server (native binary)..."
        # Create typesense data directory if it doesn't exist
        mkdir -p "$PROJECT_ROOT/typesense-data"
        
        # Start Typesense using native binary
        typesense-server \
            --data-dir "$PROJECT_ROOT/typesense-data" \
            --api-key="${TYPESENSE_API_KEY}" \
            --listen-port=$TYPESENSE_PORT \
            --enable-cors \
            --enable-access-logging \
            --enable-search-logging \
            --api-address 0.0.0.0 > "$PROJECT_ROOT/typesense.log" 2>&1 &
        
        local typesense_pid=$!
        echo $typesense_pid > "$PROJECT_ROOT/typesense.pid"
        
        
        # Wait for Typesense to start
        local retries=10
        while [ $retries -gt 0 ]; do
            if curl -s "http://localhost:$TYPESENSE_PORT/health" > /dev/null 2>&1; then
                success "✅ Typesense server started successfully"
                return 0
            fi
            sleep 1
            ((retries--))
        done
        
        error "Failed to start Typesense server"
    else
        warn "Typesense server not found. Install it with: yay -S typesense"
        warn "Or use the existing script: ./start_typesense.sh"
        read -p "Continue without Typesense? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            error "Typesense is required for full functionality"
        fi
    fi
}

# ******************** Service Management ********************#
start_backend() {
    log "🚀 Starting Python backend..."
    
    cd "$PROJECT_ROOT"
    
    # Start backend in background
    info "Launching FastAPI server on port $API_PORT..."
    uv run uvicorn api.main:app \
        --host 0.0.0.0 \
        --port $API_PORT \
        --reload \
        --reload-dir api \
        --log-level info > "$PROJECT_ROOT/backend.log" 2>&1 &
    
    local backend_pid=$!
    echo $backend_pid > "$PROJECT_ROOT/backend.pid"
    
    # Wait for backend to start
    local retries=30  # Increase timeout to 30 seconds
    while [ $retries -gt 0 ]; do
        if curl -s "http://localhost:$API_PORT/health" > /dev/null 2>&1; then
            success "✅ Backend started successfully (PID: $backend_pid)"
            return 0
        fi
        info "Waiting for backend to start... ($retries seconds remaining)"
        sleep 1
        ((retries--))
    done
    
    # Even if we didn't get a successful health check, check if the process is running
    if ps -p $backend_pid > /dev/null 2>&1; then
        warn "Backend process is running but health check failed. Continuing anyway..."
        return 0
    fi
    
    error "Backend failed to start. Check $PROJECT_ROOT/backend.log for details."
}

start_frontend() {
    log "🌐 Starting Next.js frontend..."
    
    cd "$FRONTEND_DIR"
    
    # Start frontend in background
    info "Launching Next.js server on port $FRONTEND_PORT..."
    yarn start -p $FRONTEND_PORT > "$PROJECT_ROOT/frontend.log" 2>&1 &
    
    local frontend_pid=$!
    echo $frontend_pid > "$PROJECT_ROOT/frontend.pid"
    
    # Wait for frontend to start
    local retries=20
    while [ $retries -gt 0 ]; do
        if curl -s "http://localhost:$FRONTEND_PORT" > /dev/null 2>&1; then
            success "✅ Frontend started successfully (PID: $frontend_pid)"
            return 0
        fi
        sleep 1
        ((retries--))
    done
    
    error "Frontend failed to start. Check $PROJECT_ROOT/frontend.log for details."
}

# ******************** Cleanup Functions ********************#
cleanup() {
    log "🧹 Cleaning up processes..."
    
    # Kill backend
    if [ -f "$PROJECT_ROOT/backend.pid" ]; then
        local backend_pid=$(cat "$PROJECT_ROOT/backend.pid")
        kill $backend_pid 2>/dev/null || true
        rm -f "$PROJECT_ROOT/backend.pid"
        info "Backend process stopped"
    fi
    
    # Kill frontend
    if [ -f "$PROJECT_ROOT/frontend.pid" ]; then
        local frontend_pid=$(cat "$PROJECT_ROOT/frontend.pid")
        kill $frontend_pid 2>/dev/null || true
        rm -f "$PROJECT_ROOT/frontend.pid"
        info "Frontend process stopped"
    fi
    
    # Kill any remaining processes on our ports
    for port in $API_PORT $FRONTEND_PORT; do
        lsof -ti ":$port" | xargs kill -9 2>/dev/null || true
    done
    
    # Stop Typesense if running natively
    if [ -f "$PROJECT_ROOT/typesense.pid" ]; then
        local typesense_pid=$(cat "$PROJECT_ROOT/typesense.pid")
        kill $typesense_pid 2>/dev/null || true
        rm -f "$PROJECT_ROOT/typesense.pid"
        info "Typesense process stopped"
    fi
    
    # Stop and remove Docker containers if they exist (fallback)
    if command -v docker &> /dev/null; then
        docker stop typesense-tds 2>/dev/null || true
        docker rm typesense-tds 2>/dev/null || true
    fi
    
    success "✅ Cleanup completed"
}

# ******************** Status Check ********************#
check_status() {
    echo
    log "📊 Service Status Check:"
    
    # Backend status
    if curl -s "http://localhost:$API_PORT/health" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅ Backend${NC} - http://localhost:$API_PORT"
    else
        echo -e "  ${RED}❌ Backend${NC} - http://localhost:$API_PORT"
    fi
    
    # Frontend status
    if curl -s "http://localhost:$FRONTEND_PORT" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅ Frontend${NC} - http://localhost:$FRONTEND_PORT"
    else
        echo -e "  ${RED}❌ Frontend${NC} - http://localhost:$FRONTEND_PORT"
    fi
    
    # Typesense status
    if curl -s "http://localhost:$TYPESENSE_PORT/health" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅ Typesense${NC} - http://localhost:$TYPESENSE_PORT"
    else
        echo -e "  ${RED}❌ Typesense${NC} - http://localhost:$TYPESENSE_PORT"
    fi
}

# ******************** Main Execution ********************#
show_banner() {
    echo -e "${CYAN}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║              Teaching Assistant Full Stack Runner             ║"
    echo "║                        Arch Linux Edition                     ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  start     - Start the full stack (default)"
    echo "  stop      - Stop all services"
    echo "  restart   - Restart all services"
    echo "  status    - Check service status"
    echo "  logs      - Show logs"
    echo "  clean     - Clean build artifacts"
    echo "  help      - Show this help message"
    echo
    echo "Environment Variables:"
    echo "  API_PORT       - Backend port (default: 8000)"
    echo "  FRONTEND_PORT  - Frontend port (default: 3000)"
    echo "  TYPESENSE_PORT - Typesense port (default: 8108)"
}

# ******************** Command Handlers ********************#
cmd_start() {
    show_banner
    log "🚀 Starting Teaching Assistant Full Stack..."
    
    check_system_requirements
    check_ports
    setup_environment
    check_typesense
    setup_backend
    setup_frontend
    start_backend
    start_frontend
    
    echo
    success "🎉 Full stack started successfully!"
    echo
    echo -e "${CYAN}Access your application:${NC}"
    echo -e "  📱 Frontend: ${GREEN}http://localhost:$FRONTEND_PORT${NC}"
    echo -e "  🔧 API:      ${GREEN}http://localhost:$API_PORT${NC}"
    echo -e "  📊 Docs:     ${GREEN}http://localhost:$API_PORT/docs${NC}"
    echo
    echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
    
    # Setup signal handlers
    trap cleanup EXIT INT TERM
    
    # Monitor services
    while true; do
        sleep 10
        check_status
    done
}

cmd_stop() {
    log "🛑 Stopping all services..."
    cleanup
}

cmd_restart() {
    log "🔄 Restarting full stack..."
    cmd_stop
    sleep 2
    cmd_start
}

cmd_status() {
    show_banner
    check_status
}

cmd_logs() {
    echo "📋 Showing logs (press Ctrl+C to exit)..."
    echo
    tail -f "$LOG_FILE" "$PROJECT_ROOT/backend.log" "$PROJECT_ROOT/frontend.log" 2>/dev/null
}

cmd_clean() {
    log "🧹 Cleaning build artifacts..."
    
    # Stop services first
    cleanup
    
    # Clean Python cache
    find "$PROJECT_ROOT" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$PROJECT_ROOT" -type f -name "*.pyc" -delete 2>/dev/null || true
    
    # Clean Next.js build
    rm -rf "$FRONTEND_DIR/.next" "$FRONTEND_DIR/out" 2>/dev/null || true
    
    # Clean logs
    rm -f "$PROJECT_ROOT"/*.log "$PROJECT_ROOT"/*.pid 2>/dev/null || true
    
    success "✅ Cleanup completed"
}

# ******************** Main Script Logic ********************#
case "${1:-start}" in
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_restart
        ;;
    status)
        cmd_status
        ;;
    logs)
        cmd_logs
        ;;
    clean)
        cmd_clean
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        echo "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac
