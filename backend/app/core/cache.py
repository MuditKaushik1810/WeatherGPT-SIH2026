"""
Short-TTL in-memory response cache. Interface (get/set) stays stable even if
this is later swapped for a Postgres- or Redis-backed cache — nothing that
calls get()/set() needs to change.
"""
import time

_store: dict[str, tuple[float, dict]] = {}
DEFAULT_TTL_SECONDS = 900  # 15 minutes


def get(key: str):
    entry = _store.get(key)
    if not entry:
        return None
    expires_at, value = entry
    if time.time() > expires_at:
        del _store[key]
        return None
    return value


def set(key: str, value: dict, ttl: int = DEFAULT_TTL_SECONDS):
    _store[key] = (time.time() + ttl, value)


def clear():
    """Wipe the entire cache — used by tests, and available for an admin/debug endpoint."""
    _store.clear()
