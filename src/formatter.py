from datetime import datetime
import html
import os
from urllib.parse import urlencode
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from .config import CURRENCY, TP_MARKER


# Справочник городов для популярных IATA-кодов (ru / he)
AIRPORT_NAMES: dict[str, dict[str, str]] = {
    "TLV": {"ru": "Тель-Авив", "he": "תל אביב"},
    "LCA": {"ru": "Ларнака", "he": "לרנקה"},
    "PFO": {"ru": "Пафос", "he": "פאפוס"},
    "ATH": {"ru": "Афины", "he": "אתונה"},
    "SKG": {"ru": "Салоники", "he": "סלוניקי"},
    "HER": {"ru": "Ираклион", "he": "הרקליון"},
    "RHO": {"ru": "Родос", "he": "רודוס"},
    "CFU": {"ru": "Корфу", "he": "קורפו"},
    "FCO": {"ru": "Рим", "he": "רומא"},
    "MXP": {"ru": "Милан", "he": "מילאנו"},
    "BGY": {"ru": "Бергамо / Милан", "he": "ברגמו / מילאנו"},
    "VCE": {"ru": "Венеция", "he": "ונציה"},
    "NAP": {"ru": "Неаполь", "he": "נאפולי"},
    "CTA": {"ru": "Катания", "he": "קטניה"},
    "PMO": {"ru": "Палермо", "he": "פלרמו"},
    "BLQ": {"ru": "Болонья", "he": "בולוניה"},
    "BUD": {"ru": "Будапешт", "he": "בודפשט"},
    "VIE": {"ru": "Вена", "he": "וינה"},
    "PRG": {"ru": "Прага", "he": "פראג"},
    "WAW": {"ru": "Варшава", "he": "ורשה"},
    "KRK": {"ru": "Краков", "he": "קרקוב"},
    "SOF": {"ru": "София", "he": "סופיה"},
    "OTP": {"ru": "Бухарест", "he": "בוקרשט"},
    "BCN": {"ru": "Барселона", "he": "ברצלונה"},
    "MAD": {"ru": "Мадрид", "he": "מדריד"},
    "AGP": {"ru": "Малага", "he": "מלאגה"},
    "LTN": {"ru": "Лондон (Лутон)", "he": "לונדון (לוטון)"},
    "STN": {"ru": "Лондон (Станстед)", "he": "לונדון (סטנסטד)"},
    "LGW": {"ru": "Лондон (Гатвик)", "he": "לונדון (גטוויק)"},
    "LHR": {"ru": "Лондон (Хитроу)", "he": "לונדון (הית'רו)"},
    "CDG": {"ru": "Париж", "he": "פריז"},
    "ORY": {"ru": "Париж (Орли)", "he": "פריז (אורלי)"},
    "BVA": {"ru": "Париж (Бове)", "he": "פריז (בובה)"},
    "BER": {"ru": "Берлин", "he": "ברלין"},
    "FRA": {"ru": "Франкфурт", "he": "פרנקפורט"},
    "MUC": {"ru": "Мюнхен", "he": "מינכן"},
    "AMS": {"ru": "Амстердам", "he": "אמסטרדם"},
    "BRU": {"ru": "Брюссель", "he": "בריסל"},
    "ZRH": {"ru": "Цюрих", "he": "ציריך"},
    "GVA": {"ru": "Женева", "he": "ז'נבה"},
    "IST": {"ru": "Стамбул", "he": "איסטנבול"},
    "SAW": {"ru": "Стамбул (Сабиха)", "he": "איסטנבול (סביחה)"},
    "DXB": {"ru": "Дубай", "he": "דובאי"},
    "AUH": {"ru": "Абу-Даби", "he": "אבו דאבי"},
    "AMM": {"ru": "Амман", "he": "עמאן"},
    "TIV": {"ru": "Тиват", "he": "טיבט"},
    "BEG": {"ru": "Белград", "he": "בלגרד"},
    "TIA": {"ru": "Тирана", "he": "טירנה"},
    "MLA": {"ru": "Мальта", "he": "מלטה"},
    "TBS": {"ru": "Тбилиси", "he": "טביליסי"},
    "EVN": {"ru": "Ереван", "he": "ירוואן"},
    "TFS": {"ru": "Тенерифе", "he": "טנריף"},
}


def _get_timezone() -> ZoneInfo:
    tz_name = (os.environ.get("DEAL_TIMEZONE") or "Asia/Jerusalem").strip()
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("Asia/Jerusalem")


def format_airport_label(code: str, lang: str = "ru") -> str:
    clean_code = (code or "").strip().upper()
    if not clean_code:
        return "???"
    entry = AIRPORT_NAMES.get(clean_code)
    if not entry:
        return clean_code
    city = entry.get(lang) or entry.get("ru") or entry.get("he")
    if not city:
        return clean_code
    return f"{clean_code} ({city})"


def _parse_date_value(raw_value: str | None, tz: ZoneInfo) -> tuple[datetime | None, bool]:
    """
    Возвращает (datetime_объект, has_explicit_time).
    Для строки формата YYYY-MM-DD не делает сдвига по таймзоне, чтобы не потерять день.
    """
    if not raw_value:
        return None, False
    text = str(raw_value).strip()
    if not text:
        return None, False

    # Чистая дата без времени: YYYY-MM-DD
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        try:
            dt = datetime.strptime(text, "%Y-%m-%d")
            return dt, False
        except ValueError:
            pass

    # ISO-строка с временем / смещением
    normalized = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is not None:
            dt = dt.astimezone(tz)
        return dt, True
    except ValueError:
        pass

    # Запасной разбор первых 10 символов
    prefix = text[:10]
    if len(prefix) == 10:
        try:
            dt = datetime.strptime(prefix, "%Y-%m-%d")
            return dt, False
        except ValueError:
            pass

    return None, False


def _format_single_date(dt: datetime, ref_year: int) -> str:
    if dt.year != ref_year:
        return dt.strftime("%d.%m.%Y")
    return dt.strftime("%d.%m")


def _format_dates(dep_raw: str | None, ret_raw: str | None, lang: str, tz: ZoneInfo) -> str:
    dep_dt, _ = _parse_date_value(dep_raw, tz)
    ret_dt, _ = _parse_date_value(ret_raw, tz)
    now_year = datetime.now(tz).year

    if dep_dt and ret_dt:
        ref_year = dep_dt.year if dep_dt.year != now_year else now_year
        return f"{_format_single_date(dep_dt, ref_year)} — {_format_single_date(ret_dt, ref_year)}"

    if dep_dt:
        dep_str = _format_single_date(dep_dt, now_year)
        return f"вылет {dep_str}" if lang != "he" else f"יציאה {dep_str}"

    if ret_dt:
        ret_str = _format_single_date(ret_dt, now_year)
        return f"возврат {ret_str}" if lang != "he" else f"חזרה {ret_str}"

    return "уточняются" if lang != "he" else "יתעדכן"


def build_affiliate_link(flight: dict) -> str:
    origin = str(flight.get("origin") or "TLV").strip().upper()
    destination = str(flight.get("destination") or "").strip().upper()
    depart_date = str(flight.get("departure_at") or "")[:10].replace("-", "")
    return_date = str(flight.get("return_at") or "")[:10].replace("-", "")

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
    if resolved_lang not in {"ru", "he"}:
        resolved_lang = "ru"

    tz = _get_timezone()
    origin_code = str(flight.get("origin") or "TLV").strip().upper()
    dest_code = str(flight.get("destination") or "???").strip().upper()

    origin_label = format_airport_label(origin_code, resolved_lang)
    dest_label = format_airport_label(dest_code, resolved_lang)

    price = str(flight.get("value") if flight.get("value") is not None else "?").strip()
    airline = str(flight.get("airline") or "").strip().upper()
    dep_raw = flight.get("departure_at")
    ret_raw = flight.get("return_at")

    try:
        transfers = int(flight.get("number_of_changes") or 0)
    except (TypeError, ValueError):
        transfers = 0

    link = build_affiliate_link(flight)
    dates_line = _format_dates(dep_raw, ret_raw, resolved_lang, tz)
    route_type = _format_route_type(transfers, resolved_lang)

    if not airline:
        airline_display = "уточняется" if resolved_lang != "he" else "יתעדכן"
    else:
        airline_display = airline

    e_origin = html.escape(origin_label)
    e_dest = html.escape(dest_label)
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
