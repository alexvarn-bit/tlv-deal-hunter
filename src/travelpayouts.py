import requests
from .config import TP_TOKEN, ORIGIN, CURRENCY, MARKET


def fetch_latest_tlv_prices(limit: int = 30) -> list[dict]:
    url = "https://api.travelpayouts.com/aviasales/v3/get_latest_prices"
    params = {
        "origin": ORIGIN,
        "currency": CURRENCY,
        "market": MARKET,
        "limit": limit,
        "show_to_affiliates": "true",
        "token": TP_TOKEN,
    }
    resp = requests.get(url, params=params, timeout=20)
    resp.raise_for_status()
    payload = resp.json()
    if not payload.get("success"):
        raise RuntimeError(f"Travelpayouts API error: {payload}")
    return payload.get("data", [])
