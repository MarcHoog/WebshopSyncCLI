import pytest
import io
import os

from syncly.webhook.discord import send_discord_webhook

def test_send_discord_webhook_with_file():
    """
    Integration test that posts a real message and file to Discord using the webhook URL from environment variables.
    """
    webhook_url = os.environ.get("DISCORD_TEST_WEBHOOK_URL")
    if not webhook_url:
        pytest.skip("No Discord webhook URL provided for integration test.")

    file_content = b"Test file content for Discord webhook."
    test_file = io.BytesIO(file_content)
    test_file.name = "testfile.txt"

    result = send_discord_webhook(
        webhook_url,
        "Integration test succeeded!",
        status="success",
        title="Integration Test",
        fields=[{"name": "Test Field", "value": "Test Value"}],
        footer="Test Footer",
        files=test_file
    )
    assert result is True
