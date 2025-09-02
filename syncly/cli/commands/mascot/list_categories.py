from collections import Counter

from rich.table import Table
from rich.console import Console

from syncly.clients.perfion.client import PerfionClient


def add_arguments(parser):
    """
    No arguments for list_categories: pulls all products and shows unique categories.
    """
    # No extra CLI arguments needed for this command.
    return


def handle(args, console: Console):
    """
    Handle the perfion list-categories command by fetching all products
    (across all pages) and displaying a unique list of categories with counts.
    """
    console.print("Fetching all Perfion products (this may take a moment)...", style="dim")
    client = PerfionClient()
    result = client.get_products(per_page=1000, total_pages=-1)

    if not result.data:
        console.print("[yellow]No products returned from Perfion[/yellow]")
        return

    # Assume each product dict contains a 'CategoryName' key for the Perfion category.
    # Fallback: try common alternatives if that key is missing.
    category_field = None
    sample = result.data[0]
    for key in ("Category", "CategoryName", "category", "category_name"):
        if key in sample:
            category_field = key
            break

    if not category_field:
        console.print("[red]Unable to locate a category field in Perfion product data[/red]")
        return

    # Count occurrences of each category
    categories = Counter()
    for product in result.data:
        cat = product.get(category_field)
        if cat:
            categories[cat] += 1

    table = Table(title="Perfion Categories")
    table.add_column("Category", style="cyan", no_wrap=True)
    table.add_column("Count", style="magenta", justify="right")

    for cat, count in categories.most_common():
        table.add_row(str(cat), str(count))

    console.print(table)
