from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

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
