#!/bin/bash

# ******************** Development Helper Script ********************#
# Manage separate deployment for development

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    echo "TDS Teaching Assistant - Separate Deployment Manager"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup         - Initial setup (install dependencies)"
    echo "  dev           - Start development servers"
    echo "  build         - Build both backend and frontend"
    echo "  start         - Start production servers"
    echo "  stop          - Stop all services"
    echo "  restart       - Restart all services"
    echo "  logs          - Show logs from all services"
    echo "  health        - Check health of all services"
    echo "  clean         - Clean build artifacts"
    echo "  docker        - Start with Docker Compose"
    echo "  docker-stop   - Stop Docker services"
    echo "  help          - Show this help message"
    echo ""
}

check_dependencies() {
    print_status "Checking dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed."
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is required but not installed."
        exit 1
    fi
    
    # Check package managers
    if command -v yarn &> /dev/null; then
        PACKAGE_MANAGER="yarn"
    elif command -v npm &> /dev/null; then
        PACKAGE_MANAGER="npm"
    else
        print_error "Neither npm nor yarn is available."
        exit 1
    fi
    
    print_success "Dependencies check passed"
}

setup_project() {
    print_status "Setting up TDS Teaching Assistant..."
    
    check_dependencies
    
    # Setup backend
    print_status "Setting up backend..."
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
    fi
    source .venv/bin/activate
    pip install uv
    uv pip install -r uv.lock
    
    # Setup frontend
    print_status "Setting up frontend..."
    cd frontend
    $PACKAGE_MANAGER install
    cd ..
    
    # Copy environment files
    if [ ! -f ".env.backend" ]; then
        print_status "Creating backend environment file..."
        cp .env.backend .env.backend.local 2>/dev/null || true
    fi
    
    if [ ! -f "frontend/.env.production" ]; then
        print_status "Creating frontend environment file..."
        cp frontend/.env.production frontend/.env.local 2>/dev/null || true
    fi
    
    print_success "Setup completed successfully!"
    print_warning "Please configure your environment files:"
    print_warning "  - .env.backend (backend configuration)"
    print_warning "  - frontend/.env.production (frontend configuration)"
}

start_dev() {
    print_status "Starting development servers..."
    
    # Start backend in background
    print_status "Starting backend server..."
    ./start_backend.sh &
    BACKEND_PID=$!
    
    # Wait a bit for backend to start
    sleep 5
    
    # Start frontend in background
    print_status "Starting frontend server..."
    ./start_frontend.sh &
    FRONTEND_PID=$!
    
    # Store PIDs for cleanup
    echo $BACKEND_PID > .backend.pid
    echo $FRONTEND_PID > .frontend.pid
    
    print_success "Development servers started!"
    print_status "Backend: http://localhost:8000"
    print_status "Frontend: http://localhost:3000"
    print_status "API Docs: http://localhost:8000/docs"
    
    # Wait for user to stop
    trap 'kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; rm -f .backend.pid .frontend.pid; exit' INT TERM
    wait
}

build_project() {
    print_status "Building project..."
    
    # Build frontend
    print_status "Building frontend..."
    cd frontend
    $PACKAGE_MANAGER run build
    cd ..
    
    print_success "Build completed!"
}

start_production() {
    print_status "Starting production servers..."
    
    # Check if built
    if [ ! -d "frontend/.next" ]; then
        print_warning "Frontend not built. Building now..."
        build_project
    fi
    
    # Start services
    ./start_backend.sh &
    BACKEND_PID=$!
    
    sleep 5
    
    ./start_frontend.sh &
    FRONTEND_PID=$!
    
    echo $BACKEND_PID > .backend.pid
    echo $FRONTEND_PID > .frontend.pid
    
    print_success "Production servers started!"
    
    # Wait for user to stop
    trap 'kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; rm -f .backend.pid .frontend.pid; exit' INT TERM
    wait
}

stop_services() {
    print_status "Stopping services..."
    
    if [ -f ".backend.pid" ]; then
        kill $(cat .backend.pid) 2>/dev/null || true
        rm -f .backend.pid
    fi
    
    if [ -f ".frontend.pid" ]; then
        kill $(cat .frontend.pid) 2>/dev/null || true
        rm -f .frontend.pid
    fi
    
    # Kill any remaining processes
    pkill -f "uvicorn.*main_api_only" 2>/dev/null || true
    pkill -f "next.*start" 2>/dev/null || true
    
    print_success "Services stopped!"
}

show_logs() {
    print_status "Showing logs..."
    print_warning "This is a basic implementation. For production, use proper logging."
    
    # Show recent logs if they exist
    if [ -f "backend.log" ]; then
        echo "=== Backend Logs ==="
        tail -50 backend.log
    fi
    
    if [ -f "frontend.log" ]; then
        echo "=== Frontend Logs ==="
        tail -50 frontend.log
    fi
}

check_health() {
    print_status "Checking service health..."
    
    # Check backend
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        print_success "Backend: Healthy"
    else
        print_error "Backend: Unhealthy or not running"
    fi
    
    # Check frontend
    if curl -f http://localhost:3000 >/dev/null 2>&1; then
        print_success "Frontend: Healthy"
    else
        print_error "Frontend: Unhealthy or not running"
    fi
}

clean_project() {
    print_status "Cleaning build artifacts..."
    
    # Clean frontend
    rm -rf frontend/.next
    rm -rf frontend/node_modules/.cache
    
    # Clean Python cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    
    print_success "Cleanup completed!"
}

start_docker() {
    print_status "Starting with Docker Compose..."
    
    if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
        print_error "Docker and Docker Compose are required."
        exit 1
    fi
    
    docker-compose -f docker-compose.separate.yml up --build
}

stop_docker() {
    print_status "Stopping Docker services..."
    docker-compose -f docker-compose.separate.yml down
    print_success "Docker services stopped!"
}

# Main command handler
case "${1:-help}" in
    setup)
        setup_project
        ;;
    dev)
        start_dev
        ;;
    build)
        build_project
        ;;
    start)
        start_production
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        sleep 2
        start_production
        ;;
    logs)
        show_logs
        ;;
    health)
        check_health
        ;;
    clean)
        clean_project
        ;;
    docker)
        start_docker
        ;;
    docker-stop)
        stop_docker
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
