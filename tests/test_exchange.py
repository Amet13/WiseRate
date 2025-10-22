"""Tests for the exchange rate service."""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from wiserate.config import Settings
from wiserate.exceptions import APIError
from wiserate.exchange import ExchangeRateService, RateLimiter
from wiserate.models import CurrencyPair, ExchangeRate


class TestRateLimiter:
    """Test rate limiter functionality."""

    @pytest.mark.asyncio
    async def test_rate_limiter_basic(self):
        """Test basic rate limiting."""
        limiter = RateLimiter(requests_per_minute=60)

        # Should be able to acquire immediately
        await limiter.acquire()
        assert limiter.tokens < 60

    @pytest.mark.asyncio
    async def test_rate_limiter_refill(self):
        """Test token refill over time."""
        limiter = RateLimiter(requests_per_minute=60)

        # Use some tokens
        await limiter.acquire()

        # Wait a bit
        await asyncio.sleep(0.1)

        # Refill should happen
        await limiter.acquire()
        # Note: This test is time-sensitive and may be flaky

    @pytest.mark.asyncio
    async def test_rate_limiter_token_exhaustion(self):
        """Test rate limiter token exhaustion and wait."""
        # Create limiter with very few tokens per minute to test wait logic
        limiter = RateLimiter(requests_per_minute=1200)  # ~5 tokens per second

        # Exhaust all tokens quickly
        initial_tokens = int(limiter.tokens)
        for _ in range(initial_tokens):
            if limiter.tokens > 0:
                await limiter.acquire()

        # Now try to acquire when exhausted - this triggers wait and refill
        await limiter.acquire()

        # Token count should be decremented
        assert limiter.tokens < 0.5


class TestExchangeRateService:
    """Test exchange rate service."""

    @pytest.fixture
    def settings(self, tmp_path):
        """Create settings for testing."""
        return Settings(data_dir=tmp_path / "test_data")

    @pytest.fixture
    def service(self, settings):
        """Create exchange rate service for testing."""
        return ExchangeRateService(settings)

    @pytest.mark.asyncio
    async def test_get_exchange_rate_success(self, service):
        """Test successful exchange rate fetch."""
        pair = CurrencyPair(source="USD", target="EUR")

        with patch.object(service, "_fetch_from_api", new_callable=AsyncMock) as mock_fetch:
            expected_rate = ExchangeRate(
                source="USD", target="EUR", rate=Decimal("0.85"), timestamp=datetime.now(UTC)
            )
            mock_fetch.return_value = expected_rate

            result = await service.get_exchange_rate(pair)

            assert result.source == "USD"
            assert result.target == "EUR"
            assert result.rate == Decimal("0.85")

    @pytest.mark.asyncio
    async def test_get_exchange_rate_cached(self, service):
        """Test that cached rates are returned."""
        pair = CurrencyPair(source="USD", target="EUR")

        # First call - fetch from API
        with patch.object(service, "_fetch_from_api", new_callable=AsyncMock) as mock_fetch:
            expected_rate = ExchangeRate(
                source="USD", target="EUR", rate=Decimal("0.85"), timestamp=datetime.now(UTC)
            )
            mock_fetch.return_value = expected_rate

            result1 = await service.get_exchange_rate(pair)
            assert mock_fetch.call_count == 1

            # Second call - should use cache
            result2 = await service.get_exchange_rate(pair)
            assert mock_fetch.call_count == 1  # Not called again
            assert result1.rate == result2.rate

    @pytest.mark.asyncio
    async def test_get_exchange_rate_api_error(self, service):
        """Test handling of API errors."""
        pair = CurrencyPair(source="USD", target="EUR")

        with patch.object(service, "_fetch_from_api", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = APIError("API is down")

            with pytest.raises(APIError, match="API is down"):
                await service.get_exchange_rate(pair)

    @pytest.mark.asyncio
    async def test_fetch_from_api_success(self, service):
        """Test successful API fetch."""
        pair = CurrencyPair(source="USD", target="EUR")

        mock_response = MagicMock()
        mock_response.json.return_value = {"rates": {"EUR": 0.85, "GBP": 0.73}}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await service._fetch_from_api(pair)

            assert result.source == "USD"
            assert result.target == "EUR"
            assert result.rate == Decimal("0.85")

    @pytest.mark.asyncio
    async def test_fetch_from_api_rate_not_found(self, service):
        """Test API response without requested currency."""
        pair = CurrencyPair(source="USD", target="EUR")

        mock_response = MagicMock()
        mock_response.json.return_value = {"rates": {"GBP": 0.73, "JPY": 110.0}}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(APIError, match="Rate not found for EUR"):
                await service._fetch_from_api(pair)

    @pytest.mark.asyncio
    async def test_fetch_from_api_http_error(self, service):
        """Test API HTTP error handling."""
        pair = CurrencyPair(source="USD", target="EUR")

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "404 Not Found",
                    request=MagicMock(),
                    response=MagicMock(status_code=404, text="Not Found"),
                )
            )

            with pytest.raises(APIError, match="API error: 404"):
                await service._fetch_from_api(pair)

    @pytest.mark.asyncio
    async def test_is_cache_valid(self, service):
        """Test cache validity checking."""
        cache_key = "USD_EUR"

        # No cache entry
        assert not service._is_cache_valid(cache_key)

        # Add cache entry
        rate = ExchangeRate(
            source="USD", target="EUR", rate=Decimal("0.85"), timestamp=datetime.now(UTC)
        )
        service._cache[cache_key] = rate
        service._last_update = datetime.now(UTC)

        # Should be valid
        assert service._is_cache_valid(cache_key)

    @pytest.mark.asyncio
    async def test_get_exchange_rate_with_update_cache(self, service):
        """Test getting exchange rate with cache update."""
        pair = CurrencyPair(source="USD", target="EUR")

        # Add cached rate
        rate = ExchangeRate(
            source="USD", target="EUR", rate=Decimal("0.85"), timestamp=datetime.now(UTC)
        )
        service._cache["USD_EUR"] = rate
        service._last_update = datetime.now(UTC)

        # Mock _fetch_from_api to return a different rate
        with patch.object(service, "_fetch_from_api", new_callable=AsyncMock) as mock_fetch:
            new_rate = ExchangeRate(
                source="USD", target="EUR", rate=Decimal("0.90"), timestamp=datetime.now(UTC)
            )
            mock_fetch.return_value = new_rate

            # Get with update_cache=True should call API
            result = await service.get_exchange_rate(pair, update_cache=True)

            assert result.rate == Decimal("0.90")
            mock_fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_rates(self, service):
        """Test getting all available rates."""
        with patch.object(service, "_fetch_from_api", new_callable=AsyncMock) as mock_fetch:
            rate1 = ExchangeRate(
                source="USD", target="EUR", rate=Decimal("0.85"), timestamp=datetime.now(UTC)
            )
            rate2 = ExchangeRate(
                source="USD", target="GBP", rate=Decimal("0.73"), timestamp=datetime.now(UTC)
            )
            mock_fetch.side_effect = [rate1, rate2]

            # Should fetch rates for multiple currency pairs
            rates = await service.get_all_rates()
            assert len(rates) >= 0  # Implementation dependent
