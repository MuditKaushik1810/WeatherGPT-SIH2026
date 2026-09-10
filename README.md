# WeatherGPT — SIH 2026

**Problem Statement ID:** SIH26068

**Title:** WeatherGPT: Conversational AI for Weather Forecasting, Alerts, and Climate Information

**Theme:** Disaster Management · **Category:** Software

WeatherGPT is a grounded, proactive, role-aware weather-intelligence platform for IMD/MoES. It turns live weather data, forecasts, alerts, and curated domain rules into clear conversational guidance, including multilingual and voice-enabled access.

## Problem statement

Weather data is spread across portals, bulletins, satellite products, and forecast systems. Individuals, farmers, travellers, and disaster stakeholders need fast, contextual, actionable answers rather than raw data alone.

## Proposed solution

WeatherGPT combines a React web application with a FastAPI service. It retrieves live forecast data through a fail-safe source ladder, grounds conversational answers in verified data, supports Indian languages and browser voice features, and provides dedicated Farmer, Travel, and Disaster workflows.

## Key features

- Live current conditions and hourly forecasts with graceful fallbacks
- Grounded, multi-turn conversational weather assistance
- Multilingual UI and voice input/output
- Farmer Mode: crop planning and crop-watch advisories
- Route-aware travel planning and disaster-awareness views
- Traceable data provenance and an API test suite in continuous integration

## Technology stack

- **Frontend:** React, Vite, Vitest
- **Backend:** Python, FastAPI, Pytest
- **Data/services:** WeatherAPI, Open-Meteo, Nominatim, Geoapify; optional Gemini/Groq for answer phrasing
- **Deployment:** Render

## Architecture and documentation

- [Architecture overview](docs/architecture.md)
- [Architecture and build plan](docs/SIH26068_WeatherGPT_Architecture_and_Build_Plan.md)
- [Feature brief](docs/SIH26068_WeatherGPT_Feature_Brief.md)
- [Deployment notes](docs/DEPLOYMENT.md)
- [Submission checklist](SUBMISSION_GUIDE.md)

## Team

Add each official team member and their contribution before submitting.

| Name | Role / contribution |
| --- | --- |
| _Add team member_ | _Add role_ |

## Quick start — backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate   # or your preferred venv tool
pip install -r requirements.txt
cp .env.example .env    # fill in real values, never commit this file
pytest -v                # confirm the test suite passes before you start
uvicorn app.main:app --reload
```

Then visit `http://localhost:8000/` for the health check,
`http://localhost:8000/weather/Delhi` to see the degradation ladder in action,
or `http://localhost:8000/docs` for the auto-generated API docs. `POST /chat`
answers natural-language questions (grounded); set `GEMINI_API_KEY` in `.env` for
LLM-phrased answers, otherwise it returns a deterministic grounded answer.

## Quick start — frontend

```bash
cd frontend
npm install
npm run dev      # Vite dev server (usually http://localhost:5173)
npm test         # Vitest suite
npm run build    # production build
```

Set `VITE_API_BASE_URL` (see `frontend/.env.example`) to point at the backend;
it defaults to `http://localhost:8000`. On the Home screen, enter a location and
it fetches live weather from the backend's `/home/{location}` endpoint.

## Current status

**Sprint 1 (foundation) — complete and deployed.** Backend: static geocoding
(~510 Indian cities + Nominatim fallback); a keyed **WeatherAPI** forecast
connector (primary) with **Open-Meteo** as fallback and a preloaded **historical
baseline** tier below that; a separate Open-Meteo Air Quality connector; the
degradation ladder (exact → regional → historical baseline → source-unavailable →
honest gap — never a bare refusal); normalization to the shared data shape; and a
short-TTL cache — all covered by a `pytest` suite in CI. Endpoints
`/weather/{location}` and the composite `/home/{location}` (current + hourly + a
rule-based recommendation). Deployed on Render: the FastAPI backend and a
React/Vite static-site frontend (`render.yaml` + `docs/DEPLOYMENT.md`).

**Sprint 2 (conversational core) — in place.** The grounded chat pipeline behind
`POST /chat`: rule/keyword **intent extraction** → degradation-ladder retrieval →
a **grounding assembler** (the anti-hallucination step — the model only rephrases
verified facts, never invents) → an answer from **Gemini Flash** (Groq fallback;
both keyed via env; fail-soft to a deterministic grounded answer when no key). It
is forecast-aware ("tomorrow" / "this week" pull the day's forecast), never
bare-refuses, and caches settled answers briefly (short TTL). Frontend
(React + Vite): a live-wired **Home** tab, a **Disaster** tab, a **Travel
Planner** tab, **Farmer Mode** (Crop Watch + Crop Planning), a unified fixed
bottom nav, and a themed **Chat** screen — opened from Home's "Ask WeatherGPT"
card / floating button, with situational suggestions, a provenance chip on every
answer, and Web Speech voice input **and** output. The UI is **multilingual**:
a lightweight app-wide i18n layer (en, hi, bn, ta, mr, pa) re-renders the whole
app in the chosen language, which also drives the LLM answer language and browser
voice. `POST /chat` is **multi-turn** — it carries a context location + recent
history, so a bare follow-up ("what about tomorrow?") resolves against the last
place instead of dead-ending. A user **Settings** screen (default/saved locations,
language, farmer preferences) lives off the header menu, and the **chat
conversation persists** on-device (~1 day) and restores on return. Vitest suite
in CI.

Still open in Sprint 2: native-speaker review of the bn/ta/mr/pa UI strings, and
migrating the Disaster/Travel/Farmer screens onto the i18n keys. Next up is
**Sprint 3** — the Farmer Advisory backend (crop rules, Disease Suitability Model,
risk scoring) and the Trip Planner backend. A real IMD warnings connector
(currently a fail-soft stub) also remains. See the Architecture doc, Section 8,
for the full living status and backlog.
