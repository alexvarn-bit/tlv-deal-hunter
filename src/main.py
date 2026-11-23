from datetime import datetime
import json
import os
from pathlib import Path
import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from .config import MAX_PRICE_USD, STATE_FILE
from .travelpayouts import fetch_latest_tlv_prices
from .formatter import format_deal_post
from .telegram_sender import send_channel_message, send_channel_photo


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw.strip())
    except ValueError:
        return default


def _get_timezone() -> ZoneInfo:
    tz_name = (os.environ.get("DEAL_TIMEZONE") or "Asia/Jerusalem").strip()
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("Asia/Jerusalem")


def _parse_iso_date(raw_value: str | None, tz: ZoneInfo) -> datetime | None:
    if not raw_value:
        return None
    text = str(raw_value).strip()
    if not text:
        return None

    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        if len(text) == 10:
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                pass

    normalized = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is not None:
            dt = dt.astimezone(tz)
        return dt.replace(tzinfo=None)
    except ValueError:
        pass

    prefix = text[:10]
    if len(prefix) == 10:
        try:
            return datetime.strptime(prefix, "%Y-%m-%d")
        except ValueError:
            pass

    return None


def _has_valid_departure_date(flight: dict, today_date, tz: ZoneInfo) -> bool:
    dep_dt = _parse_iso_date(flight.get("departure_at"), tz)
    if dep_dt is None:
        return False
    return dep_dt.date() >= today_date


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
    max_price = _env_float("MAX_PRICE_USD", float(MAX_PRICE_USD))
    max_posts = max(1, _env_int("MAX_POSTS_PER_RUN", 5))
    send_delay = max(0.0, _env_float("SEND_DELAY_SECONDS", 2.5))
    state_path = (os.environ.get("STATE_FILE") or STATE_FILE).strip()

    disable_preview = _env_flag("DISABLE_LINK_PREVIEW", default=True)
    send_photo = _env_flag("SEND_CITY_PHOTO", default=True)
    force_republish = _env_flag("FORCE_REPUBLISH", default=False)
    dry_run = _env_flag("DRY_RUN", default=False)

    tz = _get_timezone()
    today_date = datetime.now(tz).date()

    state = load_state(state_path)
    posted = state.setdefault("posted", {})
    flights = fetch_latest_tlv_prices(limit=100, max_date_lookups=15)

    fetched_count = len(flights)
    skipped_no_date = 0
    skipped_price = 0
    skipped_dup = 0
    skipped_city = 0
    skipped_cap = 0
    new_count = 0
    sample_prices: list[float] = []
    candidates: list[tuple[float, str, dict]] = []

    for flight in flights:
        if not _has_valid_departure_date(flight, today_date, tz):
            skipped_no_date += 1
            continue

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

        dest = str(flight.get("destination") or "").strip().upper()
        candidates.append((price_val, dest, flight))

    candidates.sort(key=lambda item: item[0])

    seen_destinations_in_run: set[str] = set()
    selected_for_run: list[tuple[float, dict]] = []

    for price_val, dest, flight in candidates:
        if dest and dest in seen_destinations_in_run:
            skipped_city += 1
            continue
        if len(selected_for_run) >= max_posts:
            skipped_cap += 1
            continue
        if dest:
            seen_destinations_in_run.add(dest)
        selected_for_run.append((price_val, flight))

    for idx, (price_val, flight) in enumerate(selected_for_run):
        key = make_deal_key(flight, lang=lang)
        dest = str(flight.get("destination") or "").strip().upper()
        text = format_deal_post(flight, lang=lang)

        if dry_run:
            print(f"[DRY_RUN] Would publish key={key} photo={send_photo}:\n{text}\n---")
            new_count += 1
            continue

        if idx > 0 and send_delay > 0:
            time.sleep(send_delay)

        if send_photo:
            msg_id = send_channel_photo(
                text=text,
                destination_code=dest,
                disable_web_page_preview=disable_preview,
            )
        else:
            msg_id = send_channel_message(
                text=text,
                disable_web_page_preview=disable_preview,
            )

        posted[key] = {
            "message_id": msg_id,
            "price": price_val,
            "lang": lang,
            "departure_at": str(flight.get("departure_at") or "")[:10],
            "return_at": str(flight.get("return_at") or "")[:10],
        }
        new_count += 1
        save_state(state_path, state)

    min_price_str = f"{min(sample_prices):.2f}" if sample_prices else "n/a"
    max_price_seen_str = f"{max(sample_prices):.2f}" if sample_prices else "n/a"

    print(
        f"STATUS=OK | LANG={lang} | MAX_PRICE={max_price:.2f} | "
        f"FETCHED={fetched_count} | SKIP_NO_DATE={skipped_no_date} | "
        f"SKIP_PRICE={skipped_price} | SKIP_DUP={skipped_dup} | "
        f"SKIP_CITY={skipped_city} | SKIP_CAP={skipped_cap} | "
        f"PUBLISHED={new_count} | SEEN_PRICES={min_price_str}..{max_price_seen_str}"
    )

    if new_count == 0:
        if fetched_count == 0:
            print("REASON=ZERO: Travelpayouts returned 0 flights.")
        elif skipped_no_date == fetched_count:
            print("REASON=ZERO: None of the fetched flights had valid upcoming departure dates.")
        elif skipped_dup > 0:
            print("REASON=ZERO: Remaining cheap flights were already posted (SKIP_DUP).")
        else:
            print("REASON=ZERO: No flights matched publication criteria.")


if __name__ == "__main__":
    run()
