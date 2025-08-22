import requests
import json
from datetime import datetime, UTC
from typing import List, Optional, Union, IO

def send_discord_webhook(
    webhook_url: str,
    message: str,
    status: str = "success",
    title: Optional[str] = None,
    fields: Optional[List[dict]] = None,
    footer: Optional[str] = None,
    files: Optional[Union[IO, List[IO]]] = None
):
    """
    Sends a rich formatted message to a Discord channel via webhook, optionally with file(s) as binary streams.
    """
    color_map = {
        "success": 0x00FF00,  # Green
        "error": 0xFF0000     # Red
    }
    color = color_map.get(status, 0x00FF00)

    embed = {
        "description": message,
        "color": color,
        "timestamp": datetime.now(UTC).isoformat()
    }
    if title:
        embed["title"] = title
    if fields:
        embed["fields"] = fields
    if footer:
        embed["footer"] = {"text": footer}

    payload = {
        "embeds": [embed]
    }

    files_to_send = []
    if files:
        if not isinstance(files, list):
            files = [files]
        for file_obj in files:
            files_to_send.append(('file', (getattr(file_obj, 'name', 'file'), file_obj)))

    # Send request
    if files_to_send:
        response = requests.post(
            webhook_url,
            data={'payload_json': json.dumps(payload)},
            files=files_to_send
        )
    else:
        response = requests.post(webhook_url, json=payload)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"Failed to send Discord webhook: {e}")
        return False
    return True
