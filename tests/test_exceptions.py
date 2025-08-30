"""Tests for custom exceptions."""

import pytest

from wiserate.exceptions import (
    AlertError,
    APIError,
    CacheError,
    ConfigurationError,
    ValidationError,
    WiseRateError,
)


class TestWiseRateError:
    """Test base exception class."""

    def test_wise_rate_error_inheritance(self):
        """Test that WiseRateError inherits from Exception."""
        error = WiseRateError("Test error")
        assert isinstance(error, Exception)
        assert isinstance(error, WiseRateError)

    def test_wise_rate_error_message(self):
        """Test that WiseRateError preserves the message."""
        message = "Test error message"
        error = WiseRateError(message)
        assert str(error) == message


class TestConfigurationError:
    """Test ConfigurationError exception."""

    def test_configuration_error_inheritance(self):
        """Test that ConfigurationError inherits from WiseRateError."""
        error = ConfigurationError("Config error")
        assert isinstance(error, WiseRateError)
        assert isinstance(error, ConfigurationError)

    def test_configuration_error_message(self):
        """Test that ConfigurationError preserves the message."""
        message = "Configuration error message"
        error = ConfigurationError(message)
        assert str(error) == message


class TestAPIError:
    """Test APIError exception."""

    def test_api_error_inheritance(self):
        """Test that APIError inherits from WiseRateError."""
        error = APIError("API error")
        assert isinstance(error, WiseRateError)
        assert isinstance(error, APIError)

    def test_api_error_message(self):
        """Test that APIError preserves the message."""
        message = "API error message"
        error = APIError(message)
        assert str(error) == message


class TestValidationError:
    """Test ValidationError exception."""

    def test_validation_error_inheritance(self):
        """Test that ValidationError inherits from WiseRateError."""
        error = ValidationError("Validation error")
        assert isinstance(error, WiseRateError)
        assert isinstance(error, ValidationError)

    def test_validation_error_message(self):
        """Test that ValidationError preserves the message."""
        message = "Validation error message"
        error = ValidationError(message)
        assert str(error) == message


class TestCacheError:
    """Test CacheError exception."""

    def test_cache_error_inheritance(self):
        """Test that CacheError inherits from WiseRateError."""
        error = CacheError("Cache error")
        assert isinstance(error, WiseRateError)
        assert isinstance(error, CacheError)

    def test_cache_error_message(self):
        """Test that CacheError preserves the message."""
        message = "Cache error message"
        error = CacheError(message)
        assert str(error) == message


class TestAlertError:
    """Test AlertError exception."""

    def test_alert_error_inheritance(self):
        """Test that AlertError inherits from WiseRateError."""
        error = AlertError("Alert error")
        assert isinstance(error, WiseRateError)
        assert isinstance(error, AlertError)

    def test_alert_error_message(self):
        """Test that AlertError preserves the message."""
        message = "Alert error message"
        error = AlertError(message)
        assert str(error) == message


class TestExceptionHierarchy:
    """Test exception hierarchy and relationships."""

    def test_exception_hierarchy(self):
        """Test that all exceptions are properly related."""
        # All should inherit from WiseRateError
        assert issubclass(ConfigurationError, WiseRateError)
        assert issubclass(APIError, WiseRateError)
        assert issubclass(ValidationError, WiseRateError)
        assert issubclass(CacheError, WiseRateError)
        assert issubclass(AlertError, WiseRateError)

        # All should inherit from Exception
        assert issubclass(WiseRateError, Exception)
        assert issubclass(ConfigurationError, Exception)
        assert issubclass(APIError, Exception)
        assert issubclass(ValidationError, Exception)
        assert issubclass(CacheError, Exception)
        assert issubclass(AlertError, Exception)

    def test_exception_instances(self):
        """Test that exceptions can be instantiated and caught properly."""
        try:
            raise ConfigurationError("Config test")
        except ConfigurationError as e:
            assert str(e) == "Config test"
        except Exception:
            pytest.fail("ConfigurationError should be caught by ConfigurationError")

        try:
            raise APIError("API test")
        except APIError as e:
            assert str(e) == "API test"
        except Exception:
            pytest.fail("APIError should be caught by APIError")

        try:
            raise ValidationError("Validation test")
        except ValidationError as e:
            assert str(e) == "Validation test"
        except Exception:
            pytest.fail("ValidationError should be caught by ValidationError")

        try:
            raise CacheError("Cache test")
        except CacheError as e:
            assert str(e) == "Cache test"
        except Exception:
            pytest.fail("CacheError should be caught by CacheError")

        try:
            raise AlertError("Alert test")
        except AlertError as e:
            assert str(e) == "Alert test"
        except Exception:
            pytest.fail("AlertError should be caught by AlertError")
