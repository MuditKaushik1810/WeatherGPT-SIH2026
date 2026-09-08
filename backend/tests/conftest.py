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
def no_weatherapi_key(monkeypatch):
    """
    Ensure the WeatherAPI key is unset by default, so the connector fails soft
    (and makes NO live call) unless a test explicitly opts in with monkeypatch.
    Keeps the suite deterministic regardless of a developer's shell env, and
    honors CLAUDE.md's "never hit live endpoints from the test suite".
    """
    monkeypatch.delenv("WEATHERAPI_KEY", raising=False)
