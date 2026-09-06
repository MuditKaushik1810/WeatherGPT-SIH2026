from unittest.mock import patch

from app.core import degradation_ladder


@patch("app.core.degradation_ladder.imd.fetch_warnings")
@patch("app.core.degradation_ladder.open_meteo.fetch_forecast")
def test_normal_location_returns_exact_tier(mock_forecast, mock_warnings):
    mock_forecast.return_value = {
        "temp": 27.0,
        "condition": "light rain",
        "precipitation_chance": 0.6,
        "source": "Open-Meteo",
        "data_tier": "exact",
        "fetched_at": "2026-09-05T00:00:00Z",
    }
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


@patch("app.core.degradation_ladder.imd.fetch_warnings")
@patch("app.core.degradation_ladder.open_meteo.fetch_forecast")
def test_active_imd_warning_is_surfaced(mock_forecast, mock_warnings):
    mock_forecast.return_value = {
        "temp": 30.0, "condition": "overcast", "precipitation_chance": 0.8,
        "source": "Open-Meteo", "data_tier": "exact", "fetched_at": "2026-09-05T00:00:00Z",
    }
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


def _unavailable_forecast():
    """An Open-Meteo record as returned when the source fails soft."""
    return {
        "temp": None, "humidity": None, "precipitation_chance": None,
        "condition": None, "source": "Open-Meteo", "data_tier": "unavailable",
        "fetched_at": "2026-09-06T00:00:00Z", "_raw_hourly": None,
    }


@patch("app.core.degradation_ladder.imd.fetch_warnings")
@patch("app.core.degradation_ladder.open_meteo.fetch_forecast")
def test_forecast_source_down_but_warning_active_degrades_not_crashes(mock_forecast, mock_warnings):
    # Open-Meteo is down, but IMD still has an official warning to surface.
    mock_forecast.return_value = _unavailable_forecast()
    mock_warnings.return_value = {
        "warnings": ["Cyclone warning - Odisha coast"],
        "source": "IMD", "data_tier": "exact", "fetched_at": "2026-09-06T00:00:00Z",
    }

    result = degradation_ladder.get_weather("Puri")

    assert result["data_tier"] == "source_unavailable"
    assert result["temp"] is None
    assert result["warnings"] == ["Cyclone warning - Odisha coast"]
    assert result["source"] == "IMD"
    assert "message" in result


@patch("app.core.degradation_ladder.imd.fetch_warnings")
@patch("app.core.degradation_ladder.open_meteo.fetch_forecast")
def test_all_live_sources_down_never_bare_refuses(mock_forecast, mock_warnings):
    # Both live sources unavailable — still an honest, message-bearing record,
    # never an unhandled crash (which is what the raw connector used to do).
    mock_forecast.return_value = _unavailable_forecast()
    mock_warnings.return_value = {
        "warnings": [], "source": "IMD", "data_tier": "unavailable",
        "fetched_at": "2026-09-06T00:00:00Z",
    }

    result = degradation_ladder.get_weather("Delhi")

    assert result["data_tier"] == "source_unavailable"
    assert result["warnings"] == []
    assert result["message"]


@patch("app.core.degradation_ladder.imd.fetch_warnings")
@patch("app.core.degradation_ladder.open_meteo.fetch_forecast")
def test_transient_source_outage_is_not_cached(mock_forecast, mock_warnings):
    # A brief outage must not be served stale for the full TTL after recovery.
    mock_forecast.return_value = _unavailable_forecast()
    mock_warnings.return_value = {
        "warnings": [], "source": "IMD", "data_tier": "unavailable",
        "fetched_at": "2026-09-06T00:00:00Z",
    }
    first = degradation_ladder.get_weather("Jaipur")
    assert first["data_tier"] == "source_unavailable"

    # Source recovers on the next call — we must re-fetch, not serve the cached gap.
    mock_forecast.return_value = {
        "temp": 33.0, "humidity": 40, "precipitation_chance": 0.1,
        "condition": "clear sky", "source": "Open-Meteo", "data_tier": "exact",
        "fetched_at": "2026-09-06T00:05:00Z", "_raw_hourly": {},
    }
    second = degradation_ladder.get_weather("Jaipur")
    assert second["data_tier"] == "exact"
    assert second["temp"] == 33.0
