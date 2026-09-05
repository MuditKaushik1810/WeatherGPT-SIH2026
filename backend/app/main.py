"""
WeatherGPT API — entrypoint.
Run locally with: uvicorn app.main:app --reload --app-dir backend
"""
from fastapi import FastAPI

from app.core.degradation_ladder import get_weather

app = FastAPI(title="WeatherGPT API", version="0.1.0")


@app.get("/")
def health_check():
    return {"status": "ok", "service": "WeatherGPT API"}


@app.get("/weather/{location_name}")
def weather(location_name: str):
    """
    Sprint 1 smoke-test endpoint — returns the normalized weather record for a
    location, tagged with its data_tier. This is NOT the final /chat endpoint
    (Section 3.10 of the Architecture doc) — that comes in Sprint 2 once the
    LLM/grounding layer is built on top of this.
    """
    return get_weather(location_name)
