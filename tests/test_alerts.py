"""Tests for the alert service."""

from decimal import Decimal
from pathlib import Path

import pytest

from wiserate.alerts import AlertService
from wiserate.config import Settings
from wiserate.models import Alert, CurrencyPair, ExchangeRate


class TestAlertService:
    """Test alert service functionality."""

    @pytest.fixture
    def settings(self, tmp_path):
        """Create settings for testing."""
        return Settings(data_dir=tmp_path / "test_data")

    @pytest.fixture
    def service(self, settings):
        """Create alert service for testing."""
        return AlertService(settings)

    def test_add_alert(self, service):
        """Test adding a new alert."""
        pair = CurrencyPair(source="USD", target="EUR")
        threshold = Decimal("0.90")

        alert = service.add_alert(pair, threshold, is_above=True)

        assert alert.currency_pair == pair
        assert alert.threshold == threshold
        assert alert.is_above is True
        assert alert.enabled is True

    def test_remove_alert(self, service):
        """Test removing an alert."""
        pair = CurrencyPair(source="USD", target="EUR")
        threshold = Decimal("0.90")

        # Add alert
        service.add_alert(pair, threshold)

        # Remove alert
        result = service.remove_alert(pair)
        assert result is True

        # Try to remove again
        result = service.remove_alert(pair)
        assert result is False

    def test_get_alert(self, service):
        """Test retrieving a specific alert."""
        pair = CurrencyPair(source="USD", target="EUR")
        threshold = Decimal("0.90")

        # No alert exists
        assert service.get_alert(pair) is None

        # Add alert
        service.add_alert(pair, threshold)

        # Get alert
        alert = service.get_alert(pair)
        assert alert is not None
        assert alert.threshold == threshold

    def test_get_all_alerts(self, service):
        """Test retrieving all alerts."""
        assert len(service.get_all_alerts()) == 0

        # Add multiple alerts
        service.add_alert(CurrencyPair(source="USD", target="EUR"), Decimal("0.90"))
        service.add_alert(CurrencyPair(source="GBP", target="USD"), Decimal("1.25"))

        alerts = service.get_all_alerts()
        assert len(alerts) == 2

    def test_check_alerts_triggered(self, service):
        """Test alert triggering when threshold is crossed."""
        pair = CurrencyPair(source="USD", target="EUR")
        threshold = Decimal("0.90")

        # Add alert for rate going above threshold
        service.add_alert(pair, threshold, is_above=True)

        # Create exchange rate above threshold
        rate = ExchangeRate(source="USD", target="EUR", rate=Decimal("0.95"))

        # Check alerts
        triggered = service.check_alerts(rate)

        assert len(triggered) == 1
        assert triggered[0].threshold == threshold

    def test_check_alerts_not_triggered(self, service):
        """Test alert not triggering when threshold is not crossed."""
        pair = CurrencyPair(source="USD", target="EUR")
        threshold = Decimal("0.90")

        # Add alert for rate going above threshold
        service.add_alert(pair, threshold, is_above=True)

        # Create exchange rate below threshold
        rate = ExchangeRate(source="USD", target="EUR", rate=Decimal("0.85"))

        # Check alerts
        triggered = service.check_alerts(rate)

        assert len(triggered) == 0

    def test_check_alerts_below_threshold(self, service):
        """Test alert for rate going below threshold."""
        pair = CurrencyPair(source="USD", target="EUR")
        threshold = Decimal("0.90")

        # Add alert for rate going below threshold
        service.add_alert(pair, threshold, is_above=False)

        # Create exchange rate below threshold
        rate = ExchangeRate(source="USD", target="EUR", rate=Decimal("0.85"))

        # Check alerts
        triggered = service.check_alerts(rate)

        assert len(triggered) == 1

    def test_enable_disable_alert(self, service):
        """Test enabling and disabling alerts."""
        pair = CurrencyPair(source="USD", target="EUR")
        threshold = Decimal("0.90")

        # Add alert
        service.add_alert(pair, threshold)

        # Disable alert
        result = service.disable_alert(pair)
        assert result is True

        alert = service.get_alert(pair)
        assert alert.enabled is False

        # Enable alert
        result = service.enable_alert(pair)
        assert result is True

        alert = service.get_alert(pair)
        assert alert.enabled is True

    def test_clear_all_alerts(self, service):
        """Test clearing all alerts."""
        # Add multiple alerts
        service.add_alert(CurrencyPair(source="USD", target="EUR"), Decimal("0.90"))
        service.add_alert(CurrencyPair(source="GBP", target="USD"), Decimal("1.25"))

        assert len(service.get_all_alerts()) == 2

        # Clear all
        service.clear_all_alerts()

        assert len(service.get_all_alerts()) == 0

    def test_save_and_load_alerts(self, settings):
        """Test saving and loading alerts from file."""
        # Create service and add alerts
        service1 = AlertService(settings)
        pair = CurrencyPair(source="USD", target="EUR")
        service1.add_alert(pair, Decimal("0.90"))

        # Create new service instance - should load alerts
        service2 = AlertService(settings)
        alerts = service2.get_all_alerts()

        assert len(alerts) == 1
        assert alerts[0].threshold == Decimal("0.90")

    def test_get_alert_key(self, service):
        """Test alert key generation."""
        pair = CurrencyPair(source="USD", target="EUR")
        key = service._get_alert_key(pair)

        assert key == "USD_EUR"

