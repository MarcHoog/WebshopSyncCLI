
from rich.console import Console
from rich.table import Table

from diffsync_cli.clients.perfion.client import PerfionClient

def add_arguments(parser):
    """
    Add arguments for the 'list-values' command.
    """
    parser.add_argument(
        "attribute_name",
        type=str,
        help="Name of the Perfion attribute to list possible values for",
    )

def handle(args, console: Console):
    """
    Handle the 'list-values' command: fetch all products and list unique attribute values.

    Args:
        args: Parsed CLI arguments.
        console: Rich console for output.
    """
    attribute = args.attribute_name

    console.print(f"Fetching all Perfion products to collect values for [bold cyan]{attribute}[/bold cyan]...", style="dim")
    client = PerfionClient()
    result = client.get_products(per_page=1000, total_pages=-1)

    if not result.data:
        console.print("[yellow]No products returned from Perfion[/yellow]")
        return

    values = []
    missing_count = 0
    for product in result.data:
        val = product.get(attribute)
        if val is None:
            missing_count += 1
        else:
            values.append(val)

    if not values:
        console.print(f"[red]No values found for attribute '{attribute}'[/red]")
        return

    unique_values = sorted(set(values))

    table = Table(title=f"{attribute}", caption="all found values", box=None)
    table.add_column("Value", style="green")
    for val in unique_values:
        table.add_row(str(val))

    console.print(table)

    if missing_count:
        console.print(f"[yellow]{missing_count} product(s) missing attribute '{attribute}'[/yellow]")
