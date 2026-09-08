"""
Conversational core + POST /chat tests. External calls mocked: the LLM
(app.connectors.llm.complete) and the data layer (degradation_ladder.get_weather)
are patched, so nothing hits a live endpoint (CLAUDE.md).

The point is the two guarantees end-to-end: the answer is grounded in the
retrieved record, and the endpoint NEVER bare-refuses — including when the LLM
is unavailable (deterministic fallback) and when no location is found.
"""
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core import chat
from app.main import app


def _exact_record():
    return {
        "location": "Delhi", "temp": 31.9, "condition": "light rain shower",
        "precipitation_chance": 0.77, "humidity": 84, "feels_like": 32.4,
        "wind_speed": 11.5, "aqi": 158, "warnings": [], "source": "WeatherAPI",
        "data_tier": "exact", "fetched_at": "2026-09-09T09:00:00Z",
    }


@patch("app.core.degradation_ladder.get_weather")
@patch("app.connectors.llm.complete")
def test_answer_query_uses_llm_when_available(mock_llm, mock_get_weather):
    mock_get_weather.return_value = _exact_record()
    mock_llm.return_value = "It's 31.9°C with a light rain shower in Delhi."

    result = chat.answer_query("what's the weather in Delhi?")

    assert result["answer"] == "It's 31.9°C with a light rain shower in Delhi."
    assert result["data_tier"] == "exact"
    assert result["source"] == "WeatherAPI"
    assert result["query_class"] == "realtime"
    assert result["audio_url"] is None
    mock_get_weather.assert_called_once_with("Delhi")


@patch("app.core.degradation_ladder.get_weather")
@patch("app.connectors.llm.complete", return_value=None)   # no LLM available
def test_answer_query_falls_back_to_grounded_facts_never_bare_refuses(mock_llm, mock_get_weather):
    mock_get_weather.return_value = _exact_record()

    result = chat.answer_query("weather in Delhi")

    # Deterministic, grounded, non-empty — built straight from the facts.
    assert "31.9°C" in result["answer"]
    assert "Delhi" in result["answer"]
    assert result["data_tier"] == "exact"


@patch("app.core.degradation_ladder.get_weather")
@patch("app.connectors.llm.complete", return_value=None)
def test_answer_query_historical_baseline_is_framed_as_typical(mock_llm, mock_get_weather):
    mock_get_weather.return_value = {
        "location": "Delhi", "temp": 28.7, "condition": None, "precipitation_chance": None,
        "humidity": None, "feels_like": None, "wind_speed": None, "aqi": 164, "warnings": [],
        "source": "Historical", "data_tier": "historical_baseline", "fetched_at": "x",
        "message": "Live forecast for 'Delhi' is temporarily unavailable...",
    }
    result = chat.answer_query("weather in Delhi")
    assert result["data_tier"] == "historical_baseline"
    assert "typical" in result["answer"].lower()


@patch("app.core.degradation_ladder.get_weather")
@patch("app.connectors.llm.complete", return_value=None)
def test_answer_query_with_no_location_asks_for_one_without_fetching(mock_llm, mock_get_weather):
    result = chat.answer_query("hello, what can you do?")

    mock_get_weather.assert_not_called()           # nothing to fetch without a place
    assert result["data_tier"] == "unresolved_location"
    assert result["query_class"] == "realtime"
    assert "city" in result["answer"].lower() or "district" in result["answer"].lower()


@patch("app.core.degradation_ladder.get_weather")
@patch("app.connectors.llm.complete")
def test_chat_endpoint_returns_contract_shape(mock_llm, mock_get_weather):
    mock_get_weather.return_value = _exact_record()
    mock_llm.return_value = "31.9°C, light rain in Delhi."
    client = TestClient(app)

    resp = client.post("/chat", json={"query": "weather in Delhi", "language": "en"})

    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"answer", "data_tier", "source", "query_class", "audio_url"}
    assert body["answer"] == "31.9°C, light rain in Delhi."
    assert body["query_class"] == "realtime"
