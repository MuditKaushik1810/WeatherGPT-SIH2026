# Deployment Guide — WeatherGPT

A single deployed instance on **Render's free tier**: the FastAPI backend as a
web service, the React/Vite frontend as a static site. Zero cost. This satisfies
the Sprint 1 "deploy a working instance early" goal (Architecture doc, Section 4).

> **Prereqs:** the repo is pushed to GitHub, and you have a free Render account
> (https://render.com, sign in with GitHub). Steps that create services / set
> secrets are yours to click through — the repo just carries the config.

---

## 1. Backend — FastAPI web service (via `render.yaml`)

The repo root has a `render.yaml` Blueprint that fully describes the backend
service, so you don't hand-enter build/start commands.

1. Render dashboard → **New +** → **Blueprint**.
2. Connect this GitHub repo. Render reads `render.yaml` and shows the
   `weathergpt-api` web service. Click **Apply**.
3. It builds (`pip install -r requirements.txt` in `backend/`) and starts
   (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`). First build ~2–3 min.
4. When live, note the URL, e.g. `https://weathergpt-api.onrender.com`.

> **Manual alternative (what the current live instance uses).** You can also
> create it as **New + → Web Service** by hand with the same **Root Directory**
> (`backend`), **Build Command** (`pip install -r requirements.txt`), and
> **Start Command** (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`). The
> live instance was created this way and is served at
> `https://weathergpt-sih2026.onrender.com` — either path yields the same
> service; the `render.yaml` above just makes it reproducible.

5. **Set the forecast API key.** In the service's **Environment** tab, add
   **`WEATHERAPI_KEY`** = your key from https://www.weatherapi.com/ (free plan).
   This is the primary forecast source; without it the app fails soft to
   Open-Meteo, then to historical baselines. (`FRONTEND_ORIGINS` is set in
   step 3 of the next section, once the frontend URL exists.)

   While you're there, add **`GEOAPIFY_API_KEY`** = your key from
   https://www.geoapify.com/ (free plan) — it powers the Trip Planner's routing,
   reverse geocoding, and nearby-facility lookup (`POST /trip-plan`). Without it
   that one endpoint fails soft to a "routing unavailable" shape; the rest of
   the app is unaffected. (LLM keys `GEMINI_API_KEY` / `GROQ_API_KEY` are
   optional — `/chat` returns deterministic grounded answers without them.)

**Verify the backend:**
- `https://<your-api>.onrender.com/` → `{"status":"ok","service":"WeatherGPT API"}`
- `https://<your-api>.onrender.com/home/Delhi` → current + hourly + recommendation;
  with the key set, `current.source` reads `"WeatherAPI"` (it falls back to
  `"Open-Meteo"`, then `"Historical"`, if a source is unavailable)
- `https://<your-api>.onrender.com/docs` → the auto-generated Swagger UI

---

## 2. Frontend — Vite static site

Done in the dashboard (not the blueprint) because its build needs the backend
URL from step 1.

1. Render dashboard → **New +** → **Static Site** → connect the same repo.
2. Settings:
   - **Root Directory:** `frontend`
   - **Build Command:** `npm ci && npm run build`
   - **Publish Directory:** `dist`
3. Add an environment variable:
   - **`VITE_API_BASE_URL`** = the backend URL from step 1 (e.g.
     `https://weathergpt-api.onrender.com`). Vite bakes this in at build time.
4. Deploy, and note the static-site URL, e.g. `https://weathergpt-web.onrender.com`.

---

## 3. Wire CORS (connect the two)

The backend only accepts browser calls from origins in `FRONTEND_ORIGINS`.

1. Render → the `weathergpt-api` service → **Environment** → set
   **`FRONTEND_ORIGINS`** = the frontend URL from step 2
   (e.g. `https://weathergpt-web.onrender.com`).
2. Save — the API redeploys. The frontend can now call it from the browser.

**Verify end-to-end:** open the frontend URL, enter a location, and confirm live
weather loads (no CORS error in the browser console).

---

## Notes & gotchas

- **Free-tier spin-down:** a free web service sleeps after ~15 min idle and takes
  ~30–60 s to wake on the next request. For a live demo, hit the API once a
  minute or two beforehand to keep it warm (or upgrade the instance for the day).
- **Timezone data:** `tzdata` is in `requirements.txt`, so `ZoneInfo("Asia/Kolkata")`
  works even on minimal images.
- **Auto-deploy:** `autoDeploy: true` redeploys the backend on every push to the
  connected branch. Turn it off in the dashboard if you'd rather deploy manually.
- **Python version:** pinned to 3.11.9 via `PYTHON_VERSION` (matches CI).
- **Alternatives:** the same setup works on Railway (backend) + Vercel/Netlify
  (frontend); only the dashboard steps differ, not the app.
