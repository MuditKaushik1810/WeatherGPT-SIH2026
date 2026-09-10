"""Geoapify connector — routing, reverse geocoding, facilities (mocked HTTP)."""
from unittest.mock import MagicMock, patch

import requests

from app.connectors import geoapify


def _resp(payload):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = payload
    return resp


# --- routing -------------------------------------------------------------------

def test_route_parses_distance_time_geometry_and_name(monkeypatch):
    monkeypatch.setenv("GEOAPIFY_API_KEY", "k")
    payload = {"features": [{
        "properties": {
            "distance": 299317, "time": 10750.9,
            "legs": [{"steps": [
                {"name": "NH-48", "distance": 200000},
                {"name": "City Road", "distance": 5000},
                {"name": "NH-48", "distance": 50000},
            ]}],
        },
        "geometry": {"type": "MultiLineString", "coordinates": [[[77.39, 28.53], [76.0, 27.5]]]},
    }]}
    with patch.object(geoapify.requests, "get", return_value=_resp(payload)):
        out = geoapify.route({"lat": 28.53, "lon": 77.39}, {"lat": 26.91, "lon": 75.78})

    assert out["ok"] is True
    assert out["distance_m"] == 299317
    assert out["time_s"] == 10750.9
    assert out["route_name"] == "NH-48"       # most distance across its steps
    assert out["geometry"] == [[77.39, 28.53], [76.0, 27.5]]
    assert out["source"] == "Geoapify"


def test_route_without_key_fails_soft(monkeypatch):
    # conftest already unsets GEOAPIFY_API_KEY — no HTTP should be attempted.
    with patch.object(geoapify.requests, "get", side_effect=AssertionError("must not call")):
        out = geoapify.route({"lat": 1, "lon": 2}, {"lat": 3, "lon": 4})
    assert out["ok"] is False
    assert out["geometry"] == []
    assert out["distance_m"] is None


def test_route_fails_soft_on_network_error(monkeypatch):
    monkeypatch.setenv("GEOAPIFY_API_KEY", "k")
    with patch.object(geoapify.requests, "get", side_effect=requests.ConnectionError("down")):
        out = geoapify.route({"lat": 1, "lon": 2}, {"lat": 3, "lon": 4})
    assert out["ok"] is False
    assert out["route_name"] is None


def test_route_name_none_when_no_named_steps(monkeypatch):
    monkeypatch.setenv("GEOAPIFY_API_KEY", "k")
    payload = {"features": [{
        "properties": {"distance": 100, "time": 10, "legs": [{"steps": [{"distance": 100}]}]},
        "geometry": {"type": "LineString", "coordinates": [[1, 2], [3, 4]]},
    }]}
    with patch.object(geoapify.requests, "get", return_value=_resp(payload)):
        out = geoapify.route({"lat": 2, "lon": 1}, {"lat": 4, "lon": 3})
    assert out["route_name"] is None
    assert out["geometry"] == [[1, 2], [3, 4]]   # LineString handled too


# --- reverse geocoding ---------------------------------------------------------

def test_reverse_geocode_prefers_city(monkeypatch):
    monkeypatch.setenv("GEOAPIFY_API_KEY", "k")
    payload = {"features": [{"properties": {"city": "Alwar", "state": "Rajasthan",
                                            "formatted": "Alwar, RJ, India"}}]}
    with patch.object(geoapify.requests, "get", return_value=_resp(payload)):
        assert geoapify.reverse_geocode(27.55, 76.6) == "Alwar"


def test_reverse_geocode_fails_soft_to_none(monkeypatch):
    monkeypatch.setenv("GEOAPIFY_API_KEY", "k")
    with patch.object(geoapify.requests, "get", side_effect=requests.Timeout("slow")):
        assert geoapify.reverse_geocode(27.55, 76.6) is None


def test_reverse_geocode_without_key_returns_none():
    with patch.object(geoapify.requests, "get", side_effect=AssertionError("must not call")):
        assert geoapify.reverse_geocode(27.55, 76.6) is None


# --- facilities ----------------------------------------------------------------

def test_facilities_counts_by_exact_category(monkeypatch):
    monkeypatch.setenv("GEOAPIFY_API_KEY", "k")
    payload = {"features": [
        {"properties": {"categories": ["catering", "catering.restaurant"]}},
        {"properties": {"categories": ["catering.restaurant"]}},
        {"properties": {"categories": ["service.vehicle.fuel"]}},
        # broader parent only — must NOT count as a hospital
        {"properties": {"categories": ["healthcare"]}},
        {"properties": {"categories": ["healthcare", "healthcare.hospital"]}},
    ]}
    with patch.object(geoapify.requests, "get", return_value=_resp(payload)):
        out = geoapify.facilities(27.55, 76.6)

    assert out["restaurants"] == 2
    assert out["fuel_stations"] == 1
    assert out["hospitals"] == 1        # the bare "healthcare" one is excluded
    assert out["hotels"] == 0
    assert out["parking"] == 0


def test_facilities_fails_soft_to_none(monkeypatch):
    monkeypatch.setenv("GEOAPIFY_API_KEY", "k")
    with patch.object(geoapify.requests, "get", side_effect=requests.ConnectionError("down")):
        out = geoapify.facilities(27.55, 76.6)
    assert all(v is None for v in out.values())
