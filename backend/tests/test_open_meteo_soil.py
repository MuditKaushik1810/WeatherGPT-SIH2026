"""Open-Meteo soil-moisture connector — fail-soft, day-averaged (mocked HTTP)."""
from unittest.mock import MagicMock, patch

import requests

from app.connectors import open_meteo_soil


def test_returns_day_averaged_soil_moisture():
    payload = {"hourly": {"soil_moisture_3_to_9cm": [0.20, 0.30, 0.10]}}
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = payload
    with patch.object(open_meteo_soil.requests, "get", return_value=resp):
        out = open_meteo_soil.fetch_soil_moisture(21.25, 81.63)

    assert out["soil_moisture"] == 0.2      # mean of the three
    assert out["data_tier"] == "exact"
    assert out["source"] == "Open-Meteo"


def test_fails_soft_on_network_error():
    with patch.object(open_meteo_soil.requests, "get", side_effect=requests.ConnectionError("down")):
        out = open_meteo_soil.fetch_soil_moisture(21.25, 81.63)

    assert out["soil_moisture"] is None     # never raises
    assert out["data_tier"] == "unavailable"


def test_fails_soft_on_empty_series():
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"hourly": {"soil_moisture_3_to_9cm": [None, None]}}
    with patch.object(open_meteo_soil.requests, "get", return_value=resp):
        out = open_meteo_soil.fetch_soil_moisture(21.25, 81.63)

    assert out["soil_moisture"] is None
