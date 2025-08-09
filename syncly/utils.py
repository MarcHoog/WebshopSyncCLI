import base64
import requests
from PIL import Image
import io

def normalize_string(string: str):
    return string.strip().lower()

def append_if_not_exists(item, target_list):
    """Append an item to the target list if it does not already exist."""
    if item and item not in target_list:
        target_list.append(item)

def base64_endcode_image(path):
    with open(path, 'rb') as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string

def base64_image_from_url(url, target_resolution=(854, 480)):
    """
    Fetch an image from a URL, scale it down to the target resolution, and return its base64 encoding.

    Args:
        url (str): The URL of the image.
        target_resolution (tuple): The desired resolution (width, height) for the image.

    Returns:
        str: Base64-encoded string of the scaled image.
    """
    result = requests.get(url)
    result.raise_for_status()
    image = Image.open(io.BytesIO(result.content))
    image.thumbnail(target_resolution)
    buffer = io.BytesIO()
    image.save(buffer, format=image.format)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')
