"""
Shared pytest fixtures. autouse=True means this runs before every single
test automatically — nobody needs to remember to import it.
"""
import pytest

from app.core import cache


@pytest.fixture(autouse=True)
def clear_cache_between_tests():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def no_external_api_keys(monkeypatch):
    """
    Unset every external API key by default, so the keyed connectors (WeatherAPI,
    Gemini, Groq) fail soft and make NO live call unless a test explicitly opts in
    with monkeypatch/mock. Keeps the suite deterministic regardless of a
    developer's shell env, and honors CLAUDE.md's "never hit live endpoints".
    """
    for key in ("WEATHERAPI_KEY", "GEMINI_API_KEY", "GROQ_API_KEY"):
        monkeypatch.delenv(key, raising=False)
