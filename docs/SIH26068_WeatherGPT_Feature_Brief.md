# WeatherGPT — Feature Brief
### SIH 2026 · SIH26068 · Every planned feature, why it's worth building, and how feasible it is in a 12–13 day window

This document exists to answer one question per feature: **is this worth the time it will take, and how risky is it to build?** It's a companion to the Architecture & Build Plan (which covers *how* things connect) and the Product Mockup (which shows *what it looks like*) — this one is the honest spec sheet: what each feature is, why it earns its place, and where the real risk sits.

**How to read the Priority tags:** `Flagship` = the actual differentiation argument, never cut. `Core` = table-stakes, satisfies the PS's literal brief. `Secondary` = a genuine feature, real value, but not what separates this submission from a competent generic chatbot. `Stretch` = worth having if time allows, explicitly not promised.

---

## Quick reference

| # | Feature | Category | Priority | Effort | Sprint |
|---|---|---|---|---|---|
| 1 | Grounded Conversational Core | Core layer | Core | Medium | 2 |
| 2 | Data Foundation & Degradation Ladder | Core layer | Core | Medium | 1 |
| 3 | Proactive Alerting | Core layer | Core | Low | 4 |
| 4 | Farmer Advisory Dashboard | Flagship | Flagship | High | 3 |
| 5 | Disease Suitability Model | Flagship | Flagship | Medium–High | 3 |
| 6 | Trend Engine | Flagship (shared) | Flagship | Medium | 3 |
| 7 | Disaster Manager View | Disaster mgmt. | Secondary | Low | 4 |
| 8 | Disaster Safety Guidance + Emergency Mode | Disaster mgmt. | Secondary–Flagship* | Medium | 4 |
| 9 | Trip Planner (route-aware stop planner) | Secondary | Secondary | Medium | 3 |
| 10 | Historical Analytics Dashboard | Secondary | Secondary | Low | 5 |
| 11 | Personalized Daily Digest | Secondary | Secondary | Low | 4 |
| 12 | PWA + Connectivity Layer | Accessibility | Core** | Medium | 4 |
| 13 | Testing, CI & Documentation | Engineering quality | Core | Low–Medium | 1, 5 |
| 14 | Wider/region-specific crop rule table | Stretch | Stretch | Medium | — |
| 15 | Fourth language | Stretch | Stretch | Low | — |
| 16 | On-device offline model | Stretch | Stretch | High, real risk | — |
| 17 | SMS query/response channel | Stretch (demo-only) | Stretch | Low (as mockup) | — |
| 18 | Real farmer/KVK validation | Stretch | Stretch | Low effort, high value | — |

*Disaster Safety Guidance is tagged Secondary–Flagship because it's genuinely on-theme for the PS's Disaster Management category and is safety-sensitive enough to deserve flagship-level care in execution, even though it's not the primary differentiation argument (that's Farmer Advisory).
**PWA is tagged Core, not Secondary, specifically because it directly serves the PS's own "rural accessibility" language — cutting it loses a literal evaluation-criteria point, not just a nice-to-have.

---

## Core Layer

### 1. Grounded Conversational Core

**What it is:** Natural-language weather Q&A in text and voice, across three Indian languages, with every answer carrying a visible source tag (`data_tier`) showing exactly which data produced it — an official IMD warning, a live Open-Meteo grid value, or a historical baseline.

**Why it's worth building:** This satisfies the PS's literal brief as a general conversational platform, and it's the foundation every other feature sits on. It's also the concrete proof of the "grounded" half of the differentiation argument (Section 2.1 of the architecture doc) — the provenance chip is the single visual element that separates this from an opaque chatbot answer.

**Feasibility:** Medium effort, low technical risk. The rule/keyword fast path handles simple queries without an LLM call at all; the LLM is only reached for genuinely ambiguous phrasing. The main real risk is prompt design quality (getting the "never bare-refuse" instruction to hold reliably across edge cases) — mitigated by the degradation ladder doing the hard work before the LLM ever sees the query.

**Honest limitation:** On a single one-off question, a generic LLM with browsing does nearly as well. This feature alone is not the pitch — see Feature 4.

---

### 2. Data Foundation & Degradation Ladder

**What it is:** The static geocoding table, Open-Meteo and IMD connectors, and the four-tier degradation ladder (exact match → nearest/regional → related-data-with-caveat → honest gap) that guarantees the system never returns a bare "insufficient data" reply.

**Why it's worth building:** This is the unglamorous piece everything else depends on, and it's the direct answer to the concern raised early in planning — that an LLM-based system would too often fail with "I don't have enough data." Open-Meteo's grid-based coverage means a true data gap is rare; the ladder handles the genuine edge cases (IMD-specific products at very fine granularity, obscure locations) gracefully instead of failing binary.

**Feasibility:** Medium effort, low technical risk, but time-sensitive — everything in Sprints 2 onward depends on this being solid, so it's scheduled first and protected from schedule slip.

---

### 3. Proactive Alerting

**What it is:** A background poller (APScheduler) checking IMD warnings against users' saved locations, surfacing an in-app banner when a match is found, with a demo-trigger endpoint so the team isn't dependent on real severe weather existing at demo time.

**Why it's worth building:** This is the concrete proof of the "proactive" row in the differentiation table — a generic chatbot is purely reactive and only responds when opened. It's also the backbone that Features 7, 8, and 11 all build on top of.

**Feasibility:** Low effort, low risk. No LLM calls involved — it's pure comparison logic, so it's unconstrained by any rate limit and cheap to build correctly.

---

## Flagship Features

### 4. Farmer Advisory Dashboard

**What it is:** A persistent crop profile (crop, field location, sowing date), an 8-crop curated rule table sourced from ICAR/GKMS advisories, a harvest/action-timing advisory, and free-text crop Q&A grounded in the rule table rather than the LLM's general training.

**Why it's worth building:** This is the actual differentiation argument, not a side addition. A generic chatbot can say "it might rain" — it cannot say "your wheat is at grain-filling stage, humidity is trending toward fungal risk, harvest before Thursday," because nobody built that persistent state and curated logic and fed it in. Existing government portals (Kisan Suvidha and similar) are form-heavy and not conversational or personalized to one field's exact stage; a generic LLM has no persistent profile and no cited source for farming advice. This is the one feature that makes "why not just use ChatGPT" a fully answerable question.

**Feasibility:** High effort — this is deliberately the sprint's majority allocation, not compressed to fit. The real risk isn't technical (crop profile storage and rule lookups are simple), it's **research time**: sourcing real ICAR/GKMS thresholds for 8 crops properly takes real hours, which is why this research starts Day 1 in parallel with Sprint 1, not squeezed into Sprint 3.

**Honest limitation:** 8 crops with general thresholds, not hyper-local soil/variety nuance a real agronomist would weigh. This is decision support, not a replacement for an extension officer — and should be pitched that way explicitly.

---

### 5. Disease Suitability Model

**What it is:** Continuous 0–1 scoring for temperature, humidity, and growth-stage suitability per crop-disease pair (bell-curve and ramp functions), replacing a rigid binary rule like `humidity > 90% → HIGH`, averaged over a rolling 24-hour window since disease risk builds from sustained conditions.

**Why it's worth building:** A binary threshold is a poor model of biology — 88% humidity can still be risky, and 92% isn't dangerous if the temperature is wrong. Worse, a single "humidity is bad" rule is actively wrong-direction for diseases like soybean charcoal rot or cotton leaf curl virus, which are favored by hot, *dry* conditions. This model is the concrete technical depth behind the Crop Risk Index gauge — the single most visually distinctive artifact in the product.

**Feasibility:** Medium-to-high effort. The math itself is simple (still arithmetic, not ML), but sourcing real optimal-temperature and humidity-threshold numbers per crop-disease pair from ICAR's Plant Protection advisories is genuine research work, and getting these numbers wrong matters more than most other sourcing tasks in this project because it shapes advice a farmer might act on directly.

**Real risk to flag to the team:** don't ship illustrative placeholder numbers as if they were sourced facts. If the real ICAR values aren't found in time for a given crop-disease pair, it's better to narrow scope to fewer, properly-sourced pairs than to present unverified numbers with false confidence.

---

### 6. Trend Engine

**What it is:** A shared component computing a multi-year baseline (moving average) and trend direction (simple linear regression) per location/variable from the preloaded historical dataset, plus an anomaly detector comparing the current season against it.

**Why it's worth building:** This is what makes historical data genuinely useful rather than decorative. The advisory logic activates specifically when the current-season anomaly and the multi-year trend agree — e.g., below-average early rainfall *and* a 10-year trend toward later monsoon onset together justify a real recommendation, not either signal alone. It also demonstrates good software design: one well-built component serving two features (the Risk Index's baseline term and a standalone Trend-Informed Advisory query) rather than separate implementations.

**Feasibility:** Medium effort, low technical risk — `numpy.polyfit` and a moving average are basic statistics, not a modeling project. The main cost is making sure the preloaded historical dataset (Sprint 1) has enough years of coverage per location to make a trend meaningful, not just a baseline.

---

## Disaster Management

### 7. Disaster Manager View

**What it is:** A severity-sorted, aggregated view of currently active alerts across regions, layered with Trend Engine context ("this district has seen roughly N comparable events in the past decade"), built for the government/stakeholder persona the PS explicitly names.

**Why it's worth building:** The PS names disaster managers and government agencies as served users; this is the concrete UI proof that persona is actually built for, not just claimed in a pitch slide. Today, this kind of view requires manually checking multiple regional bulletins — this consolidates them, transparently sourced.

**Feasibility:** Low effort — it reuses the alerting backend and the Trend Engine entirely; it's a new front-end lens and a sort, not new backend logic.

**Honest limitation:** This is the team's least user-validated persona. Nobody on the team has real access to how an actual disaster manager works day to day, so this is a reasonable, modest guess at a useful view — deliberately not built as a full resource-allocation system, since overbuilding here risks looking like guesswork dressed up as expertise.

---

### 8. Disaster Safety Guidance + Active Emergency Mode

**What it is:** A curated Hazard Safety Guide (flood, cyclone, heatwave, thunderstorm/lightning, cold wave) sourced from NDMA's published Do's and Don'ts, surfaced as a Safety Guidance card alongside any matching active alert. At the highest severity tier, the UI shifts to Active Emergency Mode: immediate hazard-specific action steps plus a verified helpline block (NDMA National Helpline **1078**, India's general emergency number **112**), with an explicit note that district control-room numbers vary by location and must be looked up rather than hardcoded.

**Why it's worth building:** This is the most direct expression of the PS's Disaster Management theme, applied to the individual persona rather than only the government one. It's structurally the same kind of build as the crop rule table — curated content, not LLM improvisation — applied to a domain where getting it wrong matters more.

**Feasibility:** Medium effort. The technical build (a severity check + a curated JSON lookup) is straightforward; the real cost is sourcing and verifying the NDMA content and helpline numbers correctly, which was done for this brief specifically rather than assumed.

**This is the one feature in the entire product where the team should hold itself to the strictest standard of all**: never let the LLM freelance beyond the curated content, always cite NDMA as the source, and explicitly state the real-time-shelter-data gap as a known limitation rather than fabricating an answer. In the pitch, state plainly that this is prototype-stage decision support, not a claim to replace official emergency services — that honesty is a stronger position than implying more reliability than a 13-day build can actually deliver.

---

## Secondary Features

### 9. Trip Planner

**What it is:** A **route-aware trip planner**. The user enters an origin and destination; the system geocodes both, routes between them, and lays out the journey as a sequence of stops/checkpoints — each **rated** (good / use caution / not recommended) from the forecast at its ETA, and annotated with **nearby facilities** (restaurants, fuel, hotels, hospitals, parking). A horizontal timeline shows the whole route at a glance. *(The Travel tab UI is already built and merged; this is the shipped scope, replacing the earlier "day-by-day itinerary note" framing.)*

**Why it's worth building:** It turns "weather for a trip" into an *actionable route plan* — where to stop, which stretch has rain, what's around each stop — which neither a generic weather app nor a chatbot does. A genuinely different interaction shape and a strong visual demo.

**Feasibility:** Medium. The frontend (Travel tab) exists. The backend combines **Geoapify** (geocoding + routing + Places for facilities; free tier ~3k/day, **needs an API key**) with **Open-Meteo** (weather at each checkpoint's ETA). This is the project's first *keyed* external API — it adds a `GEOAPIFY_API_KEY` secret and a real free-tier rate limit to design around.

**Honest limitation:** Facility counts and route detail are only as good as Geoapify's free tier, and its rate limit constrains how many routes/checkpoints can be evaluated per day. An interactive route map is a future stretch — the current UI is a checkpoint timeline, not a rendered map.

---

### 10. Historical Analytics Dashboard

**What it is:** Filterable charts and trend lines over the preloaded historical dataset — rainfall, temperature, humidity, by location and date range — as a secondary visual tab alongside the conversational interface.

**Why it's worth building:** Makes the PS's "climate trend analysis" feature genuinely explorable, and most consumer weather apps don't expose historical trend exploration at all. It also gives visual, browsable value to a room of judges beyond one conversational answer at a time.

**Feasibility:** Low effort — the Trend Engine (Feature 6) already computes the underlying baselines and trends; this is a charting layer on top of data already produced for other features.

**Honest limitation:** Purely exploratory — it doesn't drive a decision the way the Risk Index does. Easiest feature to simplify if time gets tight.

---

### 11. Personalized Daily Digest

**What it is:** A settings screen (preferred time, language, content toggles for forecast/alerts/crop advisory/historical comparison) and a per-user scheduled job that assembles and delivers a personalized daily summary.

**Why it's worth building:** It's a natural extension of the proactive-alerting differentiation argument — the system doesn't just wait to be asked, it can also reach out on a schedule the user defines. It's also a strong demonstration of architectural reuse: the digest is assembled by calling the *existing* grounding assembler, not new core logic.

**Feasibility:** Low effort — almost entirely orchestration over components already built (the grounding assembler, the alerting layer's notification path, and — if offline — the same Background Sync queue built for the PWA layer). Genuinely cheap for the credibility signal it adds.

---

## Accessibility & Engineering Quality

### 12. PWA + Connectivity Layer

**What it is:** An installable app shell (cache-first service worker), IndexedDB local-first storage for a user's profile and recent data, a template-based offline responder answering common structured queries with zero network calls, and Background Sync queuing anything that genuinely needs the LLM.

**Why it's worth building:** This directly serves the PS's own "voice-enabled interaction for rural accessibility" language, and it's honest about what's actually achievable — not claiming true internet independence (a live LLM call always needs a network round trip eventually), but real graceful degradation across the connectivity spectrum that actually exists in rural India (mostly intermittent 2G/3G, not a clean online/offline switch). Almost no competing team is likely to build this layer as deliberately.

**Feasibility:** Medium effort, low-to-medium technical risk — built entirely on standard, free, well-documented browser APIs (Service Worker, IndexedDB, Background Sync), no exotic infrastructure. The main design work is deciding the fixed, small set of query shapes the offline responder can handle without the LLM — that list needs to be locked early since it determines what Sprint 4 actually has to build.

---

### 13. Testing, CI & Documentation

**What it is:** A `pytest` suite covering the degradation ladder, risk-index calculator, Disease Suitability Model, Trend Engine, and connectors (mocked); GitHub Actions running that suite on every push; FastAPI's auto-generated OpenAPI/Swagger documentation.

**Why it's worth building:** This is a genuine engineering-maturity signal that costs nothing and that most hackathon-scale submissions skip entirely — a 12–13 day timeline is exactly what makes it feasible where a 36-hour one wouldn't afford it. It's also directly protective: catching a regression in the Risk Index formula via a failing test beats discovering it live during a demo.

**Feasibility:** Low-to-medium effort, low risk, and worth setting up on Day 3 so every subsequent feature gets tested as it's built rather than retrofitted at the end.

---

## Stretch Tier — worth naming, not worth promising

### 14. Wider or region-specific crop rule table

Extending beyond 8 crops, or adding state-specific variants of the same crop's advisory (the same crop's real thresholds can differ meaningfully by region). **Value:** directly deepens the flagship differentiator rather than adding a new surface — the single highest-value stretch item if time allows.

### 15. Fourth language

Real accessibility value, but it's breadth on the baseline conversational layer — it doesn't change whether judges see this as more than "just a chatbot." Add only after everything else is solid.

### 16. On-device offline model (true zero-network answers)

A small in-browser model (e.g. via WebLLM) could, in principle, answer basic queries with genuinely zero network, closing the last gap in the connectivity story (Section 3.6, Layer 3). **This carries real research risk in a 12-day window** — flag it as future work in the pitch rather than committing engineering time to it now. A half-working on-device model is worse for the pitch than a clearly-stated roadmap item.

### 17. SMS query/response channel

The only channel that reaches a user with no smartphone or data plan at all — genuinely the correct answer to "how do we reach someone with zero internet access," which is a stronger and more honest claim than stretching the PWA to cover a case it structurally can't. **But real SMS sending isn't free at any meaningful volume**, which conflicts with the team's zero-cost constraint. Keep this as a demo-only mockup of the flow. Explicitly stating "we designed for this but chose not to build live infrastructure, to respect a genuine cost constraint" is a stronger signal than building a fragile, unfunded version.

### 18. Real farmer or KVK/extension-worker validation

Not a build task at all — a conversation. **Value is disproportionate to effort**: almost no competing team will have this, and even one informal validation of the crop rule table turns "we assumed these thresholds are right" into "we verified them with someone who'd actually know," which is a materially stronger claim in front of judges.

---

*Companion documents: `SIH26068_WeatherGPT_Architecture_and_Build_Plan.md` (system design and day-by-day build plan), `WeatherGPT_Mockup.html` (interactive visual walkthrough). This brief reflects the project's current planning state and should be revisited if scope changes.*
