import argparse
import pytest
from diffsync_cli.cli.commands import diff

@pytest.fixture(scope="module")
def parser():
    parser = argparse.ArgumentParser()
    diff.add_arguments(parser)
    return parser

def test_sync_ccvshop_mock_diff(parser):

    args = parser.parse_args([
        "perfion",
        "ccvshop",
        "--sync",
        "--config", ".env"
    ])

    class DummyConsole:
        def print(self, *a, **kw): pass

    diff.handle(args, console=DummyConsole())
