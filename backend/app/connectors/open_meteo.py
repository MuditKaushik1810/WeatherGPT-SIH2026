"""
Open-Meteo connector — free, no API key required, grid-based forecast data.
Docs: https://open-meteo.com/en/docs

Grid-based means this always returns a value for any Indian coordinate — there
is no "no data for this village" case here (see Architecture doc, Section 3.4).
"""
from datetime import datetime, timezone

import requests

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather codes -> human-readable condition. Open-Meteo uses the standard
# WMO code set; this covers the common ones, extend as needed.
WEATHER_CODE_MAP = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "depositing rime fog",
    51: "light drizzle", 53: "moderate drizzle", 55: "dense drizzle",
    61: "slight rain", 63: "moderate rain", 65: "heavy rain",
    71: "slight snow", 73: "moderate snow", 75: "heavy snow",
    80: "slight rain showers", 81: "moderate rain showers", 82: "violent rain showers",
    95: "thunderstorm", 96: "thunderstorm with slight hail", 99: "thunderstorm with heavy hail",
}


def fetch_forecast(lat: float, lon: float, timezone_name: str = "Asia/Kolkata") -> dict:
    """
    Fetch current + 7-day hourly forecast for a coordinate.

    IMPORTANT: always pass timezone explicitly. Open-Meteo does not
    auto-detect local timezone from coordinates — it defaults to whatever was
    last configured, which is exactly the "Asia/Singapore for Delhi
    coordinates" bug documented in the Architecture doc. Never rely on the
    default.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,weathercode",
        "timezone": timezone_name,
        "forecast_days": 7,
    }
    response = requests.get(OPEN_METEO_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    hourly = data["hourly"]
    now_index = 0  # first hourly entry is the nearest hour to "now"
    weather_code = hourly["weathercode"][now_index]

    return {
        "temp": hourly["temperature_2m"][now_index],
        "humidity": hourly["relative_humidity_2m"][now_index],
        "precipitation_chance": hourly["precipitation_probability"][now_index] / 100,
        "condition": WEATHER_CODE_MAP.get(weather_code, "unknown"),
        "source": "Open-Meteo",
        "data_tier": "exact",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        # Full hourly series kept for callers that need more than the current
        # hour (e.g. the Trip Planner, or the Disease Suitability Model's
        # 24h rolling average) — not part of the normalized shape itself.
        "_raw_hourly": hourly,
    }
