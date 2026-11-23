import os
import requests
from .config import TG_BOT_TOKEN, TG_CHANNEL_ID


def send_channel_message(
    text: str,
    token: str | None = None,
    chat_id: str | None = None,
    disable_web_page_preview: bool = False,
) -> int:
    raw_token = (token if token is not None else TG_BOT_TOKEN or os.environ.get("TG_BOT_TOKEN", "")).strip()
    raw_chat_id = (chat_id if chat_id is not None else TG_CHANNEL_ID or os.environ.get("TG_CHANNEL_ID", "")).strip()

    if not raw_token:
        raise RuntimeError(
            "Telegram bot token is empty. Check TG_BOT_TOKEN in GitHub Secrets and workflow env."
        )
    if not raw_chat_id:
        raise RuntimeError(
            "Telegram channel/chat ID is empty. Check TG_CHANNEL_ID in GitHub Secrets and workflow env."
        )

    url = f"https://api.telegram.org/bot{raw_token}/sendMessage"
    payload = {
        "chat_id": raw_chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": disable_web_page_preview,
    }

    try:
        resp = requests.post(url, json=payload, timeout=20)
    except requests.RequestException as exc:
        raise RuntimeError(f"Telegram network error: {exc}") from exc

    if not resp.ok:
        hint = ""
        if resp.status_code == 404:
            hint = " (check bot token format/value in secrets; empty/invalid token produces 404)"
        elif resp.status_code == 400:
            hint = " (check chat_id, bot permissions in channel, or HTML parse_mode syntax)"
        raise RuntimeError(f"Telegram API {resp.status_code}{hint}: {resp.text}")

    data = resp.json()
    if not data.get("ok") or "result" not in data or "message_id" not in data["result"]:
        raise RuntimeError(f"Unexpected Telegram API response payload: {data}")

    return int(data["result"]["message_id"])
