# WiseRate - Modern Justfile for task automation
# Requires: uv (https://github.com/astral-sh/uv)
# Install: curl -LsSf https://astral.sh/uv/install.sh | sh

set shell := ["bash", "-c"]
set dotenv-load := true

# Default recipe when running `just`
default: help

# Show all available recipes
help:
    @echo "WiseRate - Modern CLI Tool for Monitoring Favorable Exchange Rates"
    @echo "================================================"
    @echo ""
    @echo "Available commands:"
    @just --list

# Install development dependencies using uv
install-dev:
    #!/usr/bin/env bash
    echo "Installing development dependencies with uv..."
    uv sync --all-extras
    uv run pre-commit install
    echo ""
    echo "✅ Development environment ready!"

# Install the package using uv in editable mode
install:
    uv sync --no-dev

# Run all tests with pytest
test:
    #!/usr/bin/env bash
    echo "Running tests..."
    uv run pytest tests/ -v

# Run tests with verbose output and short traceback
test-verbose:
    uv run pytest tests/ -v --tb=short

# Run specific test file
test-file FILE="tests/test_app.py":
    uv run pytest "{{FILE}}" -v

# Run tests with coverage report
test-coverage:
    #!/usr/bin/env bash
    echo "Running tests with coverage..."
    uv run pytest tests/ -v \
        --cov=src/wiserate \
        --cov-report=html \
        --cov-report=term-missing \
        --cov-report=xml \
        --cov-fail-under=60
    echo ""
    echo "✅ Coverage report generated in htmlcov/index.html"

# Run all code quality checks
lint:
    #!/usr/bin/env bash
    echo "Running code quality checks..."
    uv run black --check --diff src/ tests/
    uv run ruff check src/ tests/
    uv run mypy src/
    echo ""
    echo "✅ All code quality checks passed!"

# Format code with black, ruff, and isort
fmt:
    #!/usr/bin/env bash
    echo "Formatting code..."
    uv run black src/ tests/
    uv run ruff check --fix src/ tests/
    uv run ruff format src/ tests/
    uv run isort src/ tests/
    echo "✅ Code formatted!"

# Format check (for CI - fails if code needs formatting)
fmt-check:
    #!/usr/bin/env bash
    echo "Checking code formatting..."
    uv run black --check src/ tests/ || exit 1
    uv run ruff check src/ tests/ || exit 1
    uv run isort --check-only src/ tests/ || exit 1
    echo "✅ Code formatting check passed!"

# Run type checking with mypy
type-check:
    uv run mypy src/

# Run type checking with pyright (additional type checker)
pyright-check:
    uv run pyright src/

# Run ruff linter
ruff:
    uv run ruff check src/ tests/

# Run ruff formatter
ruff-fmt:
    uv run ruff format src/ tests/

# Clean build artifacts
clean:
    #!/usr/bin/env bash
    echo "Cleaning build artifacts..."
    rm -rf build/
    rm -rf dist/
    rm -rf *.egg-info/
    rm -rf htmlcov/
    rm -rf .coverage
    rm -rf .pytest_cache/
    rm -rf .mypy_cache/
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    echo "✅ Clean complete!"

# Build distribution package
build: clean
    #!/usr/bin/env bash
    echo "Building distribution package..."
    uv build
    echo "✅ Build complete!"

# Run all checks locally (lint + test)
check: lint test
    @echo ""
    @echo "✅ All checks passed!"

# Run CI checks locally (format + lint + test + build)
ci: fmt lint test build
    @echo ""
    @echo "✅ CI checks passed!"

# Show current version across all files
version:
    #!/usr/bin/env bash
    echo "Current version information:"
    echo "pyproject.toml: $(grep '^version = ' pyproject.toml | cut -d'"' -f2)"
    echo "src/wiserate/__init__.py: $(grep '__version__ = ' src/wiserate/__init__.py | cut -d'"' -f2)"
    echo "src/wiserate/cli.py: $(grep '@click.version_option' src/wiserate/cli.py | sed 's/.*version="\([^"]*\)".*/\1/')"
    echo "README.md: $(grep 'uv add.*@' README.md | grep -oE '@[0-9]+\.[0-9]+\.[0-9]+' | head -1 | sed 's/@//')"

# Prepare release with version bump
release VERSION:
    #!/usr/bin/env bash
    set -e
    echo "Preparing release {{VERSION}}..."

    echo "1. Updating version in pyproject.toml..."
    sed -i '' 's/^version = ".*"/version = "{{VERSION}}"/' pyproject.toml

    echo "2. Updating version in src/wiserate/__init__.py..."
    sed -i '' 's/__version__ = ".*"/__version__ = "{{VERSION}}"/' src/wiserate/__init__.py

    echo "3. Updating version in src/wiserate/cli.py..."
    sed -i '' 's/@click\.version_option(version=".*", prog_name="WiseRate")/@click.version_option(version="{{VERSION}}", prog_name="WiseRate")/' src/wiserate/cli.py

    echo "4. Updating version in README.md..."
    # Update all installation commands to use the new version (handles both with and without 'v' prefix)
    sed -i '' 's|git+https://github.com/Amet13/WiseRate.git@v\?[0-9]\+\.[0-9]\+\.[0-9]\+|git+https://github.com/Amet13/WiseRate.git@{{VERSION}}|g' README.md

    echo "5. Verifying all versions are updated correctly..."
    PYPROJECT_VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
    INIT_VERSION=$(grep '__version__ = ' src/wiserate/__init__.py | cut -d'"' -f2)
    CLI_VERSION=$(grep '@click.version_option' src/wiserate/cli.py | sed 's/.*version="\([^"]*\)".*/\1/')
    README_VERSION=$(grep -E 'uv (pip install|add).*@' README.md | grep -oE '@[0-9]+\.[0-9]+\.[0-9]+' | head -1 | sed 's/@//')

    if [ "$PYPROJECT_VERSION" != "{{VERSION}}" ] || \
       [ "$INIT_VERSION" != "{{VERSION}}" ] || \
       [ "$CLI_VERSION" != "{{VERSION}}" ] || \
       [ "$README_VERSION" != "{{VERSION}}" ]; then
        echo "❌ Error: Version mismatch detected!"
        echo "Expected: {{VERSION}}"
        echo "pyproject.toml: $PYPROJECT_VERSION"
        echo "src/wiserate/__init__.py: $INIT_VERSION"
        echo "src/wiserate/cli.py: $CLI_VERSION"
        echo "README.md: $README_VERSION"
        exit 1
    fi
    echo "✅ All versions match: {{VERSION}}"

    echo "6. Building package..."
    just build

    echo "7. Running tests..."
    just test

    echo ""
    echo "Release {{VERSION}} prepared successfully!"
    echo "Next steps:"
    echo "  git add ."
    echo "  git commit -m 'chore: prepare release {{VERSION}}'"
    echo "  git tag {{VERSION}}"
    echo "  git push origin main --tags"

# Update dependencies
update-deps:
    #!/usr/bin/env bash
    echo "Updating dependencies..."
    uv sync --upgrade
    echo "✅ Dependencies updated!"

# Show Python version and environment info
info:
    #!/usr/bin/env bash
    echo "Environment Information:"
    echo "========================"
    python3 --version
    uv --version
    echo ""
    echo "Python Info:"
    python3 -c "import sys; print(f'Python: {sys.version}')"
    echo ""
    echo "Project Info:"
    just version

# Run the CLI application
run *ARGS:
    uv run python -m wiserate.cli {{ARGS}}

# Run CLI help
help-cli:
    uv run python -m wiserate.cli --help
