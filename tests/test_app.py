"""Tests for the main application class."""

import contextlib
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from wiserate.app import WiseRateApp
from wiserate.config import Settings
from wiserate.models import CurrencyPair, ExchangeRate


class TestWiseRateApp:
    """Test main application functionality."""

    @pytest.fixture
    def settings(self, tmp_path):
        """Create settings for testing."""
        return Settings(data_dir=tmp_path / "test_data")

    @pytest.fixture
    def app(self, settings):
        """Create application for testing."""
        return WiseRateApp(settings)

    @pytest.mark.asyncio
    async def test_start_stop(self, app):
        """Test application start and stop."""
        await app.start()
        await app.stop()
        # Should complete without errors

    @pytest.mark.asyncio
    async def test_get_exchange_rate(self, app):
        """Test getting exchange rate."""
        with patch.object(
            app.exchange_service, "get_exchange_rate", new_callable=AsyncMock
        ) as mock_get:
            mock_rate = ExchangeRate(source="USD", target="EUR", rate=Decimal("0.85"))
            mock_get.return_value = mock_rate

            result = await app.get_exchange_rate("USD", "EUR")

            assert result.source == "USD"
            assert result.target == "EUR"
            assert result.rate == Decimal("0.85")

    @pytest.mark.asyncio
    async def test_set_alert(self, app):
        """Test setting an alert."""
        result = await app.set_alert("USD", "EUR", Decimal("0.90"), is_above=True)

        assert result is True

        # Verify alert was created
        alerts = app.alert_service.get_all_alerts()
        assert len(alerts) == 1
        assert alerts[0].threshold == Decimal("0.90")

    @pytest.mark.asyncio
    async def test_remove_alert(self, app):
        """Test removing an alert."""
        # Add alert first
        await app.set_alert("USD", "EUR", Decimal("0.90"))

        # Remove alert
        result = await app.remove_alert("USD", "EUR")
        assert result is True

        # Try to remove again
        result = await app.remove_alert("USD", "EUR")
        assert result is False

    @pytest.mark.asyncio
    async def test_list_alerts_empty(self, app):
        """Test listing alerts when none exist."""
        result = await app.list_alerts()
        assert "No active alerts" in result

    @pytest.mark.asyncio
    async def test_list_alerts_with_alerts(self, app):
        """Test listing alerts."""
        # Add alerts
        await app.set_alert("USD", "EUR", Decimal("0.90"), is_above=True)
        await app.set_alert("GBP", "USD", Decimal("1.25"), is_above=False)

        result = await app.list_alerts()

        assert "Active alerts" in result
        assert "USD/EUR" in result
        assert "GBP/USD" in result
        assert "0.90" in result
        assert "1.25" in result

    @pytest.mark.asyncio
    async def test_update_all_rates(self, app):
        """Test updating all rates."""
        with patch.object(
            app.exchange_service, "get_all_rates", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = []

            await app.update_all_rates()

            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_alert_triggered_on_get_rate(self, app):
        """Test that alerts are checked when getting rates."""
        # Set up alert
        await app.set_alert("USD", "EUR", Decimal("0.90"), is_above=True)

        # Mock exchange service to return rate that triggers alert
        with patch.object(
            app.exchange_service, "get_exchange_rate", new_callable=AsyncMock
        ) as mock_get:
            mock_rate = ExchangeRate(source="USD", target="EUR", rate=Decimal("0.95"))
            mock_get.return_value = mock_rate

            await app.get_exchange_rate("USD", "EUR")

            # Alert should have been triggered
            alert = app.alert_service.get_alert(CurrencyPair(source="USD", target="EUR"))
            assert alert.last_triggered is not None

    @pytest.mark.asyncio
    async def test_get_exchange_rate_with_update_cache(self, app):
        """Test getting exchange rate with cache update."""
        with patch.object(
            app.exchange_service, "get_exchange_rate", new_callable=AsyncMock
        ) as mock_get:
            mock_rate = ExchangeRate(source="USD", target="EUR", rate=Decimal("0.85"))
            mock_get.return_value = mock_rate

            result = await app.get_exchange_rate("USD", "EUR", update_cache=True)

            assert result.source == "USD"
            mock_get.assert_called_once_with(CurrencyPair(source="USD", target="EUR"), True)

    @pytest.mark.asyncio
    async def test_get_exchange_rate_exception(self, app):
        """Test exception handling in get_exchange_rate."""
        with patch.object(
            app.exchange_service, "get_exchange_rate", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = Exception("API Error")

            with pytest.raises(Exception, match="API Error"):
                await app.get_exchange_rate("USD", "EUR")

    @pytest.mark.asyncio
    async def test_set_alert_exception(self, app):
        """Test exception handling in set_alert."""
        with patch.object(app.alert_service, "add_alert", side_effect=Exception("Alert Error")):
            result = await app.set_alert("USD", "EUR", Decimal("0.90"))
            assert result is False

    @pytest.mark.asyncio
    async def test_remove_alert_exception(self, app):
        """Test exception handling in remove_alert."""
        with patch.object(app.alert_service, "remove_alert", side_effect=Exception("Remove Error")):
            result = await app.remove_alert("USD", "EUR")
            assert result is False

    @pytest.mark.asyncio
    async def test_update_all_rates_with_alerts(self, app):
        """Test updating all rates with active alerts."""
        # Add an alert first
        await app.set_alert("USD", "EUR", Decimal("0.90"))

        with patch.object(
            app.exchange_service, "get_all_rates", new_callable=AsyncMock
        ) as mock_get:
            mock_rate = ExchangeRate(source="USD", target="EUR", rate=Decimal("0.95"))
            mock_get.return_value = [mock_rate]

            await app.update_all_rates()

            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_monitoring_loop_basic(self, app):
        """Test basic monitoring loop functionality."""
        with (
            patch.object(app.alert_service, "get_all_alerts", return_value=[]),
            patch.object(app.exchange_service, "get_exchange_rate", new_callable=AsyncMock),
        ):
            # Create a task that will be cancelled
            import asyncio

            task = asyncio.create_task(app.run_monitoring_loop(interval=0.1))

            # Let it run for a bit
            await asyncio.sleep(0.2)

            # Cancel the monitoring loop
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
