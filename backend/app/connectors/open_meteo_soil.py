"""
Open-Meteo soil-moisture connector — free, no API key, grid-based.
Docs: https://open-meteo.com/en/docs (hourly `soil_moisture_3_to_9cm`)

Soil moisture is an input to the Farmer Crop Risk Index (Architecture §3.7). It
comes from Open-Meteo specifically because WeatherAPI (our primary forecast
source) does not report it — so, like AQI, it is a SEPARATE best-effort call.

UNITS: Open-Meteo returns **volumetric water content (m³/m³)**, roughly 0.05–0.45
for real soils (wilting point ~0.12, field capacity ~0.30–0.40 for loam). The crop
rule table's `soil_moisture_opt` bands are expressed in these same volumetric units
— NOT a 0–1 "fraction of capacity" scale — so the two are directly comparable.

We use the **3–9 cm** layer (shallow root zone) and average it over the day, since
crop stress builds from sustained moisture, not one instant (§3.7).

CRITICAL RULE (CLAUDE.md, "Connectors must fail soft, always"): never raise up to
the risk model. On any error, return soil_moisture=None and let the model
renormalize its weights over the parameters it does have.
"""
import logging
from datetime import datetime, timezone

import requests

from app.connectors.open_meteo import OPEN_METEO_URL

logger = logging.getLogger(__name__)

_SOIL_LAYER = "soil_moisture_3_to_9cm"


def _unavailable_record() -> dict:
    """Soft-failure record — soil_moisture=None tells the model to skip this term."""
    return {
        "soil_moisture": None,
        "source": "Open-Meteo",
        "data_tier": "unavailable",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def fetch_soil_moisture(lat: float, lon: float, timezone_name: str = "Asia/Kolkata") -> dict:
    """
    Fetch the day-averaged shallow-root-zone soil moisture (volumetric m³/m³) for a
    coordinate. Fails soft: returns soil_moisture=None on any network error, non-2xx
    response, or unexpected/empty payload rather than raising.

    Returns:
        {
          "soil_moisture": float | None,   # volumetric water content, m³/m³
          "source": "Open-Meteo",
          "data_tier": "exact" | "unavailable",
          "fetched_at": iso timestamp string,
        }
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": _SOIL_LAYER,
        "timezone": timezone_name,
        "forecast_days": 1,
    }
    try:
        response = requests.get(OPEN_METEO_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        values = [v for v in data["hourly"][_SOIL_LAYER] if v is not None]
        if not values:
            return _unavailable_record()
        mean = round(sum(values) / len(values), 3)
        return {
            "soil_moisture": mean,
            "source": "Open-Meteo",
            "data_tier": "exact",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "?"
        body = exc.response.text[:300] if exc.response is not None else ""
        logger.warning("Open-Meteo soil-moisture HTTP %s for (%s, %s): %s", status, lat, lon, body)
        return _unavailable_record()
    except Exception as exc:
        logger.warning("Open-Meteo soil-moisture failed for (%s, %s): %r", lat, lon, exc)
        return _unavailable_record()
