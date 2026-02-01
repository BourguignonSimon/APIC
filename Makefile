# APIC - Agentic Process Improvement Consultant

PYTHON := python3
DOCKER_COMPOSE := docker-compose

.PHONY: help install test run docker

.DEFAULT_GOAL := help

help: ## Show available commands
	@echo "APIC - Available commands:"
	@echo "  make install  - Install dependencies and set up project"
	@echo "  make test     - Run all tests"
	@echo "  make run      - Start development servers (API + Frontend)"
	@echo "  make docker   - Start all services with Docker"

install: ## Install dependencies and set up project
	@echo "Creating virtual environment..."
	@if [ ! -d ".venv" ]; then $(PYTHON) -m venv .venv; fi
	@echo "Installing dependencies..."
	@.venv/bin/pip install --upgrade pip -q
	@.venv/bin/pip install -r requirements.txt -q
	@if [ -f "requirements-dev.txt" ]; then .venv/bin/pip install -r requirements-dev.txt -q; fi
	@echo "Running setup..."
	@$(PYTHON) -c "from scripts.install_utils import Installer; Installer().run_quick_setup()"
	@echo "Installation complete! Run 'make test' to verify."

test: ## Run all tests
	@$(PYTHON) -m pytest tests/ -v

run: ## Start development servers
	@echo "Starting APIC..."
	@echo "API server: http://localhost:8000"
	@echo "Frontend: http://localhost:8501"
	@echo ""
	@echo "Run in separate terminals:"
	@echo "  $(PYTHON) main.py api"
	@echo "  $(PYTHON) main.py frontend"

docker: ## Start all services with Docker
	@echo "Starting Docker services..."
	@$(DOCKER_COMPOSE) up -d
	@echo "Services started!"
	@echo "API: http://localhost:8000"
	@echo "Frontend: http://localhost:8501"
	@echo ""
	@echo "Stop with: docker-compose down"
