import yaml

from typing import Dict, Any
from importlib.resources import files


def load_yaml_config_file(namespace, file) -> Dict[str, Any]:
    data = files(namespace).joinpath(file).read_text()

    try:
        return yaml.safe_load(data)
    except Exception as e:
        raise RuntimeError(f"Error loading internal yaml config files {namespace}, {file}: {e}")

def normalize_env_var(name: str) -> str:
    """
    Normalize a string to a valid environment variable format.

    Replaces spaces and dashes with underscores, removes invalid characters,
    ensures it starts with a letter or underscore, and converts to uppercase.

    Args:
        name (str): The input string to normalize.

    Returns:
        str: Normalized string suitable as an environment variable key.
    """

    result = []
    prev_was_sep = False
    for char in name.strip():
        if char in {' ', '-'}:
            if not prev_was_sep:
                result.append('_')
                prev_was_sep = True
        elif char.isalnum() or char == '_':
            result.append(char)
            prev_was_sep = False

    normalized = ''.join(result)
    # Ensure it starts with a letter or underscore
    if normalized:
        if not normalized[0].isalpha() or normalized[0] == '_':
            normalized = '_' + normalized
    return normalized.upper()
