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

Then visit `http://localhost:8000/` for the health check, or
`http://localhost:8000/weather/Delhi` to see the degradation ladder in action,
or `http://localhost:8000/docs` for the auto-generated API docs.

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

**Sprint 1 (foundation) — largely complete.** Backend: static geocoding table
(+ Nominatim fallback), Open-Meteo forecast connector and a separate Open-Meteo
Air Quality connector (both fail-soft; current conditions read the actual current
hour), the degradation ladder, normalization to the shared data shape, and a
short-TTL cache — all covered by a `pytest` suite in CI. Endpoints:
`/weather/{location}` and the composite `/home/{location}` (current + hourly + a
rule-based recommendation), with CORS for the browser frontend. Frontend
(React + Vite): a live-wired **Home** tab (location entry, remembered via
localStorage, loading/error states), a **Disaster** tab, and a **Travel Planner**
tab, with a Vitest suite in CI. Deploy config (`render.yaml` +
`docs/DEPLOYMENT.md`) is ready.

Still open in Sprint 1: a deployed instance, the preloaded historical dataset,
expanding the geocoding table (~40 → ~500), and a real IMD warnings connector
(currently a fail-soft stub). See the Architecture doc, Section 8, for the full
status and backlog.
