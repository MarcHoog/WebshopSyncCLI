"""
CLI command for syncing and diffing data between sources and CCVShop.

Provides argument parsing, integration setup, and pretty printing of diffs and summaries.
"""

import logging
from rich.text import Text

from diffsync.logging import enable_console_logging
from diffsync.enum import DiffSyncFlags
from syncly.adapters.ccv import CCVShopAdapter
from syncly.clients.ccv.client import CCVClient
from syncly.clients.ftp import FTPClient
from syncly.adapters.mascot import MascotAdapter
from syncly.settings import Settings, load_settings
from syncly.helpers import get_env, load_env_files
from syncly.diff import AttributeOrderingDiff

def _create_adapter(settings: Settings, Adapter, client):
    logging.info(f"Setting up {Adapter} adapter...")
    try:
        adapter = Adapter(settings=settings, client=client)
    except ValueError as e:
        raise e

    return adapter # type: ignore

def _load(adapter):
    logging.info(f"Loading in data using: {adapter}. ")
    try:
        adapter.load()
    except Exception as e:
        raise e

    return adapter


def truncate(value):

    value = str(value)

    if len(value) > 200:
        return f"{value[:200]}..."

    return value

def render_diff_rich(diff, indent=0):
    """
    Recursively pretty-print a DiffSync diff dictionary using Rich.

    Args:
        diff (dict): The diff dictionary to render.
        indent (int): Current indentation level.

    Returns:
        list[Text]: List of Rich Text objects for printing.
    """
    lines = []
    ind = "  " * indent
    for record_type, children in diff.items():
        lines.append(Text(f"{ind}* {record_type}"))
        for child, child_diffs in children.items():
            plus = child_diffs.get("+", {})
            minus = child_diffs.get("-", {})
            has_plus = "+" in child_diffs
            has_minus = "-" in child_diffs
            if has_plus and not has_minus:
                lines.append(Text(f"{ind}  + {child}", style="green"))
                for attr, value in plus.items():
                    lines.append(Text(f"{ind}    + {attr}: {truncate(value)}", style="green"))
            elif has_minus and not has_plus:
                lines.append(Text(f"{ind}  - {child}", style="red"))
                for attr, value in minus.items():
                    lines.append(Text(f"{ind}    - {attr}: {truncate(value)}", style="red"))
            elif not has_plus and not has_minus:
                lines.append(Text(f"{ind}  * {child}", style="dim"))
            else:
                lines.append(Text(f"{ind}  ! {child}", style="yellow"))
                for attr, value in plus.items():
                    lines.append(Text(f"{ind}    + {attr}: {truncate(value)}", style="green"))
                for attr, value in minus.items():
                    lines.append(Text(f"{ind}    - {attr}: {truncate(value)}", style="red"))
            # Recurse into nested diffs
            child_diffs = {k: v for k, v in child_diffs.items() if k not in ("+", "-")}
            if child_diffs:
                lines.extend(render_diff_rich(child_diffs, indent + 2))
    return lines


logger = logging.getLogger(__name__)

def add_arguments(parser):
    """
    Add CLI arguments for the sync command.

    Args:
        parser (argparse.ArgumentParser): The argument parser to add arguments to.
    """
    parser.add_argument(
        "-c", "--config",
        type=str,
        help="Path to configuration file",
        default=None
    )

    parser.add_argument(
        "-s", "--sync",
        action="store_true",
        help="Perform sync operation",
        default=False
    )

    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        help="Increase verbosity level (e.g., -v, -vv, -vvv)"
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Path to output the diff file",
        default=None
    )


def handle(args, console):
    """
    Handle the sync CLI command.

    Args:
        args: Parsed CLI arguments.
        console: Rich console for output.
    """

    if args.config:
        load_env_files(args.config)

    settings = load_settings(get_env("SYNCLY_SETTINGS", "settings.yaml"))
    src = _create_adapter(
        settings,
        MascotAdapter,
        FTPClient(
            host=get_env("MASCOT_FTP_HOST"),
            user=get_env("MASCOT_FTP_USER"),
            password=get_env("MASCOT_FTP_PASSWORD"),
        )
    )

    dst = _create_adapter(
        settings,
        CCVShopAdapter,
        CCVClient(
            get_env("CCVSHOP_PUBLIC_KEY"),
            get_env("CCVSHOP_PRIVATE_KEY"),
            settings.ccv_shop.url
        ),
    )

    _load(src)
    _load(dst)

    logger.info("Creating diff")
    diff = src.diff_to(dst, diff_class=AttributeOrderingDiff)
    diff_dict = diff.dict()
    console.print("-" * 30 + " Diff Details " + "-" * 30)
    if not diff_dict:
        console.print("No Changes to be Made")
    else:
        for line in render_diff_rich(diff_dict):
            console.print(line)

    summary = diff.summary()
    summary_str = " | ".join(f"{key}: {value}" for key, value in summary.items())
    divider = "-" * 28 + " Sync Summary " + "-" * 28
    console.print(divider)
    console.print(f"[bold magenta]Sync Summary:[/bold magenta] {summary_str}")

    if args.sync:
        enable_console_logging(verbosity=3)
        console.print("Syncing...")
        src.sync_to(dst, diff=diff, flags=DiffSyncFlags.CONTINUE_ON_FAILURE)
