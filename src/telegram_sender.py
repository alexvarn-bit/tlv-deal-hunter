import json
import os
import time
import urllib.error
import urllib.request


CITY_PHOTOS: dict[str, str] = {
    "LCA": "https://images.unsplash.com/photo-1590523277543-a94d2e4eb00b?auto=format&fit=crop&w=1000&q=80",
    "PFO": "https://images.unsplash.com/photo-1580502304784-8985b3eb7260?auto=format&fit=crop&w=1000&q=80",
    "ATH": "https://images.unsplash.com/photo-1555993539-1732b0258235?auto=format&fit=crop&w=1000&q=80",
    "SKG": "https://images.unsplash.com/photo-1601581875039-e899893d520c?auto=format&fit=crop&w=1000&q=80",
    "FCO": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=1000&q=80",
    "MXP": "https://images.unsplash.com/photo-1520440229-6469a149ac8a?auto=format&fit=crop&w=1000&q=80",
    "BGY": "https://images.unsplash.com/photo-1520440229-6469a149ac8a?auto=format&fit=crop&w=1000&q=80",
    "VCE": "https://images.unsplash.com/photo-1514890547357-a9ee288728e0?auto=format&fit=crop&w=1000&q=80",
    "NAP": "https://images.unsplash.com/photo-1534308983496-4fabb1a015ee?auto=format&fit=crop&w=1000&q=80",
    "BUD": "https://images.unsplash.com/photo-1541849546-216549ae216d?auto=format&fit=crop&w=1000&q=80",
    "VIE": "https://images.unsplash.com/photo-1516550893923-42d28e5677af?auto=format&fit=crop&w=1000&q=80",
    "PRG": "https://images.unsplash.com/photo-1541849546-216549ae216d?auto=format&fit=crop&w=1000&q=80",
    "WAW": "https://images.unsplash.com/photo-1519197924294-4ba991a11128?auto=format&fit=crop&w=1000&q=80",
    "KRK": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?auto=format&fit=crop&w=1000&q=80",
    "SOF": "https://images.unsplash.com/photo-1596394516093-501ba68a0ba6?auto=format&fit=crop&w=1000&q=80",
    "OTP": "https://images.unsplash.com/photo-1584646098274-084e7af9a794?auto=format&fit=crop&w=1000&q=80",
    "BCN": "https://images.unsplash.com/photo-1583422409516-2895a77efded?auto=format&fit=crop&w=1000&q=80",
    "MAD": "https://images.unsplash.com/photo-1539037116277-4db20889f2d4?auto=format&fit=crop&w=1000&q=80",
    "LTN": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?auto=format&fit=crop&w=1000&q=80",
    "STN": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?auto=format&fit=crop&w=1000&q=80",
    "LGW": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?auto=format&fit=crop&w=1000&q=80",
    "LHR": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?auto=format&fit=crop&w=1000&q=80",
    "CDG": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=1000&q=80",
    "ORY": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=1000&q=80",
    "BVA": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=1000&q=80",
    "BER": "https://images.unsplash.com/photo-1560969184-10fe8719e047?auto=format&fit=crop&w=1000&q=80",
    "FRA": "https://images.unsplash.com/photo-1467269204594-9661b134dd2b?auto=format&fit=crop&w=1000&q=80",
    "MUC": "https://images.unsplash.com/photo-1595867818082-083862f3d630?auto=format&fit=crop&w=1000&q=80",
    "AMS": "https://images.unsplash.com/photo-1534351590666-13e3e96b5017?auto=format&fit=crop&w=1000&q=80",
    "IST": "https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?auto=format&fit=crop&w=1000&q=80",
    "SAW": "https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?auto=format&fit=crop&w=1000&q=80",
    "DXB": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=1000&q=80",
    "AUH": "https://images.unsplash.com/photo-1512632578888-169bbbc64f33?auto=format&fit=crop&w=1000&q=80",
    "TIV": "https://images.unsplash.com/photo-1555990538-1e6c3b6f6c58?auto=format&fit=crop&w=1000&q=80",
    "BEG": "https://images.unsplash.com/photo-1584646098274-084e7af9a794?auto=format&fit=crop&w=1000&q=80",
    "MLA": "https://images.unsplash.com/photo-1514222134-b57cbb8ce073?auto=format&fit=crop&w=1000&q=80",
    "TBS": "https://images.unsplash.com/photo-1565008447742-97f6f38c985c?auto=format&fit=crop&w=1000&q=80",
    "EVN": "https://images.unsplash.com/photo-1565008447742-97f6f38c985c?auto=format&fit=crop&w=1000&q=80",
}

DEFAULT_TRAVEL_PHOTO = (
    "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?auto=format&fit=crop&w=1000&q=80"
)


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


def _get_credentials() -> tuple[str, str]:
    bot_token = (os.environ.get("TG_BOT_TOKEN") or "").strip()
    chat_id = (os.environ.get("TG_CHANNEL_ID") or "").strip()

    if not bot_token:
        raise RuntimeError("Telegram bot token is empty. Check TG_BOT_TOKEN in GitHub Secrets and workflow env.")
    if not chat_id:
        raise RuntimeError("Telegram channel/chat ID is empty. Check TG_CHANNEL_ID in GitHub Secrets and workflow env.")

    print(f"TG diagnostic: token=len={len(bot_token)} preview={_mask_token(bot_token)} | chat_id=***")
    return bot_token, chat_id


def _post_telegram_api(method: str, payload: dict, bot_token: str, max_retries: int = 3) -> int | None:
    url = f"https://api.telegram.org/bot{bot_token}/{method}"
    encoded_data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    attempt = 0
    while True:
        attempt += 1
        req = urllib.request.Request(
            url,
            data=encoded_data,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
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
                hint = " (check chat_id format: -100... or @channel_username, HTML tags, or photo URL)"
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


def send_channel_message(
    text: str,
    disable_web_page_preview: bool | None = None,
    max_retries: int = 3,
) -> int | None:
    bot_token, chat_id = _get_credentials()

    if disable_web_page_preview is None:
        disable_preview = _env_flag("DISABLE_LINK_PREVIEW", default=True)
    else:
        disable_preview = bool(disable_web_page_preview)

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "link_preview_options": {
            "is_disabled": disable_preview,
        },
    }
    return _post_telegram_api("sendMessage", payload, bot_token=bot_token, max_retries=max_retries)


def get_city_photo_url(destination_code: str | None) -> str:
    code = (destination_code or "").strip().upper()
    return CITY_PHOTOS.get(code) or DEFAULT_TRAVEL_PHOTO


def send_channel_photo(
    text: str,
    destination_code: str | None = None,
    photo_url: str | None = None,
    disable_web_page_preview: bool | None = None,
    max_retries: int = 3,
) -> int | None:
    bot_token, chat_id = _get_credentials()
    resolved_photo = (photo_url or get_city_photo_url(destination_code)).strip()

    payload = {
        "chat_id": chat_id,
        "photo": resolved_photo,
        "caption": text,
        "parse_mode": "HTML",
    }
    try:
        return _post_telegram_api("sendPhoto", payload, bot_token=bot_token, max_retries=max_retries)
    except RuntimeError as exc:
        # Если Telegram не смог скачать фото по внешнему URL, падаем на текстовое сообщение без превью
        print(f"TG photo fallback to text message for dest={destination_code}: {exc}")
        return send_channel_message(
            text=text,
            disable_web_page_preview=disable_web_page_preview if disable_web_page_preview is not None else True,
            max_retries=max_retries,
        )
