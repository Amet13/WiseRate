"""Configuration management for WiseRate.

This module provides centralized configuration management using Pydantic.
It handles configuration with sensible defaults built into the application.

Key Features:
- Validation of configuration values
- Automatic data directory creation
- Type-safe configuration access
- Built-in sensible defaults
- Environment variable support

Configuration can be provided via:
1. Environment variables (highest priority)
2. Constructor parameters
3. Default values (built into the app)
"""

import os
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator

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


class Settings(BaseModel):
    """Application settings for WiseRate.

    This class manages all configuration for the WiseRate application using
    Pydantic's BaseModel. Configuration values can be provided through:

    1. Environment variables (WISERATE_*)
    2. Constructor parameters
    3. Default values (built into the app)

    Attributes:
        api_url: Base URL for free exchange rate API
        data_dir: Directory for storing cache and configuration files
        cache_ttl: How long to cache exchange rates (seconds)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_requests_per_minute: Rate limiting for API requests

    Environment Variables:
        WISERATE_API_URL: Override API URL
        WISERATE_DATA_DIR: Override data directory
        WISERATE_CACHE_TTL: Override cache TTL (seconds)
        WISERATE_LOG_LEVEL: Override log level
        WISERATE_MAX_REQUESTS_PER_MINUTE: Override rate limit

    Example:
        >>> settings = Settings()
        >>> settings.data_dir
        PosixPath('/Users/username/.wiserate')

        >>> settings = Settings(cache_ttl=300, log_level='DEBUG')
        >>> settings.cache_ttl
        300

        >>> # Using environment variables
        >>> os.environ['WISERATE_LOG_LEVEL'] = 'DEBUG'
        >>> settings = Settings()
        >>> settings.log_level
        'DEBUG'
    """

    # API settings
    api_url: str = Field(default="https://api.exchangerate-api.com/v4")

    # Application settings
    data_dir: Path = Field(default=Path.home() / ".wiserate")
    cache_ttl: int = Field(default=DEFAULT_CACHE_TTL)
    log_level: str = Field(default=DEFAULT_LOG_LEVEL)

    # Rate limiting
    max_requests_per_minute: int = Field(default=DEFAULT_MAX_REQUESTS_PER_MINUTE)

    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        """Validate all settings after model creation.

        This method is called after all field validation and can perform
        cross-field validation if needed.

        Returns:
            The validated Settings instance
        """
        # Additional validation if needed
        return self

    @field_validator("log_level", mode="before")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate and normalize log level.

        Args:
            v: The log level value to validate

        Returns:
            The validated and normalized log level

        Raises:
            ValueError: If the log level is not supported
        """
        if isinstance(v, str):
            v = v.upper()
        if v not in SUPPORTED_LOG_LEVELS:
            raise ValueError(f"Log level must be one of: {', '.join(SUPPORTED_LOG_LEVELS)}")
        return v

    @field_validator("cache_ttl", mode="before")
    @classmethod
    def validate_cache_ttl(cls, v) -> int:
        """Validate cache TTL value.

        Args:
            v: The cache TTL value to validate (can be string or int)

        Returns:
            The validated cache TTL value

        Raises:
            ValueError: If the cache TTL is invalid or out of range
        """
        # Convert string to int if needed
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
        """Validate max requests per minute value.

        Args:
            v: The max requests per minute value to validate (can be string or int)

        Returns:
            The validated max requests per minute value

        Raises:
            ValueError: If the value is invalid or out of range
        """
        # Convert string to int if needed
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
        """Initialize settings with custom values.

        This constructor allows overriding default settings via keyword arguments
        or environment variables. Environment variables have priority over defaults
        but are overridden by explicit keyword arguments.

        Args:
            **kwargs: Settings to override. Supported keys:
                - api_url: API URL for exchange rates
                - cache_ttl: Cache TTL in seconds
                - log_level: Logging level
                - max_requests_per_minute: Rate limiting value
                - data_dir: Data directory path
        """
        # Load from environment variables if not provided in kwargs
        env_config = self._load_from_env()

        # Merge: env vars < kwargs (kwargs override env vars)
        merged_config = {**env_config, **kwargs}

        # Call parent constructor with merged values
        super().__init__(**merged_config)

        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _load_from_env() -> dict:
        """Load configuration from environment variables.

        Returns:
            Dictionary of configuration values from environment variables
        """
        config: dict = {}

        # API URL
        if api_url := os.getenv("WISERATE_API_URL"):
            config["api_url"] = api_url

        # Data directory
        if data_dir := os.getenv("WISERATE_DATA_DIR"):
            config["data_dir"] = Path(data_dir)

        # Cache TTL
        if cache_ttl := os.getenv("WISERATE_CACHE_TTL"):
            try:
                config["cache_ttl"] = int(cache_ttl)
            except ValueError:
                pass  # Ignore invalid values, will use default

        # Log level
        if log_level := os.getenv("WISERATE_LOG_LEVEL"):
            config["log_level"] = log_level

        # Max requests per minute
        if max_requests := os.getenv("WISERATE_MAX_REQUESTS_PER_MINUTE"):
            try:
                config["max_requests_per_minute"] = int(max_requests)
            except ValueError:
                pass  # Ignore invalid values, will use default

        return config

    @property
    def currencies_file(self) -> Path:
        """Get the path to the currencies cache file.

        This file stores cached exchange rate data to reduce API calls.

        Returns:
            Path to the currencies.json cache file
        """
        return self.data_dir / "currencies.json"

    @property
    def alerts_file(self) -> Path:
        """Get the path to the alerts configuration file.

        This file stores user-defined price alerts and their configurations.

        Returns:
            Path to the alerts.json configuration file
        """
        return self.data_dir / "alerts.json"

    @property
    def log_file(self) -> Path:
        """Get the path to the application log file.

        All application logs are written to this file for debugging and monitoring.

        Returns:
            Path to the wiserate.log file
        """
        return self.data_dir / "wiserate.log"
