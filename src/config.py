import os
from dotenv import load_dotenv

load_dotenv()


def _env_str(name: str, default: str = "") -> str:
    return (os.getenv(name, default) or "").strip()


TP_TOKEN: str = _env_str("TP_TOKEN")
TP_MARKER: str = _env_str("TP_MARKER")
TG_BOT_TOKEN: str = _env_str("TG_BOT_TOKEN")
TG_CHANNEL_ID: str = _env_str("TG_CHANNEL_ID")

ORIGIN: str = _env_str("ORIGIN", "TLV").upper() or "TLV"
CURRENCY: str = _env_str("CURRENCY", "usd").lower() or "usd"
MARKET: str = (_env_str("BOT_LANG") or _env_str("MARKET", "ru")).lower() or "ru"
MAX_PRICE_USD: float = float(_env_str("MAX_PRICE_USD", "120") or "120")
STATE_FILE: str = _env_str("STATE_FILE", "data/posted_deals.json") or "data/posted_deals.json"
