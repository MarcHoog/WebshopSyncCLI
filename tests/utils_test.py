import pytest

@pytest.mark.parametrize("input_str,expected", [
    ("my-var name!", "MY_VAR_NAME"),
    ("123value", "_123VALUE"),
    (" normal  text ", "NORMAL_TEXT"),
    ("weird$chars%^", "WEIRDCHARS"),
    ("Already_OK", "ALREADY_OK"),
    ("", ""),
])

def test_normalize_env_var(input_str, expected):
    from syncly.utils import normalize_env_var
    assert normalize_env_var(input_str) == expected
