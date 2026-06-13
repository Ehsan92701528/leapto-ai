# Roadmap & OKRs — Leapto AI

## OKRs — Q2 2026

### O1: Ship governed conversational intake

| Key result | Target |
|------------|--------|
| KR1: Intake extraction API live (`POST /ai/extract`) | Done |
| KR2: Gold-set intent accuracy | ≥ 90% |
| KR3: Gold-set country extraction F1 | ≥ 85% |
| KR4: Widget calls API with rules fallback | Done (v14) |

### O2: Grounded programme discovery

| Key result | Target |
|------------|--------|
| KR1: RAG endpoint with citations (`POST /ai/rag/programmes`) | Done |
| KR2: RAG citation accuracy on gold set | ≥ 95% |
| KR3: Portfolio tab in widget | Done (v12+) |
| KR4: 320+ programme global cache (GB, DE, CA, AU) | Done |

### O3: Operate AI responsibly

| Key result | Target |
|------------|--------|
| KR1: RAI assessment published | Done |
| KR2: Eval run in CI on every API change | Planned |
| KR3: Audit log fields defined (extractor version, match IDs) | In progress |

---

## Roadmap (multi-quarter)

```text
2026 Q2          Q3              Q4              2027 Q1
─────────────────────────────────────────────────────────
[Extraction API] [Widget+LLM opt] [Hybrid match]  [Multi-country DB]
[RAG v1 rules]   [Analytics]      [CI eval gates] [Agent ops tools]
[Eval harness]   [Portfolio tab]  [Embeddings]    [CoE templates]
[RAI doc]        [A/B intake]     [Scale 200+ prog]
```

### Epic breakdown (Q2)

| Epic | Features | Status |
|------|----------|--------|
| **E1: AI extraction service** | Rules extractor, optional LLM, `/ai/extract`, health | In progress |
| **E2: Evaluation** | Gold sets, `run_eval.py`, release thresholds | In progress |
| **E3: Portfolio RAG** | Retrieval, citations, `/ai/rag/programmes` | In progress |
| **E4: Product documentation** | Charter, use cases, business case, RAI | In progress |
| **E5: Widget integration** | Call `/ai/extract` from pathmate-finder.js | Planned |

### Dependencies

| AI feature | Data dependency | Must be ready first |
|------------|-----------------|---------------------|
| Mentor match | `mentors.fa.json` refresh | Export pipeline |
| Portfolio match | Programme DB or JSON cache | Phase B seed |
| RAG Q&A | Same programme corpus | Portfolio match |
| LLM extraction | None (optional) | Eval harness |
| Hybrid mentor rank | Embeddings index | Baseline rule match |

---

## Backlog (next 10 stories)

1. **Widget:** Call `POST /ai/extract` on first message; merge with client parseStory as fallback.
2. **Widget:** Emit analytics events (`intake_started`, `step_completed`, `match_result`).
3. **API:** Log `extractor_version` + `path_intent` on each extract request.
4. **Eval:** Expand gold set to 100 cases (Persian + English).
5. **RAG:** Add LLM phrasing layer behind feature flag with citation check.
6. **Widget:** Portfolio tab calling `/portfolio/match` + RAG follow-up.
7. **CI:** GitHub Action running `run_eval.py` on PR.
8. **Data:** Refresh pipeline alert when `last_verified_at` > 90 days.
9. **Match:** Embedding index prototype for mentor bios.
10. **Docs:** 8-slide case study deck for interviews.
