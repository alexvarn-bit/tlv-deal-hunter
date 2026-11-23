import json
import os
from pathlib import Path
from .config import MAX_PRICE_USD, STATE_FILE
from .travelpayouts import fetch_latest_tlv_prices
from .formatter import format_deal_post
from .telegram_sender import send_channel_message


def load_state(path_str: str) -> dict:
    path = Path(path_str)
    if not path.exists():
        return {"posted": {}}
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return {"posted": {}}
    data = json.loads(raw)
    if not isinstance(data, dict):
        return {"posted": {}}
    data.setdefault("posted", {})
    return data


def save_state(path_str: str, state: dict) -> None:
    path = Path(path_str)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp_path.replace(path)


def make_deal_key(flight: dict, lang: str = "ru") -> str:
    return "|".join([
        lang.strip().lower() or "ru",
        str(flight.get("origin", "")).strip(),
        str(flight.get("destination", "")).strip(),
        str(flight.get("departure_at", ""))[:10],
        str(flight.get("return_at", ""))[:10],
        str(flight.get("value", "")).strip(),
    ])


def run() -> None:
    lang = (os.environ.get("BOT_LANG") or os.environ.get("DEAL_LANG") or "ru").strip().lower()
    disable_preview = (os.environ.get("DISABLE_LINK_PREVIEW", "false")).strip().lower() in {
        "1",
        "true",
        "yes",
    }

    state = load_state(STATE_FILE)
    posted = state.setdefault("posted", {})
    flights = fetch_latest_tlv_prices(limit=30)

    fetched_count = len(flights)
    skipped_price = 0
    skipped_dup = 0
    new_count = 0

    for flight in flights:
        price = flight.get("value")
        if price is None:
            skipped_price += 1
            continue

        try:
            price_val = float(price)
        except (TypeError, ValueError):
            skipped_price += 1
            continue

        if price_val > float(MAX_PRICE_USD):
            skipped_price += 1
            continue

        key = make_deal_key(flight, lang=lang)
        legacy_key = make_deal_key(flight, lang="")
        if key in posted or legacy_key in posted:
            skipped_dup += 1
            continue

        text = format_deal_post(flight, lang=lang)
        msg_id = send_channel_message(text, disable_web_page_preview=disable_preview)
        posted[key] = {
            "message_id": msg_id,
            "price": price_val,
            "lang": lang,
        }
        new_count += 1
        # Сохраняем сразу после каждой успешной отправки, чтобы при сбое на следующем посте не было дублей
        save_state(STATE_FILE, state)

    status = "OK"
    print(
        f"STATUS={status} | LANG={lang} | FETCHED={fetched_count} | "
        f"SKIP_PRICE={skipped_price} | SKIP_DUP={skipped_dup} | PUBLISHED={new_count}"
    )


if __name__ == "__main__":
    run()
