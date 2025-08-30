"""Configuration management for the currency exchange bot."""

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .constants import (
    DEFAULT_CACHE_TTL,
    DEFAULT_LOG_LEVEL,
    DEFAULT_MAX_REQUESTS_PER_MINUTE,
    MAX_CACHE_TTL,
    MAX_REQUESTS_PER_MINUTE,
    MIN_CACHE_TTL,
    MIN_REQUESTS_PER_MINUTE,
    SUPPORTED_LOG_LEVELS,
)


class Settings(BaseSettings):
    """Application settings."""

    # Wise API settings
    wise_api_key: Optional[str] = Field(None, alias="WISE_API_KEY", description="Wise API key")
    wise_api_url: str = Field("https://api.wise.com/v1", alias="WISE_API_URL")

    # Alternative free API (when Wise API is not available)
    fallback_api_url: str = Field("https://api.exchangerate-api.com/v4", alias="FALLBACK_API_URL")

    # Application settings
    data_dir: Path = Field(default=Path.home() / ".wiserate", alias="WISERATE_DATA_DIR")
    cache_ttl: int = Field(
        default=DEFAULT_CACHE_TTL,
        alias="WISERATE_CACHE_TTL",
        description="Cache TTL in seconds",
    )
    log_level: str = Field(default=DEFAULT_LOG_LEVEL, alias="WISERATE_LOG_LEVEL")

    # Rate limiting
    max_requests_per_minute: int = Field(
        default=DEFAULT_MAX_REQUESTS_PER_MINUTE,
        alias="WISERATE_MAX_REQUESTS_PER_MINUTE",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
    )

    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        """Validate all settings after model creation."""
        # Additional validation if needed
        return self

    @field_validator("log_level", mode="before")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate and normalize log level."""
        if isinstance(v, str):
            v = v.upper()
        if v not in SUPPORTED_LOG_LEVELS:
            raise ValueError(f"Log level must be one of: {', '.join(SUPPORTED_LOG_LEVELS)}")
        return v

    @field_validator("cache_ttl", mode="before")
    @classmethod
    def validate_cache_ttl(cls, v) -> int:
        """Validate cache TTL value."""
        # Convert string to int if needed (for environment variables)
        if isinstance(v, str):
            try:
                v = int(v)
            except ValueError:
                raise ValueError(f"Cache TTL must be a valid integer, got: {v}")

        if not MIN_CACHE_TTL <= v <= MAX_CACHE_TTL:
            raise ValueError(
                f"Cache TTL must be between {MIN_CACHE_TTL} and {MAX_CACHE_TTL} seconds"
            )
        return v

    @field_validator("max_requests_per_minute", mode="before")
    @classmethod
    def validate_max_requests(cls, v) -> int:
        """Validate max requests per minute value."""
        # Convert string to int if needed (for environment variables)
        if isinstance(v, str):
            try:
                v = int(v)
            except ValueError:
                raise ValueError(f"Max requests per minute must be a valid integer, got: {v}")

        if not MIN_REQUESTS_PER_MINUTE <= v <= MAX_REQUESTS_PER_MINUTE:
            raise ValueError(
                f"Max requests per minute must be between "
                f"{MIN_REQUESTS_PER_MINUTE} and {MAX_REQUESTS_PER_MINUTE}"
            )
        return v

    def __init__(self, **kwargs):
        """Initialize settings with custom values."""
        # Handle both constructor parameters and environment variables
        # First, create a dict with environment variable mappings
        env_kwargs = {}

        # Map constructor parameters to their environment variable names
        if "cache_ttl" in kwargs:
            env_kwargs["WISERATE_CACHE_TTL"] = str(kwargs["cache_ttl"])
        if "log_level" in kwargs:
            env_kwargs["WISERATE_LOG_LEVEL"] = kwargs["log_level"]
        if "max_requests_per_minute" in kwargs:
            env_kwargs["WISERATE_MAX_REQUESTS_PER_MINUTE"] = str(kwargs["max_requests_per_minute"])
        if "data_dir" in kwargs:
            env_kwargs["WISERATE_DATA_DIR"] = str(kwargs["data_dir"])

        # Call parent constructor with environment variables
        super().__init__(**env_kwargs)

        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

    @property
    def currencies_file(self) -> Path:
        """Get the path to the currencies cache file."""
        return self.data_dir / "currencies.json"

    @property
    def alerts_file(self) -> Path:
        """Get the path to the alerts configuration file."""
        return self.data_dir / "alerts.json"

    @property
    def log_file(self) -> Path:
        """Get the path to the log file."""
        return self.data_dir / "wiserate.log"
