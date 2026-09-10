"""
Crop Planning tests (§3.10 GET /farmer/crop-planning). Weather is mocked; the
season is made deterministic by injecting `now`. Focus: recommendations match the
season, are ranked by temperature fit, and it never bare-refuses.
"""
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.farmer import crop_planning
from app.farmer.crop_planning import get_crop_planning
from app.main import app

_KHARIF = {"Rice", "Maize", "Cotton", "Soybean", "Groundnut", "Tomato"}
_RABI = {"Wheat", "Mustard", "Gram", "Pea", "Potato", "Lentil", "Tomato"}


def _weather(temp):
    return {"location": "Raipur", "temp": temp, "data_tier": "exact", "source": "WeatherAPI"}


def test_recommends_kharif_crops_in_a_kharif_month():
    with patch.object(crop_planning.degradation_ladder, "get_weather", return_value=_weather(28.0)):
        result = get_crop_planning("Raipur", now=datetime(2026, 7, 1, tzinfo=timezone.utc))

    assert result["season"] == "Kharif"
    assert 1 <= len(result["recommendations"]) <= 4
    crops = {r["crop"] for r in result["recommendations"]}
    assert crops <= _KHARIF                       # only Kharif/all-season crops
    assert "Wheat" not in crops                    # a Rabi crop is not offered
    for r in result["recommendations"]:
        assert r["crop"] and r["suitability"] and r["reason"] and r["harvest_window"]


def test_recommends_rabi_crops_in_a_rabi_month():
    with patch.object(crop_planning.degradation_ladder, "get_weather", return_value=_weather(18.0)):
        result = get_crop_planning("Karnal", now=datetime(2026, 1, 15, tzinfo=timezone.utc))

    assert result["season"] == "Rabi"
    crops = {r["crop"] for r in result["recommendations"]}
    assert crops <= _RABI
    assert "Rice" not in crops


def test_temperature_fit_drives_suitability():
    # 26°C is squarely inside rice's 22–32 band → Excellent for a warm-season crop.
    with patch.object(crop_planning.degradation_ladder, "get_weather", return_value=_weather(26.0)):
        result = get_crop_planning("Raipur", now=datetime(2026, 7, 1, tzinfo=timezone.utc))
    top = result["recommendations"][0]
    assert top["suitability"] == "Excellent"


def test_falls_back_to_season_only_without_a_location():
    with patch.object(crop_planning.degradation_ladder, "get_weather") as gw:
        result = get_crop_planning("", now=datetime(2026, 1, 15, tzinfo=timezone.utc))
        gw.assert_not_called()                     # no location → no fetch

    assert result["data_tier"] == "seasonal"
    assert result["recommendations"]               # still recommends (season-based)
    assert result["source"] == "WeatherGPT crop rules"


def test_endpoint_returns_the_planning_shape():
    with patch.object(crop_planning.degradation_ladder, "get_weather", return_value=_weather(27.0)):
        client = TestClient(app)
        resp = client.get("/farmer/crop-planning", params={"location": "Raipur"})

    assert resp.status_code == 200
    body = resp.json()
    assert set(body) >= {"data_tier", "source", "location", "season", "climate_context", "recommendations"}
    assert body["recommendations"]
