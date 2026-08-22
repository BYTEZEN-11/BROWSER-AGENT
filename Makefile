.PHONY: help install install-dev test lint format typecheck build run run-api run-web docker-build docker-up docker-down clean

# Default target
help:
	@echo "Langraph Browser Agent - Development Commands"
	@echo ""
	@echo "Installation:"
	@echo "  install       Install production dependencies"
	@echo "  install-dev   Install development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test          Run all tests"
	@echo "  test-cov      Run tests with coverage"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint          Run ruff linter"
	@echo "  format        Format code with ruff and black"
	@echo "  typecheck     Run mypy type checker"
	@echo "  check         Run all checks (lint, format, typecheck, test)"
	@echo ""
	@echo "Running:"
	@echo "  run           Run the agent (main.py)"
	@echo "  run-api       Run FastAPI server"
	@echo "  run-web       Run Streamlit web UI"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build  Build Docker images"
	@echo "  docker-up     Start services with docker-compose"
	@echo "  docker-down   Stop services"
	@echo "  docker-logs   View docker logs"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean         Clean build artifacts and caches"
	@echo "  update        Update dependencies"

# Installation
install:
	pip install -r requirements.txt
	playwright install chromium

install-dev:
	pip install -r requirements.txt
	pip install -e ".[dev]"
	playwright install chromium
	pre-commit install

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html

# Code Quality
lint:
	ruff check .

format:
	ruff format .
	ruff check . --fix

typecheck:
	mypy main.py --ignore-missing-imports

check: lint format typecheck test

# Running
run:
	python main.py

run-api:
	python web_ui/api.py

run-web:
	streamlit run web_ui/streamlit_app.py

# Docker
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-ps:
	docker-compose ps

# Maintenance
clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache
	rm -rf build dist *.egg-info
	rm -rf .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

update:
	pip install --upgrade pip
	pip install --upgrade -r requirements.txt
	pip install --upgrade -e ".[dev]"
	playwright install chromium

# CI simulation
ci: check
	@echo "All checks passed!"