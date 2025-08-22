import logging
from rich.logging import RichHandler

def setup_global_logging(level=logging.INFO) -> None:
    """
    Set up global logging for the application using RichHandler for enhanced console output.
    """
    fmt = "%(name)s:%(lineno)d - %(message)s"

    logging.basicConfig(
        level=level,
        format=fmt,
        datefmt="[%H:%M:%S]",
        handlers=[
            RichHandler(
                rich_tracebacks=True,
                show_path=True,
                markup=True,
            )
        ],
    )
