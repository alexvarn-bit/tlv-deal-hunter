import os
from dotenv import load_dotenv

load_dotenv()

TP_TOKEN = os.environ["TP_TOKEN"]
TP_MARKER = os.environ["TP_MARKER"]
TG_BOT_TOKEN = os.environ["TG_BOT_TOKEN"]
TG_CHANNEL_ID = os.environ["TG_CHANNEL_ID"]  # e.g. "@tlv_lowcost_il" or "-100..."

ORIGIN = "TLV"
CURRENCY = "usd"
MARKET = "ru"
MAX_PRICE_USD = float(os.getenv("MAX_PRICE_USD", "120"))
STATE_FILE = "data/posted_deals.json"
