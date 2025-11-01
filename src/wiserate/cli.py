"""Command-line interface for the currency exchange bot."""

import asyncio
import sys
from collections.abc import Callable, Coroutine
from datetime import datetime
from decimal import Decimal
from functools import wraps
from typing import Any

import click
import structlog
from rich.console import Console
from rich.table import Table

from .app import WiseRateApp
from .config import Settings

console = Console()


def async_command(func: Callable[..., Coroutine[Any, Any, None]]) -> Callable[..., None]:
    """Decorator to handle async command execution with common error handling."""

    @wraps(func)
    def wrapper(ctx: Any, *args: Any, **kwargs: Any) -> None:
        async def run() -> None:
            settings = ctx.obj["settings"]
            app = WiseRateApp(settings)
            await app.start()

            try:
                await func(app, ctx, *args, **kwargs)
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                sys.exit(1)
            finally:
                await app.stop()

        asyncio.run(run())

    return wrapper


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
@click.version_option(version="2.4.0", prog_name="WiseRate")
@click.option("--log-level", default="INFO", help="Log level")
@click.pass_context
def cli(ctx: Any, log_level: str) -> None:
    """WiseRate - Modern CLI tool for monitoring currency exchange rates."""
    setup_logging(log_level)
    ctx.ensure_object(dict)

    try:
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
@async_command
async def rate(app, ctx, source: str, target: str, update: bool):
    """Get exchange rate for a currency pair."""
    rate = await app.get_exchange_rate(source.upper(), target.upper(), update)
    console.print(f"[green]1 {rate.source} = {rate.rate} {rate.target}[/green]")


@cli.command()
@click.argument("source", type=str)
@click.argument("target", type=str)
@click.argument("threshold", type=float)
@click.option("--below", is_flag=True, help="Alert when rate goes below threshold")
@click.pass_context
@async_command
async def alert(app, ctx, source: str, target: str, threshold: float, below: bool):
    """Set an exchange rate alert."""
    is_above = not below
    success = await app.set_alert(source.upper(), target.upper(), Decimal(str(threshold)), is_above)

    if success:
        direction = "below" if below else "above"
        console.print(
            f"[green]Alert set: 1 {source.upper()} {direction} {threshold} {target.upper()}[/green]"
        )
    else:
        console.print("[red]Failed to set alert[/red]")
        sys.exit(1)


@cli.command()
@click.argument("source", type=str)
@click.argument("target", type=str)
@click.pass_context
@async_command
async def remove_alert(app, ctx, source: str, target: str):
    """Remove an exchange rate alert."""
    success = await app.remove_alert(source.upper(), target.upper())

    if success:
        console.print(f"[green]Alert removed for {source.upper()}/{target.upper()}[/green]")
    else:
        console.print(f"[yellow]No alert found for {source.upper()}/{target.upper()}[/yellow]")


@cli.command()
@click.pass_context
@async_command
async def alerts(app, ctx):
    """List all active alerts."""
    alerts_text = await app.list_alerts()
    console.print(alerts_text)


@cli.command()
@click.pass_context
@async_command
async def update(app, ctx):
    """Update all currency rates."""
    await app.update_all_rates()
    console.print("[green]All currency rates updated[/green]")


@cli.command()
@click.option("--interval", default=600, help="Monitoring interval in seconds")
@click.pass_context
@async_command
async def monitor(app, ctx, interval: int):
    """Run the monitoring loop to check alerts."""
    console.print(f"[green]Starting monitoring loop (interval: {interval}s)[/green]")
    console.print("[yellow]Press Ctrl+C to stop[/yellow]")

    try:
        await app.run_monitoring_loop(interval)
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped by user[/yellow]")


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

    table.add_row("API URL", settings.api_url)
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
@async_command
async def history(app, ctx, source: str, target: str, format: str, update: bool):
    """Get historical exchange rate data."""
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
        console.print(f"{rate.source},{rate.target},{rate.rate},{rate.timestamp.isoformat()}")
    else:  # table
        table = Table(title=f"Exchange Rate: {rate.source} → {rate.target}")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Rate", str(rate.rate))
        table.add_row("Timestamp", rate.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"))
        table.add_row("Source", f"{rate.source} ({rate.source_name or 'Unknown'})")
        table.add_row("Target", f"{rate.target} ({rate.target_name or 'Unknown'})")
        console.print(table)


@cli.command()
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "csv", "table"]),
    default="table",
    help="Output format",
)
@click.pass_context
@async_command
async def export(app, ctx, format: str):
    """Export all data (rates and alerts) in various formats."""
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
        # Parse alerts text to CSV (improved parsing)
        if "No active alerts" not in alerts_text:
            lines = alerts_text.split("\n")
            # Skip header lines (usually first 2-3 lines)
            for line in lines:
                if line.startswith("•"):
                    # Parse alert line format: "• EUR/USD: above 1.05 (enabled)"
                    parts = line.replace("• ", "").split(":")
                    if len(parts) == 2:
                        pair_info = parts[0].strip()  # "EUR/USD"
                        status_info = parts[1].strip()  # "above 1.05 (enabled)"

                        if "/" in pair_info:
                            source, target = pair_info.split("/")
                            # Parse status: "above 1.05 (enabled)"
                            status_parts = status_info.split()
                            if len(status_parts) >= 3:
                                direction = status_parts[0]  # "above" or "below"
                                threshold = status_parts[1]  # "1.05"
                                enabled = "enabled" in status_info
                                is_above = direction == "above"

                                console.print(
                                    f"alert,{source},{target},{threshold},{is_above},{enabled},"
                                )
    else:  # table
        console.print(alerts_text)


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

                    # Parse and execute command
                    await execute_interactive_command(app, settings, command)

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


async def execute_interactive_command(app: WiseRateApp, settings, command: str):
    """Execute a command in interactive mode with improved parsing and validation."""
    parts = command.split()
    cmd = parts[0].lower() if parts else ""

    try:
        if cmd == "help":
            show_interactive_help()
            return

        elif cmd == "rate":
            if len(parts) < 3:
                console.print("[red]Usage: rate <source> <target> [--update][/red]")
                return

            source, target = parts[1].upper(), parts[2].upper()
            update = "--update" in parts or "-u" in parts

            rate = await app.get_exchange_rate(source, target, update)
            console.print(f"[green]1 {rate.source} = {rate.rate} {rate.target}[/green]")
            if rate.source_name and rate.target_name:
                console.print(f"[blue]{rate.source_name} → {rate.target_name}[/blue]")

        elif cmd == "alert":
            if len(parts) < 4:
                console.print("[red]Usage: alert <source> <target> <threshold> [--below][/red]")
                return

            source, target, threshold_str = parts[1].upper(), parts[2].upper(), parts[3]
            is_below = "--below" in parts

            try:
                threshold = Decimal(threshold_str)
            except ValueError:
                console.print(f"[red]Invalid threshold value: {threshold_str}[/red]")
                return

            is_above = not is_below
            success = await app.set_alert(source, target, threshold, is_above)

            if success:
                direction = "below" if is_below else "above"
                console.print(
                    f"[green]Alert set: 1 {source} {direction} {threshold} {target}[/green]"
                )
            else:
                console.print("[red]Failed to set alert[/red]")

        elif cmd == "remove-alert":
            if len(parts) < 3:
                console.print("[red]Usage: remove-alert <source> <target>[/red]")
                return

            source, target = parts[1].upper(), parts[2].upper()
            success = await app.remove_alert(source, target)

            if success:
                console.print(f"[green]Alert removed for {source}/{target}[/green]")
            else:
                console.print(f"[yellow]No alert found for {source}/{target}[/yellow]")

        elif cmd == "alerts":
            alerts_text = await app.list_alerts()
            console.print(alerts_text)

        elif cmd == "currencies":
            from .utils import EXTENDED_CURRENCIES, get_currency_name

            # Allow pagination: currencies [page]
            page = 1
            if len(parts) > 1:
                try:
                    page = int(parts[1])
                except ValueError:
                    console.print("[red]Invalid page number[/red]")
                    return

            currencies_per_page = 20
            start_idx = (page - 1) * currencies_per_page
            end_idx = start_idx + currencies_per_page

            sorted_currencies = sorted(EXTENDED_CURRENCIES)
            total_pages = (len(sorted_currencies) + currencies_per_page - 1) // currencies_per_page

            if page < 1 or page > total_pages:
                console.print(f"[red]Page {page} not found. Total pages: {total_pages}[/red]")
                return

            table = Table(title=f"Supported Currencies (Page {page}/{total_pages})")
            table.add_column("Code", style="cyan")
            table.add_column("Name", style="green")

            for currency in sorted_currencies[start_idx:end_idx]:
                name = get_currency_name(currency) or "Unknown"
                table.add_row(currency, name)

            console.print(table)

        elif cmd == "validate":
            if len(parts) < 2:
                console.print("[red]Usage: validate <currency>[/red]")
                return

            currency = parts[1].upper()
            from .utils import get_currency_name, validate_currency_code

            is_valid = validate_currency_code(currency)
            currency_name = get_currency_name(currency)

            if is_valid:
                console.print(f"[green]✓ {currency} is a valid currency code[/green]")
                if currency_name:
                    console.print(f"[blue]Currency: {currency_name}[/blue]")
            else:
                console.print(f"[red]✗ {currency} is not a valid currency code[/red]")
                console.print("[yellow]Tip: Use 3-letter ISO 4217 currency codes[/yellow]")

        elif cmd == "config":
            table = Table(title="Configuration")
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("API URL", settings.api_url)
            table.add_row("Data Directory", str(settings.data_dir))
            table.add_row("Cache TTL", f"{settings.cache_ttl}s")
            table.add_row("Log Level", settings.log_level)
            table.add_row("Max Requests/Min", str(settings.max_requests_per_minute))

            console.print(table)

        elif cmd == "update":
            console.print("[yellow]Updating all currency rates...[/yellow]")
            await app.update_all_rates()
            console.print("[green]All currency rates updated[/green]")

        elif cmd == "clear":
            console.print("[yellow]Clear command not implemented yet[/yellow]")

        else:
            console.print(f"[yellow]Unknown command: {cmd}[/yellow]")
            console.print("[yellow]Type 'help' for available commands[/yellow]")

    except Exception as e:
        console.print(f"[red]Error executing command '{cmd}': {e}[/red]")


def show_interactive_help():
    """Show comprehensive help for interactive mode."""
    help_table = Table(title="WiseRate Interactive Mode - Available Commands")
    help_table.add_column("Command", style="cyan", no_wrap=True)
    help_table.add_column("Description", style="green")
    help_table.add_column("Example", style="yellow")

    help_table.add_row("rate <src> <tgt> [--update]", "Get exchange rate", "rate EUR USD")
    help_table.add_row(
        "alert <src> <tgt> <thresh> [--below]", "Set price alert", "alert EUR USD 1.05"
    )
    help_table.add_row("remove-alert <src> <tgt>", "Remove alert", "remove-alert EUR USD")
    help_table.add_row("alerts", "List all alerts", "alerts")
    help_table.add_row("currencies [page]", "List currencies", "currencies 2")
    help_table.add_row("validate <currency>", "Validate currency code", "validate EUR")
    help_table.add_row("update", "Update all rates", "update")
    help_table.add_row("config", "Show configuration", "config")
    help_table.add_row("help", "Show this help", "help")
    help_table.add_row("quit", "Exit interactive mode", "quit")

    console.print(help_table)
    console.print("\n[yellow]Options:[/yellow]")
    console.print("  --update, -u    Update cache before getting rate")
    console.print("  --below         Alert when rate goes below threshold")


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
