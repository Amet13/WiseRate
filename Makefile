.PHONY: help install install-dev test test-verbose test-file test-coverage lint format type-check clean build check ci release version

help: ## Show this help message
	@echo "WiseRate - Modern CLI Tool for Monitoring Favorable Exchange Rates"
	@echo "================================================"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package using pipx (recommended)
	@echo "For regular installation, use pipx:"
	@echo "  pipx install -e ."
	@echo ""
	@echo "For development, use: make install-dev"

install-dev: ## Install development dependencies (uses venv)
	@if [ ! -d "venv" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv venv; \
		echo "✅ Virtual environment created!"; \
	fi
	@echo "Installing in development mode..."
	./venv/bin/pip install -e ".[dev]"
	./venv/bin/pre-commit install
	@echo ""
	@echo "✅ Development environment ready!"
	@echo "Note: Commands in Makefile will use venv automatically"

test: ## Run tests
	@if [ -d "venv" ]; then \
		./venv/bin/python -m pytest -v; \
	else \
		python3 -m pytest -v; \
	fi

test-verbose: ## Run tests with verbose output
	@if [ -d "venv" ]; then \
		./venv/bin/python -m pytest -v --tb=short; \
	else \
		python3 -m pytest -v --tb=short; \
	fi

test-file: ## Run specific test file (FILE=path/to/test.py)
	@if [ -d "venv" ]; then \
		./venv/bin/python -m pytest -v $(FILE); \
	else \
		python3 -m pytest -v $(FILE); \
	fi

test-coverage: ## Run tests with coverage report
	@if [ -d "venv" ]; then \
		./venv/bin/python -m pytest -v --cov=src/wiserate --cov-report=html --cov-report=term-missing --cov-report=xml --cov-fail-under=80; \
	else \
		python3 -m pytest -v --cov=src/wiserate --cov-report=html --cov-report=term-missing --cov-report=xml --cov-fail-under=80; \
	fi

lint: ## Run all linting checks
	@if [ -d "venv" ]; then \
		./venv/bin/python -m black --check --diff src/ tests/; \
		./venv/bin/python -m isort --check-only --diff src/ tests/; \
		./venv/bin/python -m flake8 src/ tests/; \
		./venv/bin/python -m mypy src/; \
	else \
		python3 -m black --check --diff src/ tests/; \
		python3 -m isort --check-only --diff src/ tests/; \
		python3 -m flake8 src/ tests/; \
		python3 -m mypy src/; \
	fi

type-check: ## Run type checking only
	@if [ -d "venv" ]; then \
		./venv/bin/python -m mypy src/; \
	else \
		python3 -m mypy src/; \
	fi

format: ## Format code
	@if [ -d "venv" ]; then \
		./venv/bin/python -m black src/ tests/; \
		./venv/bin/python -m isort src/ tests/; \
	else \
		python3 -m black src/ tests/; \
		python3 -m isort src/ tests/; \
	fi

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf venv/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build: ## Build package
	python3 -m pip install --upgrade build
	python3 -m build

check: ## Run all checks (lint + test)
	make lint
	make test

ci: ## Run CI checks locally
	make format
	make lint
	make test
	make build

version: ## Show current version across all files
	@echo "Current version information:"
	@echo "pyproject.toml: $(shell grep '^version = ' pyproject.toml | cut -d'"' -f2)"
	@echo "src/wiserate/__init__.py: $(shell grep '__version__ = ' src/wiserate/__init__.py | cut -d'"' -f2)"
	@echo "src/wiserate/cli.py: $(shell grep '@click.version_option' src/wiserate/cli.py | sed 's/.*version="\([^"]*\)".*/\1/')"
	@echo "README.md: $(shell grep 'pip install git+.*@v' README.md | sed 's/.*@v\([^"]*\)/\1/')"

release: ## Prepare release (VERSION=x.y.z)
	@echo "Preparing release $(VERSION)..."
	@echo "1. Updating version in pyproject.toml..."
	@sed -i '' 's/^version = ".*"/version = "$(VERSION)"/' pyproject.toml
	@echo "2. Updating version in src/wiserate/__init__.py..."
	@sed -i '' 's/__version__ = ".*"/__version__ = "$(VERSION)"/' src/wiserate/__init__.py
	@echo "3. Updating version in src/wiserate/cli.py..."
	@sed -i '' 's/@click\.version_option(version=".*", prog_name="WiseRate")/@click.version_option(version="$(VERSION)", prog_name="WiseRate")/' src/wiserate/cli.py
	@echo "4. Updating version in README.md..."
	@sed -i '' 's|pip install git+https://github.com/Amet13/WiseRate.git@v.*|pip install git+https://github.com/Amet13/WiseRate.git@v$(VERSION)|' README.md
	@echo "5. Building package..."
	@make build
	@echo "6. Running tests..."
	@make test
	@echo "Release $(VERSION) prepared successfully!"
	@echo "Next steps:"
	@echo "  git add ."
	@echo "  git commit -m 'chore: prepare release $(VERSION)'"
	@echo "  git tag $(VERSION)"
	@echo "  git push origin main --tags"
