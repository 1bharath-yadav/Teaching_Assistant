# Makefile for TDS Teaching Assistant

.PHONY: setup dev start stop clean test lint format backup deploy-docker deploy-k8s help

# Default target
.DEFAULT_GOAL := help

# Variables
PROJECT_ROOT := $(shell pwd)
SCRIPTS_DIR := $(PROJECT_ROOT)/scripts
LOG_DIR := $(PROJECT_ROOT)/logs
DOCKER_DIR := $(PROJECT_ROOT)/docker

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

# Help
help:
	@echo "${BLUE}TDS Teaching Assistant Commands${NC}"
	@echo "${BLUE}================================${NC}"
	@echo ""
	@echo "Usage: make [command]"
	@echo ""
	@echo "Commands:"
	@echo "  ${GREEN}setup${NC}         - Set up the project (install dependencies, create .env, etc.)"
	@echo "  ${GREEN}dev${NC}           - Start development servers"
	@echo "  ${GREEN}start${NC}         - Start production servers"
	@echo "  ${GREEN}stop${NC}          - Stop all servers"
	@echo "  ${GREEN}clean${NC}         - Clean temporary files"
	@echo "  ${GREEN}test${NC}          - Run all tests"
	@echo "  ${GREEN}test-unit${NC}     - Run unit tests"
	@echo "  ${GREEN}test-integration${NC} - Run integration tests"
	@echo "  ${GREEN}lint${NC}          - Run linters"
	@echo "  ${GREEN}format${NC}        - Format code"
	@echo "  ${GREEN}backup${NC}        - Create a backup of important files"
	@echo "  ${GREEN}docker${NC}        - Deploy with Docker"
	@echo "  ${GREEN}k8s${NC}           - Deploy to Kubernetes"
	@echo ""
	@echo "For more information, see README.md"

# Setup
setup:
	@echo "${YELLOW}Setting up the project...${NC}"
	@./setup.sh

# Development mode
dev:
	@echo "${YELLOW}Starting development servers...${NC}"
	@$(SCRIPTS_DIR)/manage_separate.sh dev

# Production mode
start:
	@echo "${YELLOW}Starting production servers...${NC}"
	@$(SCRIPTS_DIR)/manage_separate.sh start

# Stop all servers
stop:
	@echo "${YELLOW}Stopping all servers...${NC}"
	@$(SCRIPTS_DIR)/manage_separate.sh stop

# Clean
clean:
	@echo "${YELLOW}Cleaning temporary files...${NC}"
	@find . -name "__pycache__" -exec rm -rf {} +
	@find . -name "*.pyc" -delete
	@find . -name ".pytest_cache" -exec rm -rf {} +
	@find . -name "*.log" -not -path "$(LOG_DIR)/*" -exec mv {} $(LOG_DIR)/ \;
	@echo "${GREEN}Done!${NC}"

# Tests
test:
	@echo "${YELLOW}Running all tests...${NC}"
	@pytest

test-unit:
	@echo "${YELLOW}Running unit tests...${NC}"
	@pytest tests/unit

test-integration:
	@echo "${YELLOW}Running integration tests...${NC}"
	@pytest tests/integration

# Linting
lint:
	@echo "${YELLOW}Running linters...${NC}"
	@flake8 api lib data tests

# Format code
format:
	@echo "${YELLOW}Formatting code...${NC}"
	@black api lib data tests
	@isort api lib data tests

# Backup
backup:
	@echo "${YELLOW}Creating backup...${NC}"
	@mkdir -p backups
	@tar -czf backups/tds-assistant-backup-$(shell date +%Y%m%d%H%M%S).tar.gz \
		--exclude="*.pyc" \
		--exclude="__pycache__" \
		--exclude=".pytest_cache" \
		--exclude="node_modules" \
		--exclude=".next" \
		--exclude="backups" \
		--exclude="typesense-data" \
		.
	@echo "${GREEN}Backup created in backups/ directory${NC}"

# Docker deployment
docker:
	@echo "${YELLOW}Deploying with Docker...${NC}"
	@docker-compose -f $(DOCKER_DIR)/docker-compose.separate.yml up

# Kubernetes deployment
k8s:
	@echo "${YELLOW}Deploying to Kubernetes...${NC}"
	@kubectl apply -f kubernetes/namespace.yaml
	@kubectl apply -f kubernetes/configmap.yaml
	@kubectl apply -f kubernetes/secrets.yaml
	@kubectl apply -f kubernetes/backend-deployment.yaml
	@kubectl apply -f kubernetes/backend-service.yaml
	@kubectl apply -f kubernetes/frontend-deployment.yaml
	@kubectl apply -f kubernetes/frontend-service.yaml
	@kubectl apply -f kubernetes/ingress.yaml
	@echo "${GREEN}Deployment to Kubernetes complete!${NC}"
