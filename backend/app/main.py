"""
WeatherGPT API — entrypoint.
Run locally with: uvicorn app.main:app --reload --app-dir backend
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.degradation_ladder import get_weather
from app.core.home_view import get_home_view

app = FastAPI(title="WeatherGPT API", version="0.1.0")

# CORS — let the browser frontend call this API. Origins are configurable via the
# FRONTEND_ORIGINS env var (comma-separated) so the deployed frontend URL can be
# added without a code change; defaults to the local Vite dev server.
_DEFAULT_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
_origins = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", _DEFAULT_ORIGINS).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {"status": "ok", "service": "WeatherGPT API"}


@app.get("/weather/{location_name}")
def weather(location_name: str):
    """
    Current-conditions endpoint — returns the normalized weather record for a
    location, tagged with its data_tier. This is NOT the final /chat endpoint
    (Section 3.10 of the Architecture doc) — that comes in Sprint 2 once the
    LLM/grounding layer is built on top of this.
    """
    return get_weather(location_name)


@app.get("/home/{location_name}")
def home(location_name: str):
    """
    Composite Home-screen view: current conditions + hourly forecast + a
    rule-based recommendation, assembled in one response (Section 3.10).
    """
    return get_home_view(location_name)
