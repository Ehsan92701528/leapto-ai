# Leapto AI Product Program

Governed AI for conversational intake, mentor matching, and grounded programme discovery.

## Status

| Phase | Focus | Status |
|-------|--------|--------|
| **0** | Product pack (use cases, business case, roadmap, RAI, eval plan) | In progress |
| **1** | Rule-based AI extraction API + eval harness | In progress |
| **2** | Optional LLM extraction (schema-validated, fallback) | Scaffolded |
| **3** | Portfolio RAG (grounded retrieval + citations) | In progress |
| **4** | Widget integration + analytics events | Planned |
| **5** | CI eval gates + deployment | Planned |

## Documents

| Doc | Purpose |
|-----|---------|
| [00-program-charter.md](./00-program-charter.md) | Engagement framing (client, problem, stakeholders) |
| [01-use-case-portfolio.md](./01-use-case-portfolio.md) | Where AI yes / no / hybrid |
| [02-business-case.md](./02-business-case.md) | Value hypothesis, costs, risks |
| [03-roadmap-and-okrs.md](./03-roadmap-and-okrs.md) | Multi-quarter roadmap + OKRs |
| [04-responsible-ai.md](./04-responsible-ai.md) | Controls, NIST RMF mapping |
| [05-evaluation-plan.md](./05-evaluation-plan.md) | Intake + RAG eval methodology |

## Run locally (one command)

```bash
chmod +x scripts/dev-leapto-ai.sh
./scripts/dev-leapto-ai.sh
```

Then open http://localhost:5500/fa/index.html (**Cmd+Shift+R** — cache v=14).

Manual (two terminals) — see `api/pathmate-matcher/README.md`.

## Analytics (dev)

Widget logs events to browser console (`[LeaptoAI]`) and `localStorage` key `leapto_ai_events`.

In DevTools console:

```javascript
JSON.parse(localStorage.getItem("leapto_ai_events") || "[]")
```

Events: `widget_opened`, `intake_started`, `ai_extract_done`, `step_completed`, `match_result`, `portfolio_tab_opened`, `rag_result`.

## API (local)

```bash
cd api/pathmate-matcher
pip install -r requirements.txt
uvicorn main:app --reload --port 8080
```

| Endpoint | Role |
|----------|------|
| `POST /ai/extract` | Free text → structured intake + intent |
| `POST /ai/rag/programmes` | Grounded programme Q&A with citations |
| `GET /health/ai` | AI module status |
| `POST /match` | Mentor ranking (existing) |
| `POST /portfolio/match` | Reach/match/safety (existing) |

## Evaluation

```bash
cd api/pathmate-matcher
python3 eval/run_eval.py
python3 eval/run_eval.py --suite rag
python3 eval/run_eval.py --suite all
```

Release gate (target): intent accuracy ≥ 90%, country extraction F1 ≥ 85%, RAG citation accuracy ≥ 95% on gold sets.

## Optional LLM

Copy `.env.example` to `.env` and set `LEAPTO_AI_API_KEY`. Without a key, all flows use deterministic rules + retrieval only.
