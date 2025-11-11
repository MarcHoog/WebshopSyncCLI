import logging
from pathlib import Path
from ..errors import LocalFileError

logger = logging.getLogger(__name__)


class LocalFileClient:
    def __init__(self, file_path: str):
        """
        Initialize a local file client for a single file.

        Args:
            file_path: Path to the file to open
        """
        self.file_path = Path(file_path).resolve()
        self._entered = False

    def __enter__(self) -> "LocalFileClient":
        try:
            logger.debug(f"Initializing local file client for {self.file_path}")

            if not self.file_path.exists():
                raise LocalFileError(f"File does not exist: {self.file_path}")

            if not self.file_path.is_file():
                raise LocalFileError(f"Path is not a file: {self.file_path}")

            self._entered = True
            logger.info(f"Local file client initialized for: {self.file_path}")
            return self
        except (OSError, PermissionError) as e:
            logger.error(f"Failed to initialize local file client for {self.file_path}: {e}")
            raise LocalFileError(f"Local file client initialization failed: {e}") from e

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._entered:
            logger.info(f"Local file client session closed for: {self.file_path}")
            self._entered = False

    def read(self) -> bytes:
        """
        Read the file and return its contents as bytes.

        Returns:
            File contents as bytes
        """
        if not self._entered:
            logger.error("Local file client session not established. Cannot read file.")
            raise LocalFileError("Local file client session not established.")

        try:
            logger.debug(f"Reading file: {self.file_path}")

            with open(self.file_path, 'rb') as f:
                content = f.read()

            logger.info(f"Successfully read file: {self.file_path} ({len(content)} bytes)")
            return content

        except PermissionError as e:
            logger.error(f"Permission error when reading {self.file_path}: {e}")
            raise LocalFileError(f"Permission denied for file: {self.file_path}") from e
        except OSError as e:
            logger.error(f"Failed to read file {self.file_path}: {e}")
            raise LocalFileError(f"Error reading file {self.file_path}: {e}") from e
