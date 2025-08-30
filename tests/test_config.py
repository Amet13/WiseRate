"""Tests for configuration management."""

from pathlib import Path

import pytest

from wiserate.config import Settings
from wiserate.constants import (
    DEFAULT_CACHE_TTL,
    DEFAULT_LOG_LEVEL,
    DEFAULT_MAX_REQUESTS_PER_MINUTE,
    MAX_CACHE_TTL,
    MAX_REQUESTS_PER_MINUTE,
    MIN_CACHE_TTL,
    MIN_REQUESTS_PER_MINUTE,
    SUPPORTED_LOG_LEVELS,
)


class TestSettings:
    """Test Settings class."""

    def test_default_settings(self):
        """Test default configuration values."""
        settings = Settings()

        assert settings.wise_api_key is None
        assert settings.wise_api_url == "https://api.wise.com/v1"
        assert settings.fallback_api_url == "https://api.exchangerate-api.com/v4"
        assert settings.cache_ttl == DEFAULT_CACHE_TTL
        assert settings.log_level == DEFAULT_LOG_LEVEL
        assert settings.max_requests_per_minute == DEFAULT_MAX_REQUESTS_PER_MINUTE
        assert settings.data_dir == Path.home() / ".wiserate"

    def test_custom_settings(self, tmp_path):
        """Test custom configuration values."""
        custom_data_dir = tmp_path / "custom_path"
        custom_cache_ttl = 7200
        custom_log_level = "DEBUG"
        custom_max_requests = 30

        settings = Settings(
            data_dir=custom_data_dir,
            cache_ttl=custom_cache_ttl,
            log_level=custom_log_level,
            max_requests_per_minute=custom_max_requests,
        )

        assert settings.data_dir == custom_data_dir
        assert settings.cache_ttl == custom_cache_ttl
        assert settings.log_level == custom_log_level
        assert settings.max_requests_per_minute == custom_max_requests

    def test_environment_variables(self, monkeypatch):
        """Test environment variable configuration."""
        monkeypatch.setenv("WISE_API_KEY", "test_key_123")
        monkeypatch.setenv("WISERATE_CACHE_TTL", "1800")
        monkeypatch.setenv("WISERATE_LOG_LEVEL", "WARNING")
        monkeypatch.setenv("WISERATE_MAX_REQUESTS_PER_MINUTE", "45")

        settings = Settings()

        assert settings.wise_api_key == "test_key_123"
        assert settings.cache_ttl == 1800
        assert settings.log_level == "WARNING"
        assert settings.max_requests_per_minute == 45

    def test_data_directory_creation(self, tmp_path):
        """Test that data directory is created automatically."""
        custom_data_dir = tmp_path / "wiserate_data"
        _ = Settings(data_dir=custom_data_dir)

        assert custom_data_dir.exists()
        assert custom_data_dir.is_dir()

    def test_file_paths(self, tmp_path):
        """Test file path properties."""
        custom_data_dir = tmp_path / "wiserate_data"
        _ = Settings(data_dir=custom_data_dir)

        assert custom_data_dir.exists()
        assert custom_data_dir.is_dir()


class TestSettingsValidation:
    """Test configuration validation."""

    def test_cache_ttl_validation_valid(self):
        """Test valid cache TTL values."""
        # Test minimum value
        settings = Settings(cache_ttl=MIN_CACHE_TTL)
        assert settings.cache_ttl == MIN_CACHE_TTL

        # Test maximum value
        settings = Settings(cache_ttl=MAX_CACHE_TTL)
        assert settings.cache_ttl == MAX_CACHE_TTL

        # Test default value
        settings = Settings(cache_ttl=DEFAULT_CACHE_TTL)
        assert settings.cache_ttl == DEFAULT_CACHE_TTL

    def test_cache_ttl_validation_invalid(self):
        """Test invalid cache TTL values."""
        # Test below minimum
        with pytest.raises(
            ValueError,
            match=f"Cache TTL must be between {MIN_CACHE_TTL} and {MAX_CACHE_TTL} seconds",
        ):
            Settings(cache_ttl=MIN_CACHE_TTL - 1)

        # Test above maximum
        with pytest.raises(
            ValueError,
            match=f"Cache TTL must be between {MIN_CACHE_TTL} and {MAX_CACHE_TTL} seconds",
        ):
            Settings(cache_ttl=MAX_CACHE_TTL + 1)

    def test_max_requests_validation_valid(self):
        """Test valid max requests values."""
        # Test minimum value
        settings = Settings(max_requests_per_minute=MIN_REQUESTS_PER_MINUTE)
        assert settings.max_requests_per_minute == MIN_REQUESTS_PER_MINUTE

        # Test maximum value
        settings = Settings(max_requests_per_minute=MAX_REQUESTS_PER_MINUTE)
        assert settings.max_requests_per_minute == MAX_REQUESTS_PER_MINUTE

        # Test default value
        settings = Settings(max_requests_per_minute=DEFAULT_MAX_REQUESTS_PER_MINUTE)
        assert settings.max_requests_per_minute == DEFAULT_MAX_REQUESTS_PER_MINUTE

    def test_max_requests_validation_invalid(self):
        """Test invalid max requests values."""
        # Test below minimum
        with pytest.raises(
            ValueError,
            match=(
                f"Max requests per minute must be between "
                f"{MIN_REQUESTS_PER_MINUTE} and {MAX_REQUESTS_PER_MINUTE}"
            ),
        ):
            Settings(max_requests_per_minute=MIN_REQUESTS_PER_MINUTE - 1)

        # Test above maximum
        with pytest.raises(
            ValueError,
            match=(
                f"Max requests per minute must be between "
                f"{MIN_REQUESTS_PER_MINUTE} and {MAX_REQUESTS_PER_MINUTE}"
            ),
        ):
            Settings(max_requests_per_minute=MAX_REQUESTS_PER_MINUTE + 1)

    def test_log_level_validation_valid(self):
        """Test valid log level values."""
        for level in SUPPORTED_LOG_LEVELS:
            settings = Settings(log_level=level)
            assert settings.log_level == level.upper()

    def test_log_level_validation_invalid(self):
        """Test invalid log level values."""
        invalid_levels = ["INVALID", "UNKNOWN", "CUSTOM", ""]

        for level in invalid_levels:
            with pytest.raises(
                ValueError,
                match=f"Log level must be one of: {', '.join(SUPPORTED_LOG_LEVELS)}",
            ):
                Settings(log_level=level)

    def test_log_level_case_insensitive(self):
        """Test that log levels are case-insensitive."""
        settings = Settings(log_level="debug")
        assert settings.log_level == "DEBUG"

        settings = Settings(log_level="Warning")
        assert settings.log_level == "WARNING"

        settings = Settings(log_level="ERROR")
        assert settings.log_level == "ERROR"


class TestSettingsEnvironment:
    """Test environment variable handling."""

    def test_wise_api_key_environment(self, monkeypatch):
        """Test WISE_API_KEY environment variable."""
        # Test with key
        monkeypatch.setenv("WISE_API_KEY", "env_key_123")
        settings = Settings()
        assert settings.wise_api_key == "env_key_123"

        # Test without key
        monkeypatch.delenv("WISE_API_KEY", raising=False)
        settings = Settings()
        assert settings.wise_api_key is None

    def test_wise_api_url_environment(self, monkeypatch):
        """Test WISE_API_URL environment variable."""
        custom_url = "https://custom.wise.api/v2"
        monkeypatch.setenv("WISE_API_URL", custom_url)
        settings = Settings()
        assert settings.wise_api_url == custom_url

    def test_fallback_api_url_environment(self, monkeypatch):
        """Test FALLBACK_API_URL environment variable."""
        custom_url = "https://custom.fallback.api/v3"
        monkeypatch.setenv("FALLBACK_API_URL", custom_url)
        settings = Settings()
        assert settings.fallback_api_url == custom_url

    def test_data_dir_environment(self, monkeypatch, tmp_path):
        """Test WISERATE_DATA_DIR environment variable."""
        custom_dir = str(tmp_path / "custom_data")
        monkeypatch.setenv("WISERATE_DATA_DIR", custom_dir)
        settings = Settings()
        assert settings.data_dir == Path(custom_dir)

    def test_cache_ttl_environment(self, monkeypatch):
        """Test WISERATE_CACHE_TTL environment variable."""
        monkeypatch.setenv("WISERATE_CACHE_TTL", "7200")
        settings = Settings()
        assert settings.cache_ttl == 7200

    def test_log_level_environment(self, monkeypatch):
        """Test WISERATE_LOG_LEVEL environment variable."""
        monkeypatch.setenv("WISERATE_LOG_LEVEL", "DEBUG")
        settings = Settings()
        assert settings.log_level == "DEBUG"

    def test_max_requests_environment(self, monkeypatch):
        """Test WISERATE_MAX_REQUESTS_PER_MINUTE environment variable."""
        monkeypatch.setenv("WISERATE_MAX_REQUESTS_PER_MINUTE", "90")
        settings = Settings()
        assert settings.max_requests_per_minute == 90
