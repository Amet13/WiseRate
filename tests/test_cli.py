"""Tests for CLI functionality."""

import pytest
from click.testing import CliRunner

from wiserate.cli import cli


class TestCLI:
    """Test CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    def test_cli_help(self, runner):
        """Test CLI help command."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "WiseRate" in result.output
        assert "Modern CLI tool" in result.output

    def test_cli_version(self, runner):
        """Test CLI version command."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "2.3.0" in result.output

    def test_config_command(self, runner):
        """Test config command."""
        result = runner.invoke(cli, ["config"])
        assert result.exit_code == 0
        assert "Configuration" in result.output

    def test_currencies_command(self, runner):
        """Test currencies command."""
        result = runner.invoke(cli, ["currencies"])
        assert result.exit_code == 0
        assert "USD" in result.output
        assert "EUR" in result.output

    def test_validate_currency_valid(self, runner):
        """Test currency validation with valid code."""
        result = runner.invoke(cli, ["validate-currency", "USD"])
        assert result.exit_code == 0
        assert "valid currency code" in result.output

    def test_validate_currency_invalid(self, runner):
        """Test currency validation with invalid code."""
        result = runner.invoke(cli, ["validate-currency", "XXX"])
        assert result.exit_code == 0
        assert "not a valid currency code" in result.output
