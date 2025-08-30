"""Exchange rate service for fetching and managing currency rates."""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from typing import Dict, List, Optional

import httpx
import structlog
from pydantic import ValidationError

from .config import Settings
from .exceptions import APIError, CacheError
from .models import CurrencyPair, ExchangeRate
from .utils import load_json_file, retry_with_backoff, save_json_file

logger = structlog.get_logger(__name__)


class ExchangeRateService:
    """Service for managing exchange rates."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._cache: Dict[str, ExchangeRate] = {}
        self._last_update: Optional[datetime] = None
        self._rate_limiter = asyncio.Semaphore(settings.max_requests_per_minute)

    async def get_exchange_rate(self, currency_pair: CurrencyPair) -> ExchangeRate:
        """Get the current exchange rate for a currency pair."""
        cache_key = f"{currency_pair.source}_{currency_pair.target}"

        # Check cache first
        if self._is_cache_valid(cache_key):
            logger.info("Returning cached exchange rate", pair=cache_key)
            return self._cache[cache_key]

        # Fetch fresh data
        try:
            rate = await self._fetch_exchange_rate(currency_pair)
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

    async def get_all_rates(self) -> List[ExchangeRate]:
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
        async with self._rate_limiter:
            # Try Wise API first if available
            if self.settings.wise_api_key:
                try:
                    return await self._fetch_from_wise(currency_pair)
                except Exception as e:
                    logger.warning("Wise API failed, falling back to free API", error=str(e))

            # Fallback to free API
            return await self._fetch_from_fallback(currency_pair)

    async def _fetch_from_wise(self, currency_pair: CurrencyPair) -> ExchangeRate:
        """Fetch exchange rate from Wise API."""
        if not self.settings.wise_api_key:
            raise APIError("Wise API key not configured")

        async def _make_request():
            headers = {"Authorization": f"Bearer {self.settings.wise_api_key}"}
            params = {
                "source": currency_pair.source,
                "target": currency_pair.target,
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.settings.wise_api_url}/rates",
                    headers=headers,
                    params=params,
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()

        try:
            data = await retry_with_backoff(_make_request)
            rate_value = Decimal(str(data.get("rate", 0)))

            if rate_value <= 0:
                raise APIError(f"Invalid rate received from Wise API: {rate_value}")

            return ExchangeRate(
                source=currency_pair.source,
                target=currency_pair.target,
                rate=rate_value,
                timestamp=datetime.now(UTC),
            )
        except httpx.HTTPStatusError as e:
            raise APIError(f"Wise API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise APIError(f"Wise API request failed: {e}")
        except Exception as e:
            raise APIError(f"Unexpected error fetching from Wise API: {e}")

    async def _fetch_from_fallback(self, currency_pair: CurrencyPair) -> ExchangeRate:
        """Fetch exchange rate from fallback free API."""

        async def _make_request():
            url = f"{self.settings.fallback_api_url}/latest/{currency_pair.source}"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()
                return response.json()

        try:
            data = await retry_with_backoff(_make_request)
            rates = data.get("rates", {})
            target_rate = rates.get(currency_pair.target)

            if target_rate is None:
                raise APIError(f"Rate not found for {currency_pair.target}")

            rate_value = Decimal(str(target_rate))
            if rate_value <= 0:
                raise APIError(f"Invalid rate received from fallback API: {rate_value}")

            return ExchangeRate(
                source=currency_pair.source,
                target=currency_pair.target,
                rate=rate_value,
                timestamp=datetime.now(UTC),
            )
        except httpx.HTTPStatusError as e:
            raise APIError(f"Fallback API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise APIError(f"Fallback API request failed: {e}")
        except Exception as e:
            raise APIError(f"Unexpected error fetching from fallback API: {e}")

    async def _fetch_all_rates(self) -> List[ExchangeRate]:
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
        """Save exchange rate to persistent cache."""
        try:
            cache_data = load_json_file(self.settings.currencies_file)
            cache_key = f"{rate.source}_{rate.target}"
            cache_data[cache_key] = {
                "source": rate.source,
                "target": rate.target,
                "rate": str(rate.rate),
                "timestamp": rate.timestamp.isoformat(),
            }

            save_json_file(self.settings.currencies_file, cache_data)
        except Exception as e:
            logger.error("Failed to save to cache", error=str(e))
            raise CacheError(f"Failed to save rate to cache: {e}")

    async def _save_all_to_cache(self, rates: List[ExchangeRate]) -> None:
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

            save_json_file(self.settings.currencies_file, cache_data)
        except Exception as e:
            logger.error("Failed to save all rates to cache", error=str(e))
            raise CacheError(f"Failed to save all rates to cache: {e}")

    async def _load_from_cache(self) -> List[ExchangeRate]:
        """Load exchange rates from persistent cache."""
        try:
            cache_data = load_json_file(self.settings.currencies_file)
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
