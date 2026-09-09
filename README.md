# WeatherGPT — SIH 2026 (SIH26068)

A grounded, proactive, role-aware weather-intelligence platform for IMD/MoES.
See `docs/` for the full plan before writing any code.

## Docs (read in this order)
1. `docs/SIH26068_WeatherGPT_Architecture_and_Build_Plan.md` — what we're building, how it's architected, the day-by-day Sprint plan, and the API contract (Section 3.10)
2. `docs/SIH26068_WeatherGPT_Feature_Brief.md` — every feature, why it's worth building, and how feasible it is
3. `docs/SIH26068_Team_Collaboration_and_AI_Agent_Workflow.md` — Git workflow, task board, this repo's setup steps
4. `docs/WeatherGPT_Mockup.html` — open this in a browser for the visual walkthrough
5. `CLAUDE.md` / `AGENTS.md` / `.cursorrules` — read automatically by AI coding agents; identical content, different filenames for different tools

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
voice. Vitest suite in CI.

Still open in Sprint 2: a user **Settings** screen (default location + language +
farmer preferences) and **chat session persistence** (restore the last
conversation and carry follow-up context). The bn/ta/mr/pa UI strings are a
first pass awaiting native-speaker review, and the Disaster/Travel/Farmer screens
still need to migrate onto the i18n keys. A real IMD warnings connector (currently
a fail-soft stub) also remains. See the Architecture doc, Section 8, for the full
living status and backlog.
