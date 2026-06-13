# University & Course Portfolio Database — Plan

Goal: global **countries → universities → programmes** data so Leapto can recommend an apply portfolio (reach / match / safety) per candidate.

## Phases

| Phase | When | Deliverable |
|-------|------|-------------|
| **A** Schema | Week 1–2 | PostgreSQL tables + CSV import templates |
| **B** MVP data | Week 3–6 | UK Master’s, ~200–400 programmes, 5 fields |
| **C** Matching API | Week 7–10 | `POST /portfolio/match` using extended StudentIntake |
| **D** Expand | Month 3+ | Canada, Germany, Australia… |
| **E** Ops | Ongoing | Deadline/fee refresh, source audit |

## Core tables

- `countries`, `universities`, `programmes`, `programme_requirements`, `programme_costs`, `intakes`
- Every row: `source_url`, `last_verified_at`

## MVP corridor

**India / Iran → UK MSc** in CS, Business, Engineering, Health, Economics.

## Data rules

- Hard filters from DB (IELTS, GPA, fees) — not LLM guesses
- LLM later: explanations only, grounded in DB rows

## Reuse from Project 1

- Same `StudentIntake` schema (+ GPA, exams, budget fields)
- Same Gemini-style widget (second tab: «دانشگاه و دوره»)
- Path-mate upsell: “Talk to someone at this university”

## Phase A status (done)

- [x] `schema.sql` — PostgreSQL tables
- [x] CSV templates under `templates/`
- [x] `scripts/import_programmes.py` — validate + load + export JSON
- [x] Extended `StudentIntake` (gpa, ielts, budget, exams…)
- [x] `schemas/intake_extract.py` — parse scores from free text
- [x] Widget story validation (irrelevant / inappropriate / budget-aware)

## Phase B status (done)

- [x] `docker-compose.yml` — Postgres on port 5433
- [x] `scripts/generate_uk_msc_seed.py` — 50 UK MSc programmes (5 fields)
- [x] `scripts/setup_phase_b.sh` — one-shot setup
- [x] `POST /portfolio/match` — reach / match / safety
- [x] JSON cache fallback — `cache/portfolio_gb_msc.json`

## Next action (Phase C)

1. Widget tab «دانشگاه و دوره» calling `/portfolio/match`
2. Path-mate upsell per programme
3. Back-navigation in chat
4. Scale seed data toward 200–400 programmes with verified source URLs

See full detail in conversation / expand this file as we build.
