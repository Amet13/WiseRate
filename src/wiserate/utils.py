"""Utility functions for WiseRate application."""

import asyncio
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import aiofiles

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


@lru_cache(maxsize=512)
def validate_currency_code(currency: str) -> bool:
    """Validate if a currency code is valid.

    Uses LRU cache to improve performance for repeated validations.

    Args:
        currency: Currency code to validate

    Returns:
        True if currency code is valid, False otherwise
    """
    return currency.upper() in EXTENDED_CURRENCIES


@lru_cache(maxsize=256)
def get_currency_name(currency: str) -> str | None:
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


async def retry_with_backoff(func: Any, max_retries: int = 3, base_delay: float = 1.0) -> Any:
    """Retry function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e

            delay = base_delay * (2**attempt)
            await asyncio.sleep(delay)


async def load_json_file_async(
    file_path: Path, default: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Load JSON file asynchronously with error handling and validation.

    Args:
        file_path: Path to JSON file
        default: Default value if file doesn't exist or is invalid

    Returns:
        Loaded JSON data or default value

    Example:
        >>> data = await load_json_file_async(Path("config.json"), default={})
    """
    if default is None:
        default = {}

    try:
        if file_path.exists():
            # Check file size to prevent loading extremely large files
            file_size = file_path.stat().st_size
            max_size = 100 * 1024 * 1024  # 100 MB limit
            if file_size > max_size:
                raise ValueError(f"File too large: {file_size} bytes (max: {max_size})")

            async with aiofiles.open(file_path, encoding="utf-8") as f:
                content = await f.read()
                data = json.loads(content)

                # Validate that result is a dictionary
                if not isinstance(data, dict):
                    raise ValueError(f"Expected dict, got {type(data).__name__}")

                return data
    except (json.JSONDecodeError, OSError, ValueError) as e:
        # Log but don't crash - return default
        import structlog

        logger = structlog.get_logger(__name__)
        logger.warning("Failed to load JSON file", path=str(file_path), error=str(e))

    return default


def load_json_file(file_path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    """Load JSON file synchronously with error handling and validation.

    Args:
        file_path: Path to JSON file
        default: Default value if file doesn't exist or is invalid

    Returns:
        Loaded JSON data or default value

    Example:
        >>> data = load_json_file(Path("config.json"), default={})
    """
    if default is None:
        default = {}

    try:
        if file_path.exists():
            # Check file size to prevent loading extremely large files
            file_size = file_path.stat().st_size
            max_size = 100 * 1024 * 1024  # 100 MB limit
            if file_size > max_size:
                raise ValueError(f"File too large: {file_size} bytes (max: {max_size})")

            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

                # Validate that result is a dictionary
                if not isinstance(data, dict):
                    raise ValueError(f"Expected dict, got {type(data).__name__}")

                return data
    except (json.JSONDecodeError, OSError, ValueError) as e:
        # Log but don't crash - return default
        import structlog

        logger = structlog.get_logger(__name__)
        logger.warning("Failed to load JSON file", path=str(file_path), error=str(e))

    return default


async def save_json_file_async(file_path: Path, data: dict[str, Any]) -> None:
    """Save JSON file asynchronously with error handling and atomic writes.

    Uses atomic write pattern to prevent data corruption if write is interrupted.

    Args:
        file_path: Path to save JSON file
        data: Dictionary data to save

    Raises:
        OSError: If file save operation fails
        ValueError: If data is not serializable

    Example:
        >>> await save_json_file_async(Path("config.json"), {"key": "value"})
    """
    try:
        ensure_directory(file_path.parent)

        # Validate data is serializable before writing
        try:
            json.dumps(data)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Data is not JSON serializable: {e}")

        # Atomic write: write to temp file first, then rename
        temp_file = file_path.with_suffix(file_path.suffix + ".tmp")

        try:
            async with aiofiles.open(temp_file, "w", encoding="utf-8") as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))

            # Atomic rename
            import shutil

            shutil.move(str(temp_file), str(file_path))
        except Exception:
            # Clean up temp file if it still exists
            if temp_file.exists():
                temp_file.unlink()
            raise

    except OSError as e:
        raise OSError(f"Failed to save {file_path}: {e}")


def save_json_file(file_path: Path, data: dict[str, Any]) -> None:
    """Save JSON file synchronously with error handling and atomic writes.

    Uses atomic write pattern to prevent data corruption if write is interrupted.

    Args:
        file_path: Path to save JSON file
        data: Dictionary data to save

    Raises:
        OSError: If file save operation fails
        ValueError: If data is not serializable

    Example:
        >>> save_json_file(Path("config.json"), {"key": "value"})
    """
    try:
        ensure_directory(file_path.parent)

        # Validate data is serializable before writing
        try:
            json.dumps(data)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Data is not JSON serializable: {e}")

        # Atomic write: write to temp file first, then rename
        temp_file = file_path.with_suffix(file_path.suffix + ".tmp")

        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                # Ensure data is flushed to disk
                f.flush()

            # Atomic rename
            temp_file.replace(file_path)
        finally:
            # Clean up temp file if it still exists
            if temp_file.exists():
                temp_file.unlink()

    except OSError as e:
        raise OSError(f"Failed to save {file_path}: {e}")
