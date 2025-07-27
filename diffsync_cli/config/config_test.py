import pytest
import tempfile
import os

from diffsync_cli.config import normalize_env_var

@pytest.mark.parametrize("input_str,expected", [
    ("my-var name!", "MY_VAR_NAME"),
    ("123value", "_123VALUE"),
    (" normal  text ", "NORMAL_TEXT"),
    ("weird$chars%^", "WEIRDCHARS"),
    ("Already_OK", "ALREADY_OK"),
    ("", ""),
])

def test_normalize_env_var(input_str, expected):
    assert normalize_env_var(input_str) == expected

def test_configsettings_general_usage():
    from diffsync_cli.config import ConfigSettings

    # Create with some initial values
    config = ConfigSettings(api_key="secret", debug="true", number="123", truth=1)

    # Test get method with and without default/cast
    assert config.get("api_key") == "secret"
    assert config.get("missing", default="fallback") == "fallback"
    assert config.get("number", cast=int) == 123
    assert config.get("truth", cast=bool) == True

    # Test to_dict
    d = config.to_dict()
    assert d["API_KEY"] == "secret"
    assert d["DEBUG"] == "true"
    assert d["NUMBER"] == "123"


def test_configsettings_singleton_reflects_local_changes():
    from diffsync_cli.config import ConfigSettings

    singleton = ConfigSettings.instance()
    singleton._data.clear()
    singleton._data["FOO"] = "bar"

    local_ref = ConfigSettings.instance()
    assert local_ref._data["FOO"] == "bar"

    local_ref._data["FOO"] = "baz"
    assert singleton._data["FOO"] == "baz"
    # Add a new key via singleton and check local_ref sees it
    singleton._data["NEW_KEY"] = "value"
    assert local_ref._data["NEW_KEY"] == "value"


def test_configsettings_from_env_file():
    from diffsync_cli.config import ConfigSettings

    # Create a temporary .env file
    env_content = """
    # This is a comment
    API_KEY=fromenv
    DEBUG=true
    NUMBER=456
    QUOTED="quoted value"
    SINGLE_QUOTED='single quoted'
    """
    with tempfile.NamedTemporaryFile("w+", delete=False) as tmp:
        tmp.write(env_content)
        tmp_path = tmp.name

    try:
        config = ConfigSettings().from_env_file(tmp_path)
        d = config.to_dict()
        assert d["API_KEY"] == "fromenv"
        assert d["DEBUG"] == "true"
        assert d["NUMBER"] == "456"
        assert d["QUOTED"] == "quoted value"
        assert d["SINGLE_QUOTED"] == "single quoted"
    finally:
        os.remove(tmp_path)

def test_configsettings_load_env_vars(monkeypatch):
    from diffsync_cli.config import ConfigSettings

    # Set up environment variables
    monkeypatch.setenv("MYAPP_API_KEY", "envsecret")
    monkeypatch.setenv("MYAPP_DEBUG", "1")
    monkeypatch.setenv("OTHERAPP_API_KEY", "should_not_load")

    config = ConfigSettings()
    config.load_env_vars(["MYAPP"])

    d = config.to_dict()
    assert d["MYAPP_API_KEY"] == "envsecret"
    assert d["MYAPP_DEBUG"] == "1"
    assert "OTHERAPP_API_KEY" not in d


def test_validate():
    from diffsync_cli.config import ConfigSettings

    config = ConfigSettings()
    config.set("MYAPP_DEBUG", "1")
    config.verify("myapp_debug")
