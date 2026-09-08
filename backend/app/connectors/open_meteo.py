"""
Open-Meteo connector — free, no API key required, grid-based forecast data.
Docs: https://open-meteo.com/en/docs

Grid-based means this always returns a value for any Indian coordinate — there
is no "no data for this village" case here (see Architecture doc, Section 3.4).
"""
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests

logger = logging.getLogger(__name__)

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


def current_hour_index(times: list[str], timezone_name: str = "Asia/Kolkata", now=None) -> int:
    """
    Index of the current local hour within Open-Meteo's hourly `time` array.

    Open-Meteo returns the hourly series starting at 00:00 of the local day, so
    element 0 is MIDNIGHT, not "now". This finds the entry matching the current
    hour (floored) in `timezone_name`. Falls back to 0 if `times` is empty or the
    current hour isn't present — which shouldn't happen for a live forecast,
    since it always includes every hour of today.

    `now` is injectable for deterministic tests; defaults to the real current time.
    """
    if not times:
        return 0
    if now is None:
        now = datetime.now(ZoneInfo(timezone_name))
    target = now.strftime("%Y-%m-%dT%H:00")
    try:
        return times.index(target)
    except ValueError:
        return 0


def extract_hourly_forecast(raw_hourly: dict | None, hours: int = 8, start: int = 0) -> list[dict]:
    """
    Turn Open-Meteo's raw hourly arrays (the `_raw_hourly` kept on fetch_forecast's
    result) into a clean forecast list of `hours` entries starting at index
    `start` (the caller passes the current-hour index so the strip begins at
    "now", not midnight).

    Lives here because this module owns the raw hourly shape and the
    WEATHER_CODE_MAP. Returns [] if raw_hourly is missing (source failed soft),
    so callers never crash on an outage — same fail-soft principle as everywhere.
    """
    if not raw_hourly:
        return []

    times = raw_hourly.get("time", [])
    temps = raw_hourly.get("temperature_2m", [])
    codes = raw_hourly.get("weathercode", [])
    precs = raw_hourly.get("precipitation_probability", [])

    forecast = []
    for i in range(start, min(start + hours, len(times))):
        precip = precs[i] if i < len(precs) else None
        forecast.append({
            "time": times[i],
            "temp": temps[i] if i < len(temps) else None,
            "condition": (
                WEATHER_CODE_MAP.get(codes[i], "unknown") if i < len(codes) else "unknown"
            ),
            "precipitation_chance": precip / 100 if precip is not None else None,
        })
    return forecast


def summarize_today(raw_hourly: dict | None) -> dict:
    """
    Compute today's forecast extremes from Open-Meteo's raw hourly arrays, over
    the hours that share the calendar date of the first entry (Open-Meteo returns
    the hourly series in local time starting at 00:00, so this is "calendar
    today"). The recommendation engine uses these so safety advice can look
    ahead to the day's peak, not just the current hour.

    Returns {peak_temp, low_temp, peak_feels_like, max_precip_chance, max_wind},
    each None when its series is missing. All-None when raw_hourly is missing
    (source failed soft) — never raises.
    """
    empty = {
        "peak_temp": None,
        "low_temp": None,
        "peak_feels_like": None,
        "max_precip_chance": None,
        "max_wind": None,
    }
    if not raw_hourly:
        return empty

    times = raw_hourly.get("time", [])
    if not times:
        return empty

    today = times[0][:10]  # calendar date of the first entry (YYYY-MM-DD)
    temp_arr = raw_hourly.get("temperature_2m", [])
    feels_arr = raw_hourly.get("apparent_temperature", [])
    prec_arr = raw_hourly.get("precipitation_probability", [])
    wind_arr = raw_hourly.get("wind_speed_10m", [])

    temps, feels, precs, winds = [], [], [], []
    for i, when in enumerate(times):
        if when[:10] != today:
            break  # series is chronological; once past today, stop
        if i < len(temp_arr) and temp_arr[i] is not None:
            temps.append(temp_arr[i])
        if i < len(feels_arr) and feels_arr[i] is not None:
            feels.append(feels_arr[i])
        if i < len(prec_arr) and prec_arr[i] is not None:
            precs.append(prec_arr[i])
        if i < len(wind_arr) and wind_arr[i] is not None:
            winds.append(wind_arr[i])

    return {
        "peak_temp": max(temps) if temps else None,
        "low_temp": min(temps) if temps else None,
        "peak_feels_like": max(feels) if feels else None,
        "max_precip_chance": max(precs) / 100 if precs else None,
        "max_wind": max(winds) if winds else None,
    }


def _unavailable_record() -> dict:
    """
    Soft-failure record: the source could not be reached or parsed.

    Mirrors the imd.py fail-soft contract exactly — a connector NEVER raises
    up to the degradation ladder (CLAUDE.md, "Connectors must fail soft,
    always"). data_tier="unavailable" tells the normalizer/ladder to degrade
    to the next tier instead of crashing the whole pipeline over one dead
    source.
    """
    return {
        "temp": None,
        "humidity": None,
        "feels_like": None,
        "wind_speed": None,
        "precipitation_chance": None,
        "condition": None,
        "source": "Open-Meteo",
        "data_tier": "unavailable",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "_raw_hourly": None,
    }


def fetch_forecast(lat: float, lon: float, timezone_name: str = "Asia/Kolkata", now=None) -> dict:
    """
    Fetch current + 7-day hourly forecast for a coordinate.

    Fails soft: on any network error, non-2xx response, or unexpected payload
    shape, returns an "unavailable" record (see _unavailable_record) rather
    than raising — the degradation ladder depends on this never crashing.

    IMPORTANT: always pass timezone explicitly. Open-Meteo does not
    auto-detect local timezone from coordinates — it defaults to whatever was
    last configured, which is exactly the "Asia/Singapore for Delhi
    coordinates" bug documented in the Architecture doc. Never rely on the
    default.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation_probability,weathercode,wind_speed_10m",
        "timezone": timezone_name,
        "forecast_days": 7,
    }
    try:
        response = requests.get(OPEN_METEO_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        hourly = data["hourly"]
        # Open-Meteo's hourly starts at 00:00 local, so index 0 is midnight, not
        # "now" — pick the entry for the actual current hour.
        now_index = current_hour_index(hourly.get("time", []), timezone_name, now)
        weather_code = hourly["weathercode"][now_index]

        # precipitation_probability is nullable in Open-Meteo's hourly series;
        # a missing value must not cost us the whole (otherwise valid) record.
        precip_raw = hourly["precipitation_probability"][now_index]
        precip_chance = precip_raw / 100 if precip_raw is not None else None

        return {
            "temp": hourly["temperature_2m"][now_index],
            "humidity": hourly["relative_humidity_2m"][now_index],
            "feels_like": hourly["apparent_temperature"][now_index],
            "wind_speed": hourly["wind_speed_10m"][now_index],
            "precipitation_chance": precip_chance,
            "condition": WEATHER_CODE_MAP.get(weather_code, "unknown"),
            "source": "Open-Meteo",
            "data_tier": "exact",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            # Full hourly series kept for callers that need more than the
            # current hour (e.g. the Trip Planner, or the Disease Suitability
            # Model's 24h rolling average) — not part of the normalized shape.
            "_raw_hourly": hourly,
        }
    except requests.HTTPError as exc:
        # Non-2xx (e.g. a 429 rate-limit). Surface the status + Open-Meteo's
        # reason body so a production outage is diagnosable instead of silent,
        # then still fail soft — degrade the ladder, never crash it.
        status = exc.response.status_code if exc.response is not None else "?"
        body = exc.response.text[:300] if exc.response is not None else ""
        logger.warning("Open-Meteo forecast HTTP %s for (%s, %s): %s", status, lat, lon, body)
        return _unavailable_record()
    except Exception as exc:
        # Any other failure (network down, timeout, changed JSON shape). Log the
        # reason, then fail soft — a dead source degrades the ladder, never
        # crashes it. See docstring.
        logger.warning("Open-Meteo forecast failed for (%s, %s): %r", lat, lon, exc)
        return _unavailable_record()
