# WeatherGPT — Team Collaboration & AI-Agent Workflow
### SIH 2026 · SIH26068 · How the team stays in sync while working in parallel, with or without AI coding agents

This document has two parts: **Part A** is the human process (Git, tasks, reviews). **Part B** is a ready-to-copy conventions block — drop it into `CLAUDE.md` (Claude Code), `.cursorrules` or `AGENTS.md` (Cursor and most other agentic coding tools) at the repo root, and every teammate's AI agent reads it automatically at the start of every session, without anyone having to repeat instructions by hand.

---

## Part A — The Human Process

### A.1 Git setup

- **`main` is always deployable.** Nobody commits directly to it.
- **One branch per task, not per person** — name branches after the module, matching the architecture doc's components: `feature/degradation-ladder`, `feature/crop-risk-index`, `feature/disaster-safety-guide`, `feature/pwa-service-worker`. This keeps branch scope small and makes it obvious at a glance what's in flight and who owns it.
- **Small, frequent PRs.** A branch alive for more than a day or two is where both merge conflicts and stylistic drift get worse — merge early, merge often, even if a feature isn't fully done (use draft PRs for work-in-progress).
- **Pull `main` into your branch at least once a day.** This is the single biggest lever against nasty conflicts — frequent small merges are easy, one big merge on the last day is how projects break.
- **One rotating "integration owner" per week** whose specific job is reviewing and merging PRs, keeping `main` in a known-good state. Doesn't have to be the strongest coder — has to be the most reliably available person that week.

### A.2 Task tracking

Use GitHub Projects (free, lives in the same repo) with **one card per Sprint bullet point from the Architecture & Build Plan** — the sprint plan is already broken into the right granularity, don't re-invent a separate task list. Each card: assignee, status (Not Started / In Progress / In Review / Done), and which branch it lives on.

> **Current status lives in one place:** §8 (Implementation Status & Backlog) of the Architecture & Build Plan is the living record of what's shipped vs. owed — keep the board in sync with it, don't duplicate it here. As of Sprint 2, Sprints 1–2 are shipped and deployed (data foundation + degradation ladder; grounded `POST /chat`; six-language UI + voice; Settings; chat persistence). Sprint 3 (Farmer Advisory + Trip Planner backends) is next.

**Daily 15-minute async check-in** (a Slack/Discord thread is enough — doesn't need a call): what I did yesterday, what I'm doing today, what I'm blocked on. This is what surfaces "I'm also touching that file" *before* it becomes a merge conflict instead of after.

### A.3 Code review, even for AI-written code

Every PR gets a quick look from someone other than whoever drove the agent session — not a rewrite, just a check that it matches existing patterns (naming, error handling, how `data_tier` gets tagged) before inconsistency compounds across the codebase. The CI test suite (set up Sprint 1, Section 3 of the Architecture doc) backs this up automatically: a PR that breaks an existing test doesn't merge, regardless of who or what wrote it.

### A.4 Why interfaces matter more than communication

Two people's AI agents can build the IMD connector and the Open-Meteo connector fully in parallel, with zero coordination, and still plug together correctly — **if the contract between them is fixed first.** That's already true here: the internal data shape (`{location, temp, condition, precipitation_chance, humidity, feels_like, wind_speed, aqi, warnings, source, data_tier, fetched_at}` — additive metrics were added over Sprint 1–2; `data_tier` is one of exact / regional_fallback / historical_baseline / source_unavailable / unresolved_location) and the grounding assembler's expected input are defined in the Architecture doc before Sprint 1 starts. Incompatible output between teammates' work happens when interfaces are implicit or improvised per-module — you've already avoided most of that risk by design.

---

## Part B — Conventions File for AI Coding Agents

Copy everything below into `CLAUDE.md` / `.cursorrules` / `AGENTS.md` at the repo root. This is what keeps five independently-run AI sessions producing compatible code without any of them talking to each other — each one reads the same rulebook and the same existing code before writing anything new.

> **The repo-root `CLAUDE.md` / `AGENTS.md` / `.cursorrules` are the authoritative copy and have expanded since this excerpt was first written** (notably the full data contract with `humidity`/`feels_like`/`wind_speed`/`aqi` and the five `data_tier` values, and the full §3.10 endpoint shapes). Treat the repo-root files as source of truth; the excerpt below is the origin snapshot, kept for context.

```markdown
# WeatherGPT — Agent Instructions

## Before writing any code
1. Read this file in full.
2. Look at existing modules in the same layer before building a new one (e.g. before
   building a new data connector, read the existing Open-Meteo or IMD connector and
   match its structure — don't invent a new pattern for the same kind of thing).
3. Never duplicate logic that already exists elsewhere in the repo — extend or import it.

## Stack
- Backend: Python, FastAPI
- Frontend: [confirm: React or plain HTML/JS + Tailwind]
- DB: PostgreSQL (Supabase/Neon free tier)
- LLM: [confirm provider — Gemini Flash / Groq free tier]

## Non-negotiable data contract
Every weather-data record, regardless of source, is normalized to this shape before
it reaches the grounding assembler:

    {
      "location": str,
      "temp": float,
      "condition": str,
      "precipitation_chance": float,
      "warnings": list[str],
      "source": str,          # "IMD" | "Open-Meteo" | "Historical"
      "data_tier": str,       # "exact" | "regional_fallback" | "historical_baseline"
      "fetched_at": datetime,
    }

Never invent a different shape for a new connector. If a new field is genuinely
needed, add it here and update every consumer, don't create a parallel shape.

## The two rules that protect the whole product
1. **Never let the LLM answer without grounding.** Every LLM call that produces a
   user-facing answer must be given a context block built by the grounding assembler
   from real fetched/cached data. The LLM never invents a weather fact, a crop
   threshold, or a safety instruction — it only rephrases and personalizes what the
   grounding assembler gives it.
2. **Never let the LLM bare-refuse.** The final answer-generation prompt must never
   allow a plain "I don't have sufficient data" response. If real data is unavailable,
   the degradation ladder produces the nearest available alternative, tagged with its
   `data_tier`, and the LLM must present that instead of refusing outright.

## Domain content is curated, not generated
Crop rule tables, disease-suitability parameters, and disaster safety guidance are
static, sourced, hand-curated JSON/CSV files (cited to ICAR/GKMS/NDMA in comments at
the top of the file) — never something an agent should generate from general
knowledge. If a source isn't cited, flag it for a teammate to verify before merging,
don't fill in a plausible-looking number.

## Testing
Every new function in the degradation ladder, risk-index calculator, Disease
Suitability Model, or Trend Engine needs at least one `pytest` test before the PR is
considered done. Mock external API calls in tests — never hit live IMD/Open-Meteo
endpoints from the test suite.

## Style
- [team to fill in: naming conventions, linting/formatting tool, commit message format]

## Before opening a PR
- Run the test suite locally
- Confirm the branch is up to date with `main`
- Keep the PR scoped to one task from the sprint board — don't bundle unrelated changes
```

---

## Part C — Quick Reference: Where Things Live

| Question | Answer |
|---|---|
| What are we building and why | `SIH26068_WeatherGPT_Architecture_and_Build_Plan.md` |
| What does each API endpoint return | `SIH26068_WeatherGPT_Architecture_and_Build_Plan.md`, Section 3.10 |
| Is this specific feature worth the time | `SIH26068_WeatherGPT_Feature_Brief.md` |
| What should this actually look like | `WeatherGPT_Mockup.html` |
| What's the current state of the code | `main` branch, always |
| Who's doing what right now | GitHub Projects board |
| What should every AI agent session know before writing code | `CLAUDE.md` / `.cursorrules` / `AGENTS.md` (Part B above) |

---

## Part D — Repository Setup Walkthrough

Do this on Day 1, before anyone writes real feature code.

**1. Create the repo.** GitHub → New repository → name it (e.g. `weathergpt-sih2026`) → initialize with a README and a Python `.gitignore` → create.

**2. Clone it and set up the folder structure**, mirroring the Architecture doc's modules:
```bash
git clone https://github.com/<your-org>/weathergpt-sih2026.git
cd weathergpt-sih2026

mkdir -p backend/app/{connectors,core,farmer,trend,disaster,alerts,digest} \
         backend/tests \
         frontend/src/{components,screens,mocks} \
         docs

touch backend/app/main.py backend/requirements.txt backend/.env.example \
      frontend/package.json README.md CLAUDE.md
```
- `backend/app/connectors/` → `imd.py`, `open_meteo.py`, `nominatim.py`
- `backend/app/core/` → `degradation_ladder.py`, `grounding_assembler.py`, `geocoding.py`
- `backend/app/{farmer,trend,disaster,alerts,digest}/` → one folder per module from the Architecture doc
- `frontend/src/screens/` → `Chat/`, `FarmerDashboard/`, `TripPlanner/`, `DisasterView/`, `HistoricalAnalytics/`, `Offline/`
- `frontend/src/mocks/` → JSON fixtures matching Section 3.10 of the Architecture doc exactly, so frontend work can start Day 1
- `docs/` → put the Architecture doc, Feature Brief, this Workflow doc, and the mockup HTML **inside the repo**, not just in chat — this is what makes them readable context for every AI agent session automatically

**3. Add the conventions file** — paste Part B above into `CLAUDE.md` at the root (duplicate into `.cursorrules`/`AGENTS.md` for teammates using a different tool).

**4. Push the scaffold:**
```bash
git add .
git commit -m "chore: initial project scaffold"
git push origin main
```

**5. Protect `main`.** Repo → Settings → Branches → Add rule for `main` → require a pull request before merging, require CI status checks to pass before merging.

**6. Add CI** — `.github/workflows/ci.yml` running `pytest` on every push/PR, even with just one placeholder test to start. Get the pipeline itself working Day 1.

**7. Set up the task board.** Repo → Projects → board with columns Not Started / In Progress / In Review / Done — one card per Sprint bullet point from the Architecture doc.

**8. `.env.example`, never real secrets.** List required variable names (`LLM_API_KEY`, `DATABASE_URL`, etc.) with placeholder values; each person keeps their own local `.env` (gitignored).

**9. Sanity-check the whole pipeline before real work starts.** One person opens a trivial first PR (even a README edit) to confirm branch protection, CI, and review are actually wired correctly — cheaper to fix on a throwaway PR than discover broken on Day 5's real work.

---

*This document is a living reference — update Part B's stack/style placeholders once the team locks them in Sprint 1, Day 1.*
