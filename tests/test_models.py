"""Tests for the data models."""

from decimal import Decimal

import pytest

from wiserate.models import Alert, CurrencyPair, ExchangeRate


class TestCurrencyPair:
    """Test CurrencyPair model."""

    def test_valid_currency_pair(self):
        """Test creating a valid currency pair."""
        pair = CurrencyPair(source="EUR", target="USD")
        assert pair.source == "EUR"
        assert pair.target == "USD"
        assert str(pair) == "EUR/USD"

    def test_invalid_currency_code_length(self):
        """Test invalid currency code length."""
        with pytest.raises(Exception):  # Pydantic validation error
            CurrencyPair(source="EU", target="USD")

        with pytest.raises(Exception):  # Pydantic validation error
            CurrencyPair(source="EUR", target="US")

    def test_invalid_currency_code_case(self):
        """Test invalid currency code case."""
        with pytest.raises(ValueError, match="Currency codes must be 3 uppercase letters"):
            CurrencyPair(source="eur", target="USD")

        with pytest.raises(ValueError, match="Currency codes must be 3 uppercase letters"):
            CurrencyPair(source="EUR", target="usd")

    def test_invalid_currency_code_characters(self):
        """Test invalid currency code characters."""
        with pytest.raises(ValueError, match="Currency codes must be 3 uppercase letters"):
            CurrencyPair(source="EUR", target="123")

    def test_same_currencies(self):
        """Test that source and target cannot be the same."""
        with pytest.raises(ValueError, match="Source and target currencies must be different"):
            CurrencyPair(source="EUR", target="EUR")


class TestExchangeRate:
    """Test ExchangeRate model."""

    def test_valid_exchange_rate(self):
        """Test creating a valid exchange rate."""
        rate = ExchangeRate(source="EUR", target="USD", rate=Decimal("1.15"))
        assert rate.source == "EUR"
        assert rate.target == "USD"
        assert rate.rate == Decimal("1.15")
        assert str(rate) == "1 EUR = 1.15 USD"

    def test_exchange_rate_with_names(self):
        """Test exchange rate with currency names."""
        rate = ExchangeRate(
            source="EUR",
            target="USD",
            rate=Decimal("1.15"),
            source_name="Euro",
            target_name="US Dollar",
        )
        assert rate.source_name == "Euro"
        assert rate.target_name == "US Dollar"

    def test_invalid_rate(self):
        """Test invalid exchange rate."""
        with pytest.raises(Exception):  # Pydantic validation error
            ExchangeRate(source="EUR", target="USD", rate=Decimal("0"))

        with pytest.raises(Exception):  # Pydantic validation error
            ExchangeRate(source="EUR", target="USD", rate=Decimal("-1"))

    def test_format_rate(self):
        """Test rate formatting."""
        rate = ExchangeRate(source="EUR", target="USD", rate=Decimal("1.123456"))
        assert rate.format_rate(2) == "1 EUR = 1.12 USD"
        assert rate.format_rate(4) == "1 EUR = 1.1235 USD"
        assert rate.format_rate(6) == "1 EUR = 1.123456 USD"


class TestAlert:
    """Test Alert model."""

    def test_valid_alert(self):
        """Test creating a valid alert."""
        currency_pair = CurrencyPair(source="EUR", target="USD")
        alert = Alert(currency_pair=currency_pair, threshold=Decimal("1.20"))
        assert alert.currency_pair == currency_pair
        assert alert.threshold == Decimal("1.20")
        assert alert.is_above is True
        assert alert.enabled is True

    def test_alert_below_threshold(self):
        """Test alert for below threshold."""
        currency_pair = CurrencyPair(source="EUR", target="USD")
        alert = Alert(currency_pair=currency_pair, threshold=Decimal("1.20"), is_above=False)
        assert alert.is_above is False

    def test_alert_should_trigger_above(self):
        """Test alert triggering above threshold."""
        currency_pair = CurrencyPair(source="EUR", target="USD")
        alert = Alert(currency_pair=currency_pair, threshold=Decimal("1.20"))

        # Should trigger when rate goes above threshold
        assert alert.should_trigger(Decimal("1.25")) is True
        assert alert.should_trigger(Decimal("1.20")) is False
        assert alert.should_trigger(Decimal("1.15")) is False

    def test_alert_should_trigger_below(self):
        """Test alert triggering below threshold."""
        currency_pair = CurrencyPair(source="EUR", target="USD")
        alert = Alert(currency_pair=currency_pair, threshold=Decimal("1.20"), is_above=False)

        # Should trigger when rate goes below threshold
        assert alert.should_trigger(Decimal("1.15")) is True
        assert alert.should_trigger(Decimal("1.20")) is False
        assert alert.should_trigger(Decimal("1.25")) is False

    def test_alert_disabled(self):
        """Test disabled alert."""
        currency_pair = CurrencyPair(source="EUR", target="USD")
        alert = Alert(currency_pair=currency_pair, threshold=Decimal("1.20"), enabled=False)
        assert alert.should_trigger(Decimal("1.25")) is False

    def test_alert_trigger(self):
        """Test alert triggering."""
        currency_pair = CurrencyPair(source="EUR", target="USD")
        alert = Alert(currency_pair=currency_pair, threshold=Decimal("1.20"))

        assert alert.last_triggered is None
        alert.trigger()
        assert alert.last_triggered is not None
