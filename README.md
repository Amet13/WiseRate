<div align="center">
  <img src="logo.png" alt="WiseRate Logo" width="200" style="border-radius: 20px;">
  <h1>WiseRate</h1>
  <p><strong>CLI tool for monitoring favorable currency exchange rates from Wise</strong></p>
  <p>
    <a href="https://github.com/Amet13/wiserate/actions/workflows/ci.yml">
      <img src="https://github.com/Amet13/wiserate/actions/workflows/ci.yml/badge.svg" alt="CI Status">
    </a>
    <a href="https://github.com/Amet13/wiserate/blob/main/LICENSE">
      <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License">
    </a>
    <a href="https://www.python.org/downloads/">
      <img src="https://img.shields.io/badge/python-3.13-blue.svg" alt="Python 3.13">
    </a>
    <a href="https://github.com/psf/black">
      <img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style: black">
    </a>
  </p>
</div>

WiseRate is a CLI tool for monitoring favorable currency exchange rates from Wise, with support for alerts, caching, multiple API providers, and an interactive mode.

## ✨ Features

- **Modern Architecture**: Built with Python 3.13, async/await, and Pydantic v2 models
- **Multiple API Support**: Wise API (primary for favorable rates) + fallback free APIs
- **Smart Caching**: Configurable cache TTL with fallback to stale data
- **Alert System**: Set price alerts with above/below thresholds
- **Rich CLI**: Beautiful command-line interface with Click and Rich
- **Interactive Mode**: Full command-line interface for easy use
- **Multiple Output Formats**: JSON, CSV, and rich table output
- **Currency Validation**: Built-in ISO 4217 currency code validation
- **Structured Logging**: JSON logging with configurable levels
- **Rate Limiting**: Built-in API rate limiting and protection
- **Configuration Management**: Environment variables + .env file support
- **Comprehensive Testing**: Full test suite with pytest (67 tests)
- **Modern CI/CD**: GitHub Actions with automated testing and linting

## 🚀 Quick Start

### Prerequisites

- Python 3.13
- Wise API Key (optional, for better rates)

### Installation

#### Option 1: Install from GitHub Release (Recommended)

```bash
# Install latest version from main branch
pip install git+https://github.com/Amet13/WiseRate.git

# Or install specific version
pip install git+https://github.com/Amet13/WiseRate.git@v2.0.0
```

#### Option 2: Development Installation

```bash
# Clone the repository
git clone https://github.com/Amet13/WiseRate.git
cd WiseRate

# Install in development mode
pip install -e ".[dev]"

# To uninstall later:
# pip uninstall WiseRate
```

### Configuration

Create a `.env` file in your project directory:

```bash
# Optional - Wise API (for favorable rates)
WISE_API_KEY=your_wise_api_key_here

# Optional - Custom settings
WISERATE_DATA_DIR=~/.wiserate
WISERATE_CACHE_TTL=3600
WISERATE_LOG_LEVEL=INFO
```

### Basic Usage

```bash
# Test your configuration
wiserate test

# Get current exchange rate
wiserate rate EUR USD

# Update cache and get rate
wiserate rate EUR USD --update

# Set an alert when 1 EUR > 70 RUB
wiserate alert EUR RUB 70

# Set an alert when 1 GBP < 1.25 USD
wiserate alert GBP USD 1.25 --below

# List all active alerts
wiserate alerts

# Remove an alert
wiserate remove-alert EUR RUB

# Update all currency rates
wiserate update

# Start monitoring loop (check alerts every 10 minutes)
wiserate monitor --interval 600

# Show current configuration
wiserate config

# List all supported currencies
wiserate currencies

# Validate a currency code
wiserate validate-currency EUR

# Export data in different formats
wiserate export --format json
wiserate export --format csv

# Start interactive mode
wiserate interactive
```

## 🏗️ Architecture

```
src/wiserate/
├── __init__.py          # Package initialization
├── app.py              # Main application orchestrator
├── cli.py              # Command-line interface
├── config.py           # Configuration management
├── models.py           # Pydantic v2 data models
├── exchange.py         # Exchange rate service
├── alerts.py           # Alert management service
├── exceptions.py       # Custom exception classes
├── utils.py            # Utility functions
└── constants.py        # Configuration constants
```

### Key Components

- **WiseRateApp**: Main application class that orchestrates all services
- **ExchangeRateService**: Handles API calls, caching, and rate management
- **AlertService**: Handles alert creation, monitoring, and notifications
- **Settings**: Configuration management with environment variable support
- **Custom Exceptions**: Proper error handling with specific exception types
- **Utility Functions**: Currency validation, formatting, and file operations

## 🔧 Development

### Setup Development Environment

```bash
# Clone and setup
git clone https://github.com/Amet13/WiseRate.git
cd WiseRate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Use make commands for common tasks
make help          # Show all available commands
make test          # Run all tests
make lint          # Run all linting tools
make format        # Format code with Black and isort
make clean         # Clean up generated files
```

### Running Tests

```bash
# Run all tests
make test

# Run tests with verbose output
make test-verbose

# Run specific test file
make test-file FILE=tests/test_exchange.py

# Run tests with coverage (if coverage tools installed)
make test-coverage
```

### Code Quality

The project uses several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pre-commit**: Git hooks for quality checks

All tools can be run individually or together using `make` commands:

```bash
make format        # Format code (Black + isort)
make lint          # Run all linting tools
make type-check    # Run type checking with mypy
```

## 📊 API Providers

### Primary: Wise API

- **URL**: `https://api.wise.com/v1`
- **Authentication**: Bearer token
- **Rate Limits**: Varies by plan
- **Coverage**: 170+ currencies
- **Purpose**: Get favorable exchange rates for monitoring and alerts

### Fallback: Free APIs

- **Exchangerate-API**: `https://api.exchangerate-api.com/v4`
- **No authentication required**
- **Rate Limits**: Generous free tier
- **Coverage**: 170+ currencies

## 🔒 Security Features

- Environment variable configuration (no hardcoded secrets)
- Rate limiting to prevent API abuse
- Input validation with Pydantic v2 models
- Secure error handling (no sensitive data exposure)
- Custom exception handling for better security
- Input sanitization and validation

## 📈 Monitoring & Alerts

### Alert Types

- **Above Threshold**: Notify when rate goes above specified value
- **Below Threshold**: Notify when rate goes below specified value

### Monitoring Modes

- **Manual**: Check rates on-demand
- **Scheduled**: Regular updates via cron/systemd
- **Continuous**: Background monitoring loop

### Example Cron Jobs

```bash
# Check rates every hour
0 * * * * cd /path/to/wiserate && wiserate update

# Monitor alerts every 15 minutes
*/15 * * * * cd /path/to/wiserate && wiserate monitor --interval 900
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
