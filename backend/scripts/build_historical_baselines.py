"""
One-time builder for the preloaded historical dataset (Architecture doc §3.4 / §8.2).

Fetches 10 years (2016-2025) of daily mean temperature + precipitation from
Open-Meteo's Archive API for a curated set of ~150 cities (all state capitals +
the highest-population cities — see trend_cities.txt), and writes per-city DERIVED
aggregates the Trend Engine (Sprint 3) consumes:

  - clim_temp / clim_precip : 366 day-of-year averages (the multi-year baseline)
  - years / annual_temp / annual_precip : per-year values (for trend regression)

Only ~150 cities are preloaded because 510 x 10yr exceeds Open-Meteo's free
archive quota; the long tail of smaller cities gets its baseline on-demand
(fetched + cached) when the Trend Engine needs it.

RESUMABLE + rate-limit-aware: it saves progress incrementally, skips cities
already present, and backs off on HTTP 429 (sleeps through the hourly cooldown;
stops cleanly if the daily quota is hit — just re-run later to continue):

    python backend/scripts/build_historical_baselines.py

Source: Open-Meteo Archive API (https://open-meteo.com/en/docs/historical-weather-api) — free, no key.
"""
import json
import os
import sys
import time
from datetime import date

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
CITIES = os.path.join(HERE, "..", "app", "data", "static_cities.json")
TARGETS = os.path.join(HERE, "trend_cities.txt")
OUT = os.path.join(HERE, "..", "app", "data", "historical_baselines.json")
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
START, END = "2016-01-01", "2025-12-31"
YEARS = list(range(2016, 2026))
COMMENT = (
    "Preloaded historical baselines for ~150 major Indian cities (all capitals + "
    "highest-population), derived from 10 years (2016-2025) of Open-Meteo Archive "
    "daily data (https://open-meteo.com/, free). clim_temp/clim_precip = 366 "
    "day-of-year averages (multi-year baseline); years/annual_temp/annual_precip = "
    "per-year values for trend regression. Built by "
    "backend/scripts/build_historical_baselines.py; raw daily is not stored. Other "
    "cities get their baseline on-demand in the Trend Engine (Sprint 3)."
)


def fetch_city(lat, lon):
    params = {
        "latitude": lat, "longitude": lon, "start_date": START, "end_date": END,
        "daily": "temperature_2m_mean,precipitation_sum", "timezone": "Asia/Kolkata",
    }
    r = requests.get(ARCHIVE_URL, params=params, timeout=60)
    r.raise_for_status()
    return r.json()["daily"]


def aggregate(daily):
    times, temps, precs = daily["time"], daily["temperature_2m_mean"], daily["precipitation_sum"]
    doy_t = [[] for _ in range(367)]
    doy_p = [[] for _ in range(367)]
    yr_t = {y: [] for y in YEARS}
    yr_p = {y: [] for y in YEARS}
    for t, tp, pr in zip(times, temps, precs):
        y, m, d = int(t[:4]), int(t[5:7]), int(t[8:10])
        doy = date(y, m, d).timetuple().tm_yday
        if tp is not None:
            doy_t[doy].append(tp); yr_t[y].append(tp)
        if pr is not None:
            doy_p[doy].append(pr); yr_p[y].append(pr)
    mean = lambda xs: round(sum(xs) / len(xs), 1) if xs else None
    return {
        "clim_temp": [mean(doy_t[i]) for i in range(1, 367)],
        "clim_precip": [mean(doy_p[i]) for i in range(1, 367)],
        "years": YEARS,
        "annual_temp": [mean(yr_t[y]) for y in YEARS],
        "annual_precip": [round(sum(yr_p[y]), 1) if yr_p[y] else None for y in YEARS],
    }


def save(result):
    with open(OUT, "w") as f:
        json.dump(result, f, ensure_ascii=False)
        f.write("\n")


def main():
    cities = json.load(open(CITIES)); cities.pop("_comment", None)
    targets = [ln.strip() for ln in open(TARGETS) if ln.strip()]

    result = json.load(open(OUT)) if os.path.exists(OUT) else {}
    result["_comment"] = COMMENT
    todo = [n for n in targets if n in cities and n not in result]
    print(f"targets={len(targets)} done={len(targets) - len(todo)} todo={len(todo)}", flush=True)

    added = 0
    for i, name in enumerate(todo, 1):
        lat, lon = cities[name]
        for attempt in range(16):
            try:
                result[name] = aggregate(fetch_city(lat, lon)); added += 1
                break
            except requests.HTTPError as e:
                code = e.response.status_code if e.response is not None else 0
                if code != 429:
                    print(f"  SKIP {name}: HTTP {code}", flush=True); break
                reason = ""
                try:
                    reason = e.response.json().get("reason", "")
                except Exception:
                    pass
                if "Daily" in reason:
                    print(f"  DAILY limit reached at {name}; saving + stopping (re-run later).", flush=True)
                    save(result); return 2
                wait = 300 if "Hourly" in reason else 65
                print(f"  429 ({reason[:24]}) at {name}; sleep {wait}s (try {attempt + 1})", flush=True)
                time.sleep(wait)
            except Exception as e:
                print(f"  SKIP {name}: {e}", flush=True); break
        if i % 10 == 0:
            save(result); print(f"  {i}/{len(todo)} (added {added})", flush=True)
        time.sleep(1.5)

    save(result)
    have = sum(1 for n in targets if n in result)
    print(f"DONE: {have}/{len(targets)} target cities, file {os.path.getsize(OUT) / 1e6:.1f} MB", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
