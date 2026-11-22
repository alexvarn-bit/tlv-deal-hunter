import json
from pathlib import Path
from .config import MAX_PRICE_USD, STATE_FILE
from .travelpayouts import fetch_latest_tlv_prices
from .formatter import format_deal_post
from .telegram_sender import send_channel_message


def load_state(path_str: str) -> dict:
    path = Path(path_str)
    if not path.exists():
        return {"posted": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path_str: str, state: dict) -> None:
    path = Path(path_str)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_deal_key(flight: dict) -> str:
    return "|".join([
        str(flight.get("origin", "")),
        str(flight.get("destination", "")),
        str(flight.get("departure_at", ""))[:10],
        str(flight.get("return_at", ""))[:10],
        str(flight.get("value", "")),
    ])


def run() -> None:
    state = load_state(STATE_FILE)
    posted = state.setdefault("posted", {})
    flights = fetch_latest_tlv_prices(limit=30)

    new_count = 0
    for flight in flights:
        price = flight.get("value")
        if price is None or float(price) > MAX_PRICE_USD:
            continue

        key = make_deal_key(flight)
        if key in posted:
            continue

        text = format_deal_post(flight)
        msg_id = send_channel_message(text)
        posted[key] = {"message_id": msg_id, "price": price}
        new_count += 1

    if new_count > 0:
        save_state(STATE_FILE, state)
    print(f"Published {new_count} new flight deals.")


if __name__ == "__main__":
    run()
