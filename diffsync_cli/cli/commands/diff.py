"""
CLI command for syncing and diffing data between sources and CCVShop.

Provides argument parsing, integration setup, and pretty printing of diffs and summaries.
"""

import logging
import sys
from rich.text import Text

from diffsync.logging import enable_console_logging
from diffsync_cli.clients.ccv.client import CCVClient
from diffsync_cli.intergrations.ccvshop.adapters.adapter_ccv import CCVShopAdapter
from diffsync_cli.intergrations.ccvshop.adapters.adapter_mock import MockAdapter
from diffsync_cli.config import ConfigSettings

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
                    lines.append(Text(f"{ind}    + {attr}: {value}", style="green"))
            elif has_minus and not has_plus:
                lines.append(Text(f"{ind}  - {child}", style="red"))
                for attr, value in minus.items():
                    lines.append(Text(f"{ind}    - {attr}: {value}", style="red"))
            elif not has_plus and not has_minus:
                lines.append(Text(f"{ind}  * {child}", style="dim"))
            else:
                lines.append(Text(f"{ind}  ! {child}", style="yellow"))
                for attr, value in plus.items():
                    lines.append(Text(f"{ind}    + {attr}: {value}", style="green"))
                for attr, value in minus.items():
                    lines.append(Text(f"{ind}    - {attr}: {value}", style="red"))
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
        "source",
        type=str,
        help="Path to source file",
    )

    parser.add_argument(
        "destination",
        type=str,
        choices=["ccvshop"],
        help="Destination to sync to",
    )

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
    if args.destination == "ccvshop":
        handle_ccvshop_integration(args, console)

def handle_ccvshop_integration(args, console):
    """
    Handle integration with CCVShop for sync and diff operations.

    Args:
        args: Parsed CLI arguments.
        console: Rich console for output.
    """
    cfg = ConfigSettings()
    if args.config:
        logging.info(f"Loading env configuration from {args.config}")
        cfg.from_env_file(args.config)

    logging.info("Loading environment variables 'CCVSHOP'...")
    cfg.load_env_vars(["CCVSHOP"])

    logging.info("Setting up CCVShop adapter...")

    try:
        client = CCVClient(cfg=cfg)
        dst = CCVShopAdapter(cfg=cfg, client=client)
    except ValueError as e:
        logging.error(f"Error setting up CCVShop adapter: {e}")
        sys.exit(1)

    if args.source == "mock":
        logging.info("Loading environment variables 'MOCK'")
        cfg.load_env_vars(["MOCK"])
        logging.info("Setting up Mock adapter...")
        src = MockAdapter(cfg=cfg)
    else:
        logger.error("Unsupported sources! Syncing to 'ccvshop' is only supported with 'mock' and 'tricorp'")
        sys.exit(1)

    enable_console_logging(verbosity=3)
    console.print("Generating diff...")
    src.load()
    dst.load()

    diff = src.diff_to(dst)
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
        console.print("Syncing...")
        src.sync_to(dst)
