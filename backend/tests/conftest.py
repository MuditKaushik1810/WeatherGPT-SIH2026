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
