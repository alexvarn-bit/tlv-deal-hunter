import os
import requests
from .config import TG_BOT_TOKEN, TG_CHANNEL_ID


def _mask_secret(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        return "<empty>"
    if len(cleaned) <= 6:
        return f"len={len(cleaned)} (too short)"
    return f"len={len(cleaned)} preview={cleaned[:3]}...{cleaned[-3:]}"


def _check_bot_token(token: str) -> str:
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        resp = requests.get(url, timeout=15)
        data = resp.json() if resp.content else {}
        if resp.ok and data.get("ok"):
            username = data.get("result", {}).get("username", "<unknown>")
            return f"getMe OK (@{username})"
        return f"getMe {resp.status_code}: {data.get('description', resp.text)}"
    except Exception as exc:
        return f"getMe check failed: {exc}"


def send_channel_message(
    text: str,
    token: str | None = None,
    chat_id: str | None = None,
    disable_web_page_preview: bool = False,
) -> int:
    raw_token = (
        token if token is not None else TG_BOT_TOKEN or os.environ.get("TG_BOT_TOKEN", "")
    ).strip()
    raw_chat_id = (
        chat_id if chat_id is not None else TG_CHANNEL_ID or os.environ.get("TG_CHANNEL_ID", "")
    ).strip()

    if not raw_token:
        raise RuntimeError(
            "Telegram bot token is empty. Check TG_BOT_TOKEN in GitHub Secrets and workflow env."
        )
    if not raw_chat_id:
        raise RuntimeError(
            "Telegram channel/chat ID is empty. Check TG_CHANNEL_ID in GitHub Secrets and workflow env."
        )

    print(f"TG diagnostic: token={_mask_secret(raw_token)} | chat_id={raw_chat_id}")

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
            token_diag = _check_bot_token(raw_token)
            hint = (
                f" (check bot token format/value in secrets; empty/invalid token produces 404; "
                f"{_mask_secret(raw_token)}; {token_diag})"
            )
        elif resp.status_code == 400:
            hint = " (check chat_id, bot permissions in channel, or HTML parse_mode syntax)"
        elif resp.status_code == 403:
            hint = " (bot was blocked by user or lacks post permissions in channel)"
        raise RuntimeError(f"Telegram API {resp.status_code}{hint}: {resp.text}")

    data = resp.json()
    if not data.get("ok") or "result" not in data or "message_id" not in data["result"]:
        raise RuntimeError(f"Unexpected Telegram API response payload: {data}")

    return int(data["result"]["message_id"])
