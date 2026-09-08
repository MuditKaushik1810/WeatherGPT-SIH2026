"""
The degradation ladder — Architecture doc, Section 3.4.

Never returns a bare "insufficient data" result. Steps through tiers until
something usable is found, and every result is tagged with data_tier so the
grounding assembler (Sprint 2) and every UI provenance chip know exactly how
confident/specific the answer is.

`unresolved_record` and `fetch_sources` are factored out so other assemblers
(e.g. the Home view) reuse the exact same fetch + honest-gap behaviour instead
of duplicating it (CLAUDE.md: never duplicate logic — extend or import).
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from app.connectors import imd, open_meteo, open_meteo_air_quality, weatherapi
from app.core import cache, geocoding, historical, normalize


def unresolved_record(location_name: str) -> dict:
    """
    Honest gap record for a location we couldn't geocode — paired with guidance,
    never a bare refusal. Shape matches the normalized record (all metrics None).
    """
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


def fetch_forecast_with_fallback(coords: dict) -> dict:
    """
    Get a forecast record from the primary source, falling back to the secondary
    if the primary is unavailable — the live half of the degradation ladder.

    Primary is WeatherAPI (key-based, so it isn't at the mercy of a shared-IP
    rate limit); Open-Meteo (keyless, richer horizon, but 429-prone on a shared
    IP) is the fallback. Both return the identical record shape, so the caller
    can't tell which answered except via the `source` field. Both fail soft, so
    if BOTH are down this returns an "unavailable" record for the ladder to
    degrade further (→ historical_baseline).
    """
    primary = weatherapi.fetch_forecast(coords["lat"], coords["lon"])
    if primary["data_tier"] != "unavailable":
        return primary
    return open_meteo.fetch_forecast(coords["lat"], coords["lon"])


def fetch_sources(coords: dict, location_name: str) -> tuple[dict, dict, dict]:
    """
    Fetch every live connector for an already-resolved location. Connectors fail
    soft (CLAUDE.md), so this never raises — callers get "unavailable" records
    to degrade on instead of an exception.
    """
    forecast_data = fetch_forecast_with_fallback(coords)
    imd_data = imd.fetch_warnings(location_name)
    aq_data = open_meteo_air_quality.fetch_air_quality(coords["lat"], coords["lon"])
    return forecast_data, imd_data, aq_data


def apply_historical_fallback(record: dict, location_name: str, now: datetime | None = None) -> dict:
    """
    The `historical_baseline` rung of the ladder (Architecture doc §3.4).

    When every live forecast source is down (`source_unavailable`), fall back to
    the preloaded historical baseline for this date — the *typical* temperature
    for this day-of-year — rather than showing a null. This is the ladder's whole
    point: never a bare gap when a grounded alternative exists.

    Returns the record unchanged for any other tier, when the location has no
    preloaded baseline, or when the baseline has no value for today (stays
    honest instead of inventing one). The historical temp replaces `temp`; any
    live AQI and active warnings already on the record are preserved, and the
    tier/source/message are re-tagged so provenance stays truthful.

    `now` is injectable for deterministic tests; defaults to the real IST date.
    """
    if record["data_tier"] != "source_unavailable":
        return record

    baseline = historical.get_baseline(location_name)
    if baseline is None:
        return record

    if now is None:
        now = datetime.now(ZoneInfo("Asia/Kolkata"))
    doy = now.timetuple().tm_yday  # 1..366
    clim_temp = baseline.get("clim_temp") or []
    normal_temp = clim_temp[doy - 1] if 0 < doy <= len(clim_temp) else None
    if normal_temp is None:
        return record  # no usable baseline for today — stay honest

    upgraded = dict(record)
    upgraded["temp"] = normal_temp
    upgraded["source"] = "Historical"
    upgraded["data_tier"] = "historical_baseline"
    upgraded["message"] = (
        f"Live forecast for '{location_name}' is temporarily unavailable, so this "
        f"shows the typical temperature for this date (≈{normal_temp}°C, 10-year "
        "average). Any official warnings and air quality shown are current."
    )
    return upgraded


def get_weather(location_name: str) -> dict:
    """Return the normalized current-conditions record for a location."""
    cache_key = f"weather:{location_name.strip().lower()}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    coords = geocoding.resolve_location(location_name)
    if coords is None:
        return unresolved_record(location_name)

    om_data, imd_data, aq_data = fetch_sources(coords, location_name)
    result = normalize.normalize_weather_record(location_name, om_data, imd_data, aq_data)
    result = apply_historical_fallback(result, location_name)

    # Cache only settled *live* tiers. A "live is down" state — source_unavailable
    # or a historical_baseline fallback — is deliberately NOT cached, so the moment
    # the live source recovers the next request serves it instead of a stale gap
    # or baseline. (Same reason the unresolved_location gap above isn't cached.)
    if result["data_tier"] in ("exact", "regional_fallback"):
        cache.set(cache_key, result)
    return result
