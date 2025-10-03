# Contributing to WiseRate

Thank you for your interest in contributing to WiseRate! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/WiseRate.git
   cd WiseRate
   ```
3. **Add the upstream repository**:
   ```bash
   git remote add upstream https://github.com/Amet13/WiseRate.git
   ```

## Development Setup

1. **Install Python 3.13** (required)

2. **Create a virtual environment**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**:

   ```bash
   make install-dev
   ```

4. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

## Making Changes

1. **Create a new branch** for your changes:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the code style guidelines

3. **Add tests** for any new functionality

4. **Run the test suite**:

   ```bash
   make test
   ```

5. **Run linting and formatting**:
   ```bash
   make format
   make lint
   ```

## Testing

We use pytest for testing. All new features and bug fixes should include tests.

### Running Tests

```bash
# Run all tests
make test

# Run tests with verbose output
make test-verbose

# Run specific test file
make test-file FILE=tests/test_config.py

# Run tests with coverage
make test-coverage
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files as `test_*.py`
- Name test functions as `test_*`
- Use descriptive test names that explain what is being tested
- Follow the AAA pattern: Arrange, Act, Assert

Example:

```python
def test_currency_pair_validation():
    """Test that currency pair validation works correctly."""
    # Arrange
    source = "USD"
    target = "EUR"

    # Act
    pair = CurrencyPair(source=source, target=target)

    # Assert
    assert pair.source == source
    assert pair.target == target
```

## Code Style

We follow PEP 8 and use the following tools:

- **Black**: Code formatting (line length: 100)
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

### Code Style Guidelines

1. **Type Hints**: Use type hints for all function parameters and return values
2. **Docstrings**: Use Google-style docstrings for all modules, classes, and functions
3. **Line Length**: Maximum 100 characters
4. **Imports**: Sort imports using isort (will be done automatically by pre-commit)
5. **Naming Conventions**:
   - Classes: `PascalCase`
   - Functions/Variables: `snake_case`
   - Constants: `UPPER_SNAKE_CASE`
   - Private members: `_leading_underscore`

### Example Docstring

```python
def get_exchange_rate(source: str, target: str) -> ExchangeRate:
    """Get the exchange rate between two currencies.

    Args:
        source: The source currency code (e.g., 'USD')
        target: The target currency code (e.g., 'EUR')

    Returns:
        ExchangeRate object containing the rate information

    Raises:
        ValidationError: If currency codes are invalid
        APIError: If the API request fails
    """
    pass
```

## Submitting Changes

1. **Commit your changes** with descriptive commit messages:

   ```bash
   git commit -m "feat: add new feature"
   ```

   We follow [Conventional Commits](https://www.conventionalcommits.org/):

   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `style:` Code style changes (formatting, etc.)
   - `refactor:` Code refactoring
   - `test:` Adding or updating tests
   - `chore:` Maintenance tasks

2. **Push to your fork**:

   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create a Pull Request** on GitHub:
   - Use a clear and descriptive title
   - Describe what changes you made and why
   - Reference any related issues
   - Ensure all CI checks pass

## Pull Request Checklist

Before submitting a pull request, ensure:

- [ ] Code follows the project's style guidelines
- [ ] All tests pass (`make test`)
- [ ] New tests added for new functionality
- [ ] Documentation updated if needed
- [ ] Pre-commit hooks pass
- [ ] Commit messages follow conventional commits format
- [ ] Branch is up to date with main

## Questions?

If you have questions about contributing, feel free to:

- Open an issue on GitHub
- Contact the maintainers

Thank you for contributing to WiseRate! 🎉
