.PHONY: help install setup up down logs clean test lint format validate-config scan-juice-shop backup restore

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

##@ General

help: ## Display this help message
	@echo "$(BLUE)AMTD - Automated Malware Target Detection$(NC)"
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup & Installation

install: ## Install Python dependencies
	@echo "$(BLUE)Installing Python dependencies...$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)Dependencies installed successfully!$(NC)"

setup: ## Initial setup (create .env, install dependencies)
	@echo "$(BLUE)Setting up AMTD...$(NC)"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)Created .env file from .env.example$(NC)"; \
		echo "$(YELLOW)Please edit .env with your configuration$(NC)"; \
	else \
		echo "$(YELLOW).env file already exists$(NC)"; \
	fi
	@$(MAKE) install
	@echo "$(GREEN)Setup complete!$(NC)"

##@ Docker Operations

up: ## Start all Docker services
	@echo "$(BLUE)Starting AMTD services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Services started!$(NC)"
	@echo "Access points:"
	@echo "  - Jenkins:    http://localhost:8080"
	@echo "  - Juice Shop: http://localhost:3000"
	@echo "  - MinIO:      http://localhost:9001"
	@echo "  - Grafana:    http://localhost:3001"
	@echo "  - API:        http://localhost:5000"

down: ## Stop all Docker services
	@echo "$(BLUE)Stopping AMTD services...$(NC)"
	docker-compose down
	@echo "$(GREEN)Services stopped!$(NC)"

restart: ## Restart all Docker services
	@$(MAKE) down
	@$(MAKE) up

ps: ## Show status of Docker services
	docker-compose ps

logs: ## Show logs from all services
	docker-compose logs -f

logs-jenkins: ## Show Jenkins logs
	docker-compose logs -f jenkins

logs-api: ## Show API server logs
	docker-compose logs -f api

logs-postgres: ## Show PostgreSQL logs
	docker-compose logs -f postgres

##@ Development

dev: ## Start development environment
	@echo "$(BLUE)Starting development environment...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Development environment ready!$(NC)"

shell-api: ## Open shell in API container
	docker-compose exec api /bin/bash

shell-db: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U amtd -d amtd

##@ Database

db-init: ## Initialize database
	@echo "$(BLUE)Initializing database...$(NC)"
	docker-compose exec postgres psql -U amtd -d amtd -f /docker-entrypoint-initdb.d/01-init.sql
	docker-compose exec postgres psql -U amtd -d amtd -f /docker-entrypoint-initdb.d/02-schema.sql
	@echo "$(GREEN)Database initialized!$(NC)"

db-reset: ## Reset database (WARNING: destroys all data)
	@echo "$(RED)WARNING: This will delete all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(BLUE)Resetting database...$(NC)"; \
		docker-compose exec postgres psql -U amtd -d postgres -c "DROP DATABASE IF EXISTS amtd;"; \
		docker-compose exec postgres psql -U amtd -d postgres -c "CREATE DATABASE amtd;"; \
		$(MAKE) db-init; \
		echo "$(GREEN)Database reset complete!$(NC)"; \
	fi

db-backup: ## Backup database
	@echo "$(BLUE)Backing up database...$(NC)"
	@mkdir -p backups
	docker-compose exec -T postgres pg_dump -U amtd amtd > backups/amtd_backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)Database backed up!$(NC)"

db-restore: ## Restore database from latest backup
	@echo "$(BLUE)Restoring database...$(NC)"
	@LATEST=$$(ls -t backups/*.sql | head -1); \
	if [ -z "$$LATEST" ]; then \
		echo "$(RED)No backup files found!$(NC)"; \
		exit 1; \
	fi; \
	echo "Restoring from: $$LATEST"; \
	docker-compose exec -T postgres psql -U amtd amtd < $$LATEST
	@echo "$(GREEN)Database restored!$(NC)"

##@ Testing

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term
	@echo "$(GREEN)Tests complete!$(NC)"

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	pytest tests/unit/ -v
	@echo "$(GREEN)Unit tests complete!$(NC)"

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	pytest tests/integration/ -v
	@echo "$(GREEN)Integration tests complete!$(NC)"

test-coverage: ## Generate test coverage report
	pytest tests/ --cov=src --cov-report=html
	@echo "$(GREEN)Coverage report generated in htmlcov/index.html$(NC)"

##@ Code Quality

lint: ## Run linters (flake8, pylint)
	@echo "$(BLUE)Running linters...$(NC)"
	flake8 src/ --max-line-length=120 --exclude=__pycache__,*.pyc
	pylint src/ --max-line-length=120
	@echo "$(GREEN)Linting complete!$(NC)"

format: ## Format code with black
	@echo "$(BLUE)Formatting code...$(NC)"
	black src/ scripts/ tests/ --line-length=120
	isort src/ scripts/ tests/
	@echo "$(GREEN)Code formatted!$(NC)"

type-check: ## Run type checking with mypy
	@echo "$(BLUE)Running type checker...$(NC)"
	mypy src/ --ignore-missing-imports
	@echo "$(GREEN)Type checking complete!$(NC)"

##@ Configuration

validate-config: ## Validate all application configurations
	@echo "$(BLUE)Validating configurations...$(NC)"
	python scripts/validate-config.py --all
	@echo "$(GREEN)Configuration validation complete!$(NC)"

list-apps: ## List all configured applications
	@echo "$(BLUE)Configured applications:$(NC)"
	@ls -1 config/applications/*.yaml | grep -v template.yaml | xargs -I {} basename {} .yaml

list-policies: ## List all scan policies
	@echo "$(BLUE)Available scan policies:$(NC)"
	@ls -1 config/scan-policies/*.yaml | xargs -I {} basename {} .yaml

##@ Scanning

scan-juice-shop: ## Run scan on Juice Shop
	@echo "$(BLUE)Starting scan on OWASP Juice Shop...$(NC)"
	python scripts/scan-executor.py --application juice-shop --scan-type full
	@echo "$(GREEN)Scan complete!$(NC)"

scan: ## Run scan on specified application (make scan APP=myapp)
	@if [ -z "$(APP)" ]; then \
		echo "$(RED)Error: Please specify APP parameter$(NC)"; \
		echo "Usage: make scan APP=juice-shop"; \
		exit 1; \
	fi
	@echo "$(BLUE)Starting scan on $(APP)...$(NC)"
	python scripts/scan-executor.py --application $(APP) --scan-type full
	@echo "$(GREEN)Scan complete!$(NC)"

##@ Reports

reports: ## List all generated reports
	@echo "$(BLUE)Generated reports:$(NC)"
	@find reports/ -name "*.html" -o -name "*.pdf" -o -name "*.json" | sort -r | head -20

view-latest-report: ## Open latest HTML report in browser
	@LATEST=$$(find reports/ -name "*.html" | sort -r | head -1); \
	if [ -z "$$LATEST" ]; then \
		echo "$(RED)No reports found!$(NC)"; \
		exit 1; \
	fi; \
	echo "Opening: $$LATEST"; \
	xdg-open "$$LATEST" 2>/dev/null || open "$$LATEST" 2>/dev/null || echo "Please open $$LATEST manually"

##@ Cleanup

clean: ## Remove temporary files and caches
	@echo "$(BLUE)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	@echo "$(GREEN)Cleanup complete!$(NC)"

clean-reports: ## Remove old reports (keeps last 30 days)
	@echo "$(BLUE)Cleaning old reports...$(NC)"
	find reports/ -type f -mtime +30 -delete
	@echo "$(GREEN)Old reports cleaned!$(NC)"

clean-all: clean down ## Full cleanup (stop containers, remove files)
	@echo "$(BLUE)Performing full cleanup...$(NC)"
	docker-compose down -v
	rm -rf logs/*
	@echo "$(GREEN)Full cleanup complete!$(NC)"

##@ Monitoring

health: ## Check health of all services
	@echo "$(BLUE)Checking service health...$(NC)"
	@echo "Jenkins:    $$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8080 || echo 'DOWN')"
	@echo "API:        $$(curl -s -o /dev/null -w '%{http_code}' http://localhost:5000/health || echo 'DOWN')"
	@echo "Juice Shop: $$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 || echo 'DOWN')"
	@echo "MinIO:      $$(curl -s -o /dev/null -w '%{http_code}' http://localhost:9001 || echo 'DOWN')"
	@echo "Grafana:    $$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3001 || echo 'DOWN')"

metrics: ## Show system metrics
	@echo "$(BLUE)System Metrics:$(NC)"
	@docker stats --no-stream

disk-usage: ## Show disk usage
	@echo "$(BLUE)Disk Usage:$(NC)"
	@du -sh reports/ logs/ data/ 2>/dev/null || echo "No data directories found"

##@ Documentation

docs: ## Open documentation
	@echo "Opening documentation..."
	@cd docs && xdg-open README.md 2>/dev/null || open README.md 2>/dev/null || echo "Please open docs/README.md manually"

##@ Quick Start

quick-start: setup up ## Quick start (setup + start services)
	@echo "$(GREEN)AMTD is ready!$(NC)"
	@echo ""
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "1. Wait for services to start (30-60 seconds)"
	@echo "2. Access Jenkins at http://localhost:8080"
	@echo "3. Run your first scan: make scan-juice-shop"
	@echo "4. View reports: make reports"

demo: up scan-juice-shop ## Run demo scan on Juice Shop
	@echo "$(GREEN)Demo complete! View reports with: make reports$(NC)"
