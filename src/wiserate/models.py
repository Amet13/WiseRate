"""Data models for the currency exchange bot."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from .utils import validate_currency_code


class CurrencyPair(BaseModel):
    """Represents a currency pair for exchange."""

    source: str = Field(..., min_length=3, max_length=3, description="Source currency code")
    target: str = Field(..., min_length=3, max_length=3, description="Target currency code")

    @field_validator("source", "target")
    @classmethod
    def validate_currency_code(cls, v: str) -> str:
        if not v.isalpha() or not v.isupper():
            raise ValueError("Currency codes must be 3 uppercase letters")
        if not validate_currency_code(v):
            raise ValueError(f"Invalid currency code: {v}")
        return v

    @field_validator("target")
    @classmethod
    def validate_different_currencies(cls, v: str, info) -> str:
        if info.data and "source" in info.data and v == info.data["source"]:
            raise ValueError("Source and target currencies must be different")
        return v

    def __str__(self) -> str:
        return f"{self.source}/{self.target}"


class ExchangeRate(BaseModel):
    """Represents an exchange rate between two currencies."""

    source: str = Field(..., min_length=3, max_length=3)
    target: str = Field(..., min_length=3, max_length=3)
    rate: Decimal = Field(..., ge=0, description="Exchange rate")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_name: Optional[str] = None
    target_name: Optional[str] = None

    @field_validator("rate")
    @classmethod
    def validate_rate(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Exchange rate must be positive")
        return v

    def __str__(self) -> str:
        return f"1 {self.source} = {self.rate} {self.target}"

    def format_rate(self, precision: int = 6) -> str:
        """Format the exchange rate with specified precision."""
        return f"1 {self.source} = {self.rate:.{precision}f} {self.target}"


class Alert(BaseModel):
    """Represents an exchange rate alert."""

    currency_pair: CurrencyPair
    threshold: Decimal = Field(..., gt=0, description="Alert threshold")
    is_above: bool = Field(default=True, description="Alert when rate goes above threshold")
    enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_triggered: Optional[datetime] = None

    def should_trigger(self, current_rate: Decimal) -> bool:
        """Check if the alert should be triggered."""
        if not self.enabled:
            return False

        if self.is_above:
            return current_rate > self.threshold
        else:
            return current_rate < self.threshold

    def trigger(self) -> None:
        """Mark the alert as triggered."""
        self.last_triggered = datetime.now(UTC)
