"""
Trip Planner — route-aware stop planner (Architecture doc §3.10, Feature 9).

Pipeline (all fail-soft, never a bare refusal — CLAUDE.md):
  1. Resolve origin + destination with OUR geocoding (static table → Nominatim).
  2. Route between them via Geoapify (distance, time, geometry, road name).
  3. Sample the route geometry into a handful of checkpoints at even distance
     fractions; reverse-geocode each to a settlement name.
  4. For each checkpoint, pull the forecast at its ETA from OUR degradation-ladder
     pipeline (WeatherAPI → Open-Meteo), and rate the stop good / caution /
     not_recommended from rain + temperature.
  5. Attach nearby facilities per checkpoint (Geoapify Places).
  6. Assemble the §3.10 composite shape. Provenance is SPLIT — weather_source
     (our forecast pipeline) vs routing_source (Geoapify) — never collapsed.

Departures are scoped near-term: ETAs are looked up in the live hourly forecast,
which reaches ~3 days (WeatherAPI) to ~7 days (Open-Meteo). A checkpoint whose
ETA falls beyond the fetched horizon, or whose source is down, gets null metrics
and a "caution" status with an honest note — the stop still renders.
"""
import logging
from datetime import datetime, timedelta
from math import asin, cos, radians, sin, sqrt
from zoneinfo import ZoneInfo

from app.connectors import geoapify, open_meteo
from app.core import degradation_ladder, geocoding

logger = logging.getLogger(__name__)

_IST = ZoneInfo("Asia/Kolkata")
# Endpoints + interior samples. 6 total keeps external calls bounded (each
# checkpoint costs one forecast + one reverse-geocode + one places lookup) while
# giving a useful picture of the route.
_CHECKPOINT_COUNT = 6
_FACILITY_DISPLAY_CAP = 20  # counts at/above this render as "20+" (matches the UI)

# Stop-rating thresholds from rain probability (%) and temperature (°C).
_RAIN_NOT_RECOMMENDED = 60
_RAIN_CAUTION = 30
_TEMP_HOT_NOT_RECOMMENDED = 45
_TEMP_HOT_CAUTION = 40
_TEMP_COLD_CAUTION = 7


def get_trip_plan(origin: str, destination: str, departure: datetime | None = None,
                  now: datetime | None = None) -> dict:
    """
    Build the route-aware trip plan for `origin` → `destination`.

    `departure` is when the journey starts (IST); defaults to the next whole hour
    from `now`. `now` is injectable for deterministic tests. Returns the §3.10
    trip-plan shape; never raises.
    """
    now = now or datetime.now(_IST)
    departure = departure or _next_whole_hour(now)

    from_coords = geocoding.resolve_location(origin)
    to_coords = geocoding.resolve_location(destination)
    if from_coords is None or to_coords is None:
        missing = origin if from_coords is None else destination
        return _unresolved(origin, destination, departure, missing)

    routed = geoapify.route(from_coords, to_coords)
    if not routed["ok"] or not routed["geometry"]:
        return _routing_unavailable(origin, destination, departure)

    total_km = (routed["distance_m"] or 0) / 1000.0
    total_time_s = routed["time_s"] or 0

    samples = _sample_checkpoints(routed["geometry"], _CHECKPOINT_COUNT)
    checkpoints = []
    sources_seen: list[str] = []
    used_ids: set[str] = set()
    for index, (lat, lon, fraction) in enumerate(samples):
        eta = departure + timedelta(seconds=total_time_s * fraction)
        name = geoapify.reverse_geocode(lat, lon) or f"Stop {index + 1}"
        forecast = _forecast_at_eta({"lat": lat, "lon": lon}, eta, now)
        if forecast["source"]:
            sources_seen.append(forecast["source"])
        status, note = _rate_stop(forecast["temperature"], forecast["rain_probability"],
                                  is_origin=index == 0,
                                  is_destination=index == len(samples) - 1,
                                  forecast_available=forecast["available"])
        checkpoints.append({
            "id": _unique_slug(name, index, used_ids),
            "name": name,
            "distance_km": round(total_km * fraction),
            "eta": _format_time(eta),
            "temperature": forecast["temperature"],
            "weather": forecast["weather"],
            "rain_probability": forecast["rain_probability"],
            "status": status,
            "note": note,
            "facilities": _facilities_display(geoapify.facilities(lat, lon)),
        })

    weather_source = _dominant(sources_seen) or "Unavailable"
    data_tier = _trip_data_tier(checkpoints)
    condition = _route_condition(checkpoints)
    return {
        "route": {
            "from": origin.strip(),
            "to": destination.strip(),
            "distance_km": round(total_km),
            "estimated_time": _format_duration(total_time_s),
            "route_name": routed["route_name"],
            "condition": condition,
        },
        "departure": {"label": _day_label(departure, now), "time": _format_time(departure)},
        "checkpoints": checkpoints,
        "summary": _summary(origin, destination, condition, checkpoints),
        "weather_source": weather_source,
        "routing_source": "Geoapify",
        "data_tier": data_tier,
        "fetched_at": now.isoformat(),
    }


# --- forecast at a checkpoint's ETA --------------------------------------------

def _forecast_at_eta(coords: dict, eta: datetime, now: datetime) -> dict:
    """
    Forecast for a coordinate at a specific ETA, from our degradation-ladder
    pipeline. Finds the hourly entry matching the ETA hour (IST). Returns
    {temperature, weather, rain_probability (%), source, available}. `available`
    is False when the source is down or the ETA is beyond the fetched horizon —
    the caller turns that into a cautious, honestly-noted stop.
    """
    record = degradation_ladder.fetch_forecast_with_fallback(coords)
    raw = record.get("_raw_hourly")
    source = record.get("source")
    if not raw:
        return {"temperature": None, "weather": None, "rain_probability": None,
                "source": source, "available": False}

    times = raw.get("time", [])
    target = eta.strftime("%Y-%m-%dT%H:00")
    try:
        i = times.index(target)
    except ValueError:
        return {"temperature": None, "weather": None, "rain_probability": None,
                "source": source, "available": False}

    temps = raw.get("temperature_2m", [])
    precs = raw.get("precipitation_probability", [])
    texts = raw.get("condition_text", [])
    codes = raw.get("weathercode", [])

    temp = round(temps[i]) if i < len(temps) and temps[i] is not None else None
    precip = precs[i] if i < len(precs) and precs[i] is not None else None
    if i < len(texts) and texts[i] is not None:
        weather = texts[i]
    elif i < len(codes):
        weather = open_meteo.WEATHER_CODE_MAP.get(codes[i], "unknown")
    else:
        weather = None
    return {
        "temperature": temp,
        "weather": weather,
        "rain_probability": int(precip) if precip is not None else None,
        "source": source,
        "available": True,
    }


# --- stop rating ---------------------------------------------------------------

def _rate_stop(temp, rain, is_origin: bool, is_destination: bool,
               forecast_available: bool) -> tuple[str, str]:
    """Rate a stop good | caution | not_recommended from rain % + temp °C, with a note."""
    if not forecast_available:
        return "caution", "Forecast unavailable for this stop — check conditions before you go."

    rain = rain if rain is not None else 0
    if rain >= _RAIN_NOT_RECOMMENDED or (temp is not None and temp >= _TEMP_HOT_NOT_RECOMMENDED):
        return "not_recommended", (
            f"High rain probability ({rain}%). Consider delaying this stop."
            if rain >= _RAIN_NOT_RECOMMENDED
            else f"Extreme heat ({temp}°C) expected. Avoid a long stop here."
        )
    if rain >= _RAIN_CAUTION or (temp is not None and (temp >= _TEMP_HOT_CAUTION or temp <= _TEMP_COLD_CAUTION)):
        if rain >= _RAIN_CAUTION:
            return "caution", f"Rain is possible ({rain}%). Use caution around this checkpoint."
        return "caution", f"Temperature around {temp}°C — plan the stop accordingly."

    where = "begin the journey" if is_origin else "at the destination" if is_destination else "around this checkpoint"
    return "good", f"Good conditions {where}."


# --- geometry sampling ---------------------------------------------------------

def _sample_checkpoints(geometry: list[list[float]], count: int) -> list[tuple[float, float, float]]:
    """
    Pick `count` checkpoints along the polyline at even cumulative-distance
    fractions (0.0 = origin … 1.0 = destination). Returns (lat, lon, fraction) —
    geometry points are [lon, lat]. Falls back gracefully for tiny geometries.
    """
    points = [(pt[1], pt[0]) for pt in geometry]  # -> (lat, lon)
    if len(points) <= 1:
        return [(points[0][0], points[0][1], 0.0)] if points else []
    if count < 2:
        count = 2

    # Cumulative distance along the route.
    cum = [0.0]
    for (lat1, lon1), (lat2, lon2) in zip(points, points[1:]):
        cum.append(cum[-1] + _haversine_km(lat1, lon1, lat2, lon2))
    total = cum[-1]
    if total == 0:
        return [(points[0][0], points[0][1], 0.0)]

    out = []
    for k in range(count):
        fraction = k / (count - 1)
        target = fraction * total
        idx = _bisect_cum(cum, target)
        lat, lon = points[idx]
        out.append((lat, lon, fraction))
    return out


def _bisect_cum(cum: list[float], target: float) -> int:
    """Index of the polyline point nearest (at or just past) the target distance."""
    for i, d in enumerate(cum):
        if d >= target:
            return i
    return len(cum) - 1


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * r * asin(sqrt(a))


# --- aggregation + formatting --------------------------------------------------

def _facilities_display(counts: dict) -> dict:
    """Cap each facility count at the UI's "20+" convention; keep None as None."""
    out = {}
    for label, n in counts.items():
        if n is None:
            out[label] = None
        elif n >= _FACILITY_DISPLAY_CAP:
            out[label] = f"{_FACILITY_DISPLAY_CAP}+"
        else:
            out[label] = n
    return out


def _route_condition(checkpoints: list[dict]) -> str:
    statuses = {c["status"] for c in checkpoints}
    if "not_recommended" in statuses:
        return "Poor"
    if "caution" in statuses:
        return "Caution"
    return "Good"


def _trip_data_tier(checkpoints: list[dict]) -> str:
    """exact when every stop had a live forecast; regional_fallback when some
    were missing; source_unavailable when none did."""
    if not checkpoints:
        return "source_unavailable"
    with_temp = sum(1 for c in checkpoints if c["temperature"] is not None)
    if with_temp == len(checkpoints):
        return "exact"
    if with_temp == 0:
        return "source_unavailable"
    return "regional_fallback"


def _summary(origin: str, destination: str, condition: str, checkpoints: list[dict]) -> str:
    o = origin.split(",")[0].strip()
    d = destination.split(",")[0].strip()
    if condition == "Good":
        return f"Good travel conditions expected from {o} to {d}."
    if condition == "Caution":
        return f"Mostly drivable from {o} to {d}, with some stops needing caution."
    return f"Difficult conditions on the {o}–{d} route — some stops are not recommended."


def _dominant(items: list[str]) -> str | None:
    if not items:
        return None
    return max(set(items), key=items.count)


def _unique_slug(name: str, index: int, used: set[str]) -> str:
    """A URL-ish id for a checkpoint, guaranteed unique within the trip so the
    frontend's `key={id}` never collides when two stops reverse-geocode to the
    same settlement name."""
    base = "".join(ch.lower() if ch.isalnum() else "-" for ch in name).strip("-")
    base = "-".join(p for p in base.split("-") if p) or f"stop-{index + 1}"
    slug = base
    suffix = 2
    while slug in used:
        slug = f"{base}-{suffix}"
        suffix += 1
    used.add(slug)
    return slug


def _next_whole_hour(now: datetime) -> datetime:
    return (now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))


def _format_time(dt: datetime) -> str:
    return dt.strftime("%-I:%M %p")


def _format_duration(seconds: float) -> str:
    minutes = int(round(seconds / 60))
    h, m = divmod(minutes, 60)
    if h and m:
        return f"{h}h {m}m"
    if h:
        return f"{h}h"
    return f"{m}m"


def _day_label(dt: datetime, now: datetime) -> str:
    delta_days = (dt.date() - now.date()).days
    if delta_days == 0:
        return "Today"
    if delta_days == 1:
        return "Tomorrow"
    return dt.strftime("%A")


# --- fail-soft shapes ----------------------------------------------------------

def _base_failsoft(origin: str, destination: str, departure: datetime,
                   now: datetime, summary: str, data_tier: str) -> dict:
    return {
        "route": {
            "from": origin.strip(), "to": destination.strip(),
            "distance_km": None, "estimated_time": None,
            "route_name": None, "condition": "Unknown",
        },
        "departure": {"label": _day_label(departure, now), "time": _format_time(departure)},
        "checkpoints": [],
        "summary": summary,
        "weather_source": "Unavailable",
        "routing_source": "Geoapify",
        "data_tier": data_tier,
        "fetched_at": now.isoformat(),
    }


def _unresolved(origin: str, destination: str, departure: datetime, missing: str) -> dict:
    now = datetime.now(_IST)
    return _base_failsoft(
        origin, destination, departure, now,
        summary=f"Couldn't locate '{missing}'. Try a nearby major city or district name.",
        data_tier="unresolved_location",
    )


def _routing_unavailable(origin: str, destination: str, departure: datetime) -> dict:
    now = datetime.now(_IST)
    return _base_failsoft(
        origin, destination, departure, now,
        summary="Route planning is temporarily unavailable — please try again shortly.",
        data_tier="source_unavailable",
    )
