"""
Rule-based "Today's Recommendation" for the Home screen.

A transparent, deterministic suggestion derived from the current weather record
— NO LLM. Priority is safety-first: an active official warning outranks every
comfort factor. Everything is grounded in the fetched record, never invented.

On the thresholds:
  - The AQI bands follow the US EPA AQI categories (>150 "unhealthy",
    101-150 "unhealthy for sensitive groups"), which is the scale our AQI
    source (Open-Meteo `us_aqi`) reports.
  - The temperature and rain thresholds are general comfort heuristics, tunable,
    and deliberately conservative.

This is a GENERAL comfort-level suggestion, not an authoritative advisory. The
sourced/curated advisories in this product are the Farmer Advisory (ICAR/GKMS)
and Disaster Safety (NDMA) features — those are held to a stricter bar than this.
"""


def build_recommendation(record: dict) -> dict:
    """
    Return a {title, message} suggestion derived from a normalized weather record.

    Never bare-refuses: if the record has no usable data (source unavailable),
    it returns an honest "limited data" message rather than nothing.
    """
    temp = record.get("temp")
    aqi = record.get("aqi")
    precip = record.get("precipitation_chance")
    warnings = record.get("warnings") or []

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

    if temp is not None and temp >= 40:
        return {
            "title": "Beat the heat",
            "message": (
                "It's very hot — stay hydrated and avoid direct sun between "
                "noon and 3 PM."
            ),
        }

    if temp is not None and temp <= 5:
        return {
            "title": "Bundle up",
            "message": "Cold conditions — dress in warm layers before heading out.",
        }

    if aqi is not None and aqi > 150:
        return {
            "title": "Limit outdoor time",
            "message": (
                f"Air quality is poor (AQI {aqi}) — limit prolonged outdoor "
                "activity, especially if you're sensitive to pollution."
            ),
        }

    if precip is not None and precip >= 0.6:
        return {
            "title": "Carry an umbrella",
            "message": (
                f"Rain is likely ({round(precip * 100)}% chance) — keep an "
                "umbrella handy if you're heading out."
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

    return {
        "title": "Good time for a short outing",
        "message": (
            "Conditions look comfortable right now — a good time to be outdoors. "
            "Keep an eye on the sky if you'll be out a while."
        ),
    }
