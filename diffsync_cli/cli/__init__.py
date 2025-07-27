import argparse
from rich.console import Console
from diffsync_cli.cli.commands import diff, version
console = Console()

def main():
    #setup_global_logging()

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

    diff_parser = subparsers.add_parser("diff", help="Syncs between two Sources")
    diff.add_arguments(diff_parser)
    diff_parser.set_defaults(func=diff.handle)

    args = parser.parse_args()
    args.func(args, console)
