import json
import os
from pathlib import Path
import time
from .config import MAX_PRICE_USD, STATE_FILE
from .travelpayouts import fetch_latest_tlv_prices
from .formatter import format_deal_post
from .telegram_sender import send_channel_message


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


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
        (lang or "ru").strip().lower(),
        str(flight.get("origin", "")).strip().upper(),
        str(flight.get("destination", "")).strip().upper(),
        str(flight.get("departure_at", ""))[:10],
        str(flight.get("return_at", ""))[:10],
        str(flight.get("value", "")).strip(),
    ])


def run() -> None:
    lang = (
        os.environ.get("BOT_LANG")
        or os.environ.get("DEAL_LANG")
        or "ru"
    ).strip().lower()
    max_price = float(os.environ.get("MAX_PRICE_USD") or MAX_PRICE_USD)
    state_path = (os.environ.get("STATE_FILE") or STATE_FILE).strip()
    disable_preview = _env_flag("DISABLE_LINK_PREVIEW", default=False)
    force_republish = _env_flag("FORCE_REPUBLISH", default=False)
    dry_run = _env_flag("DRY_RUN", default=False)

    try:
        send_delay = float(os.environ.get("SEND_DELAY_SECONDS") or "1.5")
    except (TypeError, ValueError):
        send_delay = 1.5
    send_delay = max(0.0, send_delay)

    state = load_state(state_path)
    posted = state.setdefault("posted", {})
    flights = fetch_latest_tlv_prices(limit=30)

    fetched_count = len(flights)
    skipped_price = 0
    skipped_dup = 0
    new_count = 0
    sample_prices: list[float] = []

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

        sample_prices.append(price_val)

        if price_val > max_price:
            skipped_price += 1
            continue

        key = make_deal_key(flight, lang=lang)
        legacy_key = make_deal_key(flight, lang="")
        if not force_republish and (key in posted or legacy_key in posted):
            skipped_dup += 1
            continue

        text = format_deal_post(flight, lang=lang)
        if dry_run:
            print(f"[DRY_RUN] Would publish key={key}:\n{text}\n---")
            new_count += 1
            continue

        msg_id = send_channel_message(text, disable_web_page_preview=disable_preview)
        posted[key] = {
            "message_id": msg_id,
            "price": price_val,
            "lang": lang,
        }
        new_count += 1
        save_state(state_path, state)
        if send_delay > 0:
            time.sleep(send_delay)

    min_price_str = f"{min(sample_prices):.2f}" if sample_prices else "n/a"
    max_price_seen_str = f"{max(sample_prices):.2f}" if sample_prices else "n/a"

    print(
        f"STATUS=OK | LANG={lang} | MAX_PRICE={max_price:.2f} | "
        f"FETCHED={fetched_count} | SKIP_PRICE={skipped_price} | "
        f"SKIP_DUP={skipped_dup} | PUBLISHED={new_count} | "
        f"SEEN_PRICES={min_price_str}..{max_price_seen_str}"
    )

    if new_count == 0:
        if fetched_count == 0:
            print("REASON=ZERO: Travelpayouts returned 0 flights.")
        elif skipped_price == fetched_count:
            print(f"REASON=ZERO: All {fetched_count} flights exceeded MAX_PRICE_USD ({max_price:.2f}).")
        elif skipped_dup > 0:
            print("REASON=ZERO: Remaining cheap flights were already posted (SKIP_DUP).")
        else:
            print("REASON=ZERO: No flights matched publication criteria.")


if __name__ == "__main__":
    run()
