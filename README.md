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

## ✨ Features

- **Modern Architecture**: Built with Python 3.13, async/await, and Pydantic v2 models
- **API Integration**: Free exchange rate API with built-in caching and rate limiting
- **Smart Caching**: Configurable cache TTL with fallback to stale data and atomic writes
- **Alert System**: Set price alerts with above/below thresholds
- **Rich CLI**: Beautiful command-line interface with Click and Rich
- **Interactive Mode**: Full command-line interface for easy use
- **Multiple Output Formats**: JSON, CSV, and rich table output
- **Currency Validation**: Built-in ISO 4217 currency code validation
- **Advanced Logging**: Structured logging with file rotation and multiple formats
- **Environment Variables**: Full configuration via environment variables
- **Rate Limiting**: Built-in API rate limiting and protection
- **Configuration Management**: Built-in defaults with flexible overrides
- **Comprehensive Testing**: Full test suite with pytest and 80%+ coverage
- **Type Safety**: Strict mypy type checking for reliability
- **Security**: Input validation, secure file operations, and security policy
- **Modern CI/CD**: GitHub Actions with automated testing and linting
- **Developer Friendly**: Pre-commit hooks, EditorConfig, and comprehensive docs

## 🚀 Quick Start

### Prerequisites

- Python 3.13 or higher
- pip (Python package manager)
- Git (for installation from repository)

### Installation

**Recommended: Using pipx (easiest and safest)**

pipx installs CLI tools in isolated environments automatically:

```bash
# Install pipx (one-time setup)
brew install pipx
pipx ensurepath

# Install WiseRate
pipx install git+https://github.com/Amet13/WiseRate.git

# Or install specific version
pipx install git+https://github.com/Amet13/WiseRate.git@v2.3.0

# Verify installation
wiserate --version
```

**Alternative: Using pip in virtual environment**

```bash
# Create and activate virtual environment
python3 -m venv ~/.local/wiserate-env
source ~/.local/wiserate-env/bin/activate

# Install WiseRate
pip install git+https://github.com/Amet13/WiseRate.git

# Create a symlink for easy access (optional)
ln -s ~/.local/wiserate-env/bin/wiserate /usr/local/bin/wiserate

# Verify installation
wiserate --version
```

### Configuration

WiseRate can be configured using environment variables:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your preferences
# Supported variables:
# - WISERATE_API_URL: API endpoint URL
# - WISERATE_DATA_DIR: Data storage directory
# - WISERATE_CACHE_TTL: Cache duration in seconds (60-86400)
# - WISERATE_LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
# - WISERATE_MAX_REQUESTS_PER_MINUTE: Rate limit (10-120)
```

### Basic Usage

```bash
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
├── __init__.py         # Package initialization
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
- **Settings**: Configuration management with built-in defaults
- **Custom Exceptions**: Proper error handling with specific exception types
- **Utility Functions**: Currency validation, formatting, and file operations

## 🔧 Development

### Setup Development Environment

```bash
# Clone and setup
git clone https://github.com/Amet13/WiseRate.git
cd WiseRate

# Install development dependencies (creates venv automatically)
make install-dev

# Use make commands for common tasks
make help          # Show all available commands
make test          # Run all tests
make lint          # Run all linting tools
make format        # Format code with Black and isort
make clean         # Clean up generated files (including venv)

# Note: All make commands automatically use venv when available
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
