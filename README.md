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

Not yet scaffolded — Sprint 1, Day 1 task. Recommended: `npm create vite@latest frontend -- --template react`,
then build every screen against the mock JSON in `frontend/src/mocks/` (matching
the shapes in Section 3.10) so frontend work is fully decoupled from backend progress.

## Current status

Sprint 1 scaffold: static geocoding table (seed set of ~40 cities — expand
toward ~500), Open-Meteo connector (working, fails soft — degrades instead of
crashing when the source is unreachable), IMD connector (stub — needs real
scraping/parsing implemented), degradation ladder (working, tested), in-memory
cache, normalization to the shared data shape. See the Architecture doc for
what's next.
