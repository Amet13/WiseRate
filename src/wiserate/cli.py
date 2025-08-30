"""Command-line interface for the currency exchange bot."""

import asyncio
import sys
from datetime import datetime
from decimal import Decimal

import click
import structlog
from rich.console import Console
from rich.table import Table

from .app import WiseRateApp
from .config import Settings

console = Console()


def setup_logging(level: str) -> None:
    """Setup structured logging."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


@click.group()
@click.version_option(version="2.1.0", prog_name="WiseRate")
@click.option("--log-level", default="INFO", help="Log level")
@click.option("--config-file", type=click.Path(exists=True), help="Configuration file path")
@click.pass_context
def cli(ctx, log_level: str, config_file: str):
    """WiseRate - Modern CLI tool for monitoring favorable currency exchange rates from Wise."""
    setup_logging(log_level)
    ctx.ensure_object(dict)

    try:
        if config_file:
            settings = Settings(_env_file=config_file)
        else:
            settings = Settings()
        ctx.obj["settings"] = settings
    except Exception as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("source", type=str)
@click.argument("target", type=str)
@click.option("--update", "-u", is_flag=True, help="Update currency rates cache")
@click.pass_context
def rate(ctx, source: str, target: str, update: bool):
    """Get exchange rate for a currency pair."""
    settings = ctx.obj["settings"]

    async def run():
        app = WiseRateApp(settings)
        await app.start()

        try:
            rate = await app.get_exchange_rate(source.upper(), target.upper(), update)
            console.print(f"[green]1 {rate.source} = {rate.rate} {rate.target}[/green]")

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
        finally:
            await app.stop()

    asyncio.run(run())


@cli.command()
@click.argument("source", type=str)
@click.argument("target", type=str)
@click.argument("threshold", type=float)
@click.option("--below", is_flag=True, help="Alert when rate goes below threshold")
@click.pass_context
def alert(ctx, source: str, target: str, threshold: float, below: bool):
    """Set an exchange rate alert."""
    settings = ctx.obj["settings"]

    async def run():
        app = WiseRateApp(settings)
        await app.start()

        try:
            is_above = not below
            success = await app.set_alert(
                source.upper(), target.upper(), Decimal(str(threshold)), is_above
            )

            if success:
                direction = "below" if below else "above"
                console.print(
                    f"[green]Alert set: 1 {source.upper()} {direction} "
                    f"{threshold} {target.upper()}[/green]"
                )
            else:
                console.print("[red]Failed to set alert[/red]")
                sys.exit(1)

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
        finally:
            await app.stop()

    asyncio.run(run())


@cli.command()
@click.argument("source", type=str)
@click.argument("target", type=str)
@click.pass_context
def remove_alert(ctx, source: str, target: str):
    """Remove an exchange rate alert."""
    settings = ctx.obj["settings"]

    async def run():
        app = WiseRateApp(settings)
        await app.start()

        try:
            success = await app.remove_alert(source.upper(), target.upper())

            if success:
                console.print(f"[green]Alert removed for {source.upper()}/{target.upper()}[/green]")
            else:
                console.print(
                    f"[yellow]No alert found for {source.upper()}/{target.upper()}[/yellow]"
                )

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
        finally:
            await app.stop()

    asyncio.run(run())


@cli.command()
@click.pass_context
def alerts(ctx):
    """List all active alerts."""
    settings = ctx.obj["settings"]

    async def run():
        app = WiseRateApp(settings)
        await app.start()

        try:
            alerts_text = await app.list_alerts()
            console.print(alerts_text)

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
        finally:
            await app.stop()

    asyncio.run(run())


@cli.command()
@click.pass_context
def update(ctx):
    """Update all currency rates."""
    settings = ctx.obj["settings"]

    async def run():
        app = WiseRateApp(settings)
        await app.start()

        try:
            await app.update_all_rates()
            console.print("[green]All currency rates updated[/green]")

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
        finally:
            await app.stop()

    asyncio.run(run())


@cli.command()
@click.option("--interval", default=600, help="Monitoring interval in seconds")
@click.pass_context
def monitor(ctx, interval: int):
    """Run the monitoring loop to check alerts."""
    settings = ctx.obj["settings"]

    async def run():
        app = WiseRateApp(settings)
        await app.start()

        try:
            console.print(f"[green]Starting monitoring loop (interval: {interval}s)[/green]")
            console.print("[yellow]Press Ctrl+C to stop[/yellow]")

            await app.run_monitoring_loop(interval)

        except KeyboardInterrupt:
            console.print("\n[yellow]Monitoring stopped by user[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
        finally:
            await app.stop()

    asyncio.run(run())


@cli.command()
@click.pass_context
def test(ctx):
    """Test the application configuration and connections."""
    settings = ctx.obj["settings"]

    async def run():
        app = WiseRateApp(settings)

        try:
            await app.start()
            console.print("[green]✓ Application started successfully[/green]")
            console.print("[green]✓ Configuration loaded successfully[/green]")

        except Exception as e:
            console.print(f"[red]✗ Test failed: {e}[/red]")
            sys.exit(1)
        finally:
            await app.stop()

    asyncio.run(run())


@cli.command()
@click.pass_context
def config(ctx):
    """Show current configuration."""
    settings = ctx.obj["settings"]

    table = Table(title="WiseRate Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Wise API Key", "Set" if settings.wise_api_key else "Not set")
    table.add_row("Wise API URL", settings.wise_api_url)
    table.add_row("Fallback API URL", settings.fallback_api_url)
    table.add_row("Data Directory", str(settings.data_dir))
    table.add_row("Cache TTL", f"{settings.cache_ttl}s")
    table.add_row("Log Level", settings.log_level)
    table.add_row("Max Requests/Min", str(settings.max_requests_per_minute))

    console.print(table)


@cli.command()
@click.argument("source", type=str)
@click.argument("target", type=str)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "csv", "table"]),
    default="table",
    help="Output format",
)
@click.option("--update", "-u", is_flag=True, help="Update currency rates cache")
@click.pass_context
def history(ctx, source: str, target: str, format: str, update: bool):
    """Get historical exchange rate data."""
    settings = ctx.obj["settings"]

    async def run():
        app = WiseRateApp(settings)
        await app.start()

        try:
            # For now, just get current rate (historical data would need API support)
            rate = await app.get_exchange_rate(source.upper(), target.upper(), update)

            if format == "json":
                import json

                data = {
                    "source": rate.source,
                    "target": rate.target,
                    "rate": str(rate.rate),
                    "timestamp": rate.timestamp.isoformat(),
                    "source_name": rate.source_name,
                    "target_name": rate.target_name,
                }
                console.print(json.dumps(data, indent=2))
            elif format == "csv":
                console.print(
                    f"{rate.source},{rate.target},{rate.rate},{rate.timestamp.isoformat()}"
                )
            else:  # table
                table = Table(title=f"Exchange Rate: {rate.source} → {rate.target}")
                table.add_column("Field", style="cyan")
                table.add_column("Value", style="green")
                table.add_row("Rate", str(rate.rate))
                table.add_row("Timestamp", rate.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"))
                table.add_row("Source", f"{rate.source} ({rate.source_name or 'Unknown'})")
                table.add_row("Target", f"{rate.target} ({rate.target_name or 'Unknown'})")
                console.print(table)

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
        finally:
            await app.stop()

    asyncio.run(run())


@cli.command()
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "csv", "table"]),
    default="table",
    help="Output format",
)
@click.pass_context
def export(ctx, format: str):
    """Export all data (rates and alerts) in various formats."""
    settings = ctx.obj["settings"]

    async def run():
        app = WiseRateApp(settings)
        await app.start()

        try:
            # Get all alerts
            alerts_text = await app.list_alerts()

            if format == "json":
                import json

                data = {
                    "alerts": alerts_text,
                    "exported_at": datetime.now().isoformat(),
                }
                console.print(json.dumps(data, indent=2))
            elif format == "csv":
                console.print("type,source,target,threshold,is_above,enabled,created_at")
                # Parse alerts text to CSV (simplified)
                if "No active alerts" not in alerts_text:
                    lines = alerts_text.split("\n")[2:]  # Skip header
                    for line in lines:
                        if line.startswith("•"):
                            parts = line.replace("• ", "").split(":")
                            if len(parts) == 2:
                                pair_info = parts[0]
                                status_info = parts[1]
                                # Extract information (simplified parsing)
                                console.print(f"alert,{pair_info.replace('/', ',')},{status_info}")
            else:  # table
                console.print(alerts_text)

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
        finally:
            await app.stop()

    asyncio.run(run())


@cli.command()
@click.argument("currency", type=str)
@click.pass_context
def validate_currency(ctx, currency: str):
    """Validate a currency code."""
    from .utils import get_currency_name, validate_currency_code

    currency_upper = currency.upper()
    is_valid = validate_currency_code(currency_upper)
    currency_name = get_currency_name(currency_upper)

    if is_valid:
        console.print(f"[green]✓ {currency_upper} is a valid currency code[/green]")
        if currency_name:
            console.print(f"[blue]Currency: {currency_name}[/blue]")
    else:
        console.print(f"[red]✗ {currency_upper} is not a valid currency code[/red]")
        console.print(
            "[yellow]Tip: Use 3-letter ISO 4217 currency codes (e.g., USD, EUR, GBP)[/yellow]"
        )


@cli.command()
@click.pass_context
def currencies(ctx):
    """List all supported currency codes."""
    from .utils import EXTENDED_CURRENCIES, get_currency_name

    table = Table(title="Supported Currencies")
    table.add_column("Code", style="cyan")
    table.add_column("Name", style="green")

    for currency in sorted(EXTENDED_CURRENCIES):
        name = get_currency_name(currency) or "Unknown"
        table.add_row(currency, name)

    console.print(table)


@cli.command()
@click.pass_context
def interactive(ctx):
    """Start interactive mode for WiseRate."""
    settings = ctx.obj["settings"]

    async def run():
        app = WiseRateApp(settings)
        await app.start()

        try:
            console.print("[bold blue]Welcome to WiseRate Interactive Mode![/bold blue]")
            console.print("[yellow]Type 'help' for available commands, 'quit' to exit[/yellow]\n")

            while True:
                try:
                    command = console.input("[bold green]WiseRate> [/bold green]").strip()

                    if not command:
                        continue

                    if command.lower() in ["quit", "exit", "q"]:
                        console.print("[yellow]Goodbye![/yellow]")
                        break

                    if command.lower() == "help":
                        console.print(
                            """
[bold]Available Commands:[/bold]
• [cyan]rate <source> <target>[/cyan] - Get exchange rate
• [cyan]alert <source> <target> <threshold>[/cyan] - Set alert
• [cyan]alerts[/cyan] - List all alerts
• [cyan]currencies[/cyan] - List supported currencies
• [cyan]validate <currency>[/cyan] - Validate currency code
• [cyan]config[/cyan] - Show configuration
• [cyan]help[/cyan] - Show this help
• [cyan]quit[/cyan] - Exit interactive mode
                        """
                        )
                        continue

                    if command.lower().startswith("rate "):
                        parts = command.split()
                        if len(parts) >= 3:
                            source, target = parts[1], parts[2]
                            try:
                                rate = await app.get_exchange_rate(source.upper(), target.upper())
                                console.print(
                                    f"[green]1 {rate.source} = {rate.rate} {rate.target}[/green]"
                                )
                            except Exception as e:
                                console.print(f"[red]Error: {e}[/red]")
                        else:
                            console.print("[red]Usage: rate <source> <target>[/red]")
                        continue

                    if command.lower().startswith("alert "):
                        parts = command.split()
                        if len(parts) >= 4:
                            source, target, threshold = parts[1], parts[2], parts[3]
                            try:
                                success = await app.set_alert(
                                    source.upper(), target.upper(), Decimal(threshold)
                                )
                                if success:
                                    console.print(
                                        f"[green]Alert set for {source.upper()}/"
                                        f"{target.upper()} at {threshold}[/green]"
                                    )
                                else:
                                    console.print("[red]Failed to set alert[/red]")
                            except Exception as e:
                                console.print(f"[red]Error: {e}[/red]")
                        else:
                            console.print("[red]Usage: alert <source> <target> <threshold>[/red]")
                        continue

                    if command.lower() == "alerts":
                        try:
                            alerts_text = await app.list_alerts()
                            console.print(alerts_text)
                        except Exception as e:
                            console.print(f"[red]Error: {e}[/red]")
                        continue

                    if command.lower() == "currencies":
                        from .utils import EXTENDED_CURRENCIES, get_currency_name

                        table = Table(title="Supported Currencies")
                        table.add_column("Code", style="cyan")
                        table.add_column("Name", style="green")
                        # Show first 20 currencies
                        for currency in sorted(list(EXTENDED_CURRENCIES)[:20]):
                            name = get_currency_name(currency) or "Unknown"
                            table.add_row(currency, name)
                        console.print(table)
                        continue

                    if command.lower().startswith("validate "):
                        parts = command.split()
                        if len(parts) >= 2:
                            currency = parts[1]
                            from .utils import get_currency_name, validate_currency_code

                            currency_upper = currency.upper()
                            is_valid = validate_currency_code(currency_upper)
                            currency_name = get_currency_name(currency_upper)

                            if is_valid:
                                console.print(f"[green]✓ {currency_upper} is valid[/green]")
                                if currency_name:
                                    console.print(f"[blue]{currency_name}[/blue]")
                            else:
                                console.print(f"[red]✗ {currency_upper} is invalid[/red]")
                        else:
                            console.print("[red]Usage: validate <currency>[/red]")
                        continue

                    if command.lower() == "config":
                        table = Table(title="Configuration")
                        table.add_column("Setting", style="cyan")
                        table.add_column("Value", style="green")
                        table.add_row(
                            "Wise API Key",
                            "Set" if settings.wise_api_key else "Not set",
                        )
                        table.add_row("Data Directory", str(settings.data_dir))
                        table.add_row("Cache TTL", f"{settings.cache_ttl}s")
                        console.print(table)
                        continue

                    console.print(f"[yellow]Unknown command: {command}[/yellow]")
                    console.print("[yellow]Type 'help' for available commands[/yellow]")

                except KeyboardInterrupt:
                    console.print("\n[yellow]Use 'quit' to exit[/yellow]")
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
        finally:
            await app.stop()

    asyncio.run(run())


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
