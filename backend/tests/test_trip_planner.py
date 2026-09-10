"""
Trip Planner orchestration — checkpoint sampling, forecast-at-ETA, stop rating,
split provenance, and fail-soft behaviour. Every external call (our geocoding,
Geoapify, the forecast pipeline) is mocked — no live endpoints (CLAUDE.md).
"""
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from app.trip import trip_planner

_IST = ZoneInfo("Asia/Kolkata")
_NOW = datetime(2026, 9, 10, 7, 30, tzinfo=_IST)
_DEP = datetime(2026, 9, 10, 8, 0, tzinfo=_IST)

# A straight-ish polyline ([lon, lat]) — exact geometry is irrelevant because
# reverse_geocode and the forecast are mocked; it only needs enough points to
# sample six checkpoints along.
_GEOMETRY = [[77.0 + i * 0.1, 28.0 - i * 0.1] for i in range(11)]


def _raw_hourly(precip_by_hour: dict[int, int], last_hour: int = 14) -> dict:
    """Open-Meteo-style hourly arrays for 08:00..last_hour IST on 2026-09-10."""
    times, temps, precs, texts = [], [], [], []
    for hour in range(8, last_hour + 1):
        times.append(f"2026-09-10T{hour:02d}:00")
        temps.append(30.0)
        precs.append(precip_by_hour.get(hour, 10))
        texts.append("partly cloudy")
    return {"time": times, "temperature_2m": temps,
            "precipitation_probability": precs, "condition_text": texts}


def _forecast_record(raw):
    return {"source": "WeatherAPI", "data_tier": "exact", "_raw_hourly": raw}


def _run(resolve=None, route=None, forecast=None, reverse_names=None, facilities=None):
    """Patch every boundary and run the planner with fixed now/departure."""
    resolve = resolve or (lambda name: {"lat": 28.0, "lon": 77.0})
    route = route or {
        "ok": True, "distance_m": 300000, "time_s": 18000,  # 300 km, 5 h
        "route_name": "NH-48", "geometry": _GEOMETRY, "source": "Geoapify",
    }
    reverse_names = reverse_names or ["Noida", "Gurugram", "Neemrana",
                                      "Behror", "Alwar", "Jaipur"]
    facilities = facilities if facilities is not None else {
        "restaurants": 25, "fuel_stations": 3, "hotels": 0, "hospitals": 7, "parking": 2,
    }
    with patch.object(trip_planner.geocoding, "resolve_location", side_effect=resolve), \
         patch.object(trip_planner.geoapify, "route", return_value=route), \
         patch.object(trip_planner.geoapify, "reverse_geocode", side_effect=list(reverse_names)), \
         patch.object(trip_planner.geoapify, "facilities", return_value=facilities), \
         patch.object(trip_planner.degradation_ladder, "fetch_forecast_with_fallback",
                      return_value=_forecast_record(forecast)):
        return trip_planner.get_trip_plan("Noida", "Jaipur", departure=_DEP, now=_NOW)


def test_builds_six_checkpoints_with_distance_and_eta():
    plan = _run(forecast=_raw_hourly({}))
    cps = plan["checkpoints"]
    assert len(cps) == 6
    assert cps[0]["distance_km"] == 0 and cps[0]["eta"] == "8:00 AM"
    assert cps[-1]["distance_km"] == 300 and cps[-1]["eta"] == "1:00 PM"
    assert cps[0]["name"] == "Noida" and cps[-1]["name"] == "Jaipur"
    assert cps[0]["id"] == "noida"


def test_route_summary_and_split_provenance():
    plan = _run(forecast=_raw_hourly({}))
    assert plan["route"]["distance_km"] == 300
    assert plan["route"]["estimated_time"] == "5h"
    assert plan["route"]["route_name"] == "NH-48"
    assert plan["weather_source"] == "WeatherAPI"   # from our pipeline
    assert plan["routing_source"] == "Geoapify"     # never collapsed into one
    assert plan["data_tier"] == "exact"
    assert plan["departure"] == {"label": "Today", "time": "8:00 AM"}


def test_stop_status_derived_from_rain_at_eta():
    # 10:00 (checkpoint index 2) = 35% rain -> caution; 11:00 (index 3) = 65% -> not_recommended
    plan = _run(forecast=_raw_hourly({10: 35, 11: 65}))
    cps = plan["checkpoints"]
    assert cps[0]["status"] == "good"
    assert cps[2]["status"] == "caution" and cps[2]["rain_probability"] == 35
    assert cps[3]["status"] == "not_recommended" and cps[3]["rain_probability"] == 65
    assert plan["route"]["condition"] == "Poor"     # worst stop drives it


def test_facilities_counts_capped_for_display():
    plan = _run(forecast=_raw_hourly({}))
    fac = plan["checkpoints"][0]["facilities"]
    assert fac["restaurants"] == "20+"     # 25 -> capped
    assert fac["fuel_stations"] == 3       # small counts stay numeric
    assert fac["hotels"] == 0


def test_checkpoint_beyond_forecast_horizon_is_cautious_not_crash():
    # Hourly only reaches 10:00, so the 11:00+ checkpoints have no forecast.
    plan = _run(forecast=_raw_hourly({}, last_hour=10))
    cps = plan["checkpoints"]
    late = cps[-1]
    assert late["temperature"] is None
    assert late["status"] == "caution"
    assert "unavailable" in late["note"].lower()
    assert plan["data_tier"] == "regional_fallback"  # some stops live, some not


def test_unresolved_destination_fails_soft():
    def resolve(name):
        return {"lat": 28.0, "lon": 77.0} if name == "Noida" else None
    plan = _run(resolve=resolve, forecast=_raw_hourly({}))
    assert plan["data_tier"] == "unresolved_location"
    assert plan["checkpoints"] == []
    assert "Jaipur" in plan["summary"]
    assert plan["routing_source"] == "Geoapify"


def test_routing_unavailable_fails_soft():
    dead = {"ok": False, "distance_m": None, "time_s": None,
            "route_name": None, "geometry": [], "source": "Geoapify"}
    plan = _run(route=dead, forecast=_raw_hourly({}))
    assert plan["data_tier"] == "source_unavailable"
    assert plan["checkpoints"] == []
    assert plan["route"]["condition"] == "Unknown"


def test_duplicate_stop_names_get_unique_ids():
    # Two checkpoints reverse-geocode to the same settlement — ids must not collide
    # (the Travel tab keys on id).
    names = ["Noida", "Rewari", "Rewari", "Rewari", "Kotputli", "Jaipur"]
    plan = _run(reverse_names=names, forecast=_raw_hourly({}))
    ids = [c["id"] for c in plan["checkpoints"]]
    assert len(ids) == len(set(ids))            # all unique
    assert ids.count("rewari") == 1 and "rewari-2" in ids and "rewari-3" in ids


def test_all_stops_good_gives_good_condition():
    plan = _run(forecast=_raw_hourly({}))
    assert plan["route"]["condition"] == "Good"
    assert plan["summary"].startswith("Good travel conditions")
