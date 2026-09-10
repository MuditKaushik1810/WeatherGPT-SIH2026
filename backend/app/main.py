"""
WeatherGPT API — entrypoint.
Run locally with: uvicorn app.main:app --reload --app-dir backend
"""
import os

from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

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
from app.farmer.crop_watch import get_crop_watch  # noqa: E402
from app.farmer.crop_planning import get_crop_planning  # noqa: E402
from app.trip.trip_planner import get_trip_plan  # noqa: E402

_IST = ZoneInfo("Asia/Kolkata")

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


class ChatTurn(BaseModel):
    role: str        # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    query: str
    language: str = "en"
    user_id: str | None = None
    # Multi-turn context (both optional, backward-compatible): the location the
    # client carries forward (last resolved place or the user's default) so a
    # location-less follow-up still resolves, and the recent conversation turns
    # for phrasing coherence.
    context_location: str | None = None
    history: list[ChatTurn] | None = None


@app.post("/chat")
def chat(request: ChatRequest):
    """
    Grounded conversational endpoint (Section 3.10). Runs the Sprint 2 pipeline:
    intent extraction → degradation-ladder retrieval → grounding assembler → LLM
    answer (rephrasing only the grounded facts). Never bare-refuses — if the LLM
    is unavailable it returns a deterministic grounded answer. Returns
    {answer, data_tier, source, query_class, audio_url, location}.
    """
    history = [turn.model_dump() for turn in request.history] if request.history else None
    return answer_query(
        request.query,
        request.language,
        request.user_id,
        context_location=request.context_location,
        history=history,
    )


@app.get("/farmer/crop-watch")
def farmer_crop_watch(crop: str, location: str, days_after_sowing: int | None = None):
    """
    Composite Crop Watch view for an already-planted crop (Section 3.10): the
    weighted Crop Risk Index (§3.7), explained weather threats, growth stage, and a
    curated recommended action. Never bare-refuses — returns a stable, honest shape
    even for an unknown crop or unresolved location. `provisional: true` flags that
    the crop rule thresholds still need ICAR/GKMS verification.
    """
    return get_crop_watch(crop, location, days_after_sowing)


@app.get("/farmer/crop-planning")
def farmer_crop_planning(location: str = ""):
    """
    Crop Planning view (Section 3.10) — "what should I grow?": the current season's
    crops ranked by how well the location's temperature fits each crop's optimal
    band, with a short reason and an approximate harvest window. Grounded in the
    curated crop table + live temperature (never LLM-invented); never bare-refuses.
    """
    return get_crop_planning(location)


class TripRequest(BaseModel):
    # `from` is a Python keyword, so accept it via alias while exposing `from_`
    # internally; populate_by_name lets tests construct it with either name.
    model_config = ConfigDict(populate_by_name=True)

    from_: str = Field(alias="from")
    to: str
    # Optional ISO-8601 departure time (treated as IST when naive). Defaults to
    # the next whole hour in the planner.
    departure: str | None = None


@app.post("/trip-plan")
def trip_plan(request: TripRequest):
    """
    Route-aware stop planner (Section 3.10): geocodes origin + destination, routes
    between them (Geoapify), samples checkpoints, and rates each stop from the
    forecast at its ETA (our WeatherAPI→Open-Meteo pipeline) plus nearby facilities
    (Geoapify Places). Provenance is split — weather_source vs routing_source.
    Never bare-refuses: an unresolved endpoint or a dead source returns a stable,
    honestly-labelled shape.
    """
    departure = None
    if request.departure:
        try:
            parsed = datetime.fromisoformat(request.departure)
            departure = parsed if parsed.tzinfo else parsed.replace(tzinfo=_IST)
        except ValueError:
            departure = None  # unparseable → planner defaults to next whole hour
    return get_trip_plan(request.from_, request.to, departure=departure)
