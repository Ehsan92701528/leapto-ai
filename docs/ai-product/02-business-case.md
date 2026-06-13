# Business Case — Leapto AI Platform

## Problem statement

Leapto has strong mentor supply and brand trust, but discovery is **filter-heavy and fragile**:

- Long or repetitive intake → drop-off (observed in conversational widget testing)
- Users mix study, work, and emigration intents — static forms miss nuance
- Programme research is manual; no grounded “what can I apply to?” tool on-site

## Opportunity

A **governed AI layer** on top of existing assets:

- `data/mentors.fa.json` — mentor corpus
- `data/university-portfolio/` — programme DB
- `StudentIntake` schema — shared contract
- FastAPI services — `/match`, `/portfolio/match`, `/ai/*`

## Value hypothesis

| Initiative | Expected outcome | Leading indicator |
|------------|------------------|-------------------|
| Conversational intake | +20% completion vs form | Step funnel |
| Better mentor match | +15% session booking from widget | Click-to-contact |
| Portfolio + RAG | New revenue stream (Unipass/planning) | Tab engagement |
| Ops efficiency | −30% “which programme?” support tickets | Ticket tags |

*Targets are hypotheses to validate in beta — not claimed results yet.*

## Investment (order of magnitude)

| Item | Year 1 estimate | Notes |
|------|-----------------|-------|
| Engineering (PO + 1 FTE equiv.) | Internal / founder time | Already underway |
| LLM API (optional) | £50–300/mo at beta volume | Gated by eval |
| Postgres + hosting | £30–100/mo | Docker / small cloud |
| Eval & QA | Ongoing | Gold sets + human sample |

## Costs of **not** doing it

- Competitors with smoother AI intake capture intent-first users
- Mentor inventory under-utilised (poor matching UX)
- Consulting-style AI PO skills gap for product owner (portfolio evidence)

## Risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Hallucinated programme advice | Trust loss | RAG with citations; DB-only facts |
| Bad emigration advice | Harm | Out of scope; human escalation |
| LLM cost spike | Budget | Rules-first; cache; rate limits |
| Data staleness | Wrong fees/deadlines | `last_verified_at`, refresh pipeline |
| Privacy | Regulatory | Minimise PII; no training on live chats without consent |

## Recommended phasing

1. **Q2 2026** — Extraction API + eval harness + RAG v1 (rules)
2. **Q3 2026** — Widget integration + analytics + optional LLM extraction
3. **Q4 2026** — Hybrid mentor retrieval + portfolio tab + CI eval gates
4. **2027** — Scale programme data (DE, CA, AU); agent-assisted ops tools

## Decision requested

Proceed with **Phase 1–2** as the minimum viable AI product: intake extraction, RAG, evaluation, and Responsible AI controls — before any autonomous agent scope.
