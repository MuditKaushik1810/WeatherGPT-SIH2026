# WeatherGPT — Agent Instructions

## Before writing any code
1. Read this file in full.
2. Look at existing modules in the same layer before building a new one (e.g.
   before building a new data connector, read `backend/app/connectors/open_meteo.py`
   and match its structure — don't invent a new pattern for the same kind of thing).
3. Never duplicate logic that already exists elsewhere in the repo — extend or import it.
4. Read `docs/SIH26068_WeatherGPT_Architecture_and_Build_Plan.md` Section 3.10 before
   touching any API endpoint — the shapes there are the contract.

## Stack (confirmed Sprint 1, Day 1)
- Backend: Python 3.11+, FastAPI
- Frontend: React + Vite
- DB: PostgreSQL (Supabase free tier)
- LLM: Google Gemini Flash (free tier) — Groq as fallback if rate-limited
- Testing: pytest, mocked external calls only (never hit live IMD/Open-Meteo in tests)

## Non-negotiable data contract
Every weather-data record, regardless of source, is normalized to this shape
before it reaches the grounding assembler (see `backend/app/core/normalize.py`):

    {
      "location": str,
      "temp": float,
      "condition": str,
      "precipitation_chance": float,
      "humidity": float,       # % relative humidity (Open-Meteo forecast)
      "feels_like": float,     # apparent temperature, °C (Open-Meteo forecast)
      "wind_speed": float,     # km/h (Open-Meteo forecast)
      "aqi": int,              # US AQI scale (Open-Meteo Air Quality API — NOT India CPCB)
      "warnings": list[str],
      "source": str,          # "IMD" | "Open-Meteo" | "Historical"
      "data_tier": str,       # "exact" | "regional_fallback" | "historical_baseline" | "source_unavailable" | "unresolved_location"
      "fetched_at": datetime,
    }

Any of temp/condition/precipitation_chance/humidity/feels_like/wind_speed/aqi
may be `None` when its source is unavailable (a soft failure) — consumers must
tolerate a null metric rather than assuming every field is populated.

Adding a new field is safe — do it freely, mention it in standup. Renaming,
removing, or changing the type of an existing field is a breaking change —
that needs a visible PR everyone reviews, never a silent edit inside one branch.

Full endpoint-by-endpoint shapes (chat, farmer profile, risk score, trip plan,
disaster alerts, safety guide, historical trends, digest settings) are in
`docs/SIH26068_WeatherGPT_Architecture_and_Build_Plan.md`, Section 3.10.

## The two rules that protect the whole product
1. **Never let the LLM answer without grounding.** Every LLM call that produces
   a user-facing answer must be given a context block built by the grounding
   assembler from real fetched/cached data. The LLM never invents a weather
   fact, a crop threshold, or a safety instruction — it only rephrases and
   personalizes what the grounding assembler gives it.
2. **Never let the LLM bare-refuse.** The final answer-generation prompt must
   never allow a plain "I don't have sufficient data" response. If real data
   is unavailable, the degradation ladder (`backend/app/core/degradation_ladder.py`)
   produces the nearest available alternative, tagged with its `data_tier`,
   and the LLM presents that instead of refusing outright.

## Connectors must fail soft, always
See `backend/app/connectors/imd.py` for the pattern: a connector NEVER raises
an exception up to the degradation ladder. If a source is unreachable or
unparseable, catch it and return an empty/unavailable result with the
appropriate `data_tier` — never crash the pipeline over one bad source.

## Domain content is curated, not generated
Crop rule tables, disease-suitability parameters, and disaster safety guidance
are static, sourced, hand-curated JSON/CSV files (cite the source — ICAR,
GKMS, NDMA — in a comment at the top of the file) — never something an agent
should generate from general knowledge. If a source isn't cited, flag it for
a teammate to verify before merging; don't fill in a plausible-looking number.

## Testing
Every new function in the degradation ladder, risk-index calculator, Disease
Suitability Model, or Trend Engine needs at least one `pytest` test before the
PR is considered done. Mock external API calls — never hit live IMD/Open-Meteo
endpoints from the test suite (see `backend/tests/test_degradation_ladder.py`
for the pattern). Clear shared state (like the in-memory cache) between tests
via the `conftest.py` autouse fixture — don't let one test's cached result
leak into another's assertions.

## Style
- Python: type hints on function signatures, docstrings on every public function
- Commit messages: `type: short description` (e.g. `feat: add IMD warnings connector`,
  `fix: cache leaking between tests`, `docs: update Section 3.10`)
- One task from the sprint board per PR — don't bundle unrelated changes

## Before opening a PR
- Run `pytest -v` locally from `backend/` and confirm everything passes
- Confirm the branch is up to date with `main` (`git pull origin main` first)
- Keep the PR scoped to one task from the sprint board
