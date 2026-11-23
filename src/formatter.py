import html
import os
from urllib.parse import urlencode
from .config import CURRENCY, TP_MARKER


def build_affiliate_link(flight: dict) -> str:
    origin = str(flight.get("origin") or "TLV").strip().upper()
    destination = str(flight.get("destination") or "").strip().upper()
    depart_date = str(flight.get("departure_at") or "")[:10].replace("-", "")
    return_date = str(flight.get("return_at") or "")[:10].replace("-", "")

    # Format: <ORIGIN><DDMM><DEST><DDMM>1 when departure date is present
    if len(depart_date) == 8 and destination:
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


def _format_dates(dep: str, ret: str, lang: str) -> str:
    if dep and ret:
        return f"{dep} — {ret}"
    if dep:
        return f"вылет {dep}" if lang != "he" else f"יציאה {dep}"
    return "уточняются" if lang != "he" else "יתעדכן"


def _format_route_type(transfers: int, lang: str) -> str:
    if lang == "he":
        return "ישיר" if transfers == 0 else f"עצירות: {transfers}"
    return "прямой" if transfers == 0 else f"пересадок: {transfers}"


def format_deal_post(flight: dict, lang: str | None = None) -> str:
    resolved_lang = (
        lang
        or os.environ.get("BOT_LANG")
        or os.environ.get("DEAL_LANG")
        or "ru"
    ).strip().lower()

    origin = str(flight.get("origin") or "TLV").strip().upper()
    dest = str(flight.get("destination") or "???").strip().upper()
    price = str(flight.get("value") if flight.get("value") is not None else "?").strip()
    airline = str(flight.get("airline") or "").strip()
    dep = str(flight.get("departure_at") or "")[:10].strip()
    ret = str(flight.get("return_at") or "")[:10].strip()

    try:
        transfers = int(flight.get("number_of_changes") or 0)
    except (TypeError, ValueError):
        transfers = 0

    link = build_affiliate_link(flight)
    dates_line = _format_dates(dep, ret, resolved_lang)
    route_type = _format_route_type(transfers, resolved_lang)

    if not airline:
        airline_display = "уточняется" if resolved_lang != "he" else "יתעדכן"
    else:
        airline_display = airline

    e_origin = html.escape(origin)
    e_dest = html.escape(dest)
    e_price = html.escape(price)
    e_dates = html.escape(dates_line)
    e_airline = html.escape(airline_display)
    e_route = html.escape(route_type)
    e_link = html.escape(link, quote=True)

    if resolved_lang == "he":
        return (
            f"✈️ <b>{e_origin} → {e_dest}</b> ב-<b>${e_price}</b>\n"
            f"📅 תאריכים: {e_dates}\n"
            f"🛫 חברת תעופה: {e_airline} ({e_route})\n\n"
            f"🔗 <a href=\"{e_link}\">לבדיקה והזמנה</a>\n"
            f"<i>המחיר עדכני לרגע הפרסום ועשוי להשתנות במהירות.</i>"
        )

    return (
        f"✈️ <b>{e_origin} → {e_dest}</b> за <b>${e_price}</b>\n"
        f"📅 Даты: {e_dates}\n"
        f"🛫 Авиакомпания: {e_airline} ({e_route})\n\n"
        f"🔗 <a href=\"{e_link}\">Проверить и забронировать</a>\n"
        f"<i>Цена актуальна на момент публикации и может быстро измениться.</i>"
    )
