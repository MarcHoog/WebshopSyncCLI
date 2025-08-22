import os

from typing import Dict, Any, Optional, Callable, List
from syncly.utils import normalize_env_var


class EnvSettings:
    """
    Configuration settings loader that sources environment variables and optionally
    loads from a dictionary or `.env`-style files.

    Attributes:
        _prefixes (tuple[str, ...]): Tuple of normalized prefixes to filter environment variables.
        _data (Dict[str, str]): Internal dictionary storing config key-value pairs.
    """

    _instance: Optional["EnvSettings"] = None

    def __init__(self, **kwargs):
        """
        Initialize ConfigSettings with optional prefixes and data.

        Args:
            *prefixes: Variable length argument list of prefixes to filter env vars.
            _data (Optional[Dict[str, str]]): Optional dict of preloaded config data.
        """
        self._data: Dict[str, str] = {}
        self._data.update({normalize_env_var(k): v for k, v in kwargs.items()})

    def load_env_vars(self, prefixes: List[str]) -> "EnvSettings":
        """
        Load environment variables filtered by the configured prefixes into the config based on the Prefixes.
        """

        _prefixes = tuple(normalize_env_var(p) for p in prefixes)

        for k, v in os.environ.items():
            if k.startswith(_prefixes):
                self._data[k] = v

        return self

    def from_env_file(self, path: str) -> "EnvSettings":
        """
        Load configuration from a `.env`-style file.

        Parses key=value lines, ignoring comments and blank lines.

        Args:
            path (str): Path to the `.env` file.

        Returns:
            ConfigSettings: A ConfigSettings instance with loaded data.
        """
        data = {}
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        data[normalize_env_var(k)] = v.strip().strip('"').strip("'")

        self._data.update(data)
        return self


    def get( #type: ignore
        self,
        key: str,
        default: Any = None,
        cast: Optional[Callable[[str], Any]] = None,
    ) -> Any:
        """
        Get a configuration value with optional default and casting.

        Args:
            key (str): The configuration key to retrieve.
            default (Any, optional): The default value if key is not found. Defaults to None.
            cast (Optional[Callable[[str], Any]], optional): A function to cast the string value. Defaults to None.

        Returns:
            Any: The casted configuration value or default if missing or cast fails.
        """
        raw_value = self._data.get(normalize_env_var(key))
        if raw_value is not None:
            try:
                return cast(raw_value) if cast else raw_value
            except Exception:
                return default
        return default


    def set(self, key: str, value: Any) -> "EnvSettings":
        """
        set a new configuration key-value pair.

        Returns:
            ConfigSettings: The updated ConfigSettings instance.
        """
        self._data[normalize_env_var(key)] = value
        return self

    def verify(self, *keys: str) -> bool:
        """
        Verify the configuration settings.

        Returns:
            bool: True if all required settings are present and valid, False otherwise.
        """
        for key in keys:
            if normalize_env_var(key) not in self._data:
                return False
        return True


    def to_dict(self) -> Dict[str, str]: #type: ignore
        """
        Return the configuration data as a standard dictionary.

        Returns:
            Dict[str, str]: A copy of the internal configuration dictionary.
        """
        return dict(self._data)

    @classmethod
    def instance(cls) -> "EnvSettings":
        """
        Get the singleton instance of ConfigSettings.
        Initializes it with prefixes if not already created.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
