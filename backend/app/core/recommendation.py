"""
Rule-based "Today's Recommendation" for the Home screen.

A transparent, deterministic suggestion — NO LLM. Priority is safety-first: an
active official warning outranks every comfort factor. Everything is grounded in
the fetched record, never invented.

Two inputs:
  - `record`: the current normalized weather record (temp/aqi/humidity/feels_like
    /wind/precip/warnings).
  - `today`: today's forecast extremes from open_meteo.summarize_today
    (peak_temp/low_temp/peak_feels_like/max_precip_chance/max_wind). The SAFETY
    rules look ahead to these (a 41°C peak later today should say "beat the heat"
    even if it's mild right now); the comfort/default case uses current readings.
    When `today` is absent, safety rules fall back to the current reading.

On the thresholds (all heuristic and tunable):
  - AQI bands follow the US EPA AQI categories (>150 "unhealthy", 101-150
    "unhealthy for sensitive groups") — the scale our AQI source reports.
  - Temperature, feels-like, wind, rain and humidity thresholds are general
    comfort/safety heuristics, deliberately conservative.

This is a GENERAL comfort-level suggestion, not an authoritative advisory. The
sourced/curated advisories (Farmer Advisory — ICAR/GKMS; Disaster Safety — NDMA)
are held to a stricter bar than this.
"""


def build_recommendation(record: dict, today: dict | None = None) -> dict:
    """
    Return a {title, message} suggestion from the current record and today's
    forecast extremes. Never bare-refuses: with no usable data it returns an
    honest "limited data" message rather than nothing.
    """
    today = today or {}

    temp = record.get("temp")
    aqi = record.get("aqi")
    precip = record.get("precipitation_chance")
    humidity = record.get("humidity")
    feels_like = record.get("feels_like")
    warnings = record.get("warnings") or []

    # Safety rules use today's extremes, falling back to the current reading when
    # the forecast series isn't available (e.g. source failed soft).
    peak_temp = _coalesce(today.get("peak_temp"), temp)
    low_temp = _coalesce(today.get("low_temp"), temp)
    peak_feels = _coalesce(today.get("peak_feels_like"), feels_like)
    max_precip = _coalesce(today.get("max_precip_chance"), precip)
    max_wind = _coalesce(today.get("max_wind"), record.get("wind_speed"))

    if warnings:
        return {
            "title": "Stay alert",
            "message": (
                "An official weather warning is active for your area — follow "
                "local advisories and avoid non-essential travel."
            ),
        }

    if temp is None and aqi is None and precip is None:
        return {
            "title": "Limited data right now",
            "message": (
                "Live weather data is temporarily limited for your area — check "
                "back shortly for an updated suggestion."
            ),
        }

    if (peak_temp is not None and peak_temp >= 40) or (peak_feels is not None and peak_feels >= 45):
        return {
            "title": "Beat the heat",
            "message": (
                "It gets very hot today — stay hydrated and avoid direct sun "
                "between noon and 3 PM."
            ),
        }

    if low_temp is not None and low_temp <= 5:
        return {
            "title": "Bundle up",
            "message": "Cold conditions today — dress in warm layers before heading out.",
        }

    if aqi is not None and aqi > 150:
        return {
            "title": "Limit outdoor time",
            "message": (
                f"Air quality is poor (AQI {aqi}) — limit prolonged outdoor "
                "activity, especially if you're sensitive to pollution."
            ),
        }

    if max_wind is not None and max_wind >= 40:
        return {
            "title": "Expect strong winds",
            "message": (
                f"Strong winds are likely today (up to {round(max_wind)} km/h) — "
                "secure loose objects and take care on two-wheelers."
            ),
        }

    if max_precip is not None and max_precip >= 0.6:
        return {
            "title": "Carry an umbrella",
            "message": (
                f"Rain is likely today ({round(max_precip * 100)}% chance) — keep "
                "an umbrella handy if you're heading out."
            ),
        }

    if aqi is not None and aqi > 100:
        return {
            "title": "Sensitive groups, take care",
            "message": (
                f"Air quality is moderate (AQI {aqi}) — fine for most, but "
                "sensitive groups should take it easy outdoors."
            ),
        }

    if humidity is not None and humidity >= 80 and feels_like is not None and feels_like >= 32:
        return {
            "title": "Muggy out",
            "message": (
                f"It's muggy right now ({round(humidity)}% humidity, feels like "
                f"{round(feels_like)}°C) — stay hydrated and take it slow."
            ),
        }

    return {
        "title": "Good time for a short outing",
        "message": (
            "Conditions look comfortable today — a good time to be outdoors. "
            "Keep an eye on the sky if you'll be out a while."
        ),
    }


def _coalesce(preferred, fallback):
    """Return `preferred` unless it's None, in which case `fallback`."""
    return fallback if preferred is None else preferred
