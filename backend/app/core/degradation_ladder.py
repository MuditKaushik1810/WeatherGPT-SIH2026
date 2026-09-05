"""
The degradation ladder — Architecture doc, Section 3.4.

Never returns a bare "insufficient data" result. Steps through tiers until
something usable is found, and every result is tagged with data_tier so the
grounding assembler (Sprint 2) and every UI provenance chip know exactly how
confident/specific the answer is.
"""
from app.connectors import imd, open_meteo
from app.core import cache, geocoding, normalize


def get_weather(location_name: str) -> dict:
    cache_key = f"weather:{location_name.strip().lower()}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    coords = geocoding.resolve_location(location_name)
    if coords is None:
        # Honest gap — still paired with guidance, never a bare refusal.
        return {
            "location": location_name,
            "temp": None,
            "condition": None,
            "precipitation_chance": None,
            "warnings": [],
            "source": None,
            "data_tier": "unresolved_location",
            "fetched_at": None,
            "message": (
                f"Could not resolve '{location_name}' to a location. "
                "Try a nearby major city or district name."
            ),
        }

    om_data = open_meteo.fetch_forecast(coords["lat"], coords["lon"])
    imd_data = imd.fetch_warnings(location_name)

    result = normalize.normalize_weather_record(location_name, om_data, imd_data)
    cache.set(cache_key, result)
    return result
