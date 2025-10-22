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

        assert settings.api_url == "https://api.exchangerate-api.com/v4"
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

    def test_constructor_overrides(self):
        """Test custom configuration via constructor."""
        custom_settings = Settings(
            api_url="https://custom.api.com/v2",
            cache_ttl=1800,
            log_level="WARNING",
            max_requests_per_minute=45,
        )

        assert custom_settings.api_url == "https://custom.api.com/v2"
        assert custom_settings.cache_ttl == 1800
        assert custom_settings.log_level == "WARNING"
        assert custom_settings.max_requests_per_minute == 45

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


class TestSettingsOverrides:
    """Test configuration override handling."""

    def test_api_url_override(self):
        """Test API_URL configuration override."""
        custom_url = "https://custom.api/v2"
        settings = Settings(api_url=custom_url)
        assert settings.api_url == custom_url

    def test_cache_ttl_override(self):
        """Test cache TTL configuration override."""
        settings = Settings(cache_ttl=7200)
        assert settings.cache_ttl == 7200

    def test_data_dir_override(self, tmp_path):
        """Test data directory configuration override."""
        custom_dir = tmp_path / "custom_data"
        settings = Settings(data_dir=custom_dir)
        assert settings.data_dir == custom_dir

    def test_log_level_override(self):
        """Test log level configuration override."""
        settings = Settings(log_level="DEBUG")
        assert settings.log_level == "DEBUG"

    def test_max_requests_override(self):
        """Test max requests configuration override."""
        settings = Settings(max_requests_per_minute=90)
        assert settings.max_requests_per_minute == 90

    def test_cache_ttl_string_conversion(self):
        """Test cache TTL string to int conversion."""
        settings = Settings(cache_ttl="7200")
        assert settings.cache_ttl == 7200
        assert isinstance(settings.cache_ttl, int)

    def test_cache_ttl_string_conversion_invalid(self):
        """Test invalid cache TTL string conversion."""
        with pytest.raises(ValueError, match="Cache TTL must be a valid integer"):
            Settings(cache_ttl="invalid_number")

    def test_max_requests_string_conversion(self):
        """Test max requests string to int conversion."""
        settings = Settings(max_requests_per_minute="45")
        assert settings.max_requests_per_minute == 45
        assert isinstance(settings.max_requests_per_minute, int)

    def test_max_requests_string_conversion_invalid(self):
        """Test invalid max requests string conversion."""
        with pytest.raises(ValueError, match="Max requests per minute must be a valid integer"):
            Settings(max_requests_per_minute="invalid_number")

    def test_settings_model_config(self):
        """Test settings model configuration."""
        settings = Settings()
        assert settings.api_url is not None
        assert settings.cache_ttl > 0
        assert settings.max_requests_per_minute > 0
        assert settings.log_level in SUPPORTED_LOG_LEVELS
