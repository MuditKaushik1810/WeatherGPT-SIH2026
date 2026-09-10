# WeatherGPT — Architecture & Execution Plan
### SIH 2026 · Problem Statement SIH26068 · Software Track

---

## 1. Problem Statement Reference

| Field | Detail |
|---|---|
| **PS ID** | SIH26068 |
| **Title** | WeatherGPT: Conversational AI for Weather Forecasting, Alerts, and Climate Information |
| **Organizing Body** | Ministry of Earth Sciences (MoES) |
| **Department** | India Meteorological Department (IMD) |
| **Theme** | Disaster Management |
| **Category** | Software |

### 1.1 Background (as stated in the PS)

Weather information today is distributed across multiple portals, bulletins, satellite products, and forecast systems, making it difficult for common users, researchers, disaster managers, and government agencies to quickly obtain actionable insights. There is a need for an intelligent conversational platform that can provide real-time weather information, forecasts, warnings, climate analysis, and decision support in natural language.

### 1.2 Objective (as stated in the PS)

Develop an AI-powered chatbot platform named **WeatherGPT** that integrates meteorological datasets, forecasting models, and disaster warning systems to provide accurate, contextual, and multilingual weather intelligence through conversational interfaces.

### 1.3 Key Features Called Out in the PS

1. Real-time weather information retrieval
2. Natural language querying for weather forecasts
3. Integration with numerical weather prediction (NWP) models such as GFS/WRF
4. Extreme weather alerts and early warning dissemination
5. Location-based forecasting and advisory generation
6. Multilingual support for Indian languages
7. Climate trend and historical weather analysis
8. Voice-enabled interaction for rural accessibility

### 1.4 Expected Solution (as stated in the PS)

- A mobile-based conversational AI platform
- Backend integration with meteorological databases, websites, and APIs
- An AI/LLM-based query understanding engine
- Scalable architecture supporting real-time data ingestion

### 1.5 Suggested Technology Stack (as stated in the PS)

Python / FastAPI / Node.js · MQTT / WIS2.0 / WebSocket · LLMs (OpenAI, Llama, Gemini, etc.) · GIS tools and weather APIs · PostgreSQL / MongoDB · Docker / Kubernetes

### 1.6 Official Evaluation Parameters

Accuracy and relevance · Response latency · Multilingual capability · UI and accessibility · Scalability and innovation · Integration with real-time meteorological systems · Voice-enabled interaction for rural accessibility

---

## 2. What We Are Actually Going to Build

The PS is written at ministry/production scale — true GFS/WRF model integration, WIS2.0/MQTT infrastructure, and Kubernetes deployment are not realistic or expected inside a 36-hour build, and no judge evaluating a student prototype expects them. Our job is to build the **thinnest version that is still honest and complete against every evaluation parameter**, not the literal maximal brief.

**Positioning, stated plainly:** WeatherGPT is not "a chatbot that tells you the weather." On a single one-off question, a generic LLM with web search can already do that about as well as we can, and pretending otherwise is a losing argument in front of a judge who pushes on it. The actual product is **a grounded, proactive, role-aware decision-support system that uses conversation as its interface** — the value sits in the data engineering, persistence, and domain logic wrapped around the model, not in the model itself. Section 2.1 makes this case explicitly, because it's the question most likely to come up in evaluation and the team needs a precise, honest answer ready.

**Our scoped MVP, in one sentence:** *A grounded, retrieval-augmented conversational assistant — with a general-purpose core and a deep, purpose-built Farmer Advisory mode as its flagship differentiator — that answers natural-language weather questions in English and at least one Indian language, using real public weather/alert data, with voice input/output and proactive severe-weather alerting.*

**What we explicitly will NOT attempt**, and why that's a defensible scoping call, not a shortcut:
- Live GFS/WRF numerical model runs — these are raw output meant for meteorologists; we consume forecast *products* derived from them (via IMD/public APIs), not raw model grids.
- True WIS2.0/MQTT protocol integration — we simulate the "real-time alert" behavior with a polling job, which satisfies the *functional* requirement without needing WMO's actual message-broker infrastructure.
- Kubernetes/production deployment — a single deployed instance (Render/Railway/a cloud VM) demonstrates the same architecture without the operational overhead.

**Why this framing wins on the actual evaluation parameters:** every one of the seven official criteria (accuracy, latency, multilingual, UI/accessibility, scalability *and innovation*, real-time integration, voice) is satisfiable by the MVP above. None of the criteria explicitly require raw NWP model integration — "integration with real-time meteorological systems" is satisfied by live API integration with IMD/public weather sources.

### 2.1 Differentiation: Why Not Just Use a Regular Weather App, or a Generic LLM Directly

This is the single most important question the team needs a sharp answer to, so it's stated here explicitly rather than left implicit.

| Capability | Regular weather app | Generic LLM (ChatGPT/Gemini) | WeatherGPT |
|---|---|---|---|
| Natural-language Q&A | No | Yes | Yes |
| Voice interaction | Partial (device-level only) | Yes | Yes |
| Multilingual | Limited | Yes | Yes |
| Proactively pushes an alert without being asked | Sometimes (basic push) | **No — purely reactive, only responds when opened** | **Yes — background poller watches saved locations** |
| Persistent profile tied to a specific field/crop/location, accumulating value over time | No | **No — each chat starts cold unless the user re-explains everything** | **Yes — structured farmer/user profile** |
| Curated, sourced domain rules (crop-stage thresholds, pest triggers) | No | **No — generates a plausible-sounding answer from general training, not a cited agri-extension rule** | **Yes — explicit rule table sourced from ICAR/state advisories** |
| Traceable "which official source is this from" | No | **No — web search results are a black box to the user** | **Yes — `data_tier` tagging traces explicitly to IMD/Open-Meteo** |
| Repeatable, explainable computed score (not a fresh guess each time) | No | No | **Yes — Crop Risk Index, same formula every time** |
| Designed for low-bandwidth/low-literacy rural access | No | No (assumes smartphone + data plan + typical app fluency) | **Yes — purpose-built** |

**The argument to make to a judge, precisely:** we are not claiming a novel AI capability — a generic LLM already covers the top three rows, and pretending otherwise is a losing position. The claim is that turning a general-purpose model into a *reliable, proactive, domain-aware system* requires real systems engineering — persistence, sourced domain rules, background monitoring, auditable grounding — and that engineering, not the chat interface, is the actual product. This is also why the Farmer Advisory mode (Section 2.2, Sprint 3) is the flagship feature rather than a side addition: it is the concrete demonstration of exactly this argument, since a generic chatbot can tell a farmer it might rain, but cannot tell them their wheat is at grain-filling stage, humidity is trending toward fungal-disease risk, and they should harvest before Thursday — unless someone builds that logic and feeds it in.

### 2.2 Personas

The platform stays genuinely general-purpose at its core (satisfying the PS's literal brief of serving "individuals, researchers, disaster managers, and government agencies"), while going deep on one persona as the standout feature:

| Persona | Role in the product | Depth |
|---|---|---|
| **General individual** | Baseline conversational Q&A — current conditions, forecasts, alerts | Table-stakes; satisfies the brief, not the differentiator |
| **Traveler / trip planner** | Route-aware stop planner: rates stops along the route from the forecast at each ETA, with nearby facilities (Sprint 3; UI shipped, Geoapify backend pending) | Moderate depth — a genuine, differentiated feature |
| **Farmer (flagship persona)** | Dedicated dashboard: crop-specific advisory, risk scoring, sowing/harvest guidance (Sprint 3) | Deep, curated, sourced — this is the standout |
| **Disaster manager / government stakeholder** | Severity-sorted Disaster Manager view with Trend Engine context (Section 3.9) | Real dedicated UI now, though still the least user-validated persona — the team has no real access to actual government workflows to design against |
| **General individual, during an active alert** | Hazard-specific safety guidance and, at the highest severity tier, Active Emergency Mode (Section 3.9) | Curated, NDMA-sourced — the second-most safety-critical feature in the product after grounding itself |

**On whether this is scope creep away from the PS:** it isn't, provided the framing stays disciplined. The PS is issued by MoES/IMD as a *general* conversational platform, not an agriculture-ministry brief — and there are separate SIH problem statements this year specifically about crop disease and farmer market linkage. Pitching this as "we built a farming app" would read as drift from the assigned brief. Pitching it as *"WeatherGPT is a general conversational weather-intelligence platform for IMD; here is a deep-dive into one stakeholder group — farmers — to show what 'actionable insight' actually looks like beyond a forecast"* satisfies the literal brief while still delivering the hard-to-copy differentiation a generic weather chatbot can't touch.

> **Farmer Mode — scope (locked, Sprint 3).** Farmer Mode is a **separate agricultural mode** of WeatherGPT — *not* a fourth normal tab alongside Home / Travel / Disaster. It is entered separately and has its own internal navigation between two **distinct workflows**:
> - **Crop Planning** — recommends *what crops to grow* based on location, season and environmental suitability. ~3–4 suitable crops, each with a short reason, basic suitability context, and an approximate harvest window.
> - **Crop Watch** — monitors an *already-planted* crop using its growth stage, weather threats, climate context and crop-specific advisory logic, and **always explains why** a threat/risk is reported.
>
> **Crop Planning is a crop-*selection* feature, not a crop-monitoring or farm-management system. Crop Watch is responsible for post-planting monitoring and weather-risk advisory.** (This one sentence is the guard against the scope confusion that muddled the earlier branches: "what to plant" and "what's happening to what I planted" are different questions with different UIs and different backends. They may share infrastructure — location/weather services, crop metadata, crop rules, climate data, the farmer profile — but their user-facing purposes stay separate.)
>
> Both screens ship **demo-fixture-first** with explicit provenance (`data_tier: "demo"`, `source` naming the fixture) and a **documented, stable response shape** (Section 3.10), so swapping a fixture for a real backend call needs no UI redesign and the fixture never becomes an undocumented de-facto contract. Backend lives under a dedicated **`/farmer/*`** namespace; **Crop Watch is served by a single composite `/farmer/crop-watch`** endpoint (Section 3.10), with `/farmer/crop-profile`, `/farmer/risk-score`, `/farmer/advisory` available as reusable sub-endpoints.

### 2.3 Timeline Context: 12–13 Day Internal-Round Build

Everything above still holds — the differentiation argument, the persona structure, the scoping discipline. What changes is how much depth is achievable, and the plan below (Section 4) is rebuilt around days instead of hours accordingly.

**Working assumption on capacity:** 12–13 calendar days with a team of 5–6, realistically averaging some effective focused hours per person per day rather than continuous work — closer to a part-time sprint than a hackathon grind, since the team likely has classes/other commitments running in parallel. In raw person-hours this isn't wildly more than a 36-hour hackathon crammed across a whole team, but the *distribution* changes everything: there's room for research (sourcing real ICAR data instead of guessing), testing, iteration, sleep, and recovering from a wrong turn without it being fatal to the whole submission. That's what genuinely raises the ceiling here — not more hours, but hours that don't have to be spent in crisis mode.

**What this timeline newly makes feasible, beyond the hackathon-scoped plan:**

- **A wider, better-sourced crop list** (8 crops instead of 3–5 — see Section 4, Sprint 3) since there's time to actually research ICAR/GKMS advisory data properly rather than picking whichever crops are fastest to guess at.
- **A third language**, and doing multilingual support properly (tested across all three, not just demoed in one) rather than a single flawless language plus a risky bonus.
- **A genuine offline/PWA layer** — this is worth calling out specifically because it directly serves the PS's own "rural accessibility" framing: caching the last-fetched forecast/advisory client-side so the app remains useful on a spotty connection, installable as a home-screen PWA without needing an app store. This was explicitly out of scope for a 36-hour build; it's a strong, on-theme addition now.
- **A lightweight Disaster Manager / Stakeholder view** — an aggregated, multi-region view of active alerts (reusing the same alerting backend, just a different front-end lens), which more concretely satisfies the PS's explicit mention of "disaster managers and government agencies" than the general chat interface alone does.
- **A deeper Crop Risk Index** — incorporating the preloaded historical dataset as a baseline (e.g., "5°C above the 10-year average for this date, which raises heat-stress risk for this crop stage") rather than only current-forecast thresholds. Still arithmetic, not machine learning — just a richer formula with more inputs, which the extra research time actually supports.
- **Real automated testing and CI** — a small `pytest` suite for the degradation ladder, risk-index calculator, and connectors (mocked), wired into GitHub Actions so tests run on every push. This is a genuine engineering-maturity signal to judges and costs nothing.
- **Auto-generated API documentation** (FastAPI's built-in OpenAPI/Swagger UI) — essentially free once the backend is built cleanly, and a nice concrete artifact to show alongside the demo.
- **A real bug-bash/QA pass and multiple rehearsals**, which a 36-hour timeline structurally can't afford — this alone tends to matter more for how a demo actually lands than any single extra feature.

**What should stay out of scope even with the extra time, deliberately:**

- **Image-based pest/disease diagnosis.** It's tempting to add given the Farmer Advisory mode's momentum, but it's meaningfully a different, well-defined SIH problem statement's territory (crop disease detection via computer vision) — adding it dilutes the "we are WeatherGPT, a weather-intelligence platform" positioning from Section 2.1 rather than strengthening it. If the team wants this direction, it's a stronger case for switching PS entirely, not folding it in here.
- **Real SMS/IVR delivery.** It's on-theme for rural accessibility, but genuine SMS sending isn't free at any meaningful volume (Twilio and equivalents run out of trial credit fast), which conflicts with the team's own zero-cost constraint. A demo-only mockup of what an SMS alert *would* look like is fine to mention as a future-work slide; don't build live sending infrastructure around it.
- **True production infrastructure** (Kubernetes, WIS2.0/MQTT, raw GFS/WRF integration) — the reasoning from Section 2 (main body) still applies; more calendar time doesn't change what's realistically gradeable or necessary in a student prototype, and building toward infrastructure nobody will evaluate is time better spent on Section 2.3's actual additions above.

---

## 3. System Architecture

### 3.1 Architecture Diagram

```mermaid
flowchart TB
    subgraph Client["Client Layer"]
        WEB["Web Chat UI\n(responsive, mobile-first)"]
        VOICE["Voice Input/Output\n(mic capture + audio playback)"]
        PWA["PWA Shell + Service Worker\n(installable, caches last-fetched\ndata for offline/low-bandwidth use)"]
        DISASTER["Disaster Manager View\n(multi-region alert aggregation)"]
    end

    subgraph Gateway["API Gateway — FastAPI"]
        AUTH["Session / Location Context"]
        ROUTER["Request Router"]
    end

    subgraph NLU["Query Understanding Layer"]
        RULES["Rule/Keyword Fast Path\n(skips LLM for simple queries)"]
        LANGDETECT["Language Detection"]
        INTENT["Intent + Entity Extraction\n(location, hazard type, time range,\nquery class: realtime vs historical)\nvia LLM structured-output call — only\nwhen the fast path can't resolve it"]
    end

    subgraph Geo["Geocoding"]
        STATICGEO["Static Lookup Table\n(~500 Indian cities/districts, in-memory)"]
        NOMINATIM["Nominatim Fallback\n(only for unlisted places)"]
    end

    subgraph Realtime["Real-Time Data Path — always live-fetched"]
        CACHE["Response Cache\n(TTL-based, avoids re-fetching\nwithin a short window)"]
        IMDCONN["IMD Public Feed Connector\n(warnings, official bulletins)"]
        OWCONN["Open-Meteo Forecast API\n(grid-based — always has a value\nfor any Indian lat/lon)"]
        LADDER["Degradation Ladder\n1. exact district match\n2. nearest grid point / state-level\n3. related data + explicit caveat\n4. last resort: honest gap, never bare refusal"]
    end

    subgraph Historical["Historical/Trend Path — preloaded, static"]
        HISTDB[("Preloaded Historical Dataset\nOpen-Meteo Historical API snapshot\n— refreshed once, not per-query")]
    end

    subgraph Generation["Response Generation Layer"]
        GROUND["Grounding Assembler\n(structured data -> LLM context,\ntags data tier used)"]
        LLM["LLM Call\n(answer generation, in detected language,\nforbidden from bare 'no data' replies)"]
        TTS["Text-to-Speech\n(for voice responses)"]
    end

    subgraph Farmer["Farmer Advisory Mode — flagship differentiator"]
        CROPPROFILE[("Crop Profile\ncrop, field location, sowing date")]
        RULETABLE[("Curated Crop Rule Table\nsowing windows, thresholds,\npest/disease triggers — sourced\nfrom ICAR / state advisories")]
        SUITABILITY["Disease Suitability Model\ncontinuous temp/humidity/stage\nscores -> 24h rolling average"]
        RISKCALC["Crop Risk Index Calculator\n(disease suitability + extreme-\nweather proximity + historical\nbaseline deviation)"]
        ADVISORY["Harvest/Action Timing Advisory"]
    end

    subgraph Trend["Trend Engine — shared component"]
        BASELINE[("Multi-Year Baseline\nmoving average per location/variable")]
        REGRESS["Trend Regression\n(linear fit — direction + slope)"]
        ANOMALY["Anomaly Detector\ncurrent vs baseline"]
    end

    subgraph TripPlan["Trip Planning — route-aware stop planner"]
        TRIPROUTE["Geocode + Route\n(Geoapify: origin to destination\n+ checkpoints)"]
        TRIPRATE["Rate stops + facilities\n(weather at each ETA,\nGeoapify Places)"]
    end

    subgraph Disaster2["Disaster Safety — individual + emergency mode"]
        HAZARDGUIDE[("Curated Hazard Safety Guide\nflood/cyclone/heatwave/storm/cold —\nsourced from NDMA Do's & Don'ts")]
        SEVCHECK{"Alert severity\nat highest tier?"}
        EMERGENCY["Active Emergency Mode\naction steps + verified helplines\n(NDMA 1078, Emergency 112)"]
    end

    subgraph Digest["Personalized Digest"]
        DIGESTSCHED["Digest Scheduler\n(APScheduler, per-user preferred time)"]
    end

    subgraph Alerting["Proactive Alerting Layer"]
        POLLER["Background Poller\n(checks IMD warnings every N minutes)"]
        NOTIFY["Notification Dispatcher\n(push / in-app banner)"]
        SUBSCRIBERS["Saved User Locations"]
    end

    subgraph Storage["Persistence"]
        DB[("PostgreSQL\nusers, saved locations,\nconversation history")]
    end

    WEB --> AUTH
    VOICE -->|"Speech-to-Text"| AUTH
    PWA -.->|"caches responses for offline use"| WEB
    DISASTER --> POLLER
    DISASTER --> IMDCONN
    DISASTER --> ANOMALY
    AUTH --> ROUTER
    ROUTER --> RULES
    RULES -->|"unresolved"| LANGDETECT --> INTENT
    RULES -->|"resolved directly"| STATICGEO
    INTENT --> STATICGEO
    STATICGEO -.->|"not found"| NOMINATIM
    INTENT -->|"realtime query"| CACHE
    INTENT -->|"historical/trend query"| HISTDB
    INTENT -->|"farmer advisory query"| CROPPROFILE
    INTENT -->|"trip planning query"| TRIPROUTE
    INTENT -->|"safety/emergency query"| HAZARDGUIDE
    CACHE -.->|"cache miss"| LADDER
    LADDER --> IMDCONN
    LADDER --> OWCONN
    IMDCONN --> GROUND
    OWCONN --> GROUND
    HISTDB --> GROUND
    HISTDB --> BASELINE --> REGRESS
    OWCONN --> ANOMALY
    REGRESS --> ANOMALY --> GROUND
    ANOMALY --> RISKCALC
    CROPPROFILE --> RULETABLE --> SUITABILITY
    OWCONN --> SUITABILITY
    SUITABILITY --> RISKCALC
    RISKCALC --> ADVISORY --> GROUND
    TRIPROUTE --> TRIPRATE
    OWCONN --> TRIPRATE
    TRIPRATE --> GROUND
    IMDCONN --> SEVCHECK
    SEVCHECK -->|"yes"| EMERGENCY --> GROUND
    SEVCHECK -->|"no"| HAZARDGUIDE --> GROUND
    DIGESTSCHED --> GROUND
    DIGESTSCHED --> NOTIFY
    GROUND --> LLM
    LLM --> WEB
    LLM --> TTS --> VOICE
    POLLER --> IMDCONN
    POLLER --> SUBSCRIBERS
    POLLER --> NOTIFY --> WEB
    AUTH <--> DB
    SUBSCRIBERS <--> DB
    CROPPROFILE <--> DB
```

### 3.2 Component Breakdown

| Layer | Component | Responsibility | Suggested tools | Cost |
|---|---|---|---|---|
| Client | Web Chat UI | Chat interface, location picker, alert banner | React or plain HTML/JS + Tailwind | Free |
| Client | Voice I/O | Mic capture, playback | Browser Web Speech API | Free, runs client-side, no server call |
| Client | PWA + service worker | Installable app shell (cache-first), IndexedDB local-first storage, a template-based offline responder for common queries, Background Sync for queued requests — see Section 3.6 for the full layered strategy | Web app manifest + Service Worker API + IndexedDB + Background Sync API | Free |
| Client | Disaster Manager view | Aggregated multi-region alert view for the stakeholder persona; reuses the alerting backend, just a different lens | Same frontend framework, separate route/tab | Free |
| Gateway | FastAPI backend | Routes requests, manages session/location context | Python + FastAPI | Free (self-hosted) |
| NLU | Rule/keyword fast path | Resolves simple, well-formed queries (city name + "weather") without an LLM call | Plain Python string/regex matching | Free, and cuts LLM call volume substantially |
| NLU | Language detection | Detects query language | `langdetect` lib, or folded into the LLM call below when one is needed | Free |
| NLU | Intent/entity extraction | Pulls location, hazard type, time range, and query class (realtime vs. historical) from free text — only invoked when the fast path can't resolve the query | LLM call with structured JSON output (function calling) | Free tier (Gemini Flash / Groq) |
| Geocoding | Static lookup table | Place name → lat/lon for ~500 major Indian cities/districts, held in memory | A preloaded JSON/dict, built once | Free, zero external calls for most queries |
| Geocoding | Nominatim fallback | Only invoked when a place isn't in the static table | OpenStreetMap Nominatim | Free, generous usage policy |
| Retrieval (real-time) | IMD connector | Pulls official forecasts/bulletins/active warnings | IMD public data endpoints / bulletin pages | Free |
| Retrieval (real-time) | Open-Meteo connector | Grid-based forecast data — always returns a value for any Indian coordinate, no true "no data" case | Open-Meteo Forecast API (no key) | Free, ~10,000+ calls/day |
| Retrieval (real-time) | Degradation ladder | Steps district → state/region → related-data-with-caveat → honest gap, before ever reaching the LLM with nothing | Plain Python | Free |
| Retrieval (real-time) | Response cache | Short-TTL cache so repeated queries for the same location don't re-fetch | In-memory dict, or a Postgres table | Free |
| Retrieval (historical) | Preloaded historical dataset | Trend/climate-analysis queries only — fetched once ahead of time, not per-query | Open-Meteo Historical Weather API snapshot | Free, one-time pull |
| Generation | Grounding assembler | Formats retrieved data (real-time or historical) into a factual context block, tagged with which data tier was used | Plain Python — the anti-hallucination step | Free |
| Generation | LLM call | Generates the final natural-language answer, forbidden from bare "no data" replies | Gemini Flash free tier, or Groq | Free tier |
| Generation | LLM response cache | Caches full grounded answers for repeated/similar queries, cutting LLM call volume further | Same cache store as above | Free |
| Farmer Advisory | Crop profile | Persistent per-user crop, field location, sowing date | Postgres table | Free |
| Farmer Advisory | Curated crop rule table | Sowing windows, ideal stage-thresholds, pest/disease triggers for 8 crops, sourced from ICAR/GKMS advisories | Static JSON/CSV, hand-curated | Free |
| Farmer Advisory | Disease Suitability Model | Continuous 0–1 temperature/humidity/growth-stage scores per crop-disease pair (bell-curve/ramp functions, not binary thresholds), averaged over a rolling 24h window | Plain Python arithmetic — not ML; see Section 3.7 | Free |
| Farmer Advisory | Crop Risk Index calculator | Combines the Disease Suitability score with extreme-weather proximity and the Trend Engine's historical-baseline deviation into one 0–100 score | Plain Python arithmetic | Free |
| Farmer Advisory | Harvest/action timing advisory | Combines forecast + rule table into a concrete recommendation | Plain Python, feeds into grounding assembler | Free |
| Trend Engine | Multi-year baseline | Moving average per location/variable from the preloaded historical dataset | Plain Python / pandas | Free |
| Trend Engine | Trend regression | Direction + slope of a variable over available years (e.g. monsoon onset drifting later) | `numpy.polyfit` — basic stats, not ML | Free |
| Trend Engine | Anomaly detector | Compares current season vs. baseline; feeds the Risk Index and Trend-Informed Advisory | Plain Python; shared across features | Free |
| Trip Planning | Route + stop planner | Geocode origin/destination, route between them, and select the checkpoints along the way | Geoapify (geocoding + routing) | Free tier (API key) |
| Trip Planning | Stop rating + facilities | Forecast at each checkpoint's ETA → good/caution/not-recommended, plus nearby facilities per stop | Open-Meteo + Geoapify Places | Free tier (API key) |
| Disaster Safety | Curated Hazard Safety Guide | Do's/don'ts for flood, cyclone, heatwave, thunderstorm/lightning, cold wave — sourced from NDMA's published guidance | Static JSON, hand-curated, cited | Free |
| Disaster Safety | Active Emergency Mode | Triggers at highest alert severity; shows immediate action steps + a verified helpline block (NDMA 1078, pan-India Emergency 112); explicitly flags that district control-room numbers must be looked up per location, not hardcoded | Plain Python severity check + curated content | Free |
| Personalization | Digest scheduler | Per-user scheduled job assembling a personalized daily summary (forecast/alerts/crop advisory/trend comparison per saved preferences) and delivering via push or queued Background Sync | APScheduler, reuses the grounding assembler | Free |
| Generation | TTS | Converts answer to speech for voice mode | Browser Web Speech API (TTS) | Free, client-side |
| Alerting | Poller | Periodically checks IMD warnings against saved locations — no LLM involved, pure comparison logic, so it's unconstrained by any LLM rate limit | Simple cron-style background task (APScheduler) | Free |
| Alerting | Notification dispatcher | Pushes alerts to users with a matching saved location | In-app banner (core); browser Notification API (stretch) | Free |
| Persistence | PostgreSQL | Users, saved locations, conversation history, cache | Supabase/Neon free tier | Free |
| Quality | Automated test suite | Unit tests for degradation ladder, risk-index calculator, connectors (mocked) | `pytest` | Free |
| Quality | CI pipeline | Runs the test suite on every push | GitHub Actions | Free |
| Quality | API documentation | Auto-generated interactive API docs | FastAPI's built-in OpenAPI/Swagger UI | Free |

### 3.3 Why This Shape

The single most important design decision is the **grounding assembler** between retrieval and generation. It exists specifically to stop the LLM from hallucinating a forecast — the LLM never gets to invent weather data; it only ever rephrases data you already fetched and verified. This is also your strongest talking point with judges on the "accuracy and relevance" evaluation criterion, since it's a concrete, explainable safeguard rather than a vague "we used AI" claim.

The second most important decision is that **the LLM is not on the critical path for every query.** The rule/keyword fast path, the static geocoding table, and the alert poller all work without touching the LLM at all — which is what keeps the system inside free-tier limits and keeps latency low, both of which are explicit evaluation criteria.

---

## 3.4 Handling Data Gaps: the Degradation Ladder

The instinct to worry about "I don't have sufficient data" is right for a naively-built system, but it's fixable by design, not by prompt-tuning alone.

**Why most weather queries won't hit a real gap at all:** Open-Meteo is grid-based, not station-based — it interpolates from global NWP model output (ECMWF, GFS, ICON, etc.) at roughly 1–11km resolution, so it has *some* value for literally any coordinate in India. There's no village or district where a lat/lon lookup returns nothing. The genuine gaps are narrower than they first appear: IMD-specific products (district-level cyclone bulletins) that don't cover every sub-district, deep historical queries at very fine granularity, and off-topic questions.

**The fix is a retrieval design that degrades gracefully instead of failing binary.** Before the grounding assembler ever hands the LLM a query, it steps down through tiers:

1. **Exact match** — district-level IMD data for the exact location/metric asked about
2. **Nearest available** — Open-Meteo's grid value for that coordinate, or state/regional-level IMD data if district-level isn't available
3. **Related data + explicit caveat** — e.g., "no active cyclone warning specifically for your district, but the regional advisory for [state] shows..."
4. **Honest gap, as a true last resort** — paired with whatever adjacent data *is* available, never a bare refusal with nothing else offered

The final LLM prompt should explicitly forbid a bare "I don't have sufficient data" response and require the model to state which tier it's answering from. In a live demo, this turns a potential weak point into a strength: you can show a judge a query that visibly degrades gracefully instead of failing, which reads as stronger engineering than a system that either always mysteriously succeeds or fails ungracefully.

**Real-time data vs. historical/trend data are architecturally separate, on purpose.** Current conditions and forecasts must always be freshly fetched or short-TTL cached — never preseeded, since stale current-conditions data is actively wrong. But the PS's "climate trend and historical analysis" feature is not time-sensitive by definition, so a preloaded historical dataset (pulled once via Open-Meteo's Historical Weather API, not re-fetched per query) is the *correct* design choice there, not a shortcut. Splitting these two paths, and being able to explain why each one is built the way it is, is worth stating explicitly to judges — it shows the team understands which data needs to be live and which doesn't, rather than treating "the AI layer" as one undifferentiated blob.

---

## 3.5 Cost & Rate-Limit Strategy

**Target: $0 to build and run through the full hackathon and demo.** The rate-limit risk sits almost entirely on the LLM calls, not the weather data — Open-Meteo's free tier (~10,000+ calls/day, no key required) is not a realistic constraint at hackathon-demo scale.

| Risk | Mitigation |
|---|---|
| LLM free-tier rate limit (e.g., Gemini Flash ≈15 requests/min) | Route simple, well-formed queries (city name + "weather") through the rule/keyword fast path instead of an LLM call — this alone can cut LLM call volume by half or more |
| Repeated identical/similar queries during demo or judging | Cache full grounded LLM responses, not just raw weather data, so a second "weather in Delhi today" doesn't trigger a second LLM call |
| Background alert poller running up against limits | It never calls the LLM at all — matching a warning against saved locations is pure comparison logic, so its sweep frequency is bounded only by Open-Meteo/IMD fetch limits, which have generous headroom even at a poll interval of a few minutes across hundreds of saved locations |
| Geocoding calls adding latency/cost | A preloaded static table of ~500 major Indian cities/districts resolves the vast majority of queries with zero external calls; Nominatim is only a fallback for unlisted places |
| Real hackathon-day traffic estimate | A handful of judges making 10–20 queries total during evaluation is nowhere near any of these free-tier ceilings — the system is unlikely to ever hit a rate limit in practice |

---

## 3.6 Connectivity Strategy: Designing for Interrupted Access

This is worth treating as a first-order design concern, not a Sprint 4 add-on, since it maps directly to the PS's own "rural accessibility" language and is the area most competing teams are least likely to have thought through carefully.

**Honest framing first:** a PWA does not make a conversational AI app internet-independent — the core value (a live LLM turning fresh data into a grounded answer) fundamentally requires a network round trip, and no amount of caching changes that. The real, achievable goal is graceful degradation across the connectivity spectrum that actually exists in rural India — mostly intermittent, high-latency 2G/3G, with true zero-signal being rarer than "signal comes and goes" — not a binary "works offline / doesn't."

| Layer | Condition | What's available |
|---|---|---|
| 1 | Full connectivity | Everything — live LLM calls, live data, full feature set |
| 2 | Weak/spotty connectivity (the realistic common case) | App shell loads instantly (cache-first via service worker); last-synced profile, forecasts, alerts, and advisories readable from local storage (IndexedDB); **a lightweight offline responder** answers common structured queries ("today's forecast," "active alerts," "today's harvest advisory") directly from cached data with no LLM call and no network needed; anything genuinely novel queues via Background Sync and fires automatically the moment connectivity returns |
| 3 | True zero signal | Last-cached data only, clearly labeled with sync time ("Showing data synced 6 hours ago") — an honest limit, not a hidden one; no new live queries |
| 4 | No smartphone/data plan at all | Out of PWA's reach entirely — the only channel is SMS. Real SMS sending isn't free at meaningful volume, so this stays a demo-only mockup of the flow, not live infrastructure, to respect the zero-cost constraint (Section 3.5) |

**What makes Layer 2 the one worth real engineering effort:** it's the layer that actually reflects how most rural users experience connectivity day to day, and it's fully achievable with standard, free, well-documented browser APIs — no exotic infrastructure required:

- **Service worker, cache-first for the app shell** — HTML/CSS/JS/icons served from cache so the app opens instantly instead of showing a blank screen while it tries to load code over a weak connection.
- **IndexedDB for local-first data** — the farmer's crop profile, saved locations, and recent forecast/alert/advisory history persist client-side.
- **The offline responder** — a small template-based function (not the LLM) that formats cached structured data into a readable answer for the handful of most common query shapes. This is the piece that keeps the app *useful*, not just *readable*, without connectivity.
- **Background Sync API** — queues anything that needed the network and retries automatically on reconnect, without the user having to notice or re-trigger anything.

---

## 3.7 Crop Risk Index — weighted crop-stress model (with disease suitability as a component)

**This is the engine behind Crop Watch** (monitoring an already-planted crop), not Crop Planning. It answers: *how stressed is this specific crop by current/recent weather, and why?*

**The backbone — a weighted crop-stress score.** The two weather parameters with a well-defined per-crop optimal band — **temperature and soil moisture** — are the fit terms (temperature sourced/cited; soil moisture an approximation, see below). **Humidity is deliberately NOT a fit term** — see "Humidity is crop- and stage-specific" below. For each fit parameter, score how well the current/recent reading fits that crop's optimal range, on 0–1: **1.0 anywhere inside the range** (being in-range is ideal, edges included), with a linear fall-off outside, reaching 0 one band-width beyond an edge — a *plateau*, not a triangular peak (which would wrongly score the range's own edges as maximum stress):

```python
def parameter_score(actual, low, high):
    if low <= actual <= high:
        return 1.0
    span = (high - low) or 1.0
    dist = (low - actual) if actual < low else (actual - high)
    return max(0.0, 1 - dist / span)
```

Combine with weights (temperature dominates), and invert to a risk:

```
crop_fit    = 0.60·temperature + 0.40·soil_moisture
risk (0–1)  = 1 − crop_fit
risk_score  = round(risk × 100)      # 0–100, shown on the gauge
```

**Humidity is crop- and stage-specific, not a generic band.** A per-crop "humidity comfort band" is fake precision, and a blanket rule like `humidity > 90% → bad` is wrong-in-direction for some crops — humidity's real signal is **disease susceptibility at vulnerable growth stages**. So humidity is expressed through the **stage-aware disease threat**: each crop's key disease has a temperature+humidity favouring rule *and* `susceptible_stages`. The threat fires when the weather favours the disease, and its **level and explanation are modulated by whether the crop is at a stage the disease actually damages** — "At the Flowering stage — a susceptible window for blast — 96% humidity and 26°C favour it" rather than an unexplained humidity warning. This is the concrete, hard-to-copy domain logic (the reason Farmer Mode is the flagship): crop × stage × weather, not a threshold.

**Rainfall is a threat, not a fit term either.** Live precipitation (a probability, or a short-term amount) and a crop's *seasonal* rainfall requirement are different scales and can't be compared as a fit deviation, so rainfall surfaces as an explicit **threat** (heavy rain → drainage / waterlogging / fungal risk). The two fit parameters (temperature, soil moisture) are exactly the ones with a clean current-value-vs-optimal-band comparison. **Soil-moisture units:** Open-Meteo reports volumetric water content (m³/m³, ~0.05–0.45), so each crop's `soil_moisture_opt` band is curated in those same units — not a 0–1 fraction-of-capacity.

**Fail-soft weighting.** Any parameter can be missing (a source failed soft — CLAUDE.md's data contract). When one is absent, compute over the parameters we *do* have and **renormalize the remaining weights to sum to 1** — never fabricate a value to fill the gap. **Soil moisture** is fetched best-effort from **Open-Meteo** (a separate call, like AQI — WeatherAPI doesn't report it), so it participates when available and drops out cleanly when Open-Meteo is unreachable (429/outage) rather than breaking the score.

**Sustained, not instantaneous.** Stress and disease build over time, so parameters are averaged over the last ~24h of hourly data, not a single snapshot.

**Why the threat fired — the explanation the UI requires.** The per-parameter scores *are* the explanation (scope §3: never present an unexplained warning). The weakest parameter(s) name the problem ("low soil moisture + high temperature stress"), which drives the `threats[]` list and selects the curated `recommended_action`. This is what makes Crop Watch explainable rather than a black-box gauge, and it maps `risk_score` to a `risk_level` band (Low / Moderate / High / Very High).

**Disease suitability — one component of the index, not the whole thing.** Beyond raw parameter fit, a per-crop **key-disease** rule contributes a "disease" threat when conditions favour that crop's characteristic weather-linked disease/pest. That sub-score is itself continuous rather than a rigid threshold, for the same biological reason:

A binary rule like `humidity > 90% → HIGH risk` is a poor model of biology: 88% humidity can still be risky, and 92% humidity isn't dangerous at all if the temperature is wrong for the disease in question. The fix is scoring each factor continuously on a 0–1 scale — 0 meaning "not biologically suitable," 1 meaning "ideal conditions for the disease" — rather than a yes/no threshold.

**Temperature suitability** — most diseases have an optimal range with a bell-curve falloff on either side:

```python
def temp_suitability(T, optimal, width):
    return max(0, 1 - abs(T - optimal) / width)
```

**Humidity suitability** — most fungal diseases ramp up from a floor to a ceiling rather than switching on at one number:

```python
def humidity_suitability(H, floor=70, ceiling=90):
    if H < floor: return 0.0
    if H > ceiling: return 1.0
    return (H - floor) / (ceiling - floor)
```

**Growth-stage relevance** stays a simple lookup table (a disease that mainly threatens the vegetative stage scores low at seedling or maturity).

**Combining into one score**, weighted by which factor matters most for that specific disease:

```
Disease Suitability = w_temp × temp_suitability(T) + w_humidity × humidity_suitability(H) + w_stage × stage_score
```

**Not every disease favors humidity.** This is worth stating explicitly because it's the strongest argument for this model over a rigid rule: charcoal rot in soybean and whitefly-driven cotton leaf curl virus are both favored by *hot, dry* conditions — the opposite curve from fungal diseases like wheat rust or rice blast. A single `humidity > 90%` rule would be actively wrong-direction for two of our eight crops, not just imprecise.

| Crop | Weather-linked disease/pest | Favors |
|---|---|---|
| Wheat | Yellow/stripe rust | Cool + humid |
| Rice | Blast | High humidity + moderate temp |
| Mustard | Alternaria blight | Moderate temp + high leaf wetness |
| Gram | Botrytis gray mold | High humidity + moderate temp, dense canopy |
| Maize | Turcicum leaf blight | Cool + humid |
| Soybean | Rust (humid) vs. charcoal rot (hot + dry) | Opposite profiles on the same crop |
| Groundnut | Tikka leaf spot vs. collar rot (waterlogging) | Humid-warm vs. excess-moisture-specific |
| Cotton | Leaf curl virus (whitefly-vectored) | Warm + **dry** — favors the insect vector, not fungal humidity |

**These are illustrative shapes, not final numbers.** The actual optimal-temperature and humidity-threshold values must be sourced from ICAR's crop-specific Plant Protection advisories before shipping — this drives real advice to a farmer, so it earns the same sourcing discipline as the crop rule table itself, at an even higher bar.

**Time dimension:** disease risk builds from *sustained* favorable conditions, not one instant. Average the suitability score over the last 24 hours of actual hourly data (already available from the Sprint 1 Open-Meteo connector) rather than scoring a single snapshot.

**Where this sits in the Crop Risk Index:** the **weighted crop-stress fit is the backbone** of the 0–100 score; disease suitability contributes the "disease" threat and its explanation, and — when the Trend Engine (Section 3.8) is wired — a historical-baseline-deviation term can nudge the score for a season running anomalously against its multi-year norm. v1 ships the crop-stress backbone + the per-crop disease threat; the trend term is an additive refinement, not a blocker.

---

## 3.8 Trend Engine (shared component)

Historical data has one correct use, and it isn't just decorating a charts tab: combined with the current forecast, it drives actionable recommendations. This single component now serves two features that were previously separate:

1. **Multi-year baseline** — a moving average per location/variable computed from the preloaded historical dataset (e.g., typical monsoon onset date, typical seasonal rainfall total).
2. **Trend regression** — a simple linear fit (`numpy.polyfit`, still statistics, not ML) showing whether that variable is drifting over the available years — monsoon onset trending later, a region trending warmer for a given date.
3. **Anomaly detection** — compares this season's actual/forecast readings against the baseline.

**The advisory logic activates when the anomaly and the multi-year trend agree**, not from either signal alone — e.g., this year's early rainfall running below average *and* the 10-year trend showing monsoon onset drifting later together justify a concrete recommendation ("consider delaying sowing by roughly a week"), tagged with the data tier "historical trend + current forecast."

**Two consumers of the same component** (build once, reuse two ways):
- The Crop Risk Index's baseline-deviation term (Section 3.7)
- The standalone Trend-Informed Advisory feature for general/farmer queries about how this season compares to historical norms

*(The route-aware Trip Planner — Feature 9 / Section 3.10 — no longer consumes the Trend Engine: it plans near-term routes using live forecasts at each stop's ETA, not far-future climatology.)*

---

## 3.9 Disaster Safety Guidance & Active Emergency Mode

This is the most safety-sensitive part of the product, and it follows the grounding principle used everywhere else — curated, sourced content that the LLM formats and personalizes but never invents — held to a stricter bar here than anywhere else, since wrong guidance in this category can cause real harm, not just bad advice.

**For individuals — nearby-alert-based guidance:** a curated Hazard Safety Guide, covering five hazard types (flood, cyclone, heatwave, thunderstorm/lightning, cold wave), sourced from NDMA's published Do's and Don'ts guidance. Structurally this is the same kind of build as the crop rule table — a curated JSON lookup, not a model. When an active alert matches the user's location, the raw warning is shown alongside a Safety Guidance card built by injecting the matched hazard's curated content into the grounding context.

**Active Emergency Mode** — a visually distinct, more urgent state triggered at the highest severity tier (an IMD Red warning, or a cyclone landfall window):
- Immediate hazard-specific action steps from the same curated guide.
- A **verified helpline block**: NDMA's national helpline (**1078**), India's general emergency number (**112**), and an explicit note that the district control-room number must be looked up per location (these vary by state/district and change) rather than hardcoded as one number nationally.
- **One honest, explicitly stated gap**: real-time shelter-location data isn't realistically available to a student team. This is listed as a known limitation, not fabricated — an invented shelter address is a far worse failure than an honest "check with your local district control room for the nearest relief camp."

**For government/stakeholders — extending the Disaster Manager view:** alerts sorted by severity, layered with Trend Engine context ("this district has seen roughly N comparable events in the past decade"), and a modest severity + historical-frequency region ranking — deliberately not a full resource-allocation system, since this remains the least user-validated persona (Section 2.2) and overbuilding here risks looking like guesswork dressed up as expertise.

**Worth stating plainly in the pitch, not hiding:** this is prototype-stage decision support, not a claim to replace official emergency services — stating that directly to judges is a stronger, more credible position than implying more coverage or reliability than a 13-day student build can actually deliver.

---

## 3.10 API Contract — Endpoint Data Shapes

This is the piece that makes frontend and backend work genuinely independent (Section 4, Sprint 1) rather than only appearing to be. A "data shape" is the structure of a response — which fields exist, what each is called, what type each holds — independent of the actual values. As long as both sides agree on the shape before either starts building, the frontend cannot tell the difference between a hand-written mock and a real backend response, which is what lets Frontend/UX start Day 1 against static fixtures instead of waiting for Sprint 5.

**Lock this section before Sprint 1's real logic starts.** Changing a field name or type later is "shape drift" — it should be a visible, deliberate PR everyone sees, never a silent change inside one branch.

`GET /weather/{location}` — current-conditions record (the normalized shape from CLAUDE.md's data contract; the Home screen's `current` block reads this)
```json
{ "location": "Noida, Uttar Pradesh", "temp": 28.4, "condition": "partly cloudy",
  "precipitation_chance": 0.3, "humidity": 72, "feels_like": 31.0, "wind_speed": 12.0,
  "aqi": 86, "warnings": [], "source": "Open-Meteo", "data_tier": "exact",
  "fetched_at": "2026-09-06T09:11:33Z" }
```

`GET /home/{location}` — composite Home-screen view: current + hourly + a rule-based recommendation, in one response
```json
{ "location": "Noida, Uttar Pradesh",
  "current": { "temp": 28.4, "condition": "partly cloudy", "data_tier": "exact", "source": "Open-Meteo" },
  "hourly": [
    { "time": "2026-09-06T09:00", "temp": 28.4, "condition": "partly cloudy", "precipitation_chance": 0.3 }
  ],
  "recommendation": { "title": "Good time for a short outing",
    "message": "Conditions look comfortable right now — a good time to be outdoors." },
  "data_tier": "exact" }
```
(`current` is abbreviated above — it carries the full `GET /weather` record. `hourly` is `[]` and `recommendation` degrades to an honest "limited data" message when live sources are unavailable — never a bare refusal.)

`POST /chat`
```json
// Request — context_location + history are OPTIONAL (multi-turn support, added
// Sprint 2). context_location is the place the conversation carries forward (last
// resolved location or the user's default) so a location-less follow-up resolves
// instead of dead-ending; history is the recent turns for phrasing coherence.
{ "query": "will it rain tomorrow in Delhi?", "language": "en", "user_id": "usr_123",
  "context_location": "Delhi",
  "history": [ { "role": "user", "content": "weather in Delhi" },
               { "role": "assistant", "content": "It's 27°C, clear sky." } ] }
// Response — `location` (added Sprint 2) echoes the resolved place so the client
// can carry it forward on the next turn.
{ "answer": "Yes — 68% chance of rain tomorrow evening in Delhi.",
  "data_tier": "exact", "source": "Open-Meteo", "query_class": "realtime",
  "audio_url": null, "location": "Delhi" }
```

`GET/POST /farmer/profile`
```json
{ "user_id": "usr_123", "crop": "wheat", "field_location": "Sonipat, Haryana",
  "sowing_date": "2025-11-12", "growth_stage": "vegetative" }
```

`GET /farmer/risk-score` — the weighted crop-stress score (Section 3.7). `risk_score` is 0–100, `risk_level` a band. `components` are the per-parameter fit scores (0–1) that back the number and name the problem; a missing parameter is omitted and its weight renormalized away (fail-soft), so `components` carries only the parameters that were actually available.
```json
{ "crop": "rice", "risk_score": 72, "risk_level": "high",
  "components": { "temperature": 0.55, "soil_moisture": 0.30 },
  "problem": "Low soil moisture + high temperature stress",
  "data_tier": "exact", "source": "WeatherAPI + Open-Meteo (soil moisture)" }
```

`GET /farmer/advisory`
```json
{ "crop": "wheat", "advisory_type": "harvest_timing",
  "message": "Complete harvest before Thursday — rising humidity raises fungal risk.",
  "valid_until": "2026-09-11", "sources": ["IMD forecast", "ICAR wheat rule table"] }
```

`GET /farmer/crop-planning` — **Crop Planning** ("what should I grow?"): ~3–4 crops suited to the location + season + environmental suitability, each with a short reason and an approximate harvest window. Composite, and demo-fixture-first (`data_tier: "demo"`) until the backend lands; the frontend already renders this shape.
```json
{ "data_tier": "demo", "source": "Frontend demo fixture",
  "location": "Noida, Uttar Pradesh", "season": "Rabi",
  "climate_context": { "summary": "Cooler winter conditions suit Rabi crops in this region.",
                       "historical_note": "Based on typical seasonal conditions for the region." },
  "recommendations": [
    { "crop": "Wheat", "suitability": "Excellent",
      "reason": "Well suited to the cool Rabi season and local conditions.",
      "harvest_window": "March–April" }
  ] }
```

`GET /farmer/crop-watch` — **Crop Watch** ("what's happening to my planted crop?"): the **composite** endpoint that returns everything the Crop Watch screen needs in one response (chosen over composing from sub-endpoints, mirroring `GET /home`). Sub-endpoints `/farmer/crop-profile`, `/farmer/risk-score`, `/farmer/advisory` remain available for reuse. `components` backs `risk_score` (Section 3.7); every `threats[]` entry carries a `detail` explaining *why* it fired. Demo-fixture-first; the frontend already renders this shape.
```json
{ "data_tier": "demo", "source": "Frontend demo fixture",
  "location": "Noida, Uttar Pradesh",
  "crop": "Wheat", "days_after_sowing": 48, "crop_stage": "Vegetative", "next_stage": "Flowering",
  "risk_score": 62, "risk_level": "Moderate",
  "components": { "temperature": 0.6, "soil_moisture": 0.5 },
  "threats": [
    { "id": "disease", "label": "Disease", "level": "High", "detail": "At the Flowering stage — a susceptible window for yellow rust — 92% humidity and 14°C favour it." }
  ],
  "recommended_action": { "title": "Protect against fungal disease",
    "items": ["Scout lower leaves for early lesions", "Hold off overhead irrigation", "Prepare a preventive fungicide if humidity persists"] },
  "climate_context": { "title": "El Niño influence", "level": "Moderate",
                       "detail": "May affect seasonal rainfall patterns in your region." } }
```

`POST /trip-plan` — **route-aware stop planner**: geocodes the origin + destination, routes between them, and rates stops along the way from the forecast at each stop's ETA, plus nearby facilities. Weather comes from Open-Meteo; geocoding, routing, and facilities from **Geoapify** (§8.2). The frontend Travel tab already renders this shape (mock data today).
```json
{ "route": { "from": "Noida, Uttar Pradesh", "to": "Jaipur, Rajasthan",
             "distance_km": 280, "estimated_time": "5h 20m", "route_name": "NH48", "condition": "Good" },
  "departure": { "label": "Tomorrow", "time": "8:00 AM" },
  "checkpoints": [
    { "id": "gurugram", "name": "Gurugram", "distance_km": 42, "eta": "8:45 AM",
      "temperature": 30, "weather": "partly cloudy", "rain_probability": 20,
      "status": "good", "note": "Good stop with low rain probability.",
      "facilities": { "restaurants": "20+", "fuel_stations": 6, "hotels": "10+", "hospitals": 4, "parking": "Yes" } }
  ],
  "summary": "Good travel conditions expected from Noida to Jaipur.",
  "weather_source": "Open-Meteo", "routing_source": "Geoapify",
  "data_tier": "regional_fallback", "fetched_at": "2026-09-08T08:00:00" }
```
(`status` ∈ `good` | `caution` | `not_recommended`, derived from rain/temperature at the stop's ETA. Provenance is **split** — `weather_source` vs `routing_source` — because the weather and the routing/facilities come from different providers; don't collapse them to one `source`.)

`GET /disaster/alerts`
```json
{ "alerts": [
    { "region": "Tamil Nadu Coast", "hazard_type": "cyclone", "severity": "high",
      "valid_until": "2026-09-06T18:00:00", "source": "IMD",
      "historical_context": "6 comparable events in the last decade" } ],
  "count": 14 }
```

`GET /disaster/safety-guide`
```json
{ "hazard_type": "cyclone", "severity": "high",
  "do": ["Move away from coastal areas", "Secure loose outdoor objects"],
  "dont": ["Do not use electrical appliances during flooding"],
  "helplines": { "national": "1078", "emergency": "112", "district": "look up locally — varies" },
  "emergency_mode": true, "source": "NDMA" }
```

`GET /disaster/rescue-facilities/{location}` — **planned** (the frontend Disaster tab renders this today from a mock; no backend yet — see Section 8 backlog). Nearby emergency-support facilities — explicitly NOT designated relief camps.
```json
{ "facilities": [
    { "name": "Police Station — Sector 20", "type": "police_station",
      "address": "Noida, Uttar Pradesh", "distance_km": 2.1, "source": "Google Places" } ] }
```
(The demo mock deliberately omits `data_tier` on its placeholder entries so fake facilities are never shown as `"exact"`; a real listing endpoint may carry its own `data_tier`/`source`.)

`GET /historical/trends`
```json
{ "location": "Sonipat", "variable": "rainfall",
  "baseline": [{ "day_of_year": 1, "avg": 2.1 }],
  "current_season": [{ "date": "2026-06-01", "value": 5.4 }],
  "trend_slope": 0.3, "trend_direction": "increasing" }
```

`GET/POST /settings/digest`
```json
{ "user_id": "usr_123", "enabled": true, "delivery_time": "07:00",
  "language": "hi", "include": ["forecast", "alerts", "crop_advisory"], "channel": "push" }
```

**Note the recurring fields**: `data_tier` and `source` appear in almost every shape — this is deliberate, since it's the single field every screen's provenance chip reads from regardless of which endpoint produced the answer.

---

## 4. Step-by-Step Build Plan — 12–13 Day Sprint Structure

This replaces the hour-by-hour hackathon-day plan with a day-based sprint plan for the internal round's ~12–13 day window, for a team of 5–6. It's organized into five sprints, each ending with something demoable, so the team always has a working checkpoint rather than a big-bang integration at the end. Adjust day counts to your actual deadline, but keep the sprint ordering — later sprints depend on earlier ones being solid.

### Sprint 1 — Foundation (Days 1–3)

**Goal:** the full real-time data pipeline working end-to-end, deployment wired up from day one, and the team's research/curation work for later sprints already underway in parallel.

1. **Day 1:** Agree on stack, set up the shared repo with the folder structure and `CLAUDE.md`/`AGENTS.md` conventions file (see the Team Collaboration & AI-Agent Workflow doc), get a barebones FastAPI "hello world" deployed (Render/Railway) immediately — deployment problems are cheapest to find when nothing depends on them yet. Lock the API contract (Section 3.10) before anyone writes real logic. In parallel: the Farmer Advisory lead starts researching ICAR/GKMS crop advisory data (see Sprint 3's crop table below) — this research is slow and benefits from starting immediately rather than being squeezed into Sprint 3; **the Frontend/UX lead starts Day 1 too**, converting the mockup into the real framework and building every screen against static JSON fixtures matching Section 3.10's shapes, not waiting for real endpoints (see the note at the end of this sprint).
2. **Day 1–2:** Build the static geocoding table (~500 Indian cities/districts), the Open-Meteo connector, and the IMD warnings connector.
3. **Day 2:** Build the degradation ladder (exact match → nearest/regional → related-data-with-caveat → honest gap) and the Nominatim fallback.
4. **Day 2–3:** Normalize all sources into the shared internal data shape (`{location, temp, condition, precipitation_chance, humidity, feels_like, wind_speed, aqi, warnings, source, data_tier, fetched_at}` — `aqi` is from the separate Open-Meteo Air Quality API, US-AQI scale), pull the preloaded historical dataset (Open-Meteo Historical API, one-time fetch), and stand up the short-TTL response cache.
5. **Day 3:** Set up the `pytest` scaffold and GitHub Actions CI now, even with just a couple of tests against the degradation ladder — wiring this up early means every subsequent piece of logic gets tested as it's built, rather than retrofitted later.

**Frontend runs as a parallel track, not a Sprint 5 task:** because the API contract (Section 3.10) is fixed before any backend logic is written, the Frontend/UX lead can build every screen — chat, farmer dashboard, trip planner, disaster view, offline state — against static mock JSON from Day 1 onward, entirely decoupled from backend progress. As each real endpoint comes online in Sprints 2–4, frontend swaps one mock call for one real fetch call at a time. This turns Sprint 5 into polish and QA instead of first-time integration, which is a much safer place to be with only a few days of runway left.

**Checkpoint at end of Sprint 1:** an internal function/endpoint returns real, structured, gracefully-degrading weather data for any Indian location, deployed and covered by at least a few passing tests — and, running in parallel, a frontend shell with every screen navigable against mock data.

### Sprint 2 — Core Conversational Engine (Days 3–6, overlapping Sprint 1's tail)

**Goal:** the grounded, multilingual, voice-enabled conversational core — the technical heart of the submission.

1. **Day 3–4:** Build the rule/keyword fast path, then the LLM-based intent-extraction step (structured JSON output: location, hazard type, time range, query class) for everything the fast path can't resolve.
2. **Day 4:** Build the grounding assembler (data → factual context block, tagged with `data_tier`) and the final answer-generation prompt, with the explicit rule that the model must never return a bare "insufficient data" reply.
3. **Day 4–5:** Multilingual layer — with 12–13 days, support three languages properly (Hindi plus two more relevant to your likely demo audience — Bengali, Tamil, Marathi, or Punjabi are all well-supported by modern LLMs; pick based on your team/judges' region). Test each language individually rather than assuming parity across all three. **(Delivered: six languages — en/hi/bn/ta/mr/pa — via a whole-app i18n layer that re-renders the entire UI, not only the LLM's answers; en+hi hand-verified, the other four flagged for native-speaker review.)**
4. **Day 5:** Voice input/output via the browser's Web Speech API (STT and TTS), tested end-to-end in all three languages. **(Delivered: both directions wired — speech-to-text input and read-aloud output — in the selected language.)**
5. **Day 5–6:** Response caching for LLM answers, and a proper test pass across query types: current conditions, multi-day forecast, alert-specific queries, historical/trend queries, and deliberately-broken queries (obscure location, edge-case date) to confirm graceful degradation. **(Delivered: short-TTL caching of settled answers.)**

**Checkpoint at end of Sprint 2:** a working chat interface (even unstyled) that correctly answers a broad query set, in six languages (the whole UI, not just answers), by text and voice, grounded and never bare-refusing — **met**, and extended with conversation persistence + multi-turn context and a user Settings screen (see §8.1).

### Sprint 3 — Flagship Features: Farmer Advisory + Trip Planning (Days 6–9)

**Goal:** the differentiated features from Section 2.1/2.2 — the part of the submission that separates it from "just a chatbot."

**Farmer Advisory Dashboard** (majority of this sprint's time; do not compress this to fit the schedule — extend into Sprint 4's buffer if needed):

1. Crop profile setup (crop, field location, sowing date) as a persistent Postgres record.
2. **Expanded crop rule table — 8 crops**, covering both major Indian cropping seasons so the demo isn't season-locked:

   | Crop | Season | Example sourced threshold |
   |---|---|---|
   | Wheat | Rabi | Irrigation at 21/42/65 days after sowing depending on irrigation availability; frost/hailstorm risk at harvest (Feb–Mar) |
   | Mustard | Rabi | Aphid risk rises with cloudy weather + falling night temperature; irrigation timed to flowering (30–40 DAS) and pod-filling (60–70 DAS) stages |
   | Gram (chickpea) | Rabi | Cool-weather crop; unseasonal rain/hailstorm at harvest is the primary risk window |
   | Rice | Kharif | Sowing/transplanting timed to reliable monsoon onset; excess rain requires drainage + fungal-disease watch |
   | Cotton | Kharif | Monsoon-dependent sowing window; dry-spell irrigation triggers |
   | Maize | Kharif | Monsoon-dependent; excess-rain drainage and fungal risk, similar to rice |
   | Soybean | Kharif | Monsoon-dependent sowing; waterlogging risk in heavy-rain spells |
   | Groundnut | Kharif | Monsoon-dependent; dry-spell and excess-rain risk windows both matter for pod development |

   Source this from ICAR's seasonal Kharif/Rabi Agro-Advisories, IMD-ICAR-CRIDA District-level Crop Weather Calendars, and state Gramin Krishi Mausam Sewa (GKMS) bulletins — all public. Cite these sources explicitly in the pitch; naming real institutional sources materially strengthens credibility over an unsourced rule table.

   **Crop list (locked, Sprint 3):** wheat, rice, maize, cotton, soybean, groundnut, mustard, gram, pea, potato, tomato, lentil — the eight staples plus potato, pea, tomato, and lentil. **Optimal-temperature bands and key-disease conditions are sourced and cited per crop** in `crop_rules.json` (ICAR / ICRISAT / TNAU Agritech / IMD Mausam, plus standard extension and peer-reviewed plant-pathology references), so the response's `provisional` flag is now false. The **humidity comfort bands** and the **volumetric soil-moisture bands** remain documented **engineering approximations** — a crop's optimal volumetric soil moisture (m³/m³) is not an ICAR-published quantity (ICAR schedules irrigation by IW/CPE ratio or crop coefficients), and humidity comfort is stage/variety dependent. A domain teammate should still sanity-check all bands against local package-of-practices before the final demo.
3. Harvest/action-timing advisory logic (forecast × growth stage × rule table).
4. **Crop Risk Index — weighted crop-stress model** (Section 3.7): fit scores for **temperature and soil moisture** against each crop's optimal range, weighted `0.60·T + 0.40·soil`, inverted to a 0–100 risk and banded. **Fail-soft:** renormalize the weights over whatever's available. **Humidity is not a fit term** — its risk is crop- and stage-specific, so it drives the **stage-aware disease threat** (each crop's key disease has a temp+humidity favouring rule *and* `susceptible_stages`; the threat's level + explanation depend on the crop's current stage). **Rainfall** is an explicit threat too (heavy rain), not a fit term. **Soil moisture** is best-effort from Open-Meteo (volumetric m³/m³). The temperature bands + disease conditions are **sourced and cited** per crop in `crop_rules.json`; the humidity and volumetric soil-moisture bands are documented **approximations** (a volumetric soil-moisture optimum isn't ICAR-published).
5. **Threats + advisory from the score**: the weakest parameter(s) name the `threats[]` and select a curated `recommended_action`, so every warning is *explained* (scope §3), never a bare gauge. The Trend Engine's historical-baseline-deviation term (below) is an additive refinement to the score, not a v1 blocker.
6. Free-text crop Q&A routed through the Sprint 2 LLM pipeline with the rule table injected as grounding context.

**Trend Engine** (Section 3.8; build this in parallel with the Farmer Advisory work since both the Risk Index and Trip Planning depend on it):

1. Multi-year baseline (moving average per location/variable) from the Sprint 1 historical dataset.
2. Trend regression (`numpy.polyfit`) for direction/slope over available years.
3. Anomaly detector comparing current season against baseline — feeds the Risk Index and the standalone Trend-Informed Advisory query type ("how does this season compare to normal").

**Trip Planning — route-aware stop planner** (the frontend Travel tab already exists; this sprint wires the backend):

1. Free-text origin + destination entry; geocode both ends (Geoapify).
2. Route between them (Geoapify Routing) → distance, ETA, route name, and the checkpoints/stops along the way.
3. For each checkpoint, pull the forecast at its ETA (Open-Meteo) and rate the stop `good` / `caution` / `not_recommended` from rain/temperature.
4. Fetch nearby facilities per stop (Geoapify Places — restaurants, fuel, hotels, hospitals, parking).
5. Return the composite `/trip-plan` shape (Section 3.10) the Travel tab already renders.
6. Test with one real route — mock the Geoapify/Open-Meteo calls, per the testing rules.

**Checkpoint at end of Sprint 3:** a farmer can set up a crop profile and get a working risk score and harvest advisory; a trip query produces a route with rated stops (weather at each ETA + nearby facilities).

### Sprint 4 — Depth Tier: Alerting, Disaster View, PWA/Offline, Testing (Days 8–10, overlapping Sprint 3's tail)

**Goal:** the remaining differentiators that this extended timeline specifically makes feasible.

1. **Proactive alerting**: saved locations, background poller (APScheduler) against IMD warnings, in-app banner, and a demo-trigger endpoint to simulate an alert on demand.
2. **Disaster Manager / Stakeholder view**: a separate dashboard route showing an aggregated, severity-sorted view of currently active alerts, layered with Trend Engine context (Section 3.9) — this reuses the alerting backend and the Sprint 3 Trend Engine entirely; it's a new front-end lens plus a sort, not new backend logic.
3. **Disaster Safety Guidance + Active Emergency Mode** (Section 3.9): curate the Hazard Safety Guide (flood, cyclone, heatwave, thunderstorm/lightning, cold wave) sourced from NDMA's Do's and Don'ts guidance; wire the severity check that triggers Active Emergency Mode at the highest alert tier, showing action steps and the verified helpline block (NDMA 1078, Emergency 112). This is the most safety-sensitive feature in the product — hold it to the strictest sourcing discipline, and explicitly flag the real-time-shelter-data gap as a known limitation rather than fabricating it.
4. **PWA + connectivity layer**: build the full layered strategy from Section 3.6 — web app manifest + cache-first service worker for the app shell, IndexedDB for the farmer's profile and recent forecast/alert/advisory history, a template-based offline responder for common structured queries (no LLM/network needed), and Background Sync to queue and auto-retry anything that needed the network. This is genuinely on-theme for the PS's "rural accessibility" framing and was explicitly out of scope for the hackathon-hours version of this plan — treat it as a first-order feature, not a Sprint 4 afterthought.
5. **Personalized digest**: a settings screen (preferred time, language, content toggles) and a per-user APScheduler job that assembles a digest by reusing the grounding assembler, delivered via push or queued through the same Background Sync path built in this sprint.
6. **Expand and harden the test suite**: cover the risk-index calculator (including the Disease Suitability Model and Trend Engine), the trip-planning router, and the multilingual pipeline, not just the degradation ladder from Sprint 1. Keep CI green throughout the remaining sprints — a red CI pipeline right before the deadline is a bad place to discover a regression.

**Checkpoint at end of Sprint 4:** alerts trigger reliably and are visible in both the general and disaster-manager views; the app functions (in a degraded but real way) with the network disabled; CI is green.

### Sprint 5 — Integration, QA, Documentation & Presentation (Days 10–13)

**Goal:** everything from Sprints 1–4 unified into one coherent, polished, rehearsed submission — this sprint has room a hackathon timeline never affords, so use it properly rather than compressing it.

1. **Day 10–11 — Frontend integration and polish**: unify the chat interface, farmer dashboard, disaster-manager view, and interactive historical charts/maps (fed by the Sprint 1 historical dataset, filterable) into one coherent product with consistent navigation. Visual weather cards, language/voice toggles clearly visible, farmer dashboard as a distinct visually-separated mode.
2. **Day 11 — Full integration pass**: every feature from every sprint tested through the actual deployed UI — general queries, farmer advisory, trip planning, alerts, disaster view, PWA offline behavior, all three languages, both voice directions.
3. **Day 11–12 — Real QA/bug-bash pass**: deliberately try to break things — malformed input, missing location, network interruption, ambiguous queries, edge-case dates. Fix what's found; this is the phase a hackathon timeline structurally cannot afford, and it's disproportionately valuable for how a demo actually lands.
4. **Day 12 — Documentation**: clean README, the auto-generated API docs, and a short written summary of the differentiation argument (Section 2.1) and scoping decisions (Section 2) for submission materials.
5. **Day 12–13 — Presentation prep and rehearsal**: build the demo script (a general query, a multilingual/voice query, an alert scenario, a historical/trend query, a deliberate degradation-ladder query, a farmer-advisory query showing the risk score, a trip-planning query, and the disaster-manager view) and rehearse it multiple times — not just once or twice as the hackathon plan assumed, but enough times that the live demo is boring to the team by presentation day. Record a backup video of the full flow.
6. **Reserve real buffer** in the last day for whatever inevitably breaks — this sprint plan is ambitious, and having slack at the very end is what turns "ambitious" into "delivered" rather than "scrambled."

**Checkpoint at end of Sprint 5:** a fully integrated, tested, documented, deployed product with a rehearsed demo and a backup video — ready for submission with genuine time to spare rather than a last-minute scramble.

---

## 5. Suggested Role Split (team of 5–6, adjust to your actual size)

| Role | Focus | Primarily active in sprints |
|---|---|---|
| Backend/Data Lead | IMD + Open-Meteo connectors, caching, geocoding, deployment | 1, 5 |
| LLM/AI Lead | Intent extraction, grounding assembler, prompt design, trip-planning synthesis, multilingual testing | 2, 3 |
| Farmer Advisory Lead | Crop rule table research/curation (starts Day 1), risk-index formula, farmer dashboard logic | 1 (research), 3 |
| Full-Stack Engineer | Alerting poller, disaster-manager view, PWA/offline layer, CI/testing | 1, 4 |
| Frontend/UX Lead | Builds every screen against mock data from Day 1 (chat UI, farmer dashboard, disaster view, charts/maps view); swaps in real endpoints as they land | 1 (start), 2–4 (swap-in), 5 (polish) |
| Voice/Multilingual + QA Lead | STT/TTS wiring, language testing, bug-bash coordination, demo script, slides | 2, 5 |

*(If you're a team of 5, merge the Voice/Multilingual+QA role into whichever of LLM/Frontend has more bandwidth once their core work stabilizes. If you're a team of 6, the extra person is best spent on QA/testing depth in Sprint 5, since that's the phase a compressed timeline would otherwise shortchange.)*

---

## 6. Scope Flex (what to cut if behind, what to add if ahead)

With 12–13 days instead of 36 hours, the team shouldn't need harsh cuts — but a plan is still worth having for either direction, since schedules slip in both.

**If running behind, cut in this order** (each item further down is more central to the pitch than the one above it):

1. Third language (keep two solid languages rather than three shaky ones)
2. Personalized digest (a nice-to-have orchestration layer over things already built)
3. Disaster Manager view / Trend Engine context in it (the underlying alerting layer and Hazard Safety Guide stay intact either way)
4. PWA/offline layer (a strong differentiator, but the app still functions online without it)
5. Interactive charts/maps dashboard (the farmer advisory's core numbers still work without this; it's a visual layer, not the underlying logic)
6. Trip planning feature
7. Trend Engine's contribution to the Risk Index (fall back to Disease Suitability + extreme-weather proximity only, drop the historical-baseline term)
8. Automated test suite depth (keep the Sprint 1 baseline tests; skip expanding coverage further)

**Never cut, regardless of schedule pressure:** the grounding assembler and degradation ladder (the anti-hallucination/anti-refusal story mapping directly to the "accuracy" evaluation criterion), the Farmer Advisory Dashboard core logic — crop rule table, Disease Suitability Model, harvest-timing advisory, and Crop Risk Index (the flagship differentiation argument from Section 2.1), **Disaster Safety Guidance's sourced content and the Active Emergency Mode helpline block** (once built, this is safety-relevant content — better to ship it correctly or clearly mark it as not yet reliable than to half-cut it), the alert-trigger demo path, and a working deployed instance.

**If running ahead of schedule, in this order of value:**

1. Expand the crop rule table beyond 8 crops, or add region-specific variants (the same crop's advisory can differ meaningfully by state)
2. A fourth language
3. Push notifications via the browser Notification API (beyond the in-app banner)
4. Expand the disaster-manager view with exportable summary reports
5. A short recorded interview or informal feedback from an actual farmer/agricultural-extension contact, if the team has access to one — real user validation is a rare and valuable addition most teams won't have
6. A tiny on-device model for true zero-network offline answers (real research risk — treat as exploratory, not a commitment)

---

## 7. Final Deliverables Checklist

- [ ] Deployed, working prototype (public URL)
- [ ] Source code repository, organized, documented, with passing CI
- [ ] Automated test suite (degradation ladder, risk-index calculator, connectors)
- [ ] Auto-generated API documentation (Swagger/OpenAPI)
- [ ] Architecture diagram (this document, Section 3.1)
- [ ] Farmer Advisory Dashboard working end-to-end across all 8 crops (crop profile, harvest-timing advisory, Disease Suitability Model, Crop Risk Index with historical baseline)
- [ ] Trend Engine feeding the Risk Index and a standalone Trend-Informed Advisory query
- [ ] Trip planning flow working end-to-end for at least one route (rated stops + nearby facilities)
- [ ] Disaster Manager severity-sorted alert view with Trend Engine context
- [ ] Disaster Safety Guidance cards + Active Emergency Mode, sourced and cited to NDMA, with verified helpline block
- [ ] Personalized daily digest with working settings and scheduled delivery
- [ ] PWA installable + functions in a degraded but real way offline
- [ ] Interactive historical charts/maps dashboard with working filters
- [ ] Demo video (backup for live-demo risk)
- [ ] Presentation deck covering: differentiation argument (Section 2.1), scoped solution, architecture, live demo, scoping-decision rationale, evaluation-criteria mapping
- [ ] Test query set rehearsed multiple times against the deployed (not local) build, including farmer-advisory, trip-planning, and disaster-view queries

---

## 8. Implementation Status & Backlog (living)

This section tracks what has actually been built versus the plan above, and — most importantly — every feature that currently exists only as UI or scaffolding and still needs backend work, so nothing is silently left as a front-end-only shell. Update it as work lands; it is the bridge between this plan and the current codebase. (Sections 1–7 describe the intended design; this section describes reality.)

### 8.1 Built so far — including work that extends the original plan

**Sprint 1 data foundation (as planned):** static geocoding table + Nominatim fallback; Open-Meteo forecast connector (fail-soft); IMD warnings connector (stub, fail-soft); the degradation ladder; normalization to the shared record; short-TTL in-memory cache; `pytest` + GitHub Actions CI (backend).

**Sprint 2 conversational core (as planned) — shipped:** the grounded `POST /chat` pipeline end-to-end — rule/keyword **intent extraction** (`intent.py`: location, `query_class`, `time_range`, hazard; zero-LLM fast path) → degradation-ladder retrieval → the **grounding assembler** (`grounding.py`: turns a record into a facts-only context block tagged with `data_tier` — the anti-hallucination step) → **answer generation** via **Gemini Flash** with a **Groq** fallback (`llm.py`; both keyed via env), fail-soft to a deterministic grounded summary when no LLM is available. It is **forecast-aware** ("tomorrow"/"this week" pull the day's forecast via `forecast.py`), **never bare-refuses** (both CLAUDE.md rules hold end-to-end), and **caches settled answers** briefly (short TTL, keyed by resolved location + language + query). **Multi-turn:** `POST /chat` takes optional `context_location` + `history` and returns the resolved `location`, so a bare follow-up ("what about tomorrow?") or a location-less question resolves against the carried/last/default place instead of dead-ending (§3.10 updated).

**Additive — built but not strictly in the original plan (record it here so the doc stays honest):**
- **WeatherAPI.com forecast connector is now the PRIMARY forecast source; Open-Meteo is the fallback.** Open-Meteo is keyless and rate-limited *per IP*, so on a shared deployment IP (Render's free tier) it returns HTTP 429 "Daily API request limit exceeded" from *other tenants'* traffic — confirmed in production. WeatherAPI authenticates by key (`WEATHERAPI_KEY` env), so the quota is tied to us, not the shared IP. The ladder fetches WeatherAPI first and falls back to Open-Meteo (`fetch_forecast_with_fallback`); both return the identical record shape, so it's a true drop-in. Coded to WeatherAPI's **Free-plan** limits (3-day horizon, 100k/mo) so nothing breaks when a trial downgrades. `aqi` intentionally stays on Open-Meteo (WeatherAPI reports a 1-6 category, not the 0-500 US AQI our contract/recommendation thresholds use). Fails soft if the key is absent → falls straight to Open-Meteo, so the deploy works before the key is set.
- **`historical_baseline` tier wired into the ladder.** When every live forecast source is down, `get_weather` and `/home` now degrade to the preloaded historical baseline (typical temperature for the date) instead of a null current block — tagged `historical_baseline`, source `"Historical"`, with live AQI and any active warnings preserved. Locations with no preloaded baseline stay `source_unavailable` (honest). This is the ladder finally doing end-to-end what §3.4 describes.
- **Connector fail-soft logging.** The connectors' `except` branches now log the failure reason (HTTP status + response body) at WARNING before returning the unavailable record, so a production source outage is diagnosable in logs instead of silently swallowed.
- **Open-Meteo Air Quality connector** — a *separate* API from the forecast one, added to supply `aqi`. Returns the **US-AQI** scale, not India's CPCB scale (labelled honestly). Fails soft like every connector.
- **Extra current-conditions metrics** — `humidity`, `feels_like`, `wind_speed` added to the normalized data contract (additive; also in CLAUDE.md).
- **`source_unavailable` data_tier** — a new tier for "location resolved, but the live source is down," distinct from `unresolved_location`. Transient outages are not cached.
- **`GET /home/{location}` composite endpoint** — returns current conditions + hourly forecast + a recommendation in one response (Section 3.10). Reuses the degradation ladder's fetch/normalize.
- **Rule-based recommendation engine** (`recommendation.py`) — deterministic, safety-first, never bare-refuses. Priority: active warning → today's peak heat / feels-like → today's low (cold) → poor AQI → strong wind → high rain → moderate AQI → muggy (humidity + feels-like) → otherwise comfortable. The safety rules look ahead to the **day's forecast extremes** (`open_meteo.summarize_today`), not just the current hour. The general-purpose analogue of the curated farmer/disaster advisories; not in the Section 3.2 component table.
- **CORS** on the API (origins configurable via `FRONTEND_ORIGINS`) so the browser frontend can call it.
- **Frontend:** Home tab (weather postcard, provenance chip reading `source`/`data_tier`, hourly strip, recommendation), Disaster tab (active / no-alert states, alert-details / rescue-centers / emergency-numbers / demo-SOS panels), a shared `BottomNav` (Home / Travel / Disaster) with hash-based routing, and contract-faithful mocks in `frontend/src/mocks/`.
- **Chat screen wired to `POST /chat`** — a focused conversational screen (message thread, live grounded answers rephrased by the LLM with a provenance chip, forecast-aware for "tomorrow"/"this week", and an honest fallback if the service is unreachable). **Entry-point scope decision:** chat is opened from the **"Ask WeatherGPT"** card and the floating action button on Home — it is deliberately **NOT** a bottom-nav tab. It presents as a full screen launched from Home with a back control, keeping the primary nav to the three place-scoped views (Home / Travel / Disaster) while chat stays a task the user starts from the home surface.
- **Home wired to live data + polish** — the Home tab fetches the composite `GET /home/{location}` for real (no longer a mock), remembers the location, shows a live "updated N min ago" stamp with a spinning reload control, and loads the **default location** on open so returning users see a full weather card, not a bare screen. The floating "Ask WeatherGPT" star and a single **fixed** bottom nav are consistent across tabs.
- **App-wide multilingual UI (i18n)** — a dependency-free language layer (a module-level store read via `useSyncExternalStore`, `frontend/src/i18n/`) with a 6-language catalog (**en, hi, bn, ta, mr, pa**). Switching language re-renders the **whole app** at once and also drives the LLM answer language and browser voice; the choice persists per device. **en+hi are hand-verified; bn/ta/mr/pa are a first pass flagged in `catalog.js` for native-speaker review.** Migrating Divyansh's Disaster/Travel/Farmer mock screens onto the same keys is the remaining i18n work.
- **Voice input and output** — Web Speech API: speech-to-text into the chat input and read-aloud of any answer, both in the selected language (buttons hide where the browser lacks support).
- **User Settings screen** — reached from the header menu (a focused screen with its own back control, not a nav tab): app **language**, a **default location** + a curated **saved-places** list, and **Farmer-Mode preferences** (crop + farm location) persisted now and consumed by Farmer Mode when its live advisories land (Sprint 3). All device-scoped via `localStorage` (`lib/preferences.js`), migrating to a user profile with accounts (§8.2).
- **Chat session persistence + context** — the conversation persists on-device (~1 day) and restores on return, so leaving chat and coming back resumes it instead of starting cold (`lib/chatSession.js`); a "New chat" control starts fresh. Starter suggestions are **conditions-aware and localized** (localized label shown, English canonical query sent so backend location-parsing/grounding is unaffected).

### 8.2 Backlog — UI or scaffolding that still needs a backend

The "don't let it stay a UI-only feature" list. Each row has a working front end today; the right-hand column is the backend still owed.

| Feature (UI exists) | Current state | Backend still owed |
|---|---|---|
| Home current conditions | **✅ wired to live `GET /home`** | — |
| Location entry / selection | **✅ shipped** — location input + a **default location** and **saved-places** list in a Settings screen, persisted in `localStorage` | saved locations in Postgres once user profiles exist |
| App language / voice | **✅ shipped** — whole-app i18n (6 languages) + Web Speech voice in/out, chosen in Settings | native-speaker review of bn/ta/mr/pa; migrate Disaster/Travel/Farmer mock screens onto the i18n keys |
| Farmer-Mode preferences | UI shipped in Settings (crop + farm location, persisted) | consumed by the Sprint-3 Farmer Advisory backend (profile → risk/advisory) |
| Crop Planning (Farmer Mode) | demo fixture, provenance-labelled; shape documented (§3.10 `/farmer/crop-planning`) | real `GET /farmer/crop-planning` (location + season + climate suitability → ~3–4 crops) |
| Crop Watch (Farmer Mode) | demo fixture, provenance-labelled; shape documented (§3.10 `/farmer/crop-watch`) | composite `GET /farmer/crop-watch` backed by the weighted Crop Risk Index (§3.7) + a curated, cited crop rule table; `threats[]` each explained |
| Disaster alerts list | mock `/disaster/alerts` shape | live IMD-backed `GET /disaster/alerts` |
| Disaster alert details + safety guidance | a hardcoded generic advice line in the UI | **NDMA-sourced Hazard Safety Guide** (`GET /disaster/safety-guide`, Section 3.9) — hazard-specific, curated, cited |
| Rescue facilities | demo mock (no `data_tier`) | real `GET /disaster/rescue-facilities/{location}` (e.g. Google Places) |
| SEND SOS | demo-only; contacts no one, says so | real dispatch flow — likely **stays a demo** per the zero-cost constraint (Section 3.5); if built, needs a delivery channel |
| Travel Planner tab | route/checkpoint UI shipped (mock data) | `POST /trip-plan` backend: **Geoapify** (geocoding + routing + Places for facilities) + multi-day forecast at each ETA. Needs a `GEOAPIFY_API_KEY` secret + free-tier rate handling. Section 3.10. **The forecasting source for arbitrary multi-day stops is an open decision — see §8.3.** |
| Recommendation | rule-based (shipped) | optional Sprint-2 upgrade to the grounded-LLM advisory |

### 8.3 Engineering gaps to close

- **Deployment — DONE.** Backend live at `https://weathergpt-sih2026.onrender.com` (with `WEATHERAPI_KEY` set) and frontend static site live at `https://weathergpt-sih2026-frontend.onrender.com`, wired via `VITE_API_BASE_URL` with CORS opened through `FRONTEND_ORIGINS`. Config is reproducible in `render.yaml` + `docs/DEPLOYMENT.md`. This **closes the Sprint 1 checkpoint**: real, structured, gracefully-degrading weather data (WeatherAPI → Open-Meteo → historical) for any Indian location, deployed end-to-end. Test coverage has since grown to **106 backend + 54 frontend** tests green in CI (up from 61 + 19 at Sprint 1 close), covering the chat pipeline, grounding, forecast-awareness, caching, multi-turn context, the i18n layer, the preferences/session stores, and the Settings screen.
- **Trip Planner forecasting source — open decision (decide when the Sprint-3 backend is built).** The route-aware Trip Planner needs *reliable*, *multi-day* (up to ~14–16-day) forecasts at *arbitrary* route-stop coordinates. No current free path satisfies all three at once: WeatherAPI's Free plan caps at a 3-day horizon; Open-Meteo covers 16 days for any coordinate but is 429-prone on a shared deployment IP; and the top-cities prefetch does **not** help, because route stops are arbitrary points, not a fixed city list (and the prefetch holds historical climatology, not future-date forecasts). Options: **(a)** give the backend a dedicated egress IP (Fly.io dedicated IPv4 / a small VPS / static-IP add-on) so Open-Meteo's free per-IP quota is entirely ours — the cause-level fix, and it would let Open-Meteo be primary everywhere again; **(b)** a WeatherAPI paid tier (14-day, keyed); **(c)** client-side Open-Meteo calls from each user's own IP for the stop weather (outside the server-side grounding path, so display-only); or **(d)** scope the feature to ~10-day live forecast + clearly-labelled seasonal/historical beyond (forecast skill past ~10 days is essentially climatology anyway). Whichever we pick, this must be a deliberate choice — **not** an assumption that the prefetch/Supabase cache covers it, which it does not.

*(Closed since first drafted: the frontend test suite (Vitest + React Testing Library) and its CI job (`npm ci` → build → test); the "current conditions anchored to 00:00" bug (connectors now read the current-hour index via `open_meteo.current_hour_index`); the entire Sprint 2 conversational core (intent → grounding → LLM answer, forecast-aware, cached, multi-turn); the app-wide multilingual UI + voice in/out; and the user Settings screen with default/saved locations and chat session persistence. Still genuinely open: native-speaker review of bn/ta/mr/pa; the Sprint-3 Farmer Advisory + Trip Planner backends; a real IMD warnings connector; and migrating the Disaster/Travel/Farmer mock screens onto the i18n keys.)*

---

*Source PS text: Smart India Hackathon, sih.gov.in (CC BY 4.0), SIH26068. This build plan is independent team planning, not an official IMD/MoES specification.*
