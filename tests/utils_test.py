import pytest
import base64
import io
from PIL import Image


@pytest.mark.parametrize("input_str,expected", [
    ("my-var name!", "MY_VAR_NAME"),
    ("123value", "_123VALUE"),
    (" normal  text ", "NORMAL_TEXT"),
    ("weird$chars%^", "WEIRDCHARS"),
    ("Already_OK", "ALREADY_OK"),
    ("", ""),
])

def test_normalize_env_var(input_str, expected):
    from syncly.helpers import normalize_env_var
    assert normalize_env_var(input_str) == expected




def create_test_image_bytes(size=(800, 600), color=(255, 0, 0)):
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

class DummyResponse:
    def __init__(self, content):
        self.content = content
    def raise_for_status(self):
        pass

def test_base64_image_from_url(monkeypatch):
    from syncly.helpers import base64_image_from_url

    test_img_bytes = create_test_image_bytes()

    def mock_get(url):
        return DummyResponse(test_img_bytes)

    monkeypatch.setattr("syncly.helpers.requests.get", mock_get)

    b64_str = base64_image_from_url("http://example.com/image.png", target_resolution=(550, 550))

    img_bytes = base64.b64decode(b64_str)
    img = Image.open(io.BytesIO(img_bytes))
    assert img.size == (550, 550)
    assert img.format == "PNG"


def test_base64_image_from_url_integration():
    from syncly.helpers import base64_image_from_url

    url = "https://artikelinfo.tricorp.com/productimages/UnicontaTemp/101001antramelside.png"
    b64_str = base64_image_from_url(url, target_resolution=(550, 550))

    img_bytes = base64.b64decode(b64_str)
    img = Image.open(io.BytesIO(img_bytes))
    assert img.size == (550, 550)
    assert img.format == "PNG"
