"""Tests for utility functions."""

import json

import pytest

from wiserate.utils import (
    ensure_directory,
    format_currency_amount,
    get_currency_name,
    load_json_file,
    save_json_file,
    validate_currency_code,
)


class TestCurrencyValidation:
    """Test currency validation functions."""

    def test_validate_currency_code_valid(self):
        """Test valid currency codes."""
        assert validate_currency_code("USD") is True
        assert validate_currency_code("EUR") is True
        assert validate_currency_code("JPY") is True
        assert validate_currency_code("GBP") is True

    def test_validate_currency_code_invalid(self):
        """Test invalid currency codes."""
        assert validate_currency_code("XYZ") is False
        assert validate_currency_code("US") is False
        assert validate_currency_code("USDD") is False
        assert validate_currency_code("123") is False
        assert validate_currency_code("") is False

    def test_validate_currency_code_case_insensitive(self):
        """Test currency code case handling."""
        assert validate_currency_code("usd") is True
        assert validate_currency_code("Usd") is True
        assert validate_currency_code("USD") is True


class TestCurrencyNames:
    """Test currency name functions."""

    def test_get_currency_name_valid(self):
        """Test getting names for valid currencies."""
        assert get_currency_name("USD") == "US Dollar"
        assert get_currency_name("EUR") == "Euro"
        assert get_currency_name("GBP") == "British Pound"
        assert get_currency_name("JPY") == "Japanese Yen"

    def test_get_currency_name_invalid(self):
        """Test getting names for invalid currencies."""
        assert get_currency_name("XYZ") is None
        assert get_currency_name("") is None

    def test_get_currency_name_case_insensitive(self):
        """Test currency name case handling."""
        assert get_currency_name("usd") == "US Dollar"
        assert get_currency_name("Usd") == "US Dollar"


class TestCurrencyFormatting:
    """Test currency amount formatting."""

    def test_format_currency_amount_standard(self):
        """Test standard currency formatting (2 decimals)."""
        assert format_currency_amount(123.45, "USD") == "123.45 USD"
        assert format_currency_amount(1000.00, "EUR") == "1000.00 EUR"
        assert format_currency_amount(0.99, "GBP") == "0.99 GBP"

    def test_format_currency_amount_no_decimals(self):
        """Test currencies with no decimal places."""
        assert format_currency_amount(123.45, "JPY") == "123 JPY"
        assert format_currency_amount(1000.00, "KRW") == "1000 KRW"
        assert format_currency_amount(0.99, "IDR") == "0 IDR"

    def test_format_currency_amount_three_decimals(self):
        """Test currencies with 3 decimal places."""
        assert format_currency_amount(123.456, "BHD") == "123.456 BHD"
        assert format_currency_amount(1000.000, "KWD") == "1000.000 KWD"

    def test_format_currency_amount_custom_precision(self):
        """Test custom precision formatting."""
        assert format_currency_amount(123.456789, "USD", 4) == "123.4568 USD"
        assert format_currency_amount(1000.00, "EUR", 0) == "1000 EUR"


class TestFileOperations:
    """Test file operation utilities."""

    def test_ensure_directory(self, tmp_path):
        """Test directory creation."""
        test_dir = tmp_path / "test_subdir" / "nested"
        ensure_directory(test_dir)
        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_load_json_file_existing(self, tmp_path):
        """Test loading existing JSON file."""
        test_file = tmp_path / "test.json"
        test_data = {"key": "value", "number": 42}

        with open(test_file, "w") as f:
            json.dump(test_data, f)

        loaded_data = load_json_file(test_file)
        assert loaded_data == test_data

    def test_load_json_file_missing(self, tmp_path):
        """Test loading missing JSON file."""
        test_file = tmp_path / "missing.json"
        loaded_data = load_json_file(test_file)
        assert loaded_data == {}

    def test_load_json_file_invalid_json(self, tmp_path):
        """Test loading invalid JSON file."""
        test_file = tmp_path / "invalid.json"

        with open(test_file, "w") as f:
            f.write("invalid json content")

        loaded_data = load_json_file(test_file)
        assert loaded_data == {}

    def test_save_json_file(self, tmp_path):
        """Test saving JSON file."""
        test_file = tmp_path / "output.json"
        test_data = {"key": "value", "nested": {"inner": "data"}}

        save_json_file(test_file, test_data)

        assert test_file.exists()
        with open(test_file) as f:
            loaded_data = json.load(f)
        assert loaded_data == test_data

    def test_save_json_file_creates_directory(self, tmp_path):
        """Test that save_json_file creates parent directories."""
        test_file = tmp_path / "subdir" / "nested" / "output.json"
        test_data = {"key": "value"}

        save_json_file(test_file, test_data)

        assert test_file.exists()
        assert test_file.parent.exists()
        assert test_file.parent.parent.exists()

    def test_load_json_file_not_dict(self, tmp_path):
        """Test loading JSON file that's not a dict."""
        test_file = tmp_path / "not_dict.json"

        # Write a list instead of dict
        with open(test_file, "w") as f:
            json.dump([1, 2, 3], f)

        loaded_data = load_json_file(test_file)
        # Should return default when not a dict
        assert loaded_data == {}

    def test_save_json_file_not_serializable(self, tmp_path):
        """Test saving non-serializable data."""
        test_file = tmp_path / "not_serializable.json"

        # Try to save an object that's not JSON serializable
        class NonSerializable:
            pass

        with pytest.raises(ValueError, match="Data is not JSON serializable"):
            save_json_file(test_file, {"obj": NonSerializable()})

    def test_save_json_file_with_non_ascii(self, tmp_path):
        """Test saving JSON file with non-ASCII characters."""
        test_file = tmp_path / "unicode.json"
        test_data = {"emoji": "🎉", "japanese": "日本語", "arabic": "العربية"}

        save_json_file(test_file, test_data)

        assert test_file.exists()
        loaded_data = load_json_file(test_file)
        assert loaded_data == test_data


class TestRetryLogic:
    """Test retry with backoff functionality."""

    @pytest.mark.asyncio
    async def test_retry_with_backoff_success_first_try(self):
        """Test retry when function succeeds on first try."""
        from wiserate.utils import retry_with_backoff

        async def success_func():
            return "success"

        result = await retry_with_backoff(success_func)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_with_backoff_success_after_retries(self):
        """Test retry when function succeeds after some failures."""
        from wiserate.utils import retry_with_backoff

        call_count = 0

        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = await retry_with_backoff(failing_then_success, max_retries=3)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_with_backoff_max_retries_exceeded(self):
        """Test retry when max retries are exceeded."""
        from wiserate.utils import retry_with_backoff

        async def always_fail():
            raise ValueError("Permanent failure")

        with pytest.raises(ValueError, match="Permanent failure"):
            await retry_with_backoff(always_fail, max_retries=2)
