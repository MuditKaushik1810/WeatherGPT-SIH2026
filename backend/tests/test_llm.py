"""
LLM connector tests — all HTTP mocked (CLAUDE.md: never hit live endpoints).
The autouse fixture unsets the keys, so the default state is "no provider".
"""
from unittest.mock import patch

import requests

from app.connectors import llm


@patch("app.connectors.llm.requests.post")
def test_complete_with_no_keys_returns_none_and_makes_no_call(mock_post):
    # Keys unset by the autouse fixture -> both providers skip, no network.
    assert llm.complete("sys", "user") is None
    mock_post.assert_not_called()


@patch("app.connectors.llm.requests.post")
def test_gemini_response_is_parsed(mock_post, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    mock_post.return_value.raise_for_status.return_value = None
    mock_post.return_value.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "It is 31.9°C and rainy."}]}}]
    }
    assert llm.complete("sys", "user") == "It is 31.9°C and rainy."


@patch("app.connectors.llm.requests.post")
def test_groq_response_is_parsed(mock_post, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")   # no Gemini key -> Gemini skips, Groq used
    mock_post.return_value.raise_for_status.return_value = None
    mock_post.return_value.json.return_value = {
        "choices": [{"message": {"content": "Rain likely this evening."}}]
    }
    assert llm.complete("sys", "user") == "Rain likely this evening."


def test_complete_prefers_gemini_then_falls_back_to_groq():
    with patch("app.connectors.llm._try_gemini", return_value=None) as g, \
         patch("app.connectors.llm._try_groq", return_value="groq answer") as q:
        assert llm.complete("sys", "user") == "groq answer"
        g.assert_called_once()
        q.assert_called_once()

    # When Gemini answers, Groq is never consulted.
    with patch("app.connectors.llm._try_gemini", return_value="gemini answer"), \
         patch("app.connectors.llm._try_groq") as q2:
        assert llm.complete("sys", "user") == "gemini answer"
        q2.assert_not_called()


@patch("app.connectors.llm.requests.post")
def test_gemini_http_error_fails_soft_to_none(mock_post, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    mock_post.side_effect = requests.exceptions.HTTPError("429")
    # No Groq key, so the fallback also yields None — still no raise.
    assert llm.complete("sys", "user") is None
