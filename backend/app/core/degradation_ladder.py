"""
The degradation ladder — Architecture doc, Section 3.4.

Never returns a bare "insufficient data" result. Steps through tiers until
something usable is found, and every result is tagged with data_tier so the
grounding assembler (Sprint 2) and every UI provenance chip know exactly how
confident/specific the answer is.
"""
from app.connectors import imd, open_meteo, open_meteo_air_quality
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
            "humidity": None,
            "feels_like": None,
            "wind_speed": None,
            "aqi": None,
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
    aq_data = open_meteo_air_quality.fetch_air_quality(coords["lat"], coords["lon"])

    result = normalize.normalize_weather_record(location_name, om_data, imd_data, aq_data)

    # Don't cache a transient source outage — otherwise a brief Open-Meteo blip
    # gets served stale for the full TTL even after the source recovers. (Same
    # reason the unresolved_location gap above is returned without caching.)
    if result["data_tier"] != "source_unavailable":
        cache.set(cache_key, result)
    return result
