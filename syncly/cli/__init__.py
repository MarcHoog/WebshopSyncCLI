import argparse
from rich.console import Console
from syncly.cli.commands import version, ccv
from syncly.cli.logging import setup_global_logging
from logging import DEBUG
console = Console()

def main():
    setup_global_logging(DEBUG)

    parser = argparse.ArgumentParser(
        description="Multi-file argparse CLI example with rich output"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="Available subcommands"
    )


    version_parser = subparsers.add_parser("version", help="Prints the version")
    version_parser.set_defaults(func=version.handle)


    # CCV Client commands
    ccv_parser = subparsers.add_parser("ccv", help="CCV client commands")
    ccv_subparsers = ccv_parser.add_subparsers(dest="ccv_cmd", required=True)
    create_attr_parser = ccv_subparsers.add_parser(
        "create-attribute-set-from-txt",
        help="Create a CCV attribute set from a TXT file"
    )
    ccv.create_attribute_set_from_txt.add_arguments(create_attr_parser)
    ccv_parser.set_defaults(func=ccv.create_attribute_set_from_txt.handle)

    sync_perfion_parser = ccv_subparsers.add_parser("sync-perfion", help="Syncs between two Sources")
    ccv.sync_perfion.add_arguments(sync_perfion_parser)
    sync_perfion_parser.set_defaults(func=ccv.sync_perfion.handle)

    sync_mascot_parser = ccv_subparsers.add_parser("sync-mascot", help="Syncs between two Sources")
    ccv.sync_mascot.add_arguments(sync_mascot_parser)
    sync_mascot_parser.set_defaults(func=ccv.sync_mascot.handle)

    args = parser.parse_args()
    args.func(args, console)
