import os
import requests
from .config import CURRENCY, MARKET, ORIGIN, TP_TOKEN


def fetch_latest_tlv_prices(limit: int = 30) -> list[dict]:
    token = (TP_TOKEN or os.getenv("TP_TOKEN", "")).strip()
    if not token:
        raise RuntimeError(
            "Travelpayouts token is empty. Check TP_TOKEN in GitHub Secrets and workflow env."
        )

    url = "https://api.travelpayouts.com/aviasales/v3/get_latest_prices"
    params = {
        "origin": (ORIGIN or "TLV").strip().upper(),
        "currency": (CURRENCY or "usd").strip().lower(),
        "market": (MARKET or "ru").strip().lower(),
        "limit": limit,
        "show_to_affiliates": "true",
        "token": token,
    }

    try:
        resp = requests.get(url, params=params, timeout=20)
    except requests.RequestException as exc:
        raise RuntimeError(f"Travelpayouts network error: {exc}") from exc

    if not resp.ok:
        raise RuntimeError(f"Travelpayouts HTTP {resp.status_code}: {resp.text}")

    payload = resp.json()
    if not isinstance(payload, dict) or not payload.get("success"):
        raise RuntimeError(f"Travelpayouts API error: {payload}")

    data = payload.get("data", [])
    return data if isinstance(data, list) else []
