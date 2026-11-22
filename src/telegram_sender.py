import requests
from .config import TG_BOT_TOKEN, TG_CHANNEL_ID


def send_channel_message(text: str) -> int:
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN.strip()}/sendMessage"
    payload = {
        "chat_id": TG_CHANNEL_ID.strip(),
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    resp = requests.post(url, json=payload, timeout=20)
    if not resp.ok:
        raise RuntimeError(f"Telegram API {resp.status_code}: {resp.text}")
    data = resp.json()
    return data["result"]["message_id"]
