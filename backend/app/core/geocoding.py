"""
Geocoding: resolves a place name to (lat, lon).

Static table first (zero external calls, instant) — falls back to Nominatim
only for places not in the table. See Architecture doc, Section 3.4/3.6.
"""
import json
import os

import requests

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "static_cities.json")

with open(_DATA_PATH) as f:
    _STATIC_CITIES = json.load(f)
    _STATIC_CITIES.pop("_comment", None)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def resolve_location(name: str) -> dict | None:
    key = name.strip().lower()
    if key in _STATIC_CITIES:
        lat, lon = _STATIC_CITIES[key]
        return {"lat": lat, "lon": lon, "resolved_via": "static_table"}
    return _resolve_via_nominatim(name)


def _resolve_via_nominatim(name: str) -> dict | None:
    """
    Fallback only. Nominatim's usage policy caps requests at roughly
    1/second and requires a real, identifying User-Agent — never call this
    in a loop, and never strip the User-Agent header.
    """
    headers = {"User-Agent": "WeatherGPT-SIH2026/0.1 (student hackathon project)"}
    params = {"q": f"{name}, India", "format": "json", "limit": 1}
    try:
        response = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        results = response.json()
        if not results:
            return None
        return {
            "lat": float(results[0]["lat"]),
            "lon": float(results[0]["lon"]),
            "resolved_via": "nominatim",
        }
    except Exception:
        return None
