"""Constants for WiseRate application."""

# API Configuration
DEFAULT_TIMEOUT = 30.0
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 1.0

# Cache Configuration
DEFAULT_CACHE_TTL = 3600  # 1 hour
MAX_CACHE_TTL = 86400  # 24 hours
MIN_CACHE_TTL = 60  # 1 minute

# Rate Limiting
DEFAULT_MAX_REQUESTS_PER_MINUTE = 60
MAX_REQUESTS_PER_MINUTE = 120
MIN_REQUESTS_PER_MINUTE = 10

# Monitoring
DEFAULT_MONITORING_INTERVAL = 600  # 10 minutes
MIN_MONITORING_INTERVAL = 60  # 1 minute
MAX_MONITORING_INTERVAL = 3600  # 1 hour

# File Paths
DEFAULT_DATA_DIR = ".wiserate"
CACHE_FILE = "currencies.json"
ALERTS_FILE = "alerts.json"
LOG_FILE = "wiserate.log"

# Logging
DEFAULT_LOG_LEVEL = "INFO"
SUPPORTED_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Currency Precision
CURRENCY_PRECISION = {
    "JPY": 0,
    "KRW": 0,
    "IDR": 0,
    "VND": 0,
    "BYN": 0,  # No decimals
    "BHD": 3,
    "IQD": 3,
    "JOD": 3,
    "KWD": 3,
    "LYD": 3,
    "OMR": 3,
    "TND": 3,  # 3 decimals
    "DEFAULT": 2,  # Standard 2 decimals
}
