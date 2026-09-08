"""
WeatherAPI connector tests — all external calls mocked (CLAUDE.md: never hit
live endpoints from the test suite).

Focus: the fail-soft contract (missing key / dead / rate-limited / malformed
source returns an "unavailable" drop-in record, never raises) and that a healthy
response is translated into the same record shape as the Open-Meteo connector,
reading the *current* hour rather than midnight.
"""
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import requests

from app.connectors import weatherapi


def _healthy_payload():
    # Two hours in WeatherAPI's own format ("YYYY-MM-DD HH:MM", space + text
    # condition), so the tests exercise the time/condition translation.
    return {
        "forecast": {
            "forecastday": [
                {
                    "hour": [
                        {
                            "time": "2026-09-08 00:00", "temp_c": 24.0, "feelslike_c": 25.0,
                            "humidity": 90, "wind_kph": 6.0, "chance_of_rain": 10,
                            "condition": {"text": "Clear"},
                        },
                        {
                            "time": "2026-09-08 14:00", "temp_c": 33.0, "feelslike_c": 37.0,
                            "humidity": 45, "wind_kph": 14.0, "chance_of_rain": 20,
                            "condition": {"text": "Partly cloudy"},
                        },
                    ]
                }
            ]
        }
    }


@patch("app.connectors.weatherapi.requests.get")
def test_missing_key_fails_soft_without_calling_the_network(mock_get):
    # autouse fixture unsets WEATHERAPI_KEY, so no key is present here.
    result = weatherapi.fetch_forecast(28.6, 77.2)

    assert result["data_tier"] == "unavailable"
    assert result["source"] == "WeatherAPI"
    assert result["temp"] is None
    assert result["_raw_hourly"] is None
    mock_get.assert_not_called()  # never touch the network without a key


@patch("app.connectors.weatherapi.requests.get")
def test_healthy_response_reads_current_hour_not_midnight(mock_get, monkeypatch):
    monkeypatch.setenv("WEATHERAPI_KEY", "test-key")
    mock_get.return_value.raise_for_status.return_value = None
    mock_get.return_value.json.return_value = _healthy_payload()
    now = datetime(2026, 9, 8, 14, 15, tzinfo=ZoneInfo("Asia/Kolkata"))

    result = weatherapi.fetch_forecast(28.6, 77.2, now=now)

    assert result["data_tier"] == "exact"
    assert result["source"] == "WeatherAPI"
    assert result["temp"] == 33.0            # 14:00 entry, not midnight's 24.0
    assert result["feels_like"] == 37.0
    assert result["humidity"] == 45
    assert result["wind_speed"] == 14.0
    assert result["precipitation_chance"] == 0.2
    assert result["condition"] == "Partly cloudy"
    # _raw_hourly is in the Open-Meteo shape so the shared helpers work on it.
    assert result["_raw_hourly"]["time"][1] == "2026-09-08T14:00"
    assert result["_raw_hourly"]["condition_text"][1] == "Partly cloudy"


@patch("app.connectors.weatherapi.requests.get")
def test_http_error_returns_unavailable(mock_get, monkeypatch):
    monkeypatch.setenv("WEATHERAPI_KEY", "test-key")
    mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("429")

    result = weatherapi.fetch_forecast(28.6, 77.2)

    assert result["data_tier"] == "unavailable"
    assert result["temp"] is None


@patch("app.connectors.weatherapi.requests.get")
def test_network_error_returns_unavailable(mock_get, monkeypatch):
    monkeypatch.setenv("WEATHERAPI_KEY", "test-key")
    mock_get.side_effect = requests.exceptions.ConnectionError("network down")

    result = weatherapi.fetch_forecast(28.6, 77.2)

    assert result["data_tier"] == "unavailable"


@patch("app.connectors.weatherapi.requests.get")
def test_malformed_payload_returns_unavailable(mock_get, monkeypatch):
    monkeypatch.setenv("WEATHERAPI_KEY", "test-key")
    mock_get.return_value.raise_for_status.return_value = None
    mock_get.return_value.json.return_value = {"unexpected": "shape"}

    result = weatherapi.fetch_forecast(28.6, 77.2)

    assert result["data_tier"] == "unavailable"
