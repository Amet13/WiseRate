<div align="center">
  <img src="logo.png" alt="WiseRate Logo" width="200" style="border-radius: 20px;">
  <h1>WiseRate</h1>
  <p><strong>CLI tool for monitoring favorable currency exchange rates</strong></p>
  <p>
    <a href="https://github.com/Amet13/WiseRate/actions/workflows/ci.yml">
      <img src="https://github.com/Amet13/WiseRate/actions/workflows/ci.yml/badge.svg" alt="CI Status">
    </a>
    <a href="https://github.com/Amet13/WiseRate/blob/main/LICENSE">
      <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License">
    </a>
    <a href="https://github.com/Amet13/WiseRate/releases">
      <img src="https://img.shields.io/github/v/release/Amet13/WiseRate?label=version" alt="Latest Release">
    </a>
  </p>
</div>

WiseRate is a CLI tool for monitoring currency exchange rates, with support for alerts, caching, and an interactive mode.

## 🚀 Quick Start

### Prerequisites

- Python 3.14 or higher
- uv (ultra-fast Python package manager)
- just (modern command runner)

### Installation

**Recommended: Using uv (fastest)**

```bash
# Install globally (like pip install)
uv pip install --system git+https://github.com/Amet13/WiseRate.git@2.5.2
```

**Using pip:**

```bash
pip install git+https://github.com/Amet13/WiseRate.git@2.5.2
```

### Basic Usage

```bash
# Get exchange rate
wiserate rate USD EUR

# Set an alert
wiserate alert USD EUR 0.90 --below

# List all alerts
wiserate alerts

# Monitor alerts continuously
wiserate monitor --interval 600

# Update all rates
wiserate update

# View configuration
wiserate config

# List supported currencies
wiserate currencies
```

## 📖 Documentation

### Configuration

WiseRate can be configured via environment variables:

```bash
# API Configuration
export WISERATE_API_URL="https://api.exchangerate-api.com/v4"

# Cache Configuration
export WISERATE_CACHE_TTL=3600  # Cache for 1 hour

# Data Directory
export WISERATE_DATA_DIR="$HOME/.wiserate"

# Logging
export WISERATE_LOG_LEVEL="INFO"
export WISERATE_LOG_FILE="$HOME/.wiserate/wiserate.log"

# Rate Limiting
export WISERATE_MAX_REQUESTS_PER_MINUTE=60
```

### Commands

#### Get Exchange Rate

```bash
wiserate rate SOURCE TARGET [--update]
```

Examples:

- `wiserate rate USD EUR` - Get USD to EUR rate
- `wiserate rate GBP JPY --update` - Force update from API

#### Set Alert

```bash
wiserate alert SOURCE TARGET THRESHOLD [--above|--below]
```

Examples:

- `wiserate alert USD EUR 0.90 --below` - Alert when USD/EUR drops below 0.90
- `wiserate alert GBP USD 1.25 --above` - Alert when GBP/USD rises above 1.25

#### List Alerts

```bash
wiserate alerts
```

Shows all active alerts with their current status.

#### Remove Alert

```bash
wiserate remove-alert SOURCE TARGET
```

#### Monitor Alerts

```bash
wiserate monitor [--interval SECONDS]
```

Continuously monitors all alerts and triggers notifications when thresholds are met.

#### Update All Rates

```bash
wiserate update
```

Fetches fresh rates for all currency pairs.

#### Export Data

```bash
wiserate export [--format json|csv|table]
```

Exports all rates and alerts in the specified format.

#### Validate Currency

```bash
wiserate validate-currency CURRENCY_CODE
```

Validates if a currency code is supported.

#### List Currencies

```bash
wiserate currencies
```

Lists all supported currency codes.

## 🛠️ Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/Amet13/WiseRate.git
cd WiseRate

# Install development dependencies
just install-dev
```

### Running Tests

```bash
# Run all tests
just test

# Run with coverage
just test-coverage

# Run specific test file
just test-file tests/test_config.py
```

### Code Quality

The project uses several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **Ruff**: Fast linting and code quality (10-100x faster than flake8)
- **mypy**: Type checking
- **pyright**: Additional type checking
- **pre-commit**: Git hooks for quality checks

All tools can be run individually or together using `just` commands:

```bash
# Code Quality
just fmt            # Format code (Black + Ruff + isort)
just lint           # Run all linting tools (Black + Ruff + mypy)
just ruff           # Run ruff linter only
just ruff-fmt       # Run ruff formatter only
just type-check     # Run type checking with mypy
just pyright-check  # Run additional type checking with pyright

# Testing
just test           # Run all tests
just test-verbose   # Run tests with verbose output
just test-file FILE # Run specific test file
just test-coverage  # Run tests with coverage report

# Development
just install-dev    # Install development dependencies
just install       # Install package in editable mode
just clean         # Clean build artifacts
just build         # Build distribution package
just check         # Run lint + test
just ci            # Run full CI checks (fmt + lint + test + build)

# CLI
just run *ARGS     # Run the CLI application
just help-cli      # Show CLI help
just version       # Show version information
just info          # Show environment information
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
