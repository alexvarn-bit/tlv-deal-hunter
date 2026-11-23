from datetime import datetime
import html
import os
from urllib.parse import urlencode
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from .config import CURRENCY, TP_MARKER


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
    "BGY": {"ru": "Бергамо", "he": "ברגמו"},
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
    "LTN": {"ru": "Лондон", "he": "לונדון"},
    "STN": {"ru": "Лондон", "he": "לונדון"},
    "LGW": {"ru": "Лондон", "he": "לונדון"},
    "LHR": {"ru": "Лондон", "he": "לונדון"},
    "CDG": {"ru": "Париж", "he": "פריז"},
    "ORY": {"ru": "Париж", "he": "פריז"},
    "BVA": {"ru": "Париж", "he": "פריז"},
    "BER": {"ru": "Берлин", "he": "ברלין"},
    "FRA": {"ru": "Франкфурт", "he": "פרנקפורט"},
    "MUC": {"ru": "Мюнхен", "he": "מינכן"},
    "AMS": {"ru": "Амстердам", "he": "אמסטרדם"},
    "BRU": {"ru": "Брюссель", "he": "בריסל"},
    "ZRH": {"ru": "Цюрих", "he": "ציריך"},
    "GVA": {"ru": "Женева", "he": "ז'נבה"},
    "IST": {"ru": "Стамбул", "he": "איסטנבול"},
    "SAW": {"ru": "Стамбул", "he": "איסטנבול"},
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

AIRLINE_NAMES: dict[str, dict[str, str]] = {
    "LY": {"ru": "El Al", "he": "אל על"},
    "IZ": {"ru": "Arkia", "he": "ארקיע"},
    "6H": {"ru": "Israir", "he": "ישראייר"},
    "FR": {"ru": "Ryanair", "he": "ריאנאיר"},
    "W6": {"ru": "Wizz Air", "he": "וויז אייר"},
    "W4": {"ru": "Wizz Air", "he": "וויז אייר"},
    "U2": {"ru": "easyJet", "he": "איזיג'ט"},
    "EJU": {"ru": "easyJet", "he": "איזיג'ט"},
    "A3": {"ru": "Aegean", "he": "אג'יאן"},
    "QS": {"ru": "Smartwings", "he": "סמארטווינגס"},
    "HV": {"ru": "Transavia", "he": "טרנסאוויה"},
    "TO": {"ru": "Transavia", "he": "טרנסאוויה"},
    "VY": {"ru": "Vueling", "he": "וולינג"},
    "LO": {"ru": "LOT", "he": "לוט"},
    "OS": {"ru": "Austrian", "he": "אוסטריאן"},
    "LH": {"ru": "Lufthansa", "he": "לופטהנזה"},
    "LX": {"ru": "SWISS", "he": "סוויס"},
    "AF": {"ru": "Air France", "he": "אייר פראנס"},
    "KL": {"ru": "KLM", "he": "KLM"},
    "BA": {"ru": "British Airways", "he": "בריטיש איירווייז"},
    "IB": {"ru": "Iberia", "he": "איבריה"},
    "TK": {"ru": "Turkish Airlines", "he": "טורקיש איירליינס"},
    "PC": {"ru": "Pegasus", "he": "פגסוס"},
    "FZ": {"ru": "flydubai", "he": "פליי דובאי"},
    "EY": {"ru": "Etihad", "he": "איתיחאד"},
    "EK": {"ru": "Emirates", "he": "אמירייטס"},
    "RJ": {"ru": "Royal Jordanian", "he": "רויאל ג'ורדניאן"},
    "JU": {"ru": "Air Serbia", "he": "אייר סרביה"},
    "RO": {"ru": "TAROM", "he": "טארום"},
    "FB": {"ru": "Bulgaria Air", "he": "בולגריה אייר"},
    "KM": {"ru": "KM Malta", "he": "אייר מלטה"},
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
    return entry.get(lang) or entry.get("ru") or entry.get("he") or clean_code


def format_airline_label(airline_code: str | None, lang: str = "ru") -> str:
    code = (airline_code or "").strip().upper()
    if not code:
        return "יתעדכן" if lang == "he" else "уточняется"
    entry = AIRLINE_NAMES.get(code)
    if not entry:
        return code
    return entry.get(lang) or entry.get("ru") or entry.get("he") or code


def _parse_date_value(raw_value: str | None, tz: ZoneInfo) -> datetime | None:
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
        return dt
    except ValueError:
        pass

    prefix = text[:10]
    if len(prefix) == 10:
        try:
            return datetime.strptime(prefix, "%Y-%m-%d")
        except ValueError:
            pass

    return None


def _format_single_date(dt: datetime, ref_year: int) -> str:
    if dt.year != ref_year:
        return dt.strftime("%d.%m.%Y")
    return dt.strftime("%d.%m")


def _format_dates(dep_raw: str | None, ret_raw: str | None, lang: str, tz: ZoneInfo) -> str:
    dep_dt = _parse_date_value(dep_raw, tz)
    ret_dt = _parse_date_value(ret_raw, tz)
    now_year = datetime.now(tz).year

    if dep_dt and ret_dt:
        ref_year = dep_dt.year if dep_dt.year != now_year else now_year
        return f"{_format_single_date(dep_dt, ref_year)}–{_format_single_date(ret_dt, ref_year)}"

    if dep_dt:
        dep_str = _format_single_date(dep_dt, now_year)
        return f"вылет {dep_str}" if lang != "he" else f"יציאה {dep_str}"

    if ret_dt:
        ret_str = _format_single_date(ret_dt, now_year)
        return f"возврат {ret_str}" if lang != "he" else f"חזרה {ret_str}"

    return "даты уточняются" if lang != "he" else "תאריכים יתעדכנו"


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
    airline_label = format_airline_label(flight.get("airline"), resolved_lang)

    price = str(flight.get("value") if flight.get("value") is not None else "?").strip()
    dep_raw = flight.get("departure_at")
    ret_raw = flight.get("return_at")

    try:
        transfers = int(flight.get("number_of_changes") or 0)
    except (TypeError, ValueError):
        transfers = 0

    link = build_affiliate_link(flight)
    dates_line = _format_dates(dep_raw, ret_raw, resolved_lang, tz)
    route_type = _format_route_type(transfers, resolved_lang)

    e_origin = html.escape(origin_label)
    e_dest = html.escape(dest_label)
    e_price = html.escape(price)
    e_dates = html.escape(dates_line)
    e_airline = html.escape(airline_label)
    e_route = html.escape(route_type)
    e_link = html.escape(link, quote=True)

    if resolved_lang == "he":
        return (
            f"✈️ <b>{e_origin} → {e_dest}</b> | <b>${e_price}</b>\n"
            f"📅 {e_dates} • {e_airline} ({e_route})\n"
            f"👉 <a href=\"{e_link}\">לבדיקה והזמנה</a>"
        )

    return (
        f"✈️ <b>{e_origin} → {e_dest}</b> — <b>${e_price}</b>\n"
        f"📅 {e_dates} • {e_airline} ({e_route})\n"
        f"👉 <a href=\"{e_link}\">Проверить и забронировать</a>"
    )
