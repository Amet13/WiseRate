"""Data models for the currency exchange bot.

This module defines the core data structures used throughout WiseRate:
- CurrencyPair: Represents a currency pair for exchange operations
- ExchangeRate: Represents the exchange rate between two currencies
- Alert: Represents price alerts for exchange rates
"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from .utils import validate_currency_code


class CurrencyPair(BaseModel):
    """Represents a currency pair for exchange operations.

    A currency pair consists of a source currency and a target currency,
    both represented by 3-letter ISO 4217 currency codes.

    Attributes:
        source: The source currency code (e.g., 'USD', 'EUR')
        target: The target currency code (e.g., 'GBP', 'JPY')

    Example:
        >>> pair = CurrencyPair(source='USD', target='EUR')
        >>> str(pair)
        'USD/EUR'
    """

    source: str = Field(..., min_length=3, max_length=3, description="Source currency code")
    target: str = Field(..., min_length=3, max_length=3, description="Target currency code")

    @field_validator("source", "target")
    @classmethod
    def validate_currency_code(cls, v: str) -> str:
        """Validate that the currency code is valid.

        Args:
            v: The currency code to validate

        Returns:
            The validated currency code

        Raises:
            ValueError: If the currency code is invalid
        """
        if not v.isalpha() or not v.isupper():
            raise ValueError("Currency codes must be 3 uppercase letters")
        if not validate_currency_code(v):
            raise ValueError(f"Invalid currency code: {v}")
        return v

    @field_validator("target")
    @classmethod
    def validate_different_currencies(cls, v: str, info) -> str:
        """Validate that source and target currencies are different.

        Args:
            v: The target currency code
            info: Validation info containing model data

        Returns:
            The validated target currency code

        Raises:
            ValueError: If source and target currencies are the same
        """
        if info.data and "source" in info.data and v == info.data["source"]:
            raise ValueError("Source and target currencies must be different")
        return v

    def __str__(self) -> str:
        """Return string representation of the currency pair.

        Returns:
            String in format 'SOURCE/TARGET'
        """
        return f"{self.source}/{self.target}"


class ExchangeRate(BaseModel):
    """Represents an exchange rate between two currencies.

    This model stores the exchange rate information including the currencies,
    rate value, timestamp, and optional currency names.

    Attributes:
        source: Source currency code
        target: Target currency code
        rate: Exchange rate value (must be positive)
        timestamp: When this rate was obtained
        source_name: Optional full name of source currency
        target_name: Optional full name of target currency

    Example:
        >>> rate = ExchangeRate(source='USD', target='EUR', rate=Decimal('0.85'))
        >>> str(rate)
        '1 USD = 0.85 EUR'
    """

    source: str = Field(..., min_length=3, max_length=3)
    target: str = Field(..., min_length=3, max_length=3)
    rate: Decimal = Field(..., ge=0, description="Exchange rate")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_name: Optional[str] = None
    target_name: Optional[str] = None

    @field_validator("rate")
    @classmethod
    def validate_rate(cls, v: Decimal) -> Decimal:
        """Validate that the exchange rate is positive.

        Args:
            v: The rate value to validate

        Returns:
            The validated rate value

        Raises:
            ValueError: If the rate is not positive
        """
        if v <= 0:
            raise ValueError("Exchange rate must be positive")
        return v

    def __str__(self) -> str:
        """Return string representation of the exchange rate.

        Returns:
            String in format '1 SOURCE = RATE TARGET'
        """
        return f"1 {self.source} = {self.rate} {self.target}"

    def format_rate(self, precision: int = 6) -> str:
        """Format the exchange rate with specified decimal precision.

        Args:
            precision: Number of decimal places to show (default: 6)

        Returns:
            Formatted string representation of the exchange rate
        """
        return f"1 {self.source} = {self.rate:.{precision}f} {self.target}"


class Alert(BaseModel):
    """Represents an exchange rate alert configuration.

    An alert monitors a currency pair and triggers when the exchange rate
    crosses a specified threshold in the specified direction.

    Attributes:
        currency_pair: The currency pair to monitor
        threshold: The rate threshold value
        is_above: If True, alert when rate goes above threshold; if False, below
        enabled: Whether this alert is active
        created_at: When this alert was created
        last_triggered: When this alert was last triggered (None if never)

    Example:
        >>> pair = CurrencyPair(source='USD', target='EUR')
        >>> alert = Alert(currency_pair=pair, threshold=Decimal('0.90'), is_above=False)
    """

    currency_pair: CurrencyPair
    threshold: Decimal = Field(..., gt=0, description="Alert threshold")
    is_above: bool = Field(default=True, description="Alert when rate goes above threshold")
    enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_triggered: Optional[datetime] = None

    def should_trigger(self, current_rate: Decimal) -> bool:
        """Check if the alert should be triggered based on current rate.

        Args:
            current_rate: The current exchange rate

        Returns:
            True if the alert should trigger, False otherwise
        """
        if not self.enabled:
            return False

        if self.is_above:
            return current_rate > self.threshold
        else:
            return current_rate < self.threshold

    def trigger(self) -> None:
        """Mark the alert as triggered by updating the last_triggered timestamp."""
        self.last_triggered = datetime.now(UTC)
