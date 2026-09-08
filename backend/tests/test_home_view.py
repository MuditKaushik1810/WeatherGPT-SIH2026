"""
Home view tests — all external calls mocked (CLAUDE.md: never hit live endpoints).

Confirms the composite view stitches current + hourly + recommendation together,
reuses the ladder's fetch/normalize, and degrades honestly for an unresolvable
location.
"""
from unittest.mock import patch

from app.core import home_view


def _forecast():
    return {
        "temp": 28.4, "humidity": 72, "feels_like": 31.0, "wind_speed": 12.0,
        "precipitation_chance": 0.3, "condition": "partly cloudy",
        "source": "Open-Meteo", "data_tier": "exact",
        "fetched_at": "2026-09-06T09:00:00Z",
        "_raw_hourly": {
            "time": ["2026-09-06T09:00", "2026-09-06T10:00", "2026-09-06T11:00"],
            "temperature_2m": [28.4, 29.0, 30.1],
            "weathercode": [2, 3, 61],
            "precipitation_probability": [30, 20, 65],
        },
    }


def _aqi():
    return {
        "aqi": 86, "source": "Open-Meteo Air Quality",
        "data_tier": "exact", "fetched_at": "2026-09-06T09:00:00Z",
    }


def _warnings(warns=None):
    return {
        "warnings": warns or [], "source": "IMD",
        "data_tier": "exact" if warns else "unavailable",
        "fetched_at": "2026-09-06T09:00:00Z",
    }


@patch("app.core.degradation_ladder.open_meteo_air_quality.fetch_air_quality")
@patch("app.core.degradation_ladder.imd.fetch_warnings")
@patch("app.core.degradation_ladder.open_meteo.fetch_forecast")
def test_home_view_composes_current_hourly_recommendation(mock_forecast, mock_warnings, mock_aqi):
    mock_forecast.return_value = _forecast()
    mock_warnings.return_value = _warnings()
    mock_aqi.return_value = _aqi()

    view = home_view.get_home_view("Delhi")

    assert view["location"] == "Delhi"
    assert view["data_tier"] == "exact"
    # current block is the full normalized record
    assert view["current"]["temp"] == 28.4
    assert view["current"]["aqi"] == 86
    # hourly extracted from the raw arrays
    assert len(view["hourly"]) == 3
    assert view["hourly"][0]["condition"] == "partly cloudy"
    assert view["hourly"][2]["precipitation_chance"] == 0.65
    # recommendation present and non-empty
    assert view["recommendation"]["title"]
    assert view["recommendation"]["message"]


@patch("app.core.degradation_ladder.open_meteo_air_quality.fetch_air_quality")
@patch("app.core.degradation_ladder.imd.fetch_warnings")
@patch("app.core.degradation_ladder.open_meteo.fetch_forecast")
def test_home_view_active_warning_drives_recommendation(mock_forecast, mock_warnings, mock_aqi):
    mock_forecast.return_value = _forecast()
    mock_warnings.return_value = _warnings(["Heavy rainfall warning - Delhi"])
    mock_aqi.return_value = _aqi()

    view = home_view.get_home_view("Delhi")

    assert view["current"]["warnings"] == ["Heavy rainfall warning - Delhi"]
    assert view["recommendation"]["title"] == "Stay alert"


@patch("app.core.home_view.geocoding.resolve_location", return_value=None)
def test_home_view_unresolved_location_is_honest_gap(mock_resolve):
    view = home_view.get_home_view("ZzzNotARealPlaceXyz123")

    assert view["data_tier"] == "unresolved_location"
    assert view["hourly"] == []
    assert view["current"]["temp"] is None
    # Still a recommendation, never a bare refusal.
    assert view["recommendation"]["title"]


@patch("app.core.degradation_ladder.open_meteo_air_quality.fetch_air_quality")
@patch("app.core.degradation_ladder.imd.fetch_warnings")
@patch("app.core.degradation_ladder.open_meteo.fetch_forecast")
def test_home_view_forecast_down_degrades_to_historical_baseline(mock_forecast, mock_warnings, mock_aqi):
    # Live forecast is down for a city with a preloaded baseline (Delhi): the
    # current block shows a typical-for-today temp tagged historical_baseline
    # instead of a null current block — and still carries live AQI.
    mock_forecast.return_value = {
        "temp": None, "humidity": None, "feels_like": None, "wind_speed": None,
        "precipitation_chance": None, "condition": None, "source": "Open-Meteo",
        "data_tier": "unavailable", "fetched_at": "2026-09-06T00:00:00Z", "_raw_hourly": None,
    }
    mock_warnings.return_value = _warnings()
    mock_aqi.return_value = _aqi()

    view = home_view.get_home_view("Delhi")

    assert view["data_tier"] == "historical_baseline"
    assert view["current"]["data_tier"] == "historical_baseline"
    assert view["current"]["temp"] is not None
    assert view["current"]["aqi"] == 86
    assert view["hourly"] == []                    # no live hourly series to strip
    assert view["recommendation"]["title"]         # still a grounded suggestion


@patch("app.core.degradation_ladder.open_meteo_air_quality.fetch_air_quality")
@patch("app.core.degradation_ladder.imd.fetch_warnings")
@patch("app.core.degradation_ladder.open_meteo.fetch_forecast")
def test_home_view_recommendation_uses_today_peak(mock_forecast, mock_warnings, mock_aqi):
    # Mild right now (30°C), but hot later today (41°C) -> peak drives "Beat the heat".
    forecast = _forecast()
    forecast["temp"] = 30.0
    forecast["_raw_hourly"] = {
        "time": ["2026-09-06T09:00", "2026-09-06T15:00"],
        "temperature_2m": [30.0, 41.0],
        "apparent_temperature": [33.0, 44.0],
        "weathercode": [2, 0],
        "precipitation_probability": [10, 5],
        "wind_speed_10m": [8.0, 10.0],
    }
    mock_forecast.return_value = forecast
    mock_warnings.return_value = _warnings()
    mock_aqi.return_value = _aqi()

    view = home_view.get_home_view("Delhi")

    assert view["recommendation"]["title"] == "Beat the heat"
