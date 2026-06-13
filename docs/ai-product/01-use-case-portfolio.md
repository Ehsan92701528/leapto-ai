# AI Use Case Portfolio — Leapto

## Summary

| # | Use case | AI type | Verdict | Priority |
|---|----------|---------|---------|----------|
| 1 | Conversational intake | NLP / GenAI (governed) | **Yes** | P0 |
| 2 | Mentor matching | Rules + hybrid retrieval | **Yes** | P0 |
| 3 | University portfolio (reach/match/safety) | Rules + structured DB | **Yes (mostly rules)** | P0 |
| 4 | Programme Q&A | RAG (retrieval + optional LLM phrasing) | **Yes** | P1 |
| 5 | Visa / legal guidance | GenAI | **No** | — |
| 6 | Autonomous agent (book & pay) | Agentic | **Not yet** | P3 |

---

## 1. Conversational intake — **Yes (governed GenAI)**

**Problem:** Users describe goals in free Persian/English; rigid forms fail.

**AI approach:** Extract structured `StudentIntake` + `path_intent`. LLM optional; Pydantic validation mandatory; fallback to rules.

**Value hypothesis:** Higher completion and richer profiles → better matches → more booked sessions.

**Success metrics:** Completion rate, extraction accuracy on gold set, fallback rate.

**Guardrails:** Reject inappropriate/irrelevant; no legal advice; log extractor version.

**Why not full agent:** Probabilistic extraction needs validation layer; agent autonomy not required.

---

## 2. Mentor matching — **Yes (hybrid)**

**Problem:** 400+ mentors; filters alone miss nuance.

**AI approach:** Phase 1 rule-based scoring (shipped). Phase 2 embedding similarity over bios + hard filters.

**Value hypothesis:** Top-5 relevance improves conversion to session booking.

**Success metrics:** nDCG@5, human relevance score, click-through to profile.

**Guardrails:** Explain match reasons; no discriminatory ranking by protected attributes.

---

## 3. University portfolio — **Yes (rules + data product)**

**Problem:** Students need realistic apply lists (reach/match/safety).

**AI approach:** Hard filters from PostgreSQL/JSON cache — IELTS, GPA, fees, field. **Not** LLM-invented requirements.

**Value hypothesis:** Saves research time; increases trust in Leapto as planning tool.

**Success metrics:** Portfolio acceptance rate (user keeps ≥1 programme per bucket).

---

## 4. Programme Q&A (RAG) — **Yes**

**Problem:** “Which UK MSc CS accepts IELTS 6.5 under £30k?”

**AI approach:** Retrieve from programme corpus → answer with programme IDs + URLs. LLM may phrase; citations required.

**Value hypothesis:** Reduces support load; drives portfolio tab engagement.

**Success metrics:** Citation accuracy, answer relevance (human), abstain rate when no rows match.

**Guardrails:** No row → “I don’t know from our database”; show `source_url` / `last_verified_at` when available.

---

## 5. Visa / legal guidance — **No**

**Problem:** Users ask how to emigrate without studying.

**Why no GenAI:** High harm, regulatory sensitivity, stale policy risk.

**Product response:** Acknowledge intent → path chips (study/work/both) → human mentor escalation → static curated content only.

---

## 6. Autonomous booking agent — **Not yet**

**Dependencies:** Identity, payments (VBO), audit, consent — beyond current scope.

**Future:** Multi-step agent with human approval on payment actions.
