
from rich.console import Console

from syncly.clients.perfion.client import PerfionClient
from syncly.cli.helpers import helper_list_attribute_values

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

    helper_list_attribute_values(console, result.data, attribute)
