"""
IMD connector — official warnings/bulletins.

IMD does not offer a clean public JSON API for warnings. This file defines the
CONTRACT the rest of the pipeline depends on; the team fills in real
scraping/parsing logic in _parse_warnings().

CRITICAL RULE: this connector must never raise an exception up to the
degradation ladder. If IMD is unreachable, its page structure changed, or
parsing isn't implemented yet, fail soft and return an empty warnings list
with data_tier="unavailable" — the ladder then proceeds to the next tier
instead of crashing the whole pipeline. This mirrors the same anti-refusal
principle used everywhere else in the product (Architecture doc, Section 3.4).

TODO for whoever owns this file:
1. Inspect https://mausam.imd.gov.in (or the specific district/state bulletin
   page you're targeting) for actual structure.
2. Decide: HTML scraping (requests + BeautifulSoup) vs. any feed IMD exposes
   specifically for warnings.
3. Implement _parse_warnings() below. Keep the public fetch_warnings() return
   shape exactly as documented — everything downstream depends on it.
"""
from datetime import datetime, timezone


def fetch_warnings(location: str) -> dict:
    """
    Returns:
        {
          "warnings": list[str],       # empty list if none active, or if IMD is unreachable
          "source": "IMD",
          "data_tier": "exact" | "unavailable",
          "fetched_at": iso timestamp string,
        }
    """
    try:
        warnings = _parse_warnings(location)
        tier = "exact" if warnings is not None else "unavailable"
        return {
            "warnings": warnings or [],
            "source": "IMD",
            "data_tier": tier,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception:
        # Fail soft, always. See module docstring.
        return {
            "warnings": [],
            "source": "IMD",
            "data_tier": "unavailable",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }


def _parse_warnings(location: str):
    """
    TODO: implement real IMD scraping/parsing here.
    Return None (not an exception) if not yet implemented for this location —
    the caller treats None the same as "no data available right now."
    """
    return None
