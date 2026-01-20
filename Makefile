# APIC - Agentic Process Improvement Consultant
# Makefile for automated development tasks

.PHONY: help install install-dev test test-cov lint format typecheck migrate docker-up docker-down verify clean

# Default target
help:
	@echo "APIC Development Commands"
	@echo "========================="
	@echo ""
	@echo "Setup:"
	@echo "  make install       - Install production dependencies"
	@echo "  make install-dev   - Install development dependencies"
	@echo "  make setup         - Complete setup (install + migrate)"
	@echo ""
	@echo "Database:"
	@echo "  make migrate       - Run database migrations"
	@echo "  make migrate-new   - Create a new migration"
	@echo "  make migrate-down  - Rollback last migration"
	@echo "  make db-reset      - Reset database (drop + migrate)"
	@echo ""
	@echo "Testing:"
	@echo "  make test          - Run all tests"
	@echo "  make test-cov      - Run tests with coverage"
	@echo "  make test-install  - Run installation tests only"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo "  make typecheck     - Run type checking"
	@echo "  make check         - Run all quality checks"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up     - Start Docker containers"
	@echo "  make docker-down   - Stop Docker containers"
	@echo "  make docker-logs   - View container logs"
	@echo "  make docker-build  - Build Docker images"
	@echo ""
	@echo "Running:"
	@echo "  make run-api       - Run API server"
	@echo "  make run-frontend  - Run Streamlit frontend"
	@echo ""
	@echo "Utilities:"
	@echo "  make verify        - Verify installation"
	@echo "  make clean         - Clean temporary files"

# ============================================================================
# Installation
# ============================================================================

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

setup: install migrate verify
	@echo "Setup complete!"

# ============================================================================
# Database
# ============================================================================

migrate:
	alembic upgrade head

migrate-new:
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

migrate-down:
	alembic downgrade -1

migrate-history:
	alembic history

db-reset:
	alembic downgrade base
	alembic upgrade head

db-check:
	python -c "from src.utils.db_health import check_database_health; print(check_database_health())"

# ============================================================================
# Testing
# ============================================================================

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src --cov=config --cov-report=html --cov-report=term-missing

test-install:
	pytest tests/test_installation.py -v

test-unit:
	pytest tests/ -v -m "not integration"

test-integration:
	pytest tests/ -v -m "integration"

# ============================================================================
# Code Quality
# ============================================================================

lint:
	ruff check src/ tests/ config/
	@echo "Linting complete!"

format:
	black src/ tests/ config/
	ruff check --fix src/ tests/ config/
	@echo "Formatting complete!"

typecheck:
	mypy src/ config/ --ignore-missing-imports

check: lint typecheck
	@echo "All quality checks passed!"

# ============================================================================
# Docker
# ============================================================================

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-build:
	docker-compose build

docker-restart: docker-down docker-up

docker-clean:
	docker-compose down -v --rmi local

# ============================================================================
# Running
# ============================================================================

run-api:
	python main.py api

run-frontend:
	python main.py frontend

run: run-api

# ============================================================================
# Utilities
# ============================================================================

verify:
	python -m src.utils.install_verifier

env-check:
	python -c "from src.utils.env_validator import get_validation_report; import json; print(json.dumps(get_validation_report(), indent=2))"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "Cleaned!"

# ============================================================================
# Pre-commit
# ============================================================================

pre-commit-install:
	pre-commit install

pre-commit-run:
	pre-commit run --all-files
