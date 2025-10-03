"""Custom exceptions for WiseRate application.

This module defines all custom exceptions used throughout the application.
All exceptions inherit from WiseRateError for easy catching of all app-specific errors.

Exception Hierarchy:
    WiseRateError (base)
    ├── ConfigurationError (configuration/settings issues)
    ├── APIError (external API communication issues)
    ├── ValidationError (data validation failures)
    ├── CacheError (cache read/write issues)
    ├── AlertError (alert management issues)
    ├── RateLimitError (rate limiting issues)
    └── NetworkError (network connectivity issues)
"""

from typing import Optional


class WiseRateError(Exception):
    """Base exception for all WiseRate application errors.

    All custom exceptions in WiseRate inherit from this class,
    allowing catching all application-specific errors with a single except clause.

    Attributes:
        message: Error message describing what went wrong
        details: Optional additional details about the error
    """

    def __init__(self, message: str, details: Optional[str] = None):
        """Initialize the exception with a message and optional details.

        Args:
            message: Error message
            details: Optional additional error details
        """
        self.message = message
        self.details = details
        super().__init__(message)

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class ConfigurationError(WiseRateError):
    """Configuration-related errors.

    Raised when there are issues with application configuration,
    such as invalid settings, missing required configuration, or
    configuration file parsing errors.

    Example:
        >>> raise ConfigurationError("Invalid cache TTL", details="Must be between 60 and 86400")
    """

    pass


class APIError(WiseRateError):
    """API-related errors.

    Raised when there are issues communicating with external APIs,
    such as HTTP errors, invalid responses, or missing data in responses.

    Attributes:
        status_code: HTTP status code if applicable
        response_text: API response text if available
    """

    def __init__(
        self,
        message: str,
        details: Optional[str] = None,
        status_code: Optional[int] = None,
        response_text: Optional[str] = None,
    ):
        """Initialize API error with optional HTTP details.

        Args:
            message: Error message
            details: Optional additional error details
            status_code: HTTP status code if applicable
            response_text: API response text if available
        """
        super().__init__(message, details)
        self.status_code = status_code
        self.response_text = response_text


class ValidationError(WiseRateError):
    """Data validation errors.

    Raised when input data fails validation, such as invalid
    currency codes, malformed data, or constraint violations.

    Example:
        >>> raise ValidationError(
        ...     "Invalid currency pair",
        ...     details="Source and target must be different"
        ... )
    """

    pass


class CacheError(WiseRateError):
    """Cache-related errors.

    Raised when there are issues with cache operations,
    such as file read/write errors, JSON parsing errors,
    or cache corruption.

    Example:
        >>> raise CacheError("Failed to load cache", details="JSON decode error")
    """

    pass


class AlertError(WiseRateError):
    """Alert-related errors.

    Raised when there are issues with alert management,
    such as invalid alert configurations, alert persistence errors,
    or alert processing failures.

    Example:
        >>> raise AlertError("Failed to save alert", details="Permission denied")
    """

    pass


class RateLimitError(WiseRateError):
    """Rate limiting errors.

    Raised when rate limits are exceeded or there are issues
    with the rate limiting mechanism.

    Attributes:
        retry_after: Seconds to wait before retrying
    """

    def __init__(
        self, message: str, details: Optional[str] = None, retry_after: Optional[int] = None
    ):
        """Initialize rate limit error with optional retry information.

        Args:
            message: Error message
            details: Optional additional error details
            retry_after: Seconds to wait before retrying
        """
        super().__init__(message, details)
        self.retry_after = retry_after


class NetworkError(WiseRateError):
    """Network connectivity errors.

    Raised when there are network-related issues,
    such as connection timeouts, DNS resolution failures,
    or network unavailability.

    Example:
        >>> raise NetworkError("Connection timeout", details="Could not reach API server")
    """

    pass
