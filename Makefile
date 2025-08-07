.PHONY: help install dev test lint format clean build run docker-build docker-up docker-down

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install pre-commit
	pre-commit install

test: ## Run tests
	pytest --cov=app --cov-report=term-missing --cov-report=html

test-watch: ## Run tests in watch mode
	pytest-watch

lint: ## Run linting tools
	flake8 app tests
	mypy app

format: ## Format code
	black app tests
	isort app tests

clean: ## Clean up cache and build files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/

build: ## Build the application
	docker build -t fastapi-app .

run: ## Run the application locally
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

docker-build: ## Build Docker image
	docker-compose build

docker-up: ## Start services with Docker Compose
	docker-compose up -d

docker-down: ## Stop Docker Compose services
	docker-compose down

docker-logs: ## View Docker Compose logs
	docker-compose logs -f

migration-create: ## Create a new database migration
	alembic revision --autogenerate -m "$(message)"

migration-upgrade: ## Apply database migrations
	alembic upgrade head

migration-downgrade: ## Rollback database migration
	alembic downgrade -1
