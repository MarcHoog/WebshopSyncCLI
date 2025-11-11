import base64
from pydantic.types import AnyType
import requests
import io
import pandas as pd
import os
import logging

from io import BytesIO, StringIO
from PIL import Image, ImageOps
from typing import List, Any, Optional, Callable, Tuple
from pydantic import ValidationError

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


def append_if_not_exists(item: object, target_list: List[Any]):
    """
    Append an item to a list only if it does not already exist.
    """
    if item and item not in target_list:
        target_list.append(item)


def base64_endcode_image(path: str):
    """
    Encode an image file to a base64 string.
    """
    with open(path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    return encoded_string


def base64_image_from_url(url: str, target_resolution: Tuple[int, int] = (550, 550)):
    """
    Download an image from a URL, resize and crop to exactly target_resolution, and encode as base64.
    """
    result = requests.get(url)
    result.raise_for_status()
    image = Image.open(io.BytesIO(result.content))
    image = ImageOps.fit(image, target_resolution, Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def base64_image_from_url_contain(
    url: str,
    target_resolution: tuple[int, int] = (550, 550),
    background=(255, 255, 255, 0),  # transparent by default
) -> str:
    """
    Download an image from a URL, resize to fit inside target_resolution (no crop),
    and pad with background to exact size. Encodes result as base64.
    """
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    img = Image.open(io.BytesIO(resp.content))
    img = ImageOps.exif_transpose(img)  # fix orientation
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")

    W, H = target_resolution
    fitted = ImageOps.contain(img, (W, H), Image.Resampling.LANCZOS)

    # Create padded canvas
    canvas_mode = "RGBA" if (len(background) == 4) else "RGB"
    canvas = Image.new(canvas_mode, (W, H), background)

    x = (W - fitted.width) // 2
    y = (H - fitted.height) // 2
    canvas.paste(fitted, (x, y), fitted if fitted.mode == "RGBA" else None)

    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def normalize_env_var(name: str) -> str:
    """
    Normalize a string to a valid environment variable format.
    """
    result = []
    prev_was_sep = False
    for char in name.strip():
        if char in {" ", "-"}:
            if not prev_was_sep:
                result.append("_")
                prev_was_sep = True
        elif char.isalnum() or char == "_":
            result.append(char)
            prev_was_sep = False

    normalized = "".join(result)
    # Ensure it starts with a letter or underscore
    if normalized:
        if not normalized[0].isalpha() or normalized[0] == "_":
            normalized = "_" + normalized
    return normalized.upper()


def xlsx_bytes_to_list(
    data: bytes, sheet: str | int = 0, include_header: bool = True
) -> List[List[Any]]:
    """
    Convert Excel bytes into a list of lists using pandas.

    Returns:
        A list of lists where each inner list is a row.
    """
    df = pd.read_excel(
        BytesIO(data), sheet_name=sheet, keep_default_na=False, na_values=[]
    )
    df = df.replace({"None": None})

    if include_header:
        return [df.columns.tolist()] + df.values.tolist()
    else:
        return df.values.tolist()


def csv_bytes_to_list(
    data: bytes,
    include_header: bool = True,
    encoding: str = "utf-8",
    seperator: str = ",",
) -> List[List[Any]]:
    """
    Convert CSV bytes into a list of lists using pandas.

    Returns:
        A list of lists where each inner list is a row.
    """
    df = pd.read_csv(
        StringIO(data.decode(encoding)),
        sep=seperator,
        keep_default_na=False,
        na_values=[],
    )
    df = df.replace({"None": None})

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


def to_float(value: str) -> float:
    """
    Convert a string with either comma or dot as decimal separator to float.
    """
    if not value:
        raise ValueError("Empty string cannot be converted to float")

    # Remove thousand separators and normalize decimal separator
    value = value.replace(".", "").replace(",", ".")
    return float(value)


def pretty_validation_error(err: ValidationError) -> None:
    logger.error("Validation failed with the following errors:")
    for e in err.errors():
        loc = " → ".join(str(x) for x in e["loc"])
        msg = e["msg"]
        typ = e["type"]
        logger.error(f"  - Field: {loc}\n    Error: {msg}\n    Type: {typ}\n")
