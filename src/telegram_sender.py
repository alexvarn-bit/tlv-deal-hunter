import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _mask_token(token: str) -> str:
    clean = token.strip()
    if len(clean) <= 8:
        return "***"
    return f"{clean[:3]}...{clean[-3:]}"


def _extract_retry_after(status_code: int, body_text: str, headers) -> float | None:
    if status_code != 429:
        return None

    try:
        payload = json.loads(body_text)
        if isinstance(payload, dict):
            params = payload.get("parameters")
            if isinstance(params, dict) and params.get("retry_after") is not None:
                return float(params["retry_after"])
    except (ValueError, TypeError):
        pass

    if headers is not None:
        retry_hdr = headers.get("Retry-After")
        if retry_hdr:
            try:
                return float(retry_hdr)
            except ValueError:
                pass

    return 15.0


def send_channel_message(
    text: str,
    disable_web_page_preview: bool | None = None,
    max_retries: int = 3,
) -> int | None:
    bot_token = (os.environ.get("TG_BOT_TOKEN") or "").strip()
    chat_id = (os.environ.get("TG_CHANNEL_ID") or "").strip()

    if not bot_token:
        raise RuntimeError("Telegram bot token is empty. Check TG_BOT_TOKEN in GitHub Secrets and workflow env.")
    if not chat_id:
        raise RuntimeError("Telegram channel/chat ID is empty. Check TG_CHANNEL_ID in GitHub Secrets and workflow env.")

    if disable_web_page_preview is None:
        disable_preview = _env_flag("DISABLE_LINK_PREVIEW", default=True)
    else:
        disable_preview = bool(disable_web_page_preview)

    print(f"TG diagnostic: token=len={len(bot_token)} preview={_mask_token(bot_token)} | chat_id=***")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": disable_preview,
    }
    encoded_data = urllib.parse.urlencode(payload).encode("utf-8")

    attempt = 0
    while True:
        attempt += 1
        req = urllib.request.Request(
            url,
            data=encoded_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw_body = resp.read().decode("utf-8", errors="replace")
                data = json.loads(raw_body)
                if not data.get("ok"):
                    raise RuntimeError(f"Telegram API returned ok=false: {raw_body}")
                result = data.get("result") or {}
                return result.get("message_id")
        except urllib.error.HTTPError as err:
            body_text = err.read().decode("utf-8", errors="replace")
            hint = ""
            if err.code == 400:
                hint = " (check chat_id format: -100... or @channel_username and HTML tags)"
            elif err.code == 403:
                hint = " (check that bot is added as administrator to the channel)"
            elif err.code == 404:
                hint = " (check TG_BOT_TOKEN validity)"

            retry_after = _extract_retry_after(err.code, body_text, err.headers)
            if retry_after is not None and attempt <= max_retries:
                sleep_sec = max(2.0, retry_after + 2.0)
                print(f"TG rate limit (429): sleeping {sleep_sec:.1f}s before retry {attempt}/{max_retries}...")
                time.sleep(sleep_sec)
                continue

            raise RuntimeError(f"Telegram API {err.code}{hint}: {body_text}") from err
        except urllib.error.URLError as err:
            if attempt <= max_retries:
                sleep_sec = 2.0 * attempt
                print(f"TG network error: {err.reason}; retrying in {sleep_sec:.1f}s ({attempt}/{max_retries})...")
                time.sleep(sleep_sec)
                continue
            raise RuntimeError(f"Telegram network error after retries: {err.reason}") from err
