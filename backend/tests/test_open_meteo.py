"""
Open-Meteo connector tests — all external calls mocked (CLAUDE.md: never hit
live IMD/Open-Meteo endpoints from the test suite).

The point of these tests is the fail-soft contract: a dead, rate-limited, or
schema-changed source must return an "unavailable" record, never raise up to
the degradation ladder.
"""
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import requests

from app.connectors import open_meteo


@patch("app.connectors.open_meteo.requests.get")
def test_network_error_returns_unavailable_not_exception(mock_get):
    mock_get.side_effect = requests.exceptions.ConnectionError("network down")

    result = open_meteo.fetch_forecast(28.6, 77.2)

    assert result["data_tier"] == "unavailable"
    assert result["temp"] is None
    assert result["source"] == "Open-Meteo"


@patch("app.connectors.open_meteo.requests.get")
def test_http_error_returns_unavailable(mock_get):
    # e.g. a 429 rate-limit or 500 from Open-Meteo.
    mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("429")

    result = open_meteo.fetch_forecast(28.6, 77.2)

    assert result["data_tier"] == "unavailable"
    assert result["temp"] is None


@patch("app.connectors.open_meteo.requests.get")
def test_malformed_payload_returns_unavailable(mock_get):
    # Source reachable but its JSON shape changed — no "hourly" key.
    mock_get.return_value.raise_for_status.return_value = None
    mock_get.return_value.json.return_value = {"unexpected": "shape"}

    result = open_meteo.fetch_forecast(28.6, 77.2)

    assert result["data_tier"] == "unavailable"


@patch("app.connectors.open_meteo.requests.get")
def test_null_precipitation_still_returns_a_forecast(mock_get):
    # A missing precip value must not cost us the whole otherwise-valid record.
    mock_get.return_value.raise_for_status.return_value = None
    mock_get.return_value.json.return_value = {
        "hourly": {
            "temperature_2m": [27.0],
            "relative_humidity_2m": [80],
            "apparent_temperature": [29.0],
            "precipitation_probability": [None],
            "weathercode": [61],
            "wind_speed_10m": [12.0],
        }
    }

    result = open_meteo.fetch_forecast(28.6, 77.2)

    assert result["data_tier"] == "exact"
    assert result["temp"] == 27.0
    assert result["precipitation_chance"] is None
    assert result["condition"] == "slight rain"


@patch("app.connectors.open_meteo.requests.get")
def test_healthy_response_is_parsed(mock_get):
    mock_get.return_value.raise_for_status.return_value = None
    mock_get.return_value.json.return_value = {
        "hourly": {
            "temperature_2m": [30.5],
            "relative_humidity_2m": [55],
            "apparent_temperature": [33.2],
            "precipitation_probability": [40],
            "weathercode": [2],
            "wind_speed_10m": [8.5],
        }
    }

    result = open_meteo.fetch_forecast(28.6, 77.2)

    assert result["data_tier"] == "exact"
    assert result["temp"] == 30.5
    assert result["precipitation_chance"] == 0.4
    assert result["condition"] == "partly cloudy"
    assert result["humidity"] == 55
    assert result["feels_like"] == 33.2
    assert result["wind_speed"] == 8.5


def test_extract_hourly_forecast_parses_next_hours():
    raw = {
        "time": ["2026-09-06T09:00", "2026-09-06T10:00"],
        "temperature_2m": [28.0, 29.0],
        "weathercode": [2, 61],
        "precipitation_probability": [30, None],
    }

    result = open_meteo.extract_hourly_forecast(raw, hours=2)

    assert len(result) == 2
    assert result[0] == {
        "time": "2026-09-06T09:00",
        "temp": 28.0,
        "condition": "partly cloudy",
        "precipitation_chance": 0.3,
    }
    # A null precip in one hour must not break the row.
    assert result[1]["precipitation_chance"] is None
    assert result[1]["condition"] == "slight rain"


def test_extract_hourly_forecast_missing_data_returns_empty():
    # Source failed soft (_raw_hourly is None) — no crash, just an empty list.
    assert open_meteo.extract_hourly_forecast(None) == []
    assert open_meteo.extract_hourly_forecast({}) == []


def test_summarize_today_computes_extremes_for_today_only():
    raw = {
        "time": ["2026-09-07T00:00", "2026-09-07T12:00", "2026-09-07T23:00", "2026-09-08T00:00"],
        "temperature_2m": [22.0, 41.0, 26.0, 5.0],
        "apparent_temperature": [24.0, 45.0, 28.0, 6.0],
        "precipitation_probability": [10, 70, 20, 90],
        "wind_speed_10m": [8.0, 30.0, 12.0, 55.0],
    }

    summary = open_meteo.summarize_today(raw)

    assert summary["peak_temp"] == 41.0
    assert summary["low_temp"] == 22.0          # tomorrow's 5.0 excluded
    assert summary["peak_feels_like"] == 45.0
    assert summary["max_precip_chance"] == 0.7  # tomorrow's 90% excluded
    assert summary["max_wind"] == 30.0          # tomorrow's 55 excluded


def test_summarize_today_is_none_safe():
    assert open_meteo.summarize_today(None)["peak_temp"] is None

    partial = open_meteo.summarize_today({
        "time": ["2026-09-07T00:00", "2026-09-07T01:00"],
        "temperature_2m": [20.0, 21.0],
    })
    assert partial["peak_temp"] == 21.0
    assert partial["peak_feels_like"] is None
    assert partial["max_wind"] is None
    assert partial["max_precip_chance"] is None


def test_current_hour_index_finds_the_current_hour():
    times = [f"2026-09-07T{h:02d}:00" for h in range(24)]
    now = datetime(2026, 9, 7, 20, 34, tzinfo=ZoneInfo("Asia/Kolkata"))
    assert open_meteo.current_hour_index(times, now=now) == 20


def test_current_hour_index_falls_back_to_zero_when_absent():
    times = [f"2026-09-07T{h:02d}:00" for h in range(24)]
    absent = datetime(2099, 1, 1, 5, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
    assert open_meteo.current_hour_index(times, now=absent) == 0
    assert open_meteo.current_hour_index([], now=absent) == 0


@patch("app.connectors.open_meteo.requests.get")
def test_fetch_forecast_reads_the_current_hour_not_midnight(mock_get):
    mock_get.return_value.raise_for_status.return_value = None
    mock_get.return_value.json.return_value = {
        "hourly": {
            "time": ["2026-09-07T00:00", "2026-09-07T20:00"],
            "temperature_2m": [22.0, 31.0],
            "relative_humidity_2m": [90, 40],
            "apparent_temperature": [24.0, 35.0],
            "precipitation_probability": [10, 5],
            "weathercode": [0, 2],
            "wind_speed_10m": [5.0, 12.0],
        }
    }
    now = datetime(2026, 9, 7, 20, 15, tzinfo=ZoneInfo("Asia/Kolkata"))

    result = open_meteo.fetch_forecast(28.6, 77.2, now=now)

    assert result["data_tier"] == "exact"
    assert result["temp"] == 31.0  # 20:00 entry, not midnight's 22.0
    assert result["humidity"] == 40
    assert result["condition"] == "partly cloudy"


def test_extract_hourly_forecast_starts_at_given_index():
    raw = {
        "time": ["2026-09-07T00:00", "2026-09-07T01:00", "2026-09-07T02:00"],
        "temperature_2m": [20.0, 21.0, 22.0],
        "weathercode": [0, 1, 2],
        "precipitation_probability": [10, 20, 30],
    }

    result = open_meteo.extract_hourly_forecast(raw, hours=2, start=1)

    assert len(result) == 2
    assert result[0]["time"] == "2026-09-07T01:00"
    assert result[0]["temp"] == 21.0
