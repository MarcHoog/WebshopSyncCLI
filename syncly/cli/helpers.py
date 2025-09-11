from typing_extensions import Dict, List
from rich.console import Console
from rich.table import Table

def helper_list_attribute_values(console: Console, data: List[Dict], attribute: str):
    if not data:
        console.print("[yellow]No products returned from Perfion[/yellow]")
        return

    values = []
    missing_count = 0
    for i in data:
        val = str(i.get(attribute))
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
