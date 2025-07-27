import logging
from rich.console import Console
from rich.text import Text

class RichHandler(logging.Handler):
    def __init__(self, console=None, level=logging.NOTSET):
        super().__init__(level)
        self.console = console or Console()

    def emit(self, record):
        log_entry = self.format(record)
        style = self._get_style(record.levelname)
        text = Text(f"{log_entry}", style=style)
        self.console.print(text)

    def _get_style(self, levelname):
        styles = {
            "DEBUG": "dim cyan",
            "INFO": "gray",
            "WARNING": "bold yellow",
            "ERROR": "bold red",
            "CRITICAL": "bold white on red",
        }
        return styles.get(levelname, "")


def setup_global_logging(level=logging.INFO):
    """
    Sets up global logging to use RichHandler for pretty console output.
    Call this once at the start of your CLI.
    """
    handler = RichHandler()
    if level != logging.DEBUG:
        formatter = logging.Formatter("[%(levelname)s] - %(message)s")
    else:
        formatter = logging.Formatter("[%(levelname)s] - %(name)s %(message)s")

    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = []
    root_logger.addHandler(handler)
