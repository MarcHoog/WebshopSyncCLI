import base64
import requests
import io
import pandas as pd
import os
import logging

from io import BytesIO, StringIO
from PIL import Image, ImageOps
from typing import List, Any, Optional, Callable

logger = logging.getLogger(__name__)

def normalize_string(string: str):
    """
    Normalize a string for consistent comparisons.
    """
    return string.strip().lower()

def wrap_style(string: str):
    """
    Wrap a string in HTML span tags for styling.
    """
    return f'<span style="font-size:14px;"><span style="font-family:Verdana,Geneva,sans-serif;">{string}</span></span>'

def append_if_not_exists(item, target_list):
    """
    Append an item to a list only if it does not already exist.
    """
    if item and item not in target_list:
        target_list.append(item)

def base64_endcode_image(path):
    """
    Encode an image file to a base64 string.
    """
    with open(path, 'rb') as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string

def base64_image_from_url(url, target_resolution=(550, 550)):
    """
    Download an image from a URL, resize and crop to exactly target_resolution, and encode as base64.
    """
    result = requests.get(url)
    result.raise_for_status()
    image = Image.open(io.BytesIO(result.content))
    image = ImageOps.fit(image, target_resolution, Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def normalize_env_var(name: str) -> str:
    """
    Normalize a string to a valid environment variable format.
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



def xlsx_bytes_to_list(data: bytes, sheet: str | int = 0, include_header: bool = True) -> List[List[Any]]:
    """
    Convert Excel bytes into a list of lists using pandas.

    Returns:
        A list of lists where each inner list is a row.
    """
    df = pd.read_excel(BytesIO(data), sheet_name=sheet)

    if include_header:
        return [df.columns.tolist()] + df.values.tolist()
    else:
        return df.values.tolist()



def csv_bytes_to_list(data: bytes, include_header: bool = True, encoding: str = "utf-8", seperator: str = ",") -> List[List[Any]]:
    """
    Convert CSV bytes into a list of lists using pandas.

    Returns:
        A list of lists where each inner list is a row.
    """
    df = pd.read_csv(StringIO(data.decode(encoding)), sep=seperator)

    if include_header:
        return [df.columns.tolist()] + df.values.tolist()
    else:
        return df.values.tolist()

def load_env_files(*paths: str):
    """
    Load configuration from a `.env`-style file.
    Parses key=value lines, ignoring comments and blank lines.
    And updates os.environ accordingly using update

    Returns:
        Dict: Os.environ
    """
    data = {}

    for path in paths:
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        data[normalize_env_var(k)] = v.strip().strip('"').strip("'")
        else:
            logger.error("Couldn't find path skipping file")

    os.environ.update(data)
    return os.environ

def get_env(
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
    raw_value = os.environ.get(normalize_env_var(key))
    if raw_value is not None:
        try:
            return cast(raw_value) if cast else raw_value
        except Exception:
            logger.error("Something went wrong casting value returning default")
            return default
    return default
