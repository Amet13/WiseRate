.PHONY: help install install-dev test test-verbose test-file test-coverage lint format type-check clean build check ci release changelog version

help: ## Show this help message
	@echo "WiseRate - Modern CLI Tool for Monitoring Favorable Exchange Rates from Wise"
	@echo "================================================"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package
	pip install -e .

install-dev: ## Install development dependencies
	pip install -e ".[dev]"
	pre-commit install

test: ## Run tests
	pytest -v

test-verbose: ## Run tests with verbose output
	pytest -v --tb=short

test-file: ## Run specific test file (FILE=path/to/test.py)
	pytest -v $(FILE)

test-coverage: ## Run tests with coverage report
	pytest -v --cov=wiserate --cov-report=html --cov-report=term-missing

lint: ## Run all linting checks
	black --check --diff src/ tests/
	isort --check-only --diff src/ tests/
	flake8 src/ tests/
	mypy src/

type-check: ## Run type checking only
	mypy src/

format: ## Format code
	black src/ tests/
	isort src/ tests/

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build: ## Build package
	python -m pip install --upgrade build
	python -m build

check: ## Run all checks (lint + test)
	make lint
	make test

ci: ## Run CI checks locally
	make format
	make lint
	make test
	make build

changelog: ## Generate changelog for a version (VERSION=x.y.z)
	python scripts/generate_changelog.py $(VERSION)

version: ## Show current version across all files
	@echo "Current version information:"
	@echo "pyproject.toml: $(shell grep '^version = ' pyproject.toml | cut -d'"' -f2)"
	@echo "src/wiserate/__init__.py: $(shell grep '__version__ = ' src/wiserate/__init__.py | cut -d'"' -f2)"
	@echo "src/wiserate/cli.py: $(shell grep '@click.version_option' src/wiserate/cli.py | sed 's/.*version="\([^"]*\)".*/\1/')"
	@echo "README.md: $(shell grep 'pip install git+.*@v' README.md | sed 's/.*@v\([^"]*\)/\1/')"

release: ## Prepare release (VERSION=x.y.z)
	@echo "Preparing release $(VERSION)..."
	@echo "1. Updating version in pyproject.toml..."
	@sed -i '' 's/version = ".*"/version = "$(VERSION)"/' pyproject.toml
	@echo "2. Updating version in src/wiserate/__init__.py..."
	@sed -i '' 's/__version__ = ".*"/__version__ = "$(VERSION)"/' src/wiserate/__init__.py
	@echo "3. Updating version in src/wiserate/cli.py..."
	@sed -i '' 's/@click\.version_option(version=".*", prog_name="WiseRate")/@click.version_option(version="$(VERSION)", prog_name="WiseRate")/' src/wiserate/cli.py
	@echo "4. Updating version in README.md..."
	@sed -i '' 's|pip install git+https://github.com/Amet13/WiseRate.git@v.*|pip install git+https://github.com/Amet13/WiseRate.git@v$(VERSION)|' README.md
	@echo "5. Generating changelog..."
	@make changelog VERSION=$(VERSION)
	@echo "6. Building package..."
	@make build
	@echo "7. Running tests..."
	@make test
	@echo "Release $(VERSION) prepared successfully!"
	@echo "Next steps:"
	@echo "  git add ."
	@echo "  git commit -m 'chore: prepare release $(VERSION)'"
	@echo "  git tag v$(VERSION)"
	@echo "  git push origin main --tags"
