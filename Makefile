# Electrical Assembly Analyzer - Makefile
# ======================================
#
# This Makefile provides automation for the EA-Analyzer project, a tool for
# parsing electrical assembly diagrams and extracting knowledge graphs.
#
# Key Features:
# - Python package management with uv
# - Docker Compose integration for Neo4j database
# - Code quality tools (ruff, mypy)
# - Testing and coverage reporting
# - Development environment setup
#
# Quick Start:
#   make check        # Check required tools and dependencies
#   make dev-install  # Set up development environment
#   make start        # Start Neo4j database
#   make run          # Run the CLI tool with sample data
#   make test         # Run all tests
#   make ping         # Test Neo4j connection
#
# For more information, see README.md and CLI_README.md

.PHONY: help build run test clean install dev-install lint format check type-check docs start stop logs ping check_docker check-tools ensure-venv format-check test-watch test-coverage clean-venv really-clean help-test help-dev run-demo check_env run-web stop-web logs-web

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python
UV := uv
PACKAGE_NAME := ea-analyzer
VENV_DIR := .venv
VENV_PYTHON := $(VENV_DIR)/bin/python
VENV_UV := $(VENV_DIR)/bin/uv
# SHELL := /bin/bash
CHECKENV_SCRIPT := scripts/checkenv.bash
PRETTY_ECHO := echo -e

# Docker Compose
DOCKER_COMPOSE := docker-compose

# Load environment variables from .env file
ifneq (,$(wildcard .env))
    include .env
    export
endif

# Check if virtual environment exists
VENV_EXISTS := $(shell test -d $(VENV_DIR) && echo "yes" || echo "no")

# Required tools
REQUIRED_TOOLS := uv python ruff ${DOCKER_COMPOSE}

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

help: ## Show this help message
	@source scripts/log.bash && log_banner
	@echo ""
	@grep '##' Makefile | grep -v '^##' | grep -v '^[[:space:]]*@' | sort | awk 'BEGIN {FS = ":.*## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Quick Start:$(NC)"
	@echo "  make check        # Check required tools"
	@echo "  make dev-install  # Install development environment"
	@echo "  make test         # Run tests"
	@echo "  make run          # Run the CLI tool"
	@echo "  make run-web      # Run the web application"
	@echo "  make ping         # Test Neo4j connection"

# Check if Docker is installed
check_docker:
	@if command -v docker >/dev/null 2>&1; then \
		if docker compose version >/dev/null 2>&1; then \
			echo "$(GREEN)✓$(NC) Docker Compose v2 (docker compose) is installed"; \
		elif command -v docker-compose >/dev/null 2>&1; then \
			echo "$(GREEN)✓$(NC) Docker Compose v1 (docker-compose) is installed"; \
		else \
			echo "$(RED)✗$(NC) Error: Neither 'docker compose' nor 'docker-compose' is available. Please install Docker Compose."; \
			exit 1; \
		fi \
	else \
		echo "$(RED)✗$(NC) Error: Docker is not installed."; \
		exit 1; \
	fi

# Tool checks
check-tools: # Check that all required command-line tools are available
	@source scripts/log.bash && log_separator
	@echo "$(BLUE)Checking required tools...$(NC)"
	@$(MAKE) check_docker
	@missing_tools=""; \
	for tool in $(REQUIRED_TOOLS); do \
		if command -v $$tool >/dev/null 2>&1; then \
			version=$$($$tool --version 2>/dev/null | head -n1 || echo "unknown version"); \
			echo "$(GREEN)✓$(NC) $$tool: $$version"; \
		else \
			echo "$(RED)✗$(NC) $$tool: $(RED)NOT FOUND$(NC)"; \
			missing_tools="$$missing_tools $$tool"; \
		fi; \
	done; \
	if [ -n "$$missing_tools" ]; then \
		echo ""; \
		echo "$(RED)Missing required tools:$$missing_tools$(NC)"; \
		echo ""; \
		echo "$(YELLOW)Installation instructions:$(NC)"; \
		echo "  uv:     curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		echo "  python: https://www.python.org/downloads/"; \
		echo ""; \
		exit 1; \
	else \
		echo ""; \
		echo "$(GREEN)✓ All required tools are available!$(NC)"; \
	fi

# Check environment variables
check_env:
	@$(CHECKENV_SCRIPT) .env

check: check-tools check_env  ## Check for tool dependencies
	@source scripts/log.bash && log_separator
	@echo "$(GREEN)✓ Dependencies checked!$(NC)"
	
# Environment Setup
ensure-venv: check-tools # Ensure virtual environment exists and package is installed
	@source scripts/log.bash && log_separator
	@if [ "$(VENV_EXISTS)" != "yes" ]; then \
		echo "$(YELLOW)Virtual environment not found. Creating...$(NC)"; \
		$(UV) venv; \
		echo "$(GREEN)✓ Virtual environment created!$(NC)"; \
	fi
	@echo "$(GREEN)✓ Virtual environment ready!$(NC)"

install: check-tools ## Install the package in production mode
	@source scripts/log.bash && log_separator
	@echo "$(BLUE)Installing $(PACKAGE_NAME) in production mode...$(NC)"
	$(UV) pip install -e .

dev-install: check-tools # Install the package with development dependencies
	@source scripts/log.bash && log_separator
	@echo "$(BLUE)Installing $(PACKAGE_NAME) with development dependencies...$(NC)"
	$(UV) venv
	$(UV) pip install -e ".[dev]"
	@echo "$(GREEN)✓ Development environment ready!$(NC)"
	@echo "$(YELLOW)Activate with: source .venv/bin/activate$(NC)"

# Building
build: check-tools ## Build the package
	@source scripts/log.bash && log_separator
	@echo "$(BLUE)Building $(PACKAGE_NAME)...$(NC)"
	$(UV) build
	@echo "$(GREEN)✓ Package built successfully!$(NC)"

# Running
run: ensure-venv start ## Run the CLI tool with sample data and Neo4j
	@source scripts/log.bash && log_separator
	@echo "$(BLUE)Running Electrical Assembly Analyzer with Neo4j...$(NC)"
	@echo "$(YELLOW)Waiting for Neo4j to be ready...$(NC)"
	@sleep 5
	./ea-analyzer-cli.sh summary
	@echo "$(GREEN)✓ CLI tool completed!$(NC)"
	@echo "$(BLUE)Neo4j Browser: http://localhost:7474$(NC)"
	@echo "$(BLUE)Neo4j Bolt: bolt://localhost:7687$(NC)"
	@echo "$(BLUE)Use 'make stop' to stop services$(NC)"

# Testing
test: ensure-venv ## Run all tests
	@source scripts/log.bash && log_separator
	@echo "$(BLUE)Running tests...$(NC)"
	$(UV) run --python $(VENV_PYTHON) pytest tests/ -v
	@echo "$(GREEN)✓ All tests passed!$(NC)"

test-watch: ensure-venv # Run tests in watch mode
	@source scripts/log.bash && log_separator
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	$(UV) run --python $(VENV_PYTHON) pytest-watch tests/

test-coverage: ensure-venv ## Run tests with coverage report
	@source scripts/log.bash && log_separator
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	$(UV) run --python $(VENV_PYTHON) pytest tests/ --cov=ea_analyzer --cov-report=html --cov-report=term
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/$(NC)"

# Code Quality
lint: ensure-venv ## Run linting checks
	@source scripts/log.bash && log_separator
	@echo "$(BLUE)Running linting checks...$(NC)"
	$(UV) run --python $(VENV_PYTHON) ruff check src/ tests/
	@echo "$(GREEN)✓ Linting checks passed!$(NC)"

format: ensure-venv ## Format code with ruff
	@source scripts/log.bash && log_separator
	@echo "$(BLUE)Formatting code...$(NC)"
	$(UV) run --python $(VENV_PYTHON) ruff format src/ tests/
	@echo "$(GREEN)✓ Code formatted!$(NC)"

format-check: ensure-venv ## Check if code is properly formatted
	@source scripts/log.bash && log_separator
	@echo "$(BLUE)Checking code formatting...$(NC)"
	$(UV) run --python $(VENV_PYTHON) ruff format --check src/ tests/
	@echo "$(GREEN)✓ Code is properly formatted!$(NC)"

type-check: ensure-venv ## Run type checking with mypy
	@source scripts/log.bash && log_separator
	@echo "$(BLUE)Running type checks...$(NC)"
	$(UV) run --python $(VENV_PYTHON) mypy src/
	@echo "$(GREEN)✓ Type checks passed!$(NC)"

# Documentation
docs: # Generate documentation (placeholder)
	@echo "$(BLUE)Generating documentation...$(NC)"
	@echo "$(YELLOW)Documentation generation not yet implemented$(NC)"

# Cleanup
clean: ## Clean up build artifacts and cache files
	@source scripts/log.bash && log_separator
	@echo "$(BLUE)Cleaning up...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete!$(NC)"

clean-venv: # Remove virtual environment
	@source scripts/log.bash && log_separator
	@echo "$(BLUE)Removing virtual environment...$(NC)"
	rm -rf $(VENV_DIR)/
	@echo "$(GREEN)✓ Virtual environment removed!$(NC)"

really-clean: clean clean-venv ## Clean up build artifacts and cache files
	@source scripts/log.bash && log_separator
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.debug.yml down -v
	docker system prune --all --force --volumes && docker volume prune --force --filter all=1
	@echo "$(GREEN)✓ Cleanup complete!$(NC)"

# Utility targets


# Help for specific targets
help-test: ## Show test-related help
	@echo "$(BLUE)Test Commands$(NC)"
	@echo "=============="
	@echo "make test          - Run all tests"
	@echo "make test-watch    - Run tests in watch mode"
	@echo "make test-coverage - Run tests with coverage report"

help-dev: ## Show development-related help
	@echo "$(BLUE)Development Commands$(NC)"
	@echo "======================"
	@echo "make dev-setup     - Complete development setup"
	@echo "make dev-install   - Install with dev dependencies"
	@echo "make check         - Run all quality checks"
	@echo "make format        - Format code"
	@echo "make lint          - Run linting"
	@echo "make type-check    - Run type checking"

# Docker Compose Management
start: ## Start services using Docker Compose
	@source scripts/log.bash && log_separator
	@echo "$(BLUE)Starting services with Docker Compose...$(NC)"
	@if ! $(DOCKER_COMPOSE) ps neo4j | grep -q "Up"; then \
		$(DOCKER_COMPOSE) up -d neo4j; \
		echo "$(YELLOW)Waiting for Neo4j to be ready...$(NC)"; \
		counter=0; \
		while [ $$counter -lt 30 ]; do \
			if $(DOCKER_COMPOSE) exec neo4j cypher-shell -u $(NEO4J_USERNAME) -p $(NEO4J_PASSWORD) "RETURN 1" >/dev/null 2>&1; then \
				break; \
			fi; \
			sleep 2; \
			counter=$$((counter + 1)); \
		done; \
		echo "$(GREEN)✓ Neo4j is ready!$(NC)"; \
		echo "$(BLUE)Neo4j Browser: http://localhost:7474$(NC)"; \
		echo "$(BLUE)Bolt URI: $(NEO4J_URI)$(NC)"; \
	else \
		echo "$(YELLOW)Neo4j is already running$(NC)"; \
	fi

stop: ## Stop Docker Compose services
	@source scripts/log.bash && log_separator
	@echo "$(BLUE)Stopping services...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✓ Services stopped$(NC)"

stop-web: ## Stop all web application services
	@source scripts/log.bash && log_separator
	@echo "$(BLUE)Stopping web application services...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✓ Web application services stopped$(NC)"

ping: ## Check all services are running (Neo4j, Backend, Frontend)
	@source scripts/log.bash && log_separator
	@echo "$(BLUE)Checking all EA-Analyzer services...$(NC)"
	@echo ""
	@neo4j_status=; backend_status=; frontend_status=; \
	echo "$(YELLOW)1. Checking Neo4j...$(NC)"; \
	if ./ea-analyzer-cli.sh neo4j ping >/dev/null 2>&1; then \
		echo "$(GREEN)✓ Neo4j is running$(NC)"; \
	else \
		echo "$(RED)✗ Neo4j is not running$(NC)"; \
		neo4j_status=1; \
	fi; \
	echo ""; \
	echo "$(YELLOW)2. Checking Backend API...$(NC)"; \
	if curl -s http://localhost:8000/health >/dev/null 2>&1; then \
		echo "$(GREEN)✓ Backend API is running$(NC)"; \
		health_status=$$(curl -s http://localhost:8000/health | grep -o '"status":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo "unknown"); \
		echo "$(BLUE)  API Health: $$health_status$(NC)"; \
	else \
		echo "$(RED)✗ Backend API is not running$(NC)"; \
		backend_status=1; \
	fi; \
	echo ""; \
	echo "$(YELLOW)3. Checking Frontend...$(NC)"; \
	if curl -s -I http://localhost:3000 >/dev/null 2>&1; then \
		echo "$(GREEN)✓ Frontend is running$(NC)"; \
	else \
		echo "$(RED)✗ Frontend is not running$(NC)"; \
		frontend_status=1; \
	fi; \
	echo ""; \
	if [ -z "$$neo4j_status" ] && [ -z "$$backend_status" ] && [ -z "$$frontend_status" ]; then \
		echo "$(GREEN)✓ All services are running!$(NC)"; \
		echo ""; \
		echo "$(BLUE)Access URLs:$(NC)"; \
		echo "  Frontend:     http://localhost:3000"; \
		echo "  Backend API:  http://localhost:8000"; \
		echo "  API Docs:     http://localhost:8000/docs"; \
		echo "  Neo4j:        http://localhost:7474"; \
	else \
		echo "$(RED)✗ Some services are not running$(NC)"; \
		echo ""; \
		echo "$(YELLOW)To start all services: make run-web$(NC)"; \
		echo "$(YELLOW)To start only Neo4j: make start$(NC)"; \
		exit 1; \
	fi

logs: ## Show service logs
	@source scripts/log.bash && log_separator
	@echo "$(BLUE)Service Logs$(NC)"
	@echo "=============="
	$(DOCKER_COMPOSE) logs neo4j

logs-web: ## Show all web application service logs
	@source scripts/log.bash && log_separator
	@echo "$(BLUE)Web Application Service Logs$(NC)"
	@echo "=================================="
	$(DOCKER_COMPOSE) logs -f


run-demo: ensure-venv start ## Run complete demo
	@source scripts/log.bash && log_separator
	@echo "$(BLUE)Running Complete EA-Analyzer Demo$(NC)"
	@echo "$(YELLOW)1. Storing diagram data...$(NC)"
	./ea-analyzer-cli.sh store "$(DATA_FILE)"
	@echo "$(YELLOW)2. Showing database summary...$(NC)"
	./ea-analyzer-cli.sh neo4j summary
	@echo "$(YELLOW)3. Analyzing protection schemes...$(NC)"
	./ea-analyzer-cli.sh neo4j protection-schemes
	@echo "$(GREEN)✓ Demo completed!$(NC)"

run-web: check-tools ## Build and run the complete web application (frontend + backend + Neo4j)
	@source scripts/log.bash && log_separator
	@echo "$(BLUE)Building and starting EA-Analyzer Web Application...$(NC)"
	@echo "$(YELLOW)Building Docker images...$(NC)"
	$(DOCKER_COMPOSE) build
	@echo "$(YELLOW)Starting all services...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(YELLOW)Waiting for services to be ready...$(NC)"
	@sleep 10
	@echo "$(GREEN)✓ Web application is running!$(NC)"
	@echo ""
	@echo "$(BLUE)Access URLs:$(NC)"
	@echo "  Frontend:     http://localhost:3000"
	@echo "  Backend API:  http://localhost:8000"
	@echo "  API Docs:     http://localhost:8000/docs"
	@echo "  Neo4j:        http://localhost:7474"
	@echo ""
	@echo "$(YELLOW)Use 'make stop-web' to stop all services$(NC)"
