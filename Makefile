.PHONY: help install install-dev format lint test clean build release

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install ocalcli
	pip install -e .

install-dev: ## Install ocalcli with development dependencies
	pip install -e ".[dev]"

format: ## Format code with black and ruff
	black ocalcli tests
	ruff check --fix ocalcli tests

lint: ## Lint code with ruff
	ruff check ocalcli tests

test: ## Run tests
	pytest

test-integration: ## Run integration tests (requires OCALCLI_IT=1)
	OCALCLI_IT=1 pytest tests/integration/

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: ## Build package
	python -m build

release: ## Release to PyPI (requires twine)
	twine upload dist/*

check: format lint test ## Run all checks (format, lint, test)

dev-setup: install-dev ## Set up development environment
	@echo "Development environment set up!"
	@echo "Run 'make check' to verify everything is working."
