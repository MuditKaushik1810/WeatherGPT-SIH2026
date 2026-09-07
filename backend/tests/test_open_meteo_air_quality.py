"""
Open-Meteo Air Quality connector tests — all external calls mocked (CLAUDE.md:
never hit live IMD/Open-Meteo endpoints from the test suite).

Same fail-soft contract as the other connectors: a dead / rate-limited /
schema-changed source must return an "unavailable" record with aqi=None, never
raise up to the degradation ladder.
"""
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import requests

from app.connectors import open_meteo_air_quality


@patch("app.connectors.open_meteo_air_quality.requests.get")
def test_network_error_returns_unavailable_not_exception(mock_get):
    mock_get.side_effect = requests.exceptions.ConnectionError("network down")

    result = open_meteo_air_quality.fetch_air_quality(28.6, 77.2)

    assert result["data_tier"] == "unavailable"
    assert result["aqi"] is None
    assert result["source"] == "Open-Meteo Air Quality"


@patch("app.connectors.open_meteo_air_quality.requests.get")
def test_http_error_returns_unavailable(mock_get):
    mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("429")

    result = open_meteo_air_quality.fetch_air_quality(28.6, 77.2)

    assert result["data_tier"] == "unavailable"
    assert result["aqi"] is None


@patch("app.connectors.open_meteo_air_quality.requests.get")
def test_malformed_payload_returns_unavailable(mock_get):
    mock_get.return_value.raise_for_status.return_value = None
    mock_get.return_value.json.return_value = {"unexpected": "shape"}

    result = open_meteo_air_quality.fetch_air_quality(28.6, 77.2)

    assert result["data_tier"] == "unavailable"
    assert result["aqi"] is None


@patch("app.connectors.open_meteo_air_quality.requests.get")
def test_healthy_response_parses_aqi(mock_get):
    mock_get.return_value.raise_for_status.return_value = None
    mock_get.return_value.json.return_value = {"hourly": {"us_aqi": [86]}}

    result = open_meteo_air_quality.fetch_air_quality(28.6, 77.2)

    assert result["data_tier"] == "exact"
    assert result["aqi"] == 86
    assert result["source"] == "Open-Meteo Air Quality"


@patch("app.connectors.open_meteo_air_quality.requests.get")
def test_reads_current_hour_aqi_not_midnight(mock_get):
    mock_get.return_value.raise_for_status.return_value = None
    mock_get.return_value.json.return_value = {
        "hourly": {
            "time": ["2026-09-07T00:00", "2026-09-07T20:00"],
            "us_aqi": [40, 130],
        }
    }
    now = datetime(2026, 9, 7, 20, 5, tzinfo=ZoneInfo("Asia/Kolkata"))

    result = open_meteo_air_quality.fetch_air_quality(28.6, 77.2, now=now)

    assert result["aqi"] == 130  # 20:00 entry, not midnight's 40
