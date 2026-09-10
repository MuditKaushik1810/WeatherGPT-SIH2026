"""
Geoapify connector — routing, reverse geocoding, and nearby-facility lookup for
the Trip Planner (Architecture doc §3.10, Feature 9). Free tier, API-key based.
Docs: https://apidocs.geoapify.com/

Key is read from the GEOAPIFY_API_KEY env var (loaded from backend/.env by
main.py's load_dotenv, same pattern as WEATHERAPI_KEY). When the key is missing
every function fails soft to an unavailable result — the Trip Planner degrades
to an honest "routing unavailable" shape rather than crashing (CLAUDE.md,
"Connectors must fail soft, always").

Three public functions, each fail-soft (never raises up to the planner):
  - route(from_coords, to_coords): drive route — distance, time, geometry, name.
  - reverse_geocode(lat, lon): nearest settlement name for a checkpoint.
  - facilities(lat, lon, radius_m): counts of nearby facilities by category.
"""
import logging
import os

import requests

logger = logging.getLogger(__name__)

API_KEY_ENV = "GEOAPIFY_API_KEY"
ROUTING_URL = "https://api.geoapify.com/v1/routing"
REVERSE_URL = "https://api.geoapify.com/v1/geocode/reverse"
PLACES_URL = "https://api.geoapify.com/v2/places"

# Geoapify place categories we surface as "nearby facilities" (§3.10). Exact
# category match only — a feature is also tagged with broader parent categories
# (e.g. "healthcare"), and matching on those would conflate clinics, pharmacies
# and hospitals into one inflated count.
FACILITY_CATEGORIES = {
    "restaurants": "catering.restaurant",
    "fuel_stations": "service.vehicle.fuel",
    "hotels": "accommodation.hotel",
    "hospitals": "healthcare.hospital",
    "parking": "parking",
}


def _api_key() -> str | None:
    return os.environ.get(API_KEY_ENV)


def route(from_coords: dict, to_coords: dict, mode: str = "drive") -> dict:
    """
    Drive route between two {"lat", "lon"} coordinates.

    Returns a fail-soft dict:
        {
          "ok": bool,
          "distance_m": float | None,
          "time_s": float | None,
          "route_name": str | None,   # most-traveled named road, None if unnamed
          "geometry": list[[lon, lat]],  # ordered polyline, [] on failure
          "source": "Geoapify",
        }

    `ok` is False (and the metrics None / geometry []) on any missing key, network
    error, non-2xx, or unexpected payload — the planner degrades rather than crashes.
    """
    key = _api_key()
    if not key:
        logger.debug("%s not set; skipping Geoapify routing", API_KEY_ENV)
        return _route_unavailable()

    params = {
        "waypoints": f"{from_coords['lat']},{from_coords['lon']}|{to_coords['lat']},{to_coords['lon']}",
        "mode": mode,
        "details": "route_details",  # per-step road name + class, for route_name
        "apiKey": key,
    }
    try:
        response = requests.get(ROUTING_URL, params=params, timeout=15)
        response.raise_for_status()
        feature = response.json()["features"][0]
        props = feature["properties"]
        geometry = _flatten_geometry(feature.get("geometry", {}))
        return {
            "ok": True,
            "distance_m": props.get("distance"),
            "time_s": props.get("time"),
            "route_name": _dominant_road_name(props.get("legs", [])),
            "geometry": geometry,
            "source": "Geoapify",
        }
    except Exception as exc:  # network, HTTP, or shape — all degrade the ladder
        logger.warning("Geoapify routing failed: %r", exc)
        return _route_unavailable()


def reverse_geocode(lat: float, lon: float) -> str | None:
    """
    Nearest settlement name for a coordinate (for labelling a route checkpoint).
    Prefers city/town/village/county/name/formatted in that order. Returns None
    on any failure or if nothing sensible comes back — the planner then falls
    back to a coordinate-based label.
    """
    key = _api_key()
    if not key:
        return None
    params = {"lat": lat, "lon": lon, "type": "city", "apiKey": key}
    try:
        response = requests.get(REVERSE_URL, params=params, timeout=10)
        response.raise_for_status()
        features = response.json().get("features", [])
        if not features:
            return None
        p = features[0].get("properties", {})
        for field in ("city", "town", "village", "county", "name", "formatted"):
            value = p.get(field)
            if value:
                return value
        return None
    except Exception as exc:
        logger.warning("Geoapify reverse geocode failed for (%s, %s): %r", lat, lon, exc)
        return None


def facilities(lat: float, lon: float, radius_m: int = 8000) -> dict:
    """
    Counts of nearby facilities within `radius_m`, by category (§3.10). One Places
    call covering all categories (limit 500 so no single category saturates the
    cap and under-counts the others), bucketed by exact category match.

    Returns {"restaurants", "fuel_stations", "hotels", "hospitals", "parking"},
    each an int count, or an all-None dict on any failure. The planner applies the
    display cap ("20+"); this stays numeric so callers can reason about it.
    """
    blank = {label: None for label in FACILITY_CATEGORIES}
    key = _api_key()
    if not key:
        return blank
    params = {
        "categories": ",".join(FACILITY_CATEGORIES.values()),
        "filter": f"circle:{lon},{lat},{radius_m}",  # Geoapify order is lon,lat
        "limit": 500,
        "apiKey": key,
    }
    try:
        response = requests.get(PLACES_URL, params=params, timeout=15)
        response.raise_for_status()
        features = response.json().get("features", [])
        counts = {label: 0 for label in FACILITY_CATEGORIES}
        for feature in features:
            tags = set(feature.get("properties", {}).get("categories", []))
            for label, category in FACILITY_CATEGORIES.items():
                if category in tags:
                    counts[label] += 1
        return counts
    except Exception as exc:
        logger.warning("Geoapify places failed for (%s, %s): %r", lat, lon, exc)
        return blank


def _route_unavailable() -> dict:
    return {
        "ok": False, "distance_m": None, "time_s": None,
        "route_name": None, "geometry": [], "source": "Geoapify",
    }


def _flatten_geometry(geometry: dict) -> list[list[float]]:
    """
    Flatten a routing geometry into one ordered list of [lon, lat] points.
    Geoapify returns a MultiLineString (list of line segments); LineString is
    handled too for robustness. Returns [] for anything unexpected.
    """
    coords = geometry.get("coordinates", [])
    gtype = geometry.get("type")
    if gtype == "LineString":
        return [pt for pt in coords if isinstance(pt, list) and len(pt) >= 2]
    if gtype == "MultiLineString":
        flat: list[list[float]] = []
        for line in coords:
            flat.extend(pt for pt in line if isinstance(pt, list) and len(pt) >= 2)
        return flat
    return []


def _dominant_road_name(legs: list[dict]) -> str | None:
    """
    The name of the road carrying the most distance along the route, derived from
    route_details steps (each step has `name` + `distance`). This is the honest
    "route name" — e.g. "NE-4, Delhi - Vadodara Expressway" — rather than a
    fabricated highway number. Returns None if no step is named.
    """
    by_road: dict[str, float] = {}
    for leg in legs:
        for step in leg.get("steps", []):
            name = step.get("name")
            if not name:
                continue
            by_road[name] = by_road.get(name, 0.0) + (step.get("distance") or 0.0)
    if not by_road:
        return None
    return max(by_road.items(), key=lambda kv: kv[1])[0]
