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
