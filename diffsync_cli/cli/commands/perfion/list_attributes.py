from collections import defaultdict

from rich.console import Console

from diffsync_cli.clients.perfion.client import PerfionClient

def add_arguments(parser):
    """
    Add arguments for the 'list-attributes' command.
    """
    parser.add_argument(
        "item_number",
        type=str,
        help="Perfion item number to query",
    )
    parser.add_argument(
        "attributes",
        nargs="+",
        help="One or more attribute names to retrieve",
    )

#TODO: Fix This
def handle(args, console: Console):
    """
    Handle the 'list-attributes' command: fetch products for the given item number
    and print the requested attribute values.
    """
    item_number = args.item_number
    attributes = args.attributes

    console.print(f"Querying Perfion for item [bold cyan]{item_number}[/bold cyan]...")
    client = PerfionClient()
    result = client.get_products(
        per_page=1000,
        total_pages=-1,
        item_number=item_number,
    )

    if not result.data:
        console.print(f"[yellow]No products found for item {item_number}[/yellow]")
        return

    attr_values = defaultdict(list)
    for product in result.data:
        for attr in attributes:
            value = product.get(attr)
            if value is None:
                console.print(f"[yellow]Attribute '{attr}' not found on one or more products[/yellow]")
            else:
                attr_values[attr].append(value)

    console.print("\n[bold magenta]Aggregated Attribute Values[/bold magenta]")
    for attr in attributes:
        values = attr_values.get(attr, [])
        if values:
            unique = sorted(set(values))
            console.print(f"[green]{attr}[/green]: {', '.join(str(v) for v in unique)}")
        else:
            console.print(f"[red]{attr}[/red]: no values found")
