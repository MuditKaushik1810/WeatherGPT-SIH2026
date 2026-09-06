"""
Home screen "view model" — composes the three data blocks the Home screen needs
(current conditions + hourly forecast + a recommendation) into ONE response,
all from a single upstream Open-Meteo pull. Backs GET /home/{location}.

Reuses the degradation ladder's fetch + normalize + honest-gap helpers rather
than duplicating them (CLAUDE.md). Same discipline as everywhere else: an
unresolvable location returns a gap-shaped view, never a bare refusal.
"""
from app.connectors import open_meteo
from app.core import cache, degradation_ladder, geocoding, normalize, recommendation


def get_home_view(location_name: str) -> dict:
    """
    Assemble {location, current, hourly, recommendation, data_tier} for the Home
    screen in a single call.

    - current: the normalized weather record (same shape as GET /weather).
    - hourly: next few hours [{time, temp, condition, precipitation_chance}] — [] if unavailable.
    - recommendation: {title, message} derived from `current`, never a bare refusal.
    """
    cache_key = f"home:{location_name.strip().lower()}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    coords = geocoding.resolve_location(location_name)
    if coords is None:
        current = degradation_ladder.unresolved_record(location_name)
        return {
            "location": location_name,
            "current": current,
            "hourly": [],
            "recommendation": recommendation.build_recommendation(current),
            "data_tier": "unresolved_location",
        }

    om_data, imd_data, aq_data = degradation_ladder.fetch_sources(coords, location_name)
    current = normalize.normalize_weather_record(location_name, om_data, imd_data, aq_data)

    view = {
        "location": location_name,
        "current": current,
        "hourly": open_meteo.extract_hourly_forecast(om_data.get("_raw_hourly")),
        "recommendation": recommendation.build_recommendation(current),
        "data_tier": current["data_tier"],
    }

    # Don't cache a transient source outage (mirrors get_weather).
    if current["data_tier"] != "source_unavailable":
        cache.set(cache_key, view)
    return view
