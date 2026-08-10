.PHONY: help install install-dev test test-cov lint format typecheck smoke run docker-build docker-run clean

PYTHON ?= python3
PIP    ?= pip3

help: ## Show this help.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install runtime dependencies.
	$(PIP) install -r requirements.txt

install-dev: ## Install runtime + dev dependencies.
	$(PIP) install -r requirements.txt -r requirements-dev.txt

test: ## Run the test suite.
	pytest

test-cov: ## Run the test suite with coverage.
	pytest --cov=app --cov-report=term-missing --cov-report=html

lint: ## Run ruff on the codebase.
	ruff check app/ tests/ main.py

format: ## Auto-format with black + ruff.
	ruff check --fix app/ tests/ main.py
	black app/ tests/ main.py

typecheck: ## Run mypy.
	mypy app/

smoke: ## Smoke-test that the app can be imported.
	$(PYTHON) -c "from app import create_app; app = create_app(); print('OK:', app)"

run: ## Run the dev server.
	$(PYTHON) main.py

docker-build: ## Build the Docker image.
	docker build -t aeo-agent:1.1.0 .

docker-run: ## Run the Docker container.
	docker run --rm -p 5000:5000 --env-file .env -v $$(pwd)/data:/app/data aeo-agent:1.1.0

clean: ## Remove caches and build artifacts.
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
