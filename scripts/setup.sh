#!/bin/bash
# APIC - Automated Installation Script
# This script handles the complete installation and setup of APIC

set -e  # Exit on error

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="${PROJECT_ROOT}/.venv"
PYTHON_MIN_VERSION="3.11"
LOG_FILE="${PROJECT_ROOT}/logs/install.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Helper Functions
# ============================================================================

log() {
    echo -e "${BLUE}[INFO]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1" >> "$LOG_FILE" 2>/dev/null || true
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $1" >> "$LOG_FILE" 2>/dev/null || true
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1" >> "$LOG_FILE" 2>/dev/null || true
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >> "$LOG_FILE" 2>/dev/null || true
}

# ============================================================================
# Prerequisite Checks
# ============================================================================

check_python() {
    log "Checking Python version..."

    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')

        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
            success "Python $PYTHON_VERSION found"
            return 0
        else
            error "Python $PYTHON_VERSION found, but Python >= $PYTHON_MIN_VERSION is required"
            return 1
        fi
    else
        error "Python 3 not found. Please install Python >= $PYTHON_MIN_VERSION"
        return 1
    fi
}

check_pip() {
    log "Checking pip..."

    if command -v pip3 &> /dev/null || command -v pip &> /dev/null; then
        success "pip found"
        return 0
    else
        error "pip not found. Please install pip"
        return 1
    fi
}

check_postgres() {
    log "Checking PostgreSQL client..."

    if command -v psql &> /dev/null; then
        success "PostgreSQL client found"
        return 0
    else
        error "PostgreSQL client not found. Please install PostgreSQL (e.g., 'sudo apt install postgresql-client' or 'brew install postgresql')"
        return 1
    fi
}

check_docker() {
    log "Checking Docker..."

    if command -v docker &> /dev/null; then
        if docker info &> /dev/null; then
            success "Docker found and running"
            return 0
        else
            warning "Docker found but not running"
            return 1
        fi
    else
        warning "Docker not found (optional for local development)"
        return 0  # Not a hard requirement
    fi
}

stop_existing_containers() {
    log "Checking for existing APIC containers..."

    # Define APIC container names
    local containers=("apic-postgres" "apic-api" "apic-frontend")
    local stopped_any=false

    for container in "${containers[@]}"; do
        # Check if container exists and is running
        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            log "Stopping running container: $container"
            docker stop "$container" &> /dev/null
            stopped_any=true
        fi
    done

    # Also stop any containers from docker-compose in this project
    if [ -f "${PROJECT_ROOT}/docker-compose.yml" ]; then
        # Check if any project containers are running via docker-compose
        cd "$PROJECT_ROOT"
        local running_services
        running_services=$(docker-compose ps --services --filter "status=running" 2>/dev/null || true)
        if [ -n "$running_services" ]; then
            log "Stopping existing docker-compose services..."
            docker-compose stop &> /dev/null
            stopped_any=true
        fi
    fi

    if [ "$stopped_any" = true ]; then
        success "Existing containers stopped"
    else
        log "No existing APIC containers running"
    fi
}

# ============================================================================
# Setup Functions
# ============================================================================

create_directories() {
    log "Creating required directories..."

    mkdir -p "${PROJECT_ROOT}/uploads"
    mkdir -p "${PROJECT_ROOT}/reports"
    mkdir -p "${PROJECT_ROOT}/logs"

    success "Directories created"
}

setup_environment() {
    log "Setting up environment file..."

    if [ ! -f "${PROJECT_ROOT}/.env" ]; then
        if [ -f "${PROJECT_ROOT}/.env.example" ]; then
            cp "${PROJECT_ROOT}/.env.example" "${PROJECT_ROOT}/.env"
            success "Created .env from .env.example"
        else
            error ".env.example not found"
            return 1
        fi
    else
        warning ".env already exists, skipping"
    fi
}

create_virtualenv() {
    log "Creating virtual environment..."

    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
        success "Virtual environment created at $VENV_DIR"
    else
        warning "Virtual environment already exists"
    fi
}

install_dependencies() {
    log "Installing Python dependencies..."

    if [ -d "$VENV_DIR" ]; then
        source "${VENV_DIR}/bin/activate"
        pip install --upgrade pip
        pip install -r "${PROJECT_ROOT}/requirements.txt"
        deactivate
    else
        pip3 install --upgrade pip
        pip3 install -r "${PROJECT_ROOT}/requirements.txt"
    fi

    success "Dependencies installed"
}

initialize_database() {
    log "Initializing database..."

    if [ -f "${PROJECT_ROOT}/scripts/init_db.py" ]; then
        if [ -d "$VENV_DIR" ]; then
            source "${VENV_DIR}/bin/activate"
            python "${PROJECT_ROOT}/scripts/init_db.py"
            deactivate
        else
            python3 "${PROJECT_ROOT}/scripts/init_db.py"
        fi
        success "Database initialized"
    else
        warning "init_db.py not found, skipping database initialization"
    fi
}

run_health_check() {
    log "Running health check..."

    cd "$PROJECT_ROOT"

    if [ -d "$VENV_DIR" ]; then
        source "${VENV_DIR}/bin/activate"
        python -c "from scripts.install_utils import HealthChecker; h = HealthChecker(); r = h.run_all_checks(); print(f'Status: {r[\"overall_status\"]}')"
        deactivate
    else
        python3 -c "from scripts.install_utils import HealthChecker; h = HealthChecker(); r = h.run_all_checks(); print(f'Status: {r[\"overall_status\"]}')"
    fi
}

# ============================================================================
# Main Installation Flow
# ============================================================================

usage() {
    echo "APIC Installation Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --full          Run full installation (default)"
    echo "  --quick         Quick setup (directories and env only)"
    echo "  --docker        Docker-based installation"
    echo "  --check         Run prerequisites check only"
    echo "  --health        Run health check only"
    echo "  --help          Show this help message"
    echo ""
}

full_install() {
    echo ""
    echo "=================================================="
    echo "APIC - Full Installation"
    echo "=================================================="
    echo ""

    # Create log directory first
    mkdir -p "${PROJECT_ROOT}/logs"

    # Prerequisites
    check_python || exit 1
    check_pip || exit 1
    check_postgres || exit 1
    check_docker

    echo ""
    log "Starting installation..."
    echo ""

    # Setup
    create_directories
    setup_environment
    create_virtualenv
    install_dependencies

    # Optional: Database setup
    read -p "Initialize database? [y/N] " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        initialize_database
    fi

    echo ""
    run_health_check

    echo ""
    echo "=================================================="
    success "Installation complete!"
    echo "=================================================="
    echo ""
    echo "Next steps:"
    echo "  1. Edit .env file with your API keys"
    echo "  2. Start PostgreSQL (or use 'docker-compose up postgres')"
    echo "  3. Run 'make api' to start the API server"
    echo "  4. Run 'make frontend' to start the frontend"
    echo ""
    echo "Or use Docker:"
    echo "  docker-compose up -d"
    echo ""
}

quick_setup() {
    echo ""
    echo "=================================================="
    echo "APIC - Quick Setup"
    echo "=================================================="
    echo ""

    mkdir -p "${PROJECT_ROOT}/logs"

    create_directories
    setup_environment

    echo ""
    success "Quick setup complete!"
    echo ""
}

docker_install() {
    echo ""
    echo "=================================================="
    echo "APIC - Docker Installation"
    echo "=================================================="
    echo ""

    check_docker || exit 1

    create_directories
    setup_environment

    # Stop any existing APIC containers to avoid conflicts
    stop_existing_containers

    log "Building and starting Docker containers..."
    cd "$PROJECT_ROOT"
    docker-compose up -d --build

    echo ""
    success "Docker installation complete!"
    echo ""
    echo "Services:"
    echo "  - API: http://localhost:8000"
    echo "  - Frontend: http://localhost:8501"
    echo "  - PostgreSQL: localhost:5432"
    echo ""
}

# ============================================================================
# Main Entry Point
# ============================================================================

main() {
    cd "$PROJECT_ROOT"

    case "${1:-}" in
        --full)
            full_install
            ;;
        --quick)
            quick_setup
            ;;
        --docker)
            docker_install
            ;;
        --check)
            check_python && check_pip && check_postgres && check_docker
            ;;
        --health)
            run_health_check
            ;;
        --help|-h)
            usage
            ;;
        "")
            full_install
            ;;
        *)
            error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
}

main "$@"
