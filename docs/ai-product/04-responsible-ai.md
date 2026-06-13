# Responsible AI Assessment — Leapto

**Version:** 0.1 · **Risk tier:** Limited (user-facing guidance, not high-risk autonomous decisions)

## Scope

Conversational intake, mentor recommendations, and programme Q&A for international education planning.

## Principles applied

| Principle | Implementation |
|-----------|----------------|
| **Fairness** | Matching on study/work fit, not nationality/gender; monitor for country bias in rankings |
| **Transparency** | Show match reasons; RAG answers include programme IDs and URLs |
| **Accountability** | Human mentor booking always available; ops can review logs |
| **Human oversight** | High-risk topics (visa/legal) out of LLM scope; escalation to humans |
| **Proportionate risk** | Rules-first; LLM only with schema validation + eval gates |

## NIST AI RMF mapping (lightweight)

| Function | Leapto control |
|----------|----------------|
| **Govern** | This document; product owner owns backlog; eval before promote |
| **Map** | Use case portfolio (AI yes/no); data lineage for mentors + programmes |
| **Measure** | Gold-set eval (`run_eval.py`); funnel analytics; human relevance sampling |
| **Manage** | Fallback to rules; rollback prompt/model version; incident runbook |

## Risk register

| ID | Risk | Severity | Mitigation | Owner |
|----|------|----------|------------|-------|
| R1 | Hallucinated programme requirements | High | DB-only facts in RAG; citation required | Product + Eng |
| R2 | Harmful emigration advice | High | Out of scope; static content + mentors | Product |
| R3 | PII in model logs | Medium | Redact in logs; no third-party training without consent | Eng |
| R4 | Biased mentor ranking | Medium | Explicit scoring rules; periodic bias review | Product |
| R5 | Stale tuition/deadlines | Medium | `last_verified_at`; refresh alerts | Data |
| R6 | Over-reliance on AI | Low | “Book a human” CTA on every results screen | UX |

## Data & privacy

- Collect minimum fields needed for matching
- `additional_notes` may contain sensitive text — treat as confidential
- Retention: define 90-day log retention for beta (configurable)
- Do not send live chats to external LLM without user notice (when LLM enabled)

## Model / prompt governance

| Asset | Versioning | Promotion gate |
|-------|------------|----------------|
| Rules extractor | Git tag / semver in API | Unit + gold eval pass |
| LLM prompt (optional) | `prompts/intake_extract_v1.txt` | Eval ≥ threshold + manual review |
| RAG retrieval | Git + data hash | RAG gold set pass |

## Incident response (draft)

1. **Detect:** User report, eval regression, or monitoring alert
2. **Contain:** Disable LLM flag; rules-only mode
3. **Assess:** Scope, severity, affected users
4. **Fix:** Prompt/data/code change + re-eval
5. **Communicate:** Internal postmortem; user comms if needed

## EU AI Act note (informational)

Education chatbot / recommendation likely **limited risk** — transparency (user knows it's AI) and human fallback recommended. Not legal advice; confirm with counsel for production at scale.
