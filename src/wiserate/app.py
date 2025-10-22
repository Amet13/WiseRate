"""Main application class for the currency exchange bot."""

import asyncio
from decimal import Decimal

import structlog

from .alerts import AlertService
from .config import Settings
from .exchange import ExchangeRateService
from .models import CurrencyPair, ExchangeRate

logger = structlog.get_logger(__name__)


class WiseRateApp:
    """Main application class for the currency exchange bot."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.exchange_service = ExchangeRateService(settings)
        self.alert_service = AlertService(settings)

    async def start(self) -> None:
        """Start the application."""
        logger.info("Starting WiseRate application")
        logger.info("WiseRate application started successfully")

    async def get_exchange_rate(
        self, source: str, target: str, update_cache: bool = False
    ) -> ExchangeRate:
        """Get exchange rate for a currency pair."""
        try:
            currency_pair = CurrencyPair(source=source, target=target)
            rate = await self.exchange_service.get_exchange_rate(currency_pair, update_cache)

            # Check if any alerts should be triggered
            triggered_alerts = self.alert_service.check_alerts(rate)

            # Log triggered alerts
            for triggered_alert in triggered_alerts:
                logger.info(
                    "Alert triggered",
                    source=rate.source,
                    target=rate.target,
                    rate=str(rate.rate),
                    threshold=str(triggered_alert.threshold),
                    is_above=triggered_alert.is_above,
                )

            return rate

        except Exception as e:
            logger.error(
                "Failed to get exchange rate",
                source=source,
                target=target,
                error=str(e),
            )
            raise

    async def set_alert(
        self, source: str, target: str, threshold: Decimal, is_above: bool = True
    ) -> bool:
        """Set an exchange rate alert."""
        try:
            currency_pair = CurrencyPair(source=source, target=target)
            self.alert_service.add_alert(currency_pair, threshold, is_above)
            logger.info(
                f"Alert set: 1 {source} {'above' if is_above else 'below'} {threshold} {target}"
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to set alert",
                source=source,
                target=target,
                threshold=str(threshold),
                error=str(e),
            )
            return False

    async def remove_alert(self, source: str, target: str) -> bool:
        """Remove an exchange rate alert."""
        try:
            currency_pair = CurrencyPair(source=source, target=target)
            success = self.alert_service.remove_alert(currency_pair)

            if success:
                logger.info(f"Alert removed for {source}/{target}")

            return success

        except Exception as e:
            logger.error("Failed to remove alert", source=source, target=target, error=str(e))
            return False

    async def list_alerts(self) -> str:
        """List all active alerts."""
        alerts = self.alert_service.get_all_alerts()

        if not alerts:
            return "No active alerts"
        else:
            message = "Active alerts:\n\n"
            for alert in alerts:
                direction = "above" if alert.is_above else "below"
                status = "enabled" if alert.enabled else "disabled"
                message += (
                    f"• {alert.currency_pair.source}/{alert.currency_pair.target}: "
                    f"{direction} {alert.threshold} ({status})\n"
                )

            return message

    async def update_all_rates(self) -> None:
        """Update all exchange rates."""
        try:
            rates = await self.exchange_service.get_all_rates()
            logger.info("Updated all exchange rates", count=len(rates))

            # Check all alerts
            for rate in rates:
                self.alert_service.check_alerts(rate)

        except Exception as e:
            logger.error("Failed to update all rates", error=str(e))

    async def run_monitoring_loop(self, interval: int = 600) -> None:
        """Run the monitoring loop to check alerts periodically."""
        logger.info("Starting monitoring loop", interval_seconds=interval)

        while True:
            try:
                # Get all active alerts
                alerts = self.alert_service.get_all_alerts()

                if alerts:
                    logger.info("Checking alerts", count=len(alerts))

                    # Check each alert by getting current rates
                    for alert in alerts:
                        if alert.enabled:
                            try:
                                await self.get_exchange_rate(
                                    alert.currency_pair.source,
                                    alert.currency_pair.target,
                                )

                                # The alert checking is done in get_exchange_rate
                                logger.debug("Checked alert", pair=str(alert.currency_pair))

                            except Exception as e:
                                logger.error(
                                    "Failed to check alert",
                                    pair=str(alert.currency_pair),
                                    error=str(e),
                                )

                # Wait for next interval
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                logger.info("Monitoring loop cancelled")
                break
            except Exception as e:
                logger.error("Error in monitoring loop", error=str(e))
                await asyncio.sleep(interval)

    async def stop(self) -> None:
        """Stop the application."""
        logger.info("Stopping WiseRate application")
        # Cleanup tasks if needed
        logger.info("WiseRate application stopped")
