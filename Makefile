# APIC - Agentic Process Improvement Consultant
# Makefile for automated installation, testing, and deployment

# Configuration
PYTHON := python3
PIP := pip3
VENV_DIR := .venv
PROJECT_NAME := apic

# Docker configuration
DOCKER_COMPOSE := docker-compose
DOCKER_IMAGE := apic

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

.PHONY: help install setup test lint clean db-init docker-up docker-down \
        dev api frontend format type-check health-check venv requirements \
        db-migrate db-reset logs docker-build docker-logs docker-shell

# Default target
.DEFAULT_GOAL := help

# ============================================================================
# Help
# ============================================================================

help: ## Show this help message
	@echo "$(BLUE)APIC - Agentic Process Improvement Consultant$(NC)"
	@echo "============================================="
	@echo ""
	@echo "$(GREEN)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# ============================================================================
# Installation & Setup
# ============================================================================

install: venv requirements setup ## Complete installation (venv + deps + setup)
	@echo "$(GREEN)Installation complete!$(NC)"
	@echo "Run 'make health-check' to verify installation."

setup: ## Quick setup (directories, env file)
	@echo "$(BLUE)Running quick setup...$(NC)"
	@$(PYTHON) -c "from scripts.install_utils import Installer; i = Installer(); print(i.run_quick_setup())"
	@echo "$(GREEN)Setup complete!$(NC)"

venv: ## Create virtual environment
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	@if [ ! -d "$(VENV_DIR)" ]; then \
		$(PYTHON) -m venv $(VENV_DIR); \
		echo "$(GREEN)Virtual environment created at $(VENV_DIR)$(NC)"; \
	else \
		echo "$(YELLOW)Virtual environment already exists$(NC)"; \
	fi

requirements: ## Install Python dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	@if [ -d "$(VENV_DIR)" ]; then \
		$(VENV_DIR)/bin/pip install --upgrade pip; \
		$(VENV_DIR)/bin/pip install -r requirements.txt; \
	else \
		$(PIP) install --upgrade pip; \
		$(PIP) install -r requirements.txt; \
	fi
	@echo "$(GREEN)Dependencies installed!$(NC)"

requirements-dev: requirements ## Install development dependencies
	@echo "$(BLUE)Installing dev dependencies...$(NC)"
	@if [ -f "requirements-dev.txt" ]; then \
		if [ -d "$(VENV_DIR)" ]; then \
			$(VENV_DIR)/bin/pip install -r requirements-dev.txt; \
		else \
			$(PIP) install -r requirements-dev.txt; \
		fi \
	fi

# ============================================================================
# Development
# ============================================================================

dev: ## Start development server (API + Frontend)
	@echo "$(BLUE)Starting development servers...$(NC)"
	@echo "Open two terminals and run:"
	@echo "  Terminal 1: make api"
	@echo "  Terminal 2: make frontend"

api: ## Run FastAPI backend server
	@echo "$(BLUE)Starting FastAPI server...$(NC)"
	@$(PYTHON) main.py api

frontend: ## Run Streamlit frontend
	@echo "$(BLUE)Starting Streamlit frontend...$(NC)"
	@$(PYTHON) main.py frontend

# ============================================================================
# Testing
# ============================================================================

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	@$(PYTHON) -m pytest tests/ -v

test-cov: ## Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	@$(PYTHON) -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	@$(PYTHON) -m pytest tests/ -v -m "not integration"

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	@$(PYTHON) -m pytest tests/ -v -m "integration"

# ============================================================================
# Code Quality
# ============================================================================

lint: ## Run linting checks
	@echo "$(BLUE)Running linting...$(NC)"
	@if command -v ruff &> /dev/null; then \
		ruff check src/ tests/; \
	elif command -v flake8 &> /dev/null; then \
		flake8 src/ tests/; \
	else \
		echo "$(YELLOW)No linter found (ruff or flake8)$(NC)"; \
	fi

format: ## Format code with black
	@echo "$(BLUE)Formatting code...$(NC)"
	@if command -v black &> /dev/null; then \
		black src/ tests/ scripts/; \
	else \
		echo "$(YELLOW)black not installed$(NC)"; \
	fi

type-check: ## Run type checking with mypy
	@echo "$(BLUE)Running type checks...$(NC)"
	@$(PYTHON) -m mypy src/ --ignore-missing-imports

# ============================================================================
# Database
# ============================================================================

db-init: ## Initialize database schema
	@echo "$(BLUE)Initializing database...$(NC)"
	@$(PYTHON) scripts/init_db.py
	@echo "$(GREEN)Database initialized!$(NC)"

db-migrate: ## Run database migrations (Alembic)
	@echo "$(BLUE)Running migrations...$(NC)"
	@if [ -d "alembic" ]; then \
		alembic upgrade head; \
	else \
		echo "$(YELLOW)Alembic not configured. Running init script instead...$(NC)"; \
		$(PYTHON) scripts/init_db.py; \
	fi

db-reset: ## Reset database (DESTRUCTIVE)
	@echo "$(RED)WARNING: This will delete all data!$(NC)"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ]
	@echo "$(BLUE)Resetting database...$(NC)"
	@$(PYTHON) scripts/init_db.py --reset
	@echo "$(GREEN)Database reset complete!$(NC)"

# ============================================================================
# Docker
# ============================================================================

docker-up: ## Start all Docker services
	@echo "$(BLUE)Starting Docker services...$(NC)"
	@$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)Services started!$(NC)"
	@echo "API: http://localhost:8000"
	@echo "Frontend: http://localhost:8501"

docker-down: ## Stop all Docker services
	@echo "$(BLUE)Stopping Docker services...$(NC)"
	@$(DOCKER_COMPOSE) down
	@echo "$(GREEN)Services stopped!$(NC)"

docker-build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	@$(DOCKER_COMPOSE) build

docker-logs: ## View Docker logs
	@$(DOCKER_COMPOSE) logs -f

docker-shell: ## Open shell in API container
	@$(DOCKER_COMPOSE) exec api /bin/bash

docker-restart: ## Restart Docker services
	@$(DOCKER_COMPOSE) restart

docker-clean: ## Remove Docker containers and volumes
	@echo "$(RED)WARNING: This will remove all containers and volumes!$(NC)"
	@$(DOCKER_COMPOSE) down -v --remove-orphans

# ============================================================================
# Utilities
# ============================================================================

health-check: ## Run health checks
	@echo "$(BLUE)Running health checks...$(NC)"
	@$(PYTHON) -c "from scripts.install_utils import HealthChecker; h = HealthChecker(); import json; print(json.dumps(h.run_all_checks(), indent=2))"

clean: ## Clean build artifacts and caches
	@echo "$(BLUE)Cleaning...$(NC)"
	@rm -rf __pycache__ .pytest_cache .mypy_cache .coverage htmlcov
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@echo "$(GREEN)Clean complete!$(NC)"

clean-all: clean ## Clean everything including venv
	@echo "$(RED)Removing virtual environment...$(NC)"
	@rm -rf $(VENV_DIR)
	@echo "$(GREEN)Full clean complete!$(NC)"

logs: ## View application logs
	@if [ -d "logs" ]; then \
		tail -f logs/*.log; \
	else \
		echo "$(YELLOW)No logs directory found$(NC)"; \
	fi

version: ## Show version information
	@echo "APIC Version: 1.0.0"
	@echo "Python: $$($(PYTHON) --version)"
	@echo "Pip: $$($(PIP) --version)"

# ============================================================================
# Quick Commands
# ============================================================================

run: docker-up ## Quick start with Docker

stop: docker-down ## Quick stop

status: ## Show service status
	@$(DOCKER_COMPOSE) ps

check: lint type-check test ## Run all checks (lint, type-check, test)
