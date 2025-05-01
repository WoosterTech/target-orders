from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from target_orders.main import get_orders as get_orders_from_target
from target_orders.models import parse_orders_from_html

app = typer.Typer(rich_markup_mode="rich")
console = Console()


@app.command()
def parse_orders(
    html: Annotated[
        Path, typer.Argument(help="Path to the HTML file to parse", exists=True)
    ],
    output: Annotated[
        Path | None,
        typer.Option(
            "-o",
            "--output",
            help="Path to the output file",
            dir_okay=False,
            writable=True,
        ),
    ] = None,
    debug: Annotated[bool, typer.Option("-d", help="Enable debug mode")] = False,
):
    """Parse orders from HTML."""
    orders = parse_orders_from_html(html)
    if output is None:
        console.print("[bold green]Parsed orders:[/]")
        for order in orders:
            console.print(order)
    else:
        console.print(f"[bold green]Saving parsed orders to {output}[/]")
        with output.open("w") as f:
            f.write(orders.model_dump_json(indent=4))
        console.print("[bold green]Done[/]")


@app.command()
def get_orders(
    cookies: Annotated[Path | None, typer.Option("-c", "--cookies")] = None,
    headless: Annotated[bool, typer.Option("-H", "--headless")] = False,
    remember_me: Annotated[bool, typer.Option("-r", "--remember-me")] = True,
    output: Annotated[
        Path | None, typer.Option("-o", "--output", dir_okay=False, writable=True)
    ] = None,
):
    """Get orders from Target.com."""
    console.print("[bold green]Getting orders...[/]")

    orders = get_orders_from_target(cookies_path=cookies)

    if output is None:
        console.print(f"[bold green]Found {len(orders)} orders:[/]")
        console.print(orders)
    else:
        console.print(f"[bold green]Saving orders to {output}[/]")
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w") as f:
            f.write(orders.model_dump_json(indent=4))
        console.print("[bold green]Done[/]")
