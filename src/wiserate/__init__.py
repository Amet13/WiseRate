"""Modern currency exchange rate monitoring CLI tool."""

__version__ = "2.1.0"
__author__ = "Amet13"

from .config import Settings
from .exceptions import (
    AlertError,
    APIError,
    CacheError,
    ConfigurationError,
    ValidationError,
    WiseRateError,
)
from .models import Alert, CurrencyPair, ExchangeRate
from .utils import format_currency_amount, get_currency_name, validate_currency_code

__all__ = [
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
    "validate_currency_code",
    "get_currency_name",
    "format_currency_amount",
]
