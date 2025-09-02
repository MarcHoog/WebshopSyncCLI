import os
from rich.console import Console
from syncly.clients.ccv.client import CCVClient
from syncly.config.yaml_settings import SynclySettings
from syncly.utils import get_env


def add_arguments(parser):
    """
    Add arguments for the 'create-attribute-set-from-txt' command.
    """
    parser.add_argument(
        "txt_file",
        type=str,
        help="Path to TXT file containing attribute definitions (one per line, or tab-separated: name\\ttype\\tdescription)",
    )
    parser.add_argument(
        "--set-name",
        type=str,
        default=None,
        help="Optional name for the attribute set (for reporting purposes only)",
    )

    parser.add_argument(
        "--set-type",
        type=str,
        default="option_menu",
        help="Type of the attribute set (default: 'option_menu'). Other types can be specified as needed.",
    )

def parse_txt_file(txt_file):
    attributes = []
    with open(txt_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line or line.startswith("#"):
                continue
            attributes.append(line)
    return attributes

def handle(args, console: Console):
    """
    Handle the 'create-attribute-set-from-txt' command:
    - Parse the TXT file
    - Create each attribute in CCV via the API
    - Print results in a table
    """
    txt_file = args.txt_file
    set_name = args.set_name
    set_type = args.set_type

    if not os.path.isfile(txt_file):
        console.print(f"[red]TXT file not found: {txt_file}[/red]")
        return

    attributes = parse_txt_file(txt_file)
    if not attributes:
        console.print(f"[yellow]No valid attributes found in {txt_file}[/yellow]")
        return

    if set_name:
        console.print(f"Creating attribute set: [bold cyan]{set_name}[/bold cyan]")
    else:
        console.print(f"Creating attribute set from: [bold cyan]{txt_file}[/bold cyan]")




    settings = SynclySettings.from_yaml(get_env("SYNCLY_SETTINGS", "settings.yaml"))
    client = CCVClient(
        get_env("CCVSHOP_PUBLIC_KEY"),
        get_env("CCVSHOP_PRIVATE_KEY"),
        settings.ccv_shop.url
    )

    body = {
        "name": set_name,
        "type": set_type,
    }
    result = client.attributes.create_attribute(body)
    if not result.data or not isinstance(result.data, dict):
        console.print("[red]Failed to create attribute set[/red]")
        return

    attribute_id = result.data.get("id", "-")

    console.print(f"Created attribute set with ID: [bold green]{attribute_id}[/bold green]")

    for attr in attributes:
        client.attributes.crate_attribute_value(
            id=attribute_id,
            body={"name": attr.strip(), "default_price": 0}
        )
