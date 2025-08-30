"""Utility functions for WiseRate application."""

import asyncio
import json
from pathlib import Path
from typing import Any, Optional

# Common currency codes (ISO 4217)
COMMON_CURRENCIES = {
    "USD",
    "EUR",
    "GBP",
    "JPY",
    "AUD",
    "CAD",
    "CHF",
    "CNY",
    "SEK",
    "NZD",
    "MXN",
    "SGD",
    "HKD",
    "NOK",
    "KRW",
    "TRY",
    "RUB",
    "INR",
    "BRL",
    "ZAR",
    "PLN",
    "THB",
    "IDR",
    "HUF",
    "CZK",
    "ILS",
    "CLP",
    "PHP",
    "AED",
    "COP",
    "SAR",
    "MYR",
    "RON",
    "BGN",
    "HRK",
    "DKK",
    "ISK",
    "BAM",
    "ALL",
    "MKD",
}

# Extended currency list (you can expand this)
EXTENDED_CURRENCIES = COMMON_CURRENCIES | {
    "UAH",
    "VND",
    "EGP",
    "NGN",
    "BDT",
    "PKR",
    "KES",
    "UGX",
    "TZS",
    "ETB",
    "GHS",
    "MAD",
    "TND",
    "DZD",
    "LYD",
    "SDG",
    "SSP",
    "SOS",
    "DJF",
    "KMF",
    "BIF",
    "RWF",
    "CDF",
    "GNF",
    "MRO",
    "STD",
    "CVE",
    "GMD",
    "GWP",
    "XOF",
    "XAF",
    "XPF",
    "CLF",
    "BOV",
    "UYI",
    "UYW",
    "BWP",
    "NAD",
    "SZL",
    "LSL",
    "ZMW",
    "ZWL",
    "BND",
    "KHR",
    "LAK",
    "MMK",
    "NPR",
    "LKR",
    "MVR",
    "BTN",
}


def validate_currency_code(currency: str) -> bool:
    """Validate if a currency code is valid."""
    return currency.upper() in EXTENDED_CURRENCIES


def get_currency_name(currency: str) -> Optional[str]:
    """Get currency name from code."""
    currency_names = {
        "USD": "US Dollar",
        "EUR": "Euro",
        "GBP": "British Pound",
        "JPY": "Japanese Yen",
        "AUD": "Australian Dollar",
        "CAD": "Canadian Dollar",
        "CHF": "Swiss Franc",
        "CNY": "Chinese Yuan",
        "SEK": "Swedish Krona",
        "NZD": "New Zealand Dollar",
        "MXN": "Mexican Peso",
        "SGD": "Singapore Dollar",
        "HKD": "Hong Kong Dollar",
        "NOK": "Norwegian Krone",
        "KRW": "South Korean Won",
        "TRY": "Turkish Lira",
        "RUB": "Russian Ruble",
        "INR": "Indian Rupee",
        "BRL": "Brazilian Real",
        "ZAR": "South African Rand",
        "PLN": "Polish Złoty",
        "THB": "Thai Baht",
        "IDR": "Indonesian Rupiah",
        "HUF": "Hungarian Forint",
        "CZK": "Czech Koruna",
        "ILS": "Israeli Shekel",
        "CLP": "Chilean Peso",
        "PHP": "Philippine Peso",
        "AED": "UAE Dirham",
        "COP": "Colombian Peso",
        "SAR": "Saudi Riyal",
        "MYR": "Malaysian Ringgit",
        "RON": "Romanian Leu",
        "BGN": "Bulgarian Lev",
        "HRK": "Croatian Kuna",
        "DKK": "Danish Krone",
        "ISK": "Icelandic Króna",
        "BAM": "Bosnia-Herzegovina Convertible Mark",
        "ALL": "Albanian Lek",
        "MKD": "Macedonian Denar",
    }
    return currency_names.get(currency.upper())


def format_currency_amount(amount: float, currency: str, precision: int = 2) -> str:
    """Format currency amount with proper precision."""
    if currency in ["JPY", "KRW", "IDR", "VND", "BYN"]:
        # No decimal places for these currencies
        return f"{int(amount)} {currency}"
    elif currency in ["BHD", "IQD", "JOD", "KWD", "LYD", "OMR", "TND"]:
        # 3 decimal places for these currencies
        return f"{amount:.3f} {currency}"
    else:
        # Standard 2 decimal places
        return f"{amount:.{precision}f} {currency}"


def ensure_directory(path: Path) -> None:
    """Ensure directory exists, create if it doesn't."""
    path.mkdir(parents=True, exist_ok=True)


async def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0) -> Any:
    """Retry function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e

            delay = base_delay * (2**attempt)
            await asyncio.sleep(delay)


def load_json_file(file_path: Path, default: dict | None = None) -> dict[str, Any]:
    """Load JSON file with error handling."""
    if default is None:
        default = {}

    try:
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass

    return default


def save_json_file(file_path: Path, data: dict) -> None:
    """Save JSON file with error handling."""
    try:
        ensure_directory(file_path.parent)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        raise IOError(f"Failed to save {file_path}: {e}")
