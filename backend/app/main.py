"""
WeatherGPT API — entrypoint.
Run locally with: uvicorn app.main:app --reload --app-dir backend
"""
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load backend/.env (if present) so local dev can set WEATHERAPI_KEY /
# FRONTEND_ORIGINS without exporting them every shell. Pointed explicitly at
# backend/.env because the server runs from the repo root (--app-dir backend),
# where the default upward search wouldn't find it. A no-op in production —
# Render injects env vars directly and there's no .env file. Must run before
# any os.getenv below.
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from app.core.degradation_ladder import get_weather  # noqa: E402  (after load_dotenv, intentionally)
from app.core.home_view import get_home_view  # noqa: E402
from app.core.chat import answer_query  # noqa: E402

app = FastAPI(title="WeatherGPT API", version="0.1.0")

# CORS — let the browser frontend call this API. The deployed frontend URL is
# configured via the FRONTEND_ORIGINS env var (comma-separated). The local Vite
# dev origins are ALWAYS allowed on top of it, so local development works without
# editing the env — and allowing localhost is harmless (a page served from a
# user's own machine is not an attacker-controlled origin).
_LOCAL_DEV_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
_configured = [o.strip() for o in os.getenv("FRONTEND_ORIGINS", "").split(",") if o.strip()]
_origins = list(dict.fromkeys(_configured + _LOCAL_DEV_ORIGINS))  # dedupe, keep order
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["GET", "POST"],
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


class ChatRequest(BaseModel):
    query: str
    language: str = "en"
    user_id: str | None = None


@app.post("/chat")
def chat(request: ChatRequest):
    """
    Grounded conversational endpoint (Section 3.10). Runs the Sprint 2 pipeline:
    intent extraction → degradation-ladder retrieval → grounding assembler → LLM
    answer (rephrasing only the grounded facts). Never bare-refuses — if the LLM
    is unavailable it returns a deterministic grounded answer. Returns
    {answer, data_tier, source, query_class, audio_url}.
    """
    return answer_query(request.query, request.language, request.user_id)
