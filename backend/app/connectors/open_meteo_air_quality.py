"""
Open-Meteo Air Quality connector — free, no API key required, grid-based AQI.
Docs: https://open-meteo.com/en/docs/air-quality-api

This is a SEPARATE API from the forecast connector (different host,
air-quality-api.open-meteo.com). AQI can't be obtained by adding a field to the
forecast params — it needs its own call, which is why it lives in its own
connector rather than inside open_meteo.py.

Provenance note: this returns the **US AQI** scale (`us_aqi`), NOT India's CPCB
AQI — Open-Meteo does not publish the CPCB scale. The `source` is labelled
"Open-Meteo Air Quality" and the US-scale caveat is documented here so the UI's
provenance story stays honest (Architecture doc, Sections 2.1 / 3.3). If a real
CPCB-scale source is wired in later, swap it here and keep this return shape.

CRITICAL RULE (same as every connector — CLAUDE.md, "Connectors must fail soft,
always"): never raise up to the degradation ladder. On any network error,
non-2xx response, or unexpected payload, return an "unavailable" record with
aqi=None and let the ladder carry on.
"""
from datetime import datetime, timezone

import requests

# Reuse the forecast connector's "which hourly index is now" helper — both APIs
# return their hourly series starting at 00:00 local, so index 0 is midnight.
from app.connectors.open_meteo import current_hour_index

AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


def _unavailable_record() -> dict:
    """
    Soft-failure record — mirrors the open_meteo.py / imd.py fail-soft contract.
    aqi=None tells the normalizer there's simply no AQI to show, never a crash.
    """
    return {
        "aqi": None,
        "source": "Open-Meteo Air Quality",
        "data_tier": "unavailable",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def fetch_air_quality(lat: float, lon: float, timezone_name: str = "Asia/Kolkata", now=None) -> dict:
    """
    Fetch the current US AQI for a coordinate.

    Fails soft: returns an "unavailable" record (aqi=None) on any network error,
    non-2xx response, or unexpected payload rather than raising — the
    degradation ladder depends on this never crashing.

    Returns:
        {
          "aqi": int | None,                  # US AQI scale (not India CPCB)
          "source": "Open-Meteo Air Quality",
          "data_tier": "exact" | "unavailable",
          "fetched_at": iso timestamp string,
        }
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "us_aqi",
        "timezone": timezone_name,
        "forecast_days": 1,
    }
    try:
        response = requests.get(AIR_QUALITY_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        hourly = data["hourly"]
        # index 0 is 00:00 local, not "now" — read the actual current hour.
        now_index = current_hour_index(hourly.get("time", []), timezone_name, now)
        aqi = hourly["us_aqi"][now_index]
        return {
            "aqi": aqi,
            "source": "Open-Meteo Air Quality",
            "data_tier": "exact" if aqi is not None else "unavailable",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception:
        # Fail soft, always. See module docstring.
        return _unavailable_record()
