"""
Forecast retrieval tests (Sprint 2). Geocoding + the forecast fetch are mocked,
so nothing hits a live endpoint (CLAUDE.md). `now` is injected for determinism.
"""
from datetime import datetime
from unittest.mock import patch

from zoneinfo import ZoneInfo

from app.core import forecast

_NOW = datetime(2026, 9, 9, 10, 0, tzinfo=ZoneInfo("Asia/Kolkata"))


def _raw_hourly_3days():
    return {
        "time": [
            "2026-09-09T00:00", "2026-09-09T12:00",
            "2026-09-10T00:00", "2026-09-10T12:00",
            "2026-09-11T12:00",
        ],
        "temperature_2m": [26.0, 33.0, 27.0, 34.0, 30.0],
        "apparent_temperature": [28.0, 36.0, 29.0, 37.0, 32.0],
        "precipitation_probability": [10, 20, 40, 70, 15],
        "wind_speed_10m": [8.0, 12.0, 10.0, 15.0, 9.0],
        "condition_text": ["Clear", "Sunny", "Cloudy", "Patchy rain", "Clear"],
    }


@patch("app.core.degradation_ladder.fetch_forecast_with_fallback")
@patch("app.core.geocoding.resolve_location", return_value={"lat": 28.6, "lon": 77.2})
def test_tomorrow_is_summarized_from_the_forecast(mock_geo, mock_fetch):
    mock_fetch.return_value = {"source": "WeatherAPI", "data_tier": "exact",
                              "fetched_at": "x", "_raw_hourly": _raw_hourly_3days()}

    result = forecast.get_daily_forecast("Delhi", [1], now=_NOW)

    assert result["data_tier"] == "exact"
    assert result["source"] == "WeatherAPI"
    assert len(result["days"]) == 1
    day = result["days"][0]
    assert day["label"] == "Tomorrow"
    assert day["date"] == "2026-09-10"
    assert day["peak_temp"] == 34.0 and day["low_temp"] == 27.0
    assert day["max_precip_chance"] == 0.7          # 70% at the wettest hour
    assert day["condition"] == "Patchy rain"        # condition at the wettest hour


@patch("app.core.degradation_ladder.fetch_forecast_with_fallback")
@patch("app.core.geocoding.resolve_location", return_value={"lat": 28.6, "lon": 77.2})
def test_days_beyond_the_horizon_are_skipped(mock_geo, mock_fetch):
    mock_fetch.return_value = {"source": "WeatherAPI", "data_tier": "exact",
                              "fetched_at": "x", "_raw_hourly": _raw_hourly_3days()}
    # Offset 5 (2026-09-14) isn't in the 3-day series -> skipped, honest message.
    result = forecast.get_daily_forecast("Delhi", [5], now=_NOW)
    assert result["days"] == []
    assert result["data_tier"] == "source_unavailable"
    assert result["message"]


@patch("app.core.geocoding.resolve_location", return_value=None)
def test_unresolved_location_fails_soft(mock_geo):
    result = forecast.get_daily_forecast("ZzzNowhere", [1], now=_NOW)
    assert result["data_tier"] == "unresolved_location"
    assert result["days"] == []
    assert "resolve" in result["message"].lower()


@patch("app.core.degradation_ladder.fetch_forecast_with_fallback")
@patch("app.core.geocoding.resolve_location", return_value={"lat": 28.6, "lon": 77.2})
def test_dead_forecast_source_fails_soft(mock_geo, mock_fetch):
    mock_fetch.return_value = {"source": "Open-Meteo", "data_tier": "unavailable",
                              "fetched_at": None, "_raw_hourly": None}
    result = forecast.get_daily_forecast("Delhi", [1], now=_NOW)
    assert result["data_tier"] == "source_unavailable"
    assert result["days"] == []
