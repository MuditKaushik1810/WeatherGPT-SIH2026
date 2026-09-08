from datetime import datetime
from unittest.mock import patch

from app.core import degradation_ladder, historical


def _source_unavailable_record(location="Delhi", warnings=None, aqi=None):
    """A normalized record shaped as normalize.py returns when forecast is down."""
    return {
        "location": location, "temp": None, "condition": None,
        "precipitation_chance": None, "humidity": None, "feels_like": None,
        "wind_speed": None, "aqi": aqi, "warnings": warnings or [],
        "source": None, "data_tier": "source_unavailable",
        "fetched_at": "2026-09-06T00:00:00Z", "message": "forecast down",
    }


def _healthy_aqi():
    return {
        "aqi": 42, "source": "Open-Meteo Air Quality",
        "data_tier": "exact", "fetched_at": "2026-09-06T00:00:00Z",
    }


def _unavailable_aqi():
    return {
        "aqi": None, "source": "Open-Meteo Air Quality",
        "data_tier": "unavailable", "fetched_at": "2026-09-06T00:00:00Z",
    }


def _unavailable_forecast():
    """An Open-Meteo record as returned when the forecast source fails soft."""
    return {
        "temp": None, "humidity": None, "feels_like": None, "wind_speed": None,
        "precipitation_chance": None, "condition": None, "source": "Open-Meteo",
        "data_tier": "unavailable", "fetched_at": "2026-09-06T00:00:00Z",
        "_raw_hourly": None,
    }


@patch("app.core.degradation_ladder.imd.fetch_warnings")
@patch("app.core.degradation_ladder.open_meteo_air_quality.fetch_air_quality")
@patch("app.core.degradation_ladder.open_meteo.fetch_forecast")
def test_normal_location_returns_exact_tier(mock_forecast, mock_aqi, mock_warnings):
    mock_forecast.return_value = {
        "temp": 27.0,
        "humidity": 80,
        "feels_like": 29.0,
        "wind_speed": 11.0,
        "condition": "light rain",
        "precipitation_chance": 0.6,
        "source": "Open-Meteo",
        "data_tier": "exact",
        "fetched_at": "2026-09-05T00:00:00Z",
    }
    mock_aqi.return_value = _healthy_aqi()
    mock_warnings.return_value = {
        "warnings": [],
        "source": "IMD",
        "data_tier": "exact",
        "fetched_at": "2026-09-05T00:00:00Z",
    }

    result = degradation_ladder.get_weather("Delhi")

    assert result["data_tier"] == "exact"
    assert result["temp"] == 27.0
    assert result["location"] == "Delhi"
    # New additive metrics flow through from the connectors.
    assert result["humidity"] == 80
    assert result["feels_like"] == 29.0
    assert result["wind_speed"] == 11.0
    assert result["aqi"] == 42


@patch("app.core.degradation_ladder.imd.fetch_warnings")
@patch("app.core.degradation_ladder.open_meteo_air_quality.fetch_air_quality")
@patch("app.core.degradation_ladder.open_meteo.fetch_forecast")
def test_active_imd_warning_is_surfaced(mock_forecast, mock_aqi, mock_warnings):
    mock_forecast.return_value = {
        "temp": 30.0, "humidity": 70, "feels_like": 32.0, "wind_speed": 9.0,
        "condition": "overcast", "precipitation_chance": 0.8,
        "source": "Open-Meteo", "data_tier": "exact", "fetched_at": "2026-09-05T00:00:00Z",
    }
    mock_aqi.return_value = _healthy_aqi()
    mock_warnings.return_value = {
        "warnings": ["Heavy rainfall warning - South Delhi"],
        "source": "IMD", "data_tier": "exact", "fetched_at": "2026-09-05T00:00:00Z",
    }

    result = degradation_ladder.get_weather("Delhi")

    assert result["warnings"] == ["Heavy rainfall warning - South Delhi"]
    assert result["source"] == "IMD"


def test_unresolvable_location_returns_honest_gap_not_a_crash():
    result = degradation_ladder.get_weather("ZzzNotARealPlaceXyz123")
    assert result["data_tier"] == "unresolved_location"
    assert "message" in result
    assert result["temp"] is None
    # Record shape stays uniform even in the gap case.
    assert result["aqi"] is None


@patch("app.core.degradation_ladder.imd.fetch_warnings")
@patch("app.core.degradation_ladder.open_meteo_air_quality.fetch_air_quality")
@patch("app.core.degradation_ladder.open_meteo.fetch_forecast")
def test_forecast_source_down_but_warning_active_degrades_not_crashes(mock_forecast, mock_aqi, mock_warnings):
    # Open-Meteo forecast is down, but IMD still has an official warning, and the
    # separate AQI source is still up — surface both, don't crash.
    mock_forecast.return_value = _unavailable_forecast()
    mock_aqi.return_value = _healthy_aqi()
    mock_warnings.return_value = {
        "warnings": ["Cyclone warning - Odisha coast"],
        "source": "IMD", "data_tier": "exact", "fetched_at": "2026-09-06T00:00:00Z",
    }

    result = degradation_ladder.get_weather("Delhi")

    # Delhi has a preloaded historical baseline, so the ladder degrades one rung
    # further than a bare gap: a typical-for-this-date temp tagged
    # historical_baseline — with the live warning + AQI still surfaced.
    assert result["data_tier"] == "historical_baseline"
    assert result["temp"] is not None
    assert result["source"] == "Historical"
    assert result["warnings"] == ["Cyclone warning - Odisha coast"]
    # AQI comes from an independent source, so it survives a forecast outage.
    assert result["aqi"] == 42
    assert "message" in result


@patch("app.core.degradation_ladder.imd.fetch_warnings")
@patch("app.core.degradation_ladder.open_meteo_air_quality.fetch_air_quality")
@patch("app.core.degradation_ladder.open_meteo.fetch_forecast")
def test_all_live_sources_down_never_bare_refuses(mock_forecast, mock_aqi, mock_warnings):
    # Every live source unavailable — still an honest, message-bearing record,
    # never an unhandled crash (which is what the raw connector used to do).
    mock_forecast.return_value = _unavailable_forecast()
    mock_aqi.return_value = _unavailable_aqi()
    mock_warnings.return_value = {
        "warnings": [], "source": "IMD", "data_tier": "unavailable",
        "fetched_at": "2026-09-06T00:00:00Z",
    }

    result = degradation_ladder.get_weather("Delhi")

    # Every LIVE source is down, but Delhi's preloaded baseline still gives a
    # grounded typical-for-today temp — never a bare refusal.
    assert result["data_tier"] == "historical_baseline"
    assert result["temp"] is not None
    assert result["warnings"] == []
    assert result["aqi"] is None
    assert result["message"]


@patch("app.core.degradation_ladder.imd.fetch_warnings")
@patch("app.core.degradation_ladder.open_meteo_air_quality.fetch_air_quality")
@patch("app.core.degradation_ladder.open_meteo.fetch_forecast")
def test_transient_source_outage_is_not_cached(mock_forecast, mock_aqi, mock_warnings):
    # A brief outage must not be served stale for the full TTL after recovery.
    mock_aqi.return_value = _unavailable_aqi()
    mock_warnings.return_value = {
        "warnings": [], "source": "IMD", "data_tier": "unavailable",
        "fetched_at": "2026-09-06T00:00:00Z",
    }
    mock_forecast.return_value = _unavailable_forecast()
    first = degradation_ladder.get_weather("Delhi")
    # Delhi's baseline fills the gap — and a historical_baseline fallback is
    # deliberately NOT cached, which is exactly what lets recovery be seen below.
    assert first["data_tier"] == "historical_baseline"

    # Source recovers on the next call — we must re-fetch, not serve the cached gap.
    mock_forecast.return_value = {
        "temp": 33.0, "humidity": 40, "feels_like": 35.0, "wind_speed": 6.0,
        "precipitation_chance": 0.1, "condition": "clear sky", "source": "Open-Meteo",
        "data_tier": "exact", "fetched_at": "2026-09-06T00:05:00Z", "_raw_hourly": {},
    }
    second = degradation_ladder.get_weather("Delhi")
    assert second["data_tier"] == "exact"
    assert second["temp"] == 33.0


def test_apply_historical_fallback_fills_gap_with_baseline_for_the_date():
    # Deterministic: inject the date, expect that day-of-year's baseline temp.
    now = datetime(2026, 7, 15, 14, 0)  # doy 196
    expected = historical.get_baseline("Delhi")["clim_temp"][196 - 1]

    record = _source_unavailable_record(location="Delhi", aqi=90)
    upgraded = degradation_ladder.apply_historical_fallback(record, "Delhi", now=now)

    assert upgraded["data_tier"] == "historical_baseline"
    assert upgraded["temp"] == expected
    assert upgraded["source"] == "Historical"
    assert upgraded["aqi"] == 90          # live AQI preserved
    assert "typical temperature" in upgraded["message"]


def test_apply_historical_fallback_leaves_live_tiers_untouched():
    live = {"data_tier": "exact", "temp": 31.0, "source": "Open-Meteo"}
    assert degradation_ladder.apply_historical_fallback(live, "Delhi") is live


def test_apply_historical_fallback_stays_gap_when_no_baseline():
    # A location with no preloaded baseline must stay an honest source_unavailable.
    record = _source_unavailable_record(location="Nowhere-XYZ-123")
    result = degradation_ladder.apply_historical_fallback(record, "Nowhere-XYZ-123")
    assert result["data_tier"] == "source_unavailable"
    assert result["temp"] is None
