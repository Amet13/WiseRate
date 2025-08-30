"""Alert service for managing exchange rate alerts."""

import json
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

import structlog
from pydantic import ValidationError

from .config import Settings
from .models import Alert, CurrencyPair, ExchangeRate

logger = structlog.get_logger(__name__)


class AlertService:
    """Service for managing exchange rate alerts."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._alerts: Dict[str, Alert] = {}
        self._load_alerts()

    def add_alert(
        self, currency_pair: CurrencyPair, threshold: Decimal, is_above: bool = True
    ) -> Alert:
        """Add a new exchange rate alert."""
        alert = Alert(currency_pair=currency_pair, threshold=threshold, is_above=is_above)

        alert_key = self._get_alert_key(currency_pair)
        self._alerts[alert_key] = alert

        logger.info(
            "Alert added",
            pair=str(currency_pair),
            threshold=str(threshold),
            is_above=is_above,
        )
        self._save_alerts()

        return alert

    def remove_alert(self, currency_pair: CurrencyPair) -> bool:
        """Remove an exchange rate alert."""
        alert_key = self._get_alert_key(currency_pair)

        if alert_key in self._alerts:
            del self._alerts[alert_key]
            logger.info("Alert removed", pair=str(currency_pair))
            self._save_alerts()
            return True

        return False

    def get_alert(self, currency_pair: CurrencyPair) -> Optional[Alert]:
        """Get an alert for a specific currency pair."""
        alert_key = self._get_alert_key(currency_pair)
        return self._alerts.get(alert_key)

    def get_all_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return list(self._alerts.values())

    def check_alerts(self, exchange_rate: ExchangeRate) -> List[Alert]:
        """Check if any alerts should be triggered for the given exchange rate."""
        triggered_alerts = []
        currency_pair = CurrencyPair(source=exchange_rate.source, target=exchange_rate.target)
        alert_key = self._get_alert_key(currency_pair)

        if alert_key in self._alerts:
            alert = self._alerts[alert_key]
            if alert.should_trigger(exchange_rate.rate):
                alert.trigger()
                triggered_alerts.append(alert)
                logger.info(
                    "Alert triggered",
                    pair=str(currency_pair),
                    threshold=str(alert.threshold),
                    rate=str(exchange_rate.rate),
                )

        if triggered_alerts:
            self._save_alerts()

        return triggered_alerts

    def _get_alert_key(self, currency_pair: CurrencyPair) -> str:
        """Get the key for storing an alert."""
        return f"{currency_pair.source}_{currency_pair.target}"

    def _load_alerts(self) -> None:
        """Load alerts from persistent storage."""
        try:
            if self.settings.alerts_file.exists():
                with open(self.settings.alerts_file, "r") as f:
                    data = json.load(f)

                for alert_data in data.values():
                    try:
                        currency_pair = CurrencyPair(
                            source=alert_data["currency_pair"]["source"],
                            target=alert_data["currency_pair"]["target"],
                        )

                        alert = Alert(
                            currency_pair=currency_pair,
                            threshold=Decimal(alert_data["threshold"]),
                            is_above=alert_data["is_above"],
                            enabled=alert_data.get("enabled", True),
                            created_at=datetime.fromisoformat(alert_data["created_at"]),
                        )

                        if "last_triggered" in alert_data:
                            alert.last_triggered = datetime.fromisoformat(
                                alert_data["last_triggered"]
                            )

                        alert_key = self._get_alert_key(currency_pair)
                        self._alerts[alert_key] = alert

                    except (ValidationError, KeyError, ValueError) as e:
                        logger.warning("Invalid alert data", data=alert_data, error=str(e))

        except Exception as e:
            logger.error("Failed to load alerts", error=str(e))

    def _save_alerts(self) -> None:
        """Save alerts to persistent storage."""
        try:
            data = {}
            for alert_key, alert in self._alerts.items():
                data[alert_key] = {
                    "currency_pair": {
                        "source": alert.currency_pair.source,
                        "target": alert.currency_pair.target,
                    },
                    "threshold": str(alert.threshold),
                    "is_above": alert.is_above,
                    "enabled": alert.enabled,
                    "created_at": alert.created_at.isoformat(),
                    "last_triggered": (
                        alert.last_triggered.isoformat() if alert.last_triggered else None
                    ),
                }

            with open(self.settings.alerts_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error("Failed to save alerts", error=str(e))

    def clear_all_alerts(self) -> None:
        """Clear all alerts."""
        self._alerts.clear()
        self._save_alerts()
        logger.info("All alerts cleared")

    def enable_alert(self, currency_pair: CurrencyPair) -> bool:
        """Enable an alert."""
        alert = self.get_alert(currency_pair)
        if alert:
            alert.enabled = True
            self._save_alerts()
            logger.info("Alert enabled", pair=str(currency_pair))
            return True
        return False

    def disable_alert(self, currency_pair: CurrencyPair) -> bool:
        """Disable an alert."""
        alert = self.get_alert(currency_pair)
        if alert:
            alert.enabled = False
            self._save_alerts()
            logger.info("Alert disabled", pair=str(currency_pair))
            return True
        return False
