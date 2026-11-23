import os
import requests
from .config import CURRENCY, MARKET, ORIGIN, TP_TOKEN


def _extract_departure(item: dict) -> str:
    for key in ("departure_at", "depart_date", "departure_date"):
        val = item.get(key)
        if val and str(val).strip():
            return str(val).strip()
    return ""


def _extract_return(item: dict) -> str:
    for key in ("return_at", "return_date"):
        val = item.get(key)
        if val and str(val).strip():
            return str(val).strip()
    return ""


def _normalize_flight(item: dict, default_origin: str) -> dict:
    flight = dict(item)
    origin = str(flight.get("origin") or default_origin).strip().upper()
    dest = str(flight.get("destination") or "").strip().upper()
    flight["origin"] = origin
    flight["destination"] = dest

    dep = _extract_departure(flight)
    ret = _extract_return(flight)
    if dep:
        flight["departure_at"] = dep
    if ret:
        flight["return_at"] = ret
    return flight


def _fetch_dates_for_route(
    origin: str,
    destination: str,
    token: str,
    currency: str,
    market: str,
) -> dict | None:
    url = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
    params = {
        "origin": origin,
        "destination": destination,
        "currency": currency,
        "market": market,
        "one_way": "false",
        "sorting": "price",
        "limit": 5,
        "token": token,
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        if not resp.ok:
            return None
        payload = resp.json()
        if not isinstance(payload, dict) or not payload.get("success"):
            return None
        rows = payload.get("data") or []
        if not isinstance(rows, list):
            return None
        for row in rows:
            if not isinstance(row, dict):
                continue
            dep = _extract_departure(row)
            if dep:
                norm = _normalize_flight(row, origin)
                norm["destination"] = destination
                return norm
    except requests.RequestException:
        return None
    return None


def fetch_latest_tlv_prices(
    limit: int = 100,
    max_date_lookups: int = 15,
) -> list[dict]:
    token = (TP_TOKEN or os.getenv("TP_TOKEN", "")).strip()
    if not token:
        raise RuntimeError(
            "Travelpayouts token is empty. Check TP_TOKEN in GitHub Secrets and workflow env."
        )

    origin = (ORIGIN or "TLV").strip().upper()
    currency = (CURRENCY or "usd").strip().lower()
    market = (MARKET or "ru").strip().lower()

    url = "https://api.travelpayouts.com/aviasales/v3/get_latest_prices"
    params = {
        "origin": origin,
        "currency": currency,
        "market": market,
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

    raw_data = payload.get("data", [])
    if not isinstance(raw_data, list):
        return []

    flights: list[dict] = []
    checked_dests: set[str] = set()
    date_lookups_used = 0

    for item in raw_data:
        if not isinstance(item, dict):
            continue
        flight = _normalize_flight(item, origin)
        dest = flight.get("destination") or ""
        dep = _extract_departure(flight)

        if not dep and dest and dest not in checked_dests and date_lookups_used < max_date_lookups:
            checked_dests.add(dest)
            date_lookups_used += 1
            enriched = _fetch_dates_for_route(origin, dest, token, currency, market)
            if enriched:
                # Сохраняем более свежую/низкую цену из get_latest_prices, если она была указана
                if flight.get("value") is not None and enriched.get("value") is None:
                    enriched["value"] = flight["value"]
                if not enriched.get("airline") and flight.get("airline"):
                    enriched["airline"] = flight["airline"]
                flight = enriched

        flights.append(flight)

    return flights
