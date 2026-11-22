from urllib.parse import urlencode
from .config import TP_MARKER, CURRENCY


def build_affiliate_link(flight: dict) -> str:
    # Builds a standard Aviasales search deep link with your marker
    origin = flight.get("origin", "TLV")
    destination = flight.get("destination", "")
    depart_date = (flight.get("departure_at") or "")[:10].replace("-", "")
    return_date = (flight.get("return_at") or "")[:10].replace("-", "")

    # Format: <ORIGIN><DDMM><DEST><DDMM><MARKER> when dates are present
    if len(depart_date) == 8:
        dep_ddmm = depart_date[6:8] + depart_date[4:6]
        ret_ddmm = return_date[6:8] + return_date[4:6] if len(return_date) == 8 else ""
        code = f"{origin}{dep_ddmm}{destination}{ret_ddmm}1"
        query = urlencode({"marker": TP_MARKER, "currency": CURRENCY})
        return f"https://www.aviasales.com/search/{code}?{query}"

    query = urlencode({
        "origin_iata": origin,
        "destination_iata": destination,
        "marker": TP_MARKER,
        "currency": CURRENCY,
    })
    return f"https://www.aviasales.com/?{query}"


def format_deal_post(flight: dict) -> str:
    dest = flight.get("destination", "???")
    price = flight.get("value", "?")
    airline = flight.get("airline", "")
    dep = (flight.get("departure_at") or "")[:10]
    ret = (flight.get("return_at") or "")[:10]
    transfers = flight.get("number_of_changes", 0)
    link = build_affiliate_link(flight)

    route_type = "прямой" if transfers == 0 else f"пересадок: {transfers}"
    dates_line = f"{dep} — {ret}" if ret else f"вылет {dep}"

    return (
        f"✈️ <b>TLV → {dest}</b> за <b>${price}</b>\n"
        f"📅 Даты: {dates_line}\n"
        f"🛫 Авиакомпания: {airline} ({route_type})\n\n"
        f"🔗 <a href=\"{link}\">Проверить и забронировать</a>\n"
        f"<i>Цена актуальна на момент публикации и может быстро измениться.</i>"
    )
