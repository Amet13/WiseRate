"""Exchange rate service for fetching and managing currency rates."""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from types import TracebackType
from typing import Any

import httpx
import structlog
from pydantic import ValidationError

from .config import Settings
from .exceptions import APIError, CacheError
from .models import CurrencyPair, ExchangeRate
from .utils import load_json_file_async, retry_with_backoff, save_json_file_async

logger = structlog.get_logger(__name__)


class RateLimiter:
    """Token bucket rate limiter for API requests."""

    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.tokens = requests_per_minute
        self.last_refill = datetime.now(UTC)
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire a token, waiting if necessary."""
        async with self._lock:
            now = datetime.now(UTC)

            # Refill tokens based on time passed
            time_passed = (now - self.last_refill).total_seconds()
            tokens_to_add = int(time_passed * self.requests_per_minute / 60)
            self.tokens = min(self.requests_per_minute, self.tokens + tokens_to_add)
            self.last_refill = now

            if self.tokens <= 0:
                # Calculate wait time for next token
                wait_time = 60 / self.requests_per_minute
                await asyncio.sleep(wait_time)
                self.tokens += 1

            self.tokens -= 1


class ExchangeRateService:
    """Service for managing exchange rates."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._cache: dict[str, ExchangeRate] = {}
        self._last_update: datetime | None = None
        self._rate_limiter = RateLimiter(settings.max_requests_per_minute)
        # Create persistent AsyncClient with connection pooling
        limits = httpx.Limits(max_connections=10, max_keepalive_connections=5)
        timeout = httpx.Timeout(30.0, connect=10.0)
        self._client = httpx.AsyncClient(limits=limits, timeout=timeout)
        # Request deduplication: track pending requests to avoid duplicate API calls
        self._pending_requests: dict[str, asyncio.Task[ExchangeRate]] = {}

    async def __aenter__(self) -> ExchangeRateService:
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit - close client."""
        await self._client.aclose()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def get_exchange_rate(
        self, currency_pair: CurrencyPair, update_cache: bool = False
    ) -> ExchangeRate:
        """Get the current exchange rate for a currency pair.

        Implements request deduplication: if multiple concurrent requests
        are made for the same currency pair, they share the same API call.
        """
        cache_key = f"{currency_pair.source}_{currency_pair.target}"

        # Check cache first (unless update_cache is True)
        if not update_cache and self._is_cache_valid(cache_key):
            logger.info("Returning cached exchange rate", pair=cache_key)
            return self._cache[cache_key]

        # Check if there's already a pending request for this pair
        if cache_key in self._pending_requests:
            logger.debug("Deduplicating request", pair=cache_key)
            try:
                return await self._pending_requests[cache_key]
            except Exception:
                # If the pending request failed, remove it and continue
                self._pending_requests.pop(cache_key, None)
                raise

        # Create new request task
        request_task = asyncio.create_task(self._fetch_exchange_rate(currency_pair))
        self._pending_requests[cache_key] = request_task

        try:
            rate = await request_task
            self._cache[cache_key] = rate
            self._last_update = datetime.now(UTC)
            await self._save_to_cache(rate)
            return rate
        except Exception as e:
            logger.error("Failed to fetch exchange rate", pair=cache_key, error=str(e))
            # Try to return cached data if available
            if cache_key in self._cache:
                logger.warning("Returning stale cached data", pair=cache_key)
                return self._cache[cache_key]
            raise
        finally:
            # Clean up pending request
            self._pending_requests.pop(cache_key, None)

    async def get_all_rates(self) -> list[ExchangeRate]:
        """Get all available exchange rates."""
        try:
            rates = await self._fetch_all_rates()
            self._cache.clear()
            for rate in rates:
                cache_key = f"{rate.source}_{rate.target}"
                self._cache[cache_key] = rate
            self._last_update = datetime.now(UTC)
            await self._save_all_to_cache(rates)
            return rates
        except Exception as e:
            logger.error("Failed to fetch all rates", error=str(e))
            # Try to load from cache
            return await self._load_from_cache()

    async def _fetch_exchange_rate(self, currency_pair: CurrencyPair) -> ExchangeRate:
        """Fetch exchange rate from API."""
        # Acquire rate limit token
        await self._rate_limiter.acquire()

        # Fetch from API
        return await self._fetch_from_api(currency_pair)

    async def _fetch_from_api(self, currency_pair: CurrencyPair) -> ExchangeRate:
        """Fetch exchange rate from API."""
        logger.info(
            "Fetching exchange rate", source=currency_pair.source, target=currency_pair.target
        )

        async def _make_request() -> dict[str, Any]:
            url = f"{self.settings.api_url}/latest/{currency_pair.source}"
            response = await self._client.get(url)
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]

        try:
            data = await retry_with_backoff(_make_request)
            rates = data.get("rates", {})
            target_rate = rates.get(currency_pair.target)

            if target_rate is None:
                logger.error(
                    "Rate not found in API response",
                    source=currency_pair.source,
                    target=currency_pair.target,
                    available_rates=list(rates.keys()),
                )
                raise APIError(f"Rate not found for {currency_pair.target}")

            rate_value = Decimal(str(target_rate))
            if rate_value <= 0:
                logger.error("Invalid rate from API", rate=target_rate)
                raise APIError(f"Invalid rate received from API: {rate_value}")

            return ExchangeRate(
                source=currency_pair.source,
                target=currency_pair.target,
                rate=rate_value,
                timestamp=datetime.now(UTC),
            )
        except httpx.HTTPStatusError as e:
            logger.error(
                "API HTTP error",
                status_code=e.response.status_code,
                url=str(e.request.url),
                response=e.response.text[:200] if e.response.text else None,
            )
            raise APIError(
                f"API error: {e.response.status_code}",
                status_code=e.response.status_code,
                response_text=e.response.text[:500] if e.response.text else None,
            )
        except httpx.TimeoutException as e:
            logger.error(
                "API timeout error", url=str(e.request.url) if hasattr(e, "request") else None
            )
            raise APIError(f"API request timed out: {e}")
        except httpx.ConnectError as e:
            logger.error("API connection error", error=str(e))
            raise APIError(f"Failed to connect to API: {e}")
        except httpx.RequestError as e:
            logger.error(
                "API request error",
                error=str(e),
                url=str(e.request.url) if hasattr(e, "request") else None,
            )
            raise APIError(f"API request failed: {e}")
        except Exception as e:
            logger.error("Unexpected API error", error=str(e), error_type=type(e).__name__)
            raise APIError(f"Unexpected error fetching from API: {e}")

    async def _fetch_all_rates(self) -> list[ExchangeRate]:
        """Fetch all available exchange rates."""
        # This would need to be implemented based on the specific API
        # For now, return empty list
        return []

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid."""
        if cache_key not in self._cache:
            return False

        if not self._last_update:
            return False

        cache_age = datetime.now(UTC) - self._last_update
        return cache_age.total_seconds() < self.settings.cache_ttl

    async def _save_to_cache(self, rate: ExchangeRate) -> None:
        """Save exchange rate to persistent cache.

        Args:
            rate: Exchange rate to save to cache

        Raises:
            CacheError: If cache save operation fails
        """
        try:
            cache_data = await load_json_file_async(self.settings.currencies_file)
            cache_key = f"{rate.source}_{rate.target}"
            cache_data[cache_key] = {
                "source": rate.source,
                "target": rate.target,
                "rate": str(rate.rate),
                "timestamp": rate.timestamp.isoformat(),
            }

            await save_json_file_async(self.settings.currencies_file, cache_data)
            logger.debug("Saved rate to cache", pair=cache_key)
        except Exception as e:
            logger.error("Failed to save to cache", error=str(e))
            raise CacheError(f"Failed to save rate to cache: {e}")

    async def _save_all_to_cache(self, rates: list[ExchangeRate]) -> None:
        """Save all exchange rates to persistent cache."""
        try:
            cache_data = {}
            for rate in rates:
                cache_key = f"{rate.source}_{rate.target}"
                cache_data[cache_key] = {
                    "source": rate.source,
                    "target": rate.target,
                    "rate": str(rate.rate),
                    "timestamp": rate.timestamp.isoformat(),
                }

            await save_json_file_async(self.settings.currencies_file, cache_data)
        except Exception as e:
            logger.error("Failed to save all rates to cache", error=str(e))
            raise CacheError(f"Failed to save all rates to cache: {e}")

    async def _load_from_cache(self) -> list[ExchangeRate]:
        """Load exchange rates from persistent cache."""
        try:
            cache_data = await load_json_file_async(self.settings.currencies_file)
            rates = []

            for key, data in cache_data.items():
                try:
                    rate = ExchangeRate(
                        source=data["source"],
                        target=data["target"],
                        rate=Decimal(data["rate"]),
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                    )
                    rates.append(rate)
                except (ValidationError, KeyError, ValueError) as e:
                    logger.warning("Invalid cache entry", key=key, error=str(e))

            return rates
        except Exception as e:
            logger.error("Failed to load from cache", error=str(e))
            raise CacheError(f"Failed to load rates from cache: {e}")
