"""Modern currency exchange rate monitoring CLI tool.

WiseRate is a modern CLI application for monitoring currency exchange rates
with support for alerts, caching, and an interactive mode.

Example:
    >>> from wiserate import Settings, WiseRateApp
    >>> settings = Settings()
    >>> app = WiseRateApp(settings)
"""

__version__ = "2.3.0"
__author__ = "Amet13"

from .config import Settings
from .exceptions import (
    AlertError,
    APIError,
    CacheError,
    ConfigurationError,
    NetworkError,
    RateLimitError,
    ValidationError,
    WiseRateError,
)
from .models import Alert, CurrencyPair, ExchangeRate
from .utils import format_currency_amount, get_currency_name, validate_currency_code

__all__ = [
    "__version__",
    "__author__",
    "Settings",
    "CurrencyPair",
    "ExchangeRate",
    "Alert",
    "WiseRateError",
    "ConfigurationError",
    "APIError",
    "ValidationError",
    "CacheError",
    "AlertError",
    "RateLimitError",
    "NetworkError",
    "validate_currency_code",
    "get_currency_name",
    "format_currency_amount",
]
