"""
WeatherAPI.com connector — key-based forecast source (primary).

Why this is the PRIMARY forecast source and Open-Meteo the fallback: Open-Meteo
is keyless and rate-limited per IP, so on a shared deployment IP (e.g. Render's
free tier) it gets 429'd by other tenants' traffic — a source that randomly
fails has no business being primary in production. WeatherAPI authenticates by
API key, so our quota is tied to *us*, not the shared IP. See the Architecture
doc's degradation-ladder section.

Free-plan constraints this connector is deliberately coded to (so nothing breaks
when a trial downgrades to Free): 3-day forecast horizon, hourly data included,
100k calls/month. We only ever need the current hour + the next several hours,
well inside 3 days. Air quality is intentionally NOT taken from here — WeatherAPI
reports a 1-6 category, not the 0-500 US AQI our contract uses; AQI stays on the
Open-Meteo Air Quality connector.

Provenance: WeatherAPI.com asks free-plan users to show a "Powered by
WeatherAPI.com" attribution — surface that wherever this source is displayed.

CRITICAL RULE (same as every connector — CLAUDE.md, "Connectors must fail soft,
always"): never raise up to the degradation ladder. On a missing API key, any
network error, non-2xx response, or unexpected payload, return an "unavailable"
record and let the ladder fall through to Open-Meteo.

Docs: https://www.weatherapi.com/docs/
"""
import logging
import os
from datetime import datetime, timezone

import requests

# Reuse the forecast connector's "which hourly index is now" helper — this
# connector builds `_raw_hourly` in the SAME shape open_meteo produces, so the
# whole hourly toolchain (current_hour_index / extract_hourly_forecast /
# summarize_today) works on it unchanged (CLAUDE.md: reuse, don't duplicate).
from app.connectors.open_meteo import current_hour_index

logger = logging.getLogger(__name__)

WEATHERAPI_URL = "https://api.weatherapi.com/v1/forecast.json"
API_KEY_ENV = "WEATHERAPI_KEY"


def _unavailable_record() -> dict:
    """
    Soft-failure record — mirrors the open_meteo.py fail-soft contract exactly,
    including the `_raw_hourly: None` field, so it is a true drop-in and the
    ladder can fall through to Open-Meteo without special-casing.
    """
    return {
        "temp": None,
        "humidity": None,
        "feels_like": None,
        "wind_speed": None,
        "precipitation_chance": None,
        "condition": None,
        "source": "WeatherAPI",
        "data_tier": "unavailable",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "_raw_hourly": None,
    }


def _to_raw_hourly(forecastdays: list[dict]) -> dict:
    """
    Flatten WeatherAPI's per-day `hour[]` arrays into the Open-Meteo `_raw_hourly`
    shape so the shared hourly helpers work verbatim.

    Two translations matter:
      - time: WeatherAPI uses "YYYY-MM-DD HH:MM" (space); Open-Meteo/our helpers
        expect "YYYY-MM-DDTHH:MM" (the 'T' is what current_hour_index matches on).
      - condition: WeatherAPI gives human-readable text directly, carried in a
        `condition_text` array (extract_hourly_forecast prefers it over the WMO
        `weathercode` map, which this source doesn't use).
    """
    hours = [h for fd in forecastdays for h in fd.get("hour", [])]
    return {
        "time": [str(h.get("time", "")).replace(" ", "T")[:16] for h in hours],
        "temperature_2m": [h.get("temp_c") for h in hours],
        "apparent_temperature": [h.get("feelslike_c") for h in hours],
        "relative_humidity_2m": [h.get("humidity") for h in hours],
        "wind_speed_10m": [h.get("wind_kph") for h in hours],
        "precipitation_probability": [h.get("chance_of_rain") for h in hours],
        "condition_text": [(h.get("condition") or {}).get("text") for h in hours],
    }


def fetch_forecast(lat: float, lon: float, timezone_name: str = "Asia/Kolkata", now=None) -> dict:
    """
    Fetch current + short-range hourly forecast for a coordinate from WeatherAPI.

    Returns the exact same record shape as open_meteo.fetch_forecast (a drop-in),
    reading the current-hour values from the hourly series at the actual current
    local hour — not element 0, which is 00:00 (the midnight-anchoring trap the
    Open-Meteo connector documents).

    Fails soft: returns an "unavailable" record on a missing key, network error,
    non-2xx response, or unexpected payload — never raises. `now` is injectable
    for deterministic tests.
    """
    api_key = os.environ.get(API_KEY_ENV)
    if not api_key:
        # Expected before the key is provisioned — the ladder falls through to
        # Open-Meteo. Debug (not warning) so it isn't per-request noise.
        logger.debug("%s not set; skipping WeatherAPI, ladder falls back to Open-Meteo", API_KEY_ENV)
        return _unavailable_record()

    params = {
        "key": api_key,
        "q": f"{lat},{lon}",
        "days": 3,          # today + 2 (free-plan max): covers "tomorrow"/"this week" chat queries
        "aqi": "no",        # AQI comes from Open-Meteo (0-500 US scale); see module docstring
        "alerts": "no",
    }
    try:
        response = requests.get(WEATHERAPI_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        forecastdays = data["forecast"]["forecastday"]
        raw_hourly = _to_raw_hourly(forecastdays)

        times = raw_hourly["time"]
        i = current_hour_index(times, timezone_name, now)

        precip_raw = raw_hourly["precipitation_probability"][i]
        precip_chance = precip_raw / 100 if precip_raw is not None else None

        return {
            "temp": raw_hourly["temperature_2m"][i],
            "humidity": raw_hourly["relative_humidity_2m"][i],
            "feels_like": raw_hourly["apparent_temperature"][i],
            "wind_speed": raw_hourly["wind_speed_10m"][i],
            "precipitation_chance": precip_chance,
            "condition": raw_hourly["condition_text"][i],
            "source": "WeatherAPI",
            "data_tier": "exact",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "_raw_hourly": raw_hourly,
        }
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "?"
        body = exc.response.text[:300] if exc.response is not None else ""
        logger.warning("WeatherAPI forecast HTTP %s for (%s, %s): %s", status, lat, lon, body)
        return _unavailable_record()
    except Exception as exc:
        logger.warning("WeatherAPI forecast failed for (%s, %s): %r", lat, lon, exc)
        return _unavailable_record()
