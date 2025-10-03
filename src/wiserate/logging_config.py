"""Logging configuration for WiseRate.

This module provides centralized logging configuration with support for:
- File rotation to prevent log files from growing too large
- Structured logging with contextual information
- Multiple output formats (console and file)
- Different log levels for different environments
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

import structlog
from structlog.typing import FilteringBoundLogger


def configure_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    enable_json: bool = False,
    max_file_size: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> FilteringBoundLogger:
    """Configure structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file for file-based logging
        enable_json: If True, use JSON formatting for logs
        max_file_size: Maximum size of log file before rotation (bytes)
        backup_count: Number of backup files to keep

    Returns:
        Configured logger instance

    Example:
        >>> from pathlib import Path
        >>> logger = configure_logging(
        ...     log_level="DEBUG",
        ...     log_file=Path("~/.wiserate/wiserate.log"),
        ...     enable_json=False
        ... )
        >>> logger.info("Application started", version="2.3.0")
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure standard logging first
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
    )

    # Add file handler if log file is specified
    if log_file:
        # Ensure log directory exists
        log_file = Path(log_file).expanduser()
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Create rotating file handler
        file_handler = RotatingFileHandler(
            filename=str(log_file),
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(numeric_level)

        # Add formatter
        if enable_json:
            json_format = (
                '{"time":"%(asctime)s","level":"%(levelname)s",'
                '"name":"%(name)s","message":"%(message)s"}'
            )
            formatter = logging.Formatter(json_format)
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        file_handler.setFormatter(formatter)

        # Add handler to root logger
        logging.getLogger().addHandler(file_handler)

    # Configure structlog processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Add appropriate renderer based on format preference
    if enable_json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Return a logger instance
    return structlog.get_logger()


def get_logger(name: str) -> FilteringBoundLogger:
    """Get a logger instance for a specific module.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing request", user_id=123, action="login")
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """Mixin class to add logging capabilities to any class.

    Example:
        >>> class MyService(LoggerMixin):
        ...     def process(self):
        ...         self.logger.info("Processing started")
        ...         # ... do work ...
        ...         self.logger.info("Processing completed")
    """

    @property
    def logger(self) -> FilteringBoundLogger:
        """Get logger for this class."""
        return structlog.get_logger(self.__class__.__name__)
