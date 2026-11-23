AIRLINE_NAMES: dict[str, dict[str, str]] = {
    "LY": {"ru": "El Al", "he": "אל על"},
    "IZ": {"ru": "Arkia", "he": "ארקיע"},
    "6H": {"ru": "Israir", "he": "ישראייר"},
    "FR": {"ru": "Ryanair", "he": "ריאנאיר"},
    "W6": {"ru": "Wizz Air", "he": "וויז אייר"},
    "W4": {"ru": "Wizz Air Malta", "he": "וויז אייר מלטה"},
    "U2": {"ru": "easyJet", "he": "איזיג'ט"},
    "EJU": {"ru": "easyJet Europe", "he": "איזיג'ט אירופה"},
    "A3": {"ru": "Aegean Airlines", "he": "אג'יאן איירליינס"},
    "QS": {"ru": "Smartwings", "he": "סמארטווינגס"},
    "HV": {"ru": "Transavia", "he": "טרנסאוויה"},
    "TO": {"ru": "Transavia France", "he": "טרנסאוויה צרפת"},
    "VY": {"ru": "Vueling", "he": "וולינג"},
    "VY": {"ru": "Vueling", "he": "וולינג"},
    "LO": {"ru": "LOT Polish Airlines", "he": "לוט"},
    "OS": {"ru": "Austrian Airlines", "he": "אוסטריאן איירליינס"},
    "LH": {"ru": "Lufthansa", "he": "לופטהנזה"},
    "LX": {"ru": "SWISS", "he": "סוויס"},
    "AF": {"ru": "Air France", "he": "אייר פראנס"},
    "KL": {"ru": "KLM", "he": "KLM"},
    "BA": {"ru": "British Airways", "he": "בריטיש איירווייז"},
    "IB": {"ru": "Iberia", "he": "איבריה"},
    "TK": {"ru": "Turkish Airlines", "he": "טורקיש איירליינס"},
    "PC": {"ru": "Pegasus Airlines", "he": "פגסוס"},
    "FZ": {"ru": "flydubai", "he": "פליי דובאי"},
    "EY": {"ru": "Etihad Airways", "he": "איתיחאד איירווייז"},
    "EK": {"ru": "Emirates", "he": "אמירייטס"},
    "RJ": {"ru": "Royal Jordanian", "he": "רויאל ג'ורדניאן"},
    "JU": {"ru": "Air Serbia", "he": "אייר סרביה"},
    "RO": {"ru": "TAROM", "he": "טארום"},
    "FB": {"ru": "Bulgaria Air", "he": "בולגריה אייר"},
    "KM": {"ru": "KM Malta Airlines", "he": "אייר מלטה"},
}


def format_airline_label(airline_code: str | None, lang: str = "ru") -> str:
    code = (airline_code or "").strip().upper()
    if not code:
        return "יתעדכן" if lang == "he" else "уточняется"
    entry = AIRLINE_NAMES.get(code)
    if not entry:
        return code
    name = entry.get(lang) or entry.get("ru") or entry.get("he")
    if not name:
        return code
    return f"{name} ({code})"
