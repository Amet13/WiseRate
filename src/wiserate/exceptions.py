"""Custom exceptions for WiseRate application."""


class WiseRateError(Exception):
    """Base exception for WiseRate application."""

    pass


class ConfigurationError(WiseRateError):
    """Configuration-related errors."""

    pass


class APIError(WiseRateError):
    """API-related errors."""

    pass


class ValidationError(WiseRateError):
    """Data validation errors."""

    pass


class CacheError(WiseRateError):
    """Cache-related errors."""

    pass


class AlertError(WiseRateError):
    """Alert-related errors."""

    pass
