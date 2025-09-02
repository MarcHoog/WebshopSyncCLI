
from rich.console import Console
from typing import List, Dict, cast
from syncly.config import SynclySettings
from syncly.clients.mascot.client import InMemoryFTPClient
from syncly.intergrations.ccvshop.adapters.adapter_mascot import MascotAdapter
from syncly.cli.helpers import helper_list_attribute_values
from syncly.utils import get_env, load_env_files

def add_arguments(parser):
    """
    Add arguments for the 'list-values' command.
    """
    parser.add_argument(
        "attribute",
        type=str,
        help="Name of the Perfion attribute to list possible values for",
    )

    parser.add_argument(
        "--env-file",
        type=str,
        help="Path to environment file",
        required=False
    )

    parser.add_argument(
        "--product-info-file",
        type=str,
        help="FTP path to product info file",
        required=True,
    )

    parser.add_argument(
        "--stock-file",
        type=str,
        help="FTP path to product stock file",
        required=True,
    )

def handle(args, console: Console):
    """
    Handle the 'list-values' command: fetch all products and list unique attribute values.

    Args:
        args: Parsed CLI arguments.
        console: Rich console for output.
    """
    attribute = args.attribute_name

    if args.env_file:
        load_env_files(args.env_file)

    client = InMemoryFTPClient(
        host=get_env("MASCOT_FTP_HOST"),
        user=get_env("MASCOT_FTP_USER"),
        password=get_env("MASCOT_FTP_PASSWORD")
    )

    settings = SynclySettings()
    settings.mascot.availability = args.stock_file
    settings.mascot.product_data = args.product_info_file

    adapter = MascotAdapter(settings=settings, client=client)

    console.print(f"Fetching all Mascot products to collect values for [bold cyan]{attribute}[/bold cyan]...", style="dim")
    result = cast(List[Dict], adapter._get_products())
    helper_list_attribute_values(console, result, attribute)
