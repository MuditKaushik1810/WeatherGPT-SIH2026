"""
Crop Watch / Crop Risk Index tests (Architecture §3.7, §3.10). All external calls
are mocked — the weather record (degradation_ladder.get_weather), geocoding, and
the soil-moisture connector — so nothing hits a live endpoint (CLAUDE.md).

Focus: the weighted crop-stress score is computed and fail-soft (renormalizes over
available parameters), every threat is EXPLAINED, rainfall is a threat not a fit
term, disease fires from the key-disease rule, and the endpoint never bare-refuses.
"""
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.farmer import crop_watch
from app.farmer.crop_watch import parameter_score, get_crop_watch
from app.main import app


def _weather(**over):
    rec = {
        "location": "Raipur", "temp": 38.0, "condition": "clear sky",
        "precipitation_chance": 0.1, "humidity": 40.0, "feels_like": 41.0,
        "wind_speed": 9.0, "aqi": 80, "warnings": [], "source": "WeatherAPI",
        "data_tier": "exact", "fetched_at": "2026-09-10T09:00:00Z",
    }
    rec.update(over)
    return rec


def _mocks(weather=None, coords=True, soil=0.15):
    """Patch the three external dependencies; return the patch context managers."""
    return (
        patch.object(crop_watch.degradation_ladder, "get_weather",
                     return_value=weather if weather is not None else _weather()),
        patch.object(crop_watch.geocoding, "resolve_location",
                     return_value={"lat": 21.25, "lon": 81.63} if coords else None),
        patch.object(crop_watch.open_meteo_soil, "fetch_soil_moisture",
                     return_value={"soil_moisture": soil}),
    )


def test_parameter_score_is_a_plateau_inside_the_band():
    assert parameter_score(27, 24, 30) == 1.0     # inside
    assert parameter_score(24, 24, 30) == 1.0     # at the edge — still in-range, ideal
    assert parameter_score(33, 24, 30) == 0.5     # one half-span outside
    assert parameter_score(36, 24, 30) == 0.0     # a full band-width outside, clamped


def test_stressed_crop_scores_high_and_every_threat_is_explained():
    gw, geo, soil = _mocks()  # rice at 38C / 40% RH / 0.15 soil — all outside comfort
    with gw, geo, soil:
        result = get_crop_watch("rice", "Raipur", days_after_sowing=40)

    assert result["risk_score"] > 50
    assert result["risk_level"] in ("High", "Very High")
    assert set(result["components"]) == {"temperature", "soil_moisture"}   # humidity isn't a fit term
    ids = {t["id"] for t in result["threats"]}
    assert {"heat", "dry_soil"} <= ids
    assert "dry_air" not in ids and "humid" not in ids           # no generic humidity threat
    assert all(t["detail"] for t in result["threats"])          # each explains WHY
    assert result["recommended_action"]["items"]                # concrete action
    assert result["provisional"] is False                       # temp + disease sourced
    assert result["crop_stage"] == "Vegetative"                 # 40/120 days


def test_missing_soil_moisture_renormalizes_rather_than_breaking():
    gw, geo, soil = _mocks(soil=None)   # Open-Meteo soil unavailable
    with gw, geo, soil:
        result = get_crop_watch("rice", "Raipur", days_after_sowing=40)

    assert result["risk_score"] is not None                     # still computes
    assert "soil_moisture" not in result["components"]          # dropped, weights renormalized
    assert set(result["components"]) == {"temperature"}


def test_disease_threat_fires_from_the_key_disease_rule():
    # Rice fit-comfortable on temp/soil but blast is strongly favoured (20-28C, RH >=88%).
    gw, geo, soil = _mocks(weather=_weather(temp=26.0, humidity=98.0, precipitation_chance=0.2), soil=0.35)
    with gw, geo, soil:
        result = get_crop_watch("rice", "Raipur", days_after_sowing=40)

    disease = next((t for t in result["threats"] if t["id"] == "disease"), None)
    assert disease is not None and disease["level"] == "High"
    assert "blast" in disease["detail"].lower()
    assert "blast" in result["recommended_action"]["title"].lower()  # action names the disease


def test_disease_threat_is_growth_stage_specific():
    # Same blast-favouring weather (26C / 98% RH) — the risk depends on the crop's stage.
    def watch(days):
        gw, geo, soil = _mocks(weather=_weather(temp=26.0, humidity=98.0, precipitation_chance=0.2), soil=0.35)
        with gw, geo, soil:
            return get_crop_watch("rice", "Raipur", days_after_sowing=days)

    veg = next(t for t in watch(40)["threats"] if t["id"] == "disease")    # Vegetative — susceptible
    mat = next(t for t in watch(115)["threats"] if t["id"] == "disease")   # Maturity — not susceptible
    assert veg["level"] == "High" and "Vegetative" in veg["detail"]
    assert mat["level"] == "Low" and "lower-risk stage" in mat["detail"]


def test_heavy_rain_is_a_threat_not_a_fit_term():
    gw, geo, soil = _mocks(weather=_weather(temp=27.0, humidity=80.0, precipitation_chance=0.85), soil=0.35)
    with gw, geo, soil:
        result = get_crop_watch("rice", "Raipur", days_after_sowing=40)

    rain = next((t for t in result["threats"] if t["id"] == "rain"), None)
    assert rain is not None and rain["level"] == "High"
    assert "rainfall" not in result["components"]               # never a fit component


def test_unknown_crop_is_honest_not_a_crash():
    gw, geo, soil = _mocks()
    with gw, geo, soil:
        result = get_crop_watch("dragonfruit", "Raipur")

    assert result["risk_score"] is None
    assert result["data_tier"] == "unresolved_location"
    assert "isn't in the crop rule table" in result["message"]


def test_unresolved_location_is_honest():
    gw, geo, soil = _mocks(weather=_weather(data_tier="unresolved_location"), coords=False)
    with gw, geo, soil:
        result = get_crop_watch("rice", "Nowhereville")

    assert result["risk_score"] is None
    assert result["threats"] == []


def test_endpoint_returns_the_composite_shape():
    gw, geo, soil = _mocks()
    with gw, geo, soil:
        client = TestClient(app)
        resp = client.get("/farmer/crop-watch", params={"crop": "rice", "location": "Raipur", "days_after_sowing": 40})

    assert resp.status_code == 200
    body = resp.json()
    for key in ("risk_score", "risk_level", "components", "threats", "recommended_action", "provisional", "crop_stage"):
        assert key in body
    assert body["provisional"] is False
