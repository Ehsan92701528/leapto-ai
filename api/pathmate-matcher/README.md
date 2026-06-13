# Leapto Path Mate Matcher API

Student intake form + rule-based matching over `data/mentors.fa.json`.

## Setup

```bash
cd api/pathmate-matcher
pip install -r requirements.txt
```

Ensure mentor data exists:

```bash
python3 ../../tools/mentor-export/extract_mentors.py --lang fa
```

## Run API locally

```bash
cd api/pathmate-matcher
uvicorn main:app --reload --port 8080
```

- Health: http://localhost:8080/health
- Form options: http://localhost:8080/options
- JSON Schema: http://localhost:8080/schema/student-intake
- Demo form: http://localhost:8080/demo
- Match: `POST http://localhost:8080/match`

## Website widget (Step 4)

Files embedded on the FA homepage (`horizon/fa/index.html`):

| File | Role |
|------|------|
| `horizon/assets/js/pathmate-finder.config.js` | API URL (auto-detects localhost vs production) |
| `horizon/assets/js/pathmate-finder.js` | Modal form + results |
| `horizon/assets/css/pathmate-finder.css` | Widget styles |

### Local test (website + API)

Terminal 1 — API:

```bash
cd api/pathmate-matcher
uvicorn main:app --reload --port 8080
```

Terminal 2 — static site (**must serve from `horizon/`, not `horizon/fa/`**):

```bash
cd /Users/ehsanhosseini/leapto-github/horizon
chmod +x serve-local.sh
./serve-local.sh 5500
```

Open **http://localhost:5500/fa/index.html** (not `http://localhost:5500/index.html`).

Why: CSS and images live in `horizon/assets/`. Pages under `fa/` link to `../assets/...`. If you run the server inside `fa/`, those files 404 and the page looks unstyled.

| URL | What it is |
|-----|------------|
| http://localhost:8080/health | API only (JSON) — use `curl`, not the browser for layout |
| http://localhost:5500/fa/index.html | Website with CSS |

### Production

1. Deploy the API (e.g. `https://api.leapto.co.uk`)
2. Set `apiBaseUrl` in `pathmate-finder.config.js` if auto-detect is not enough
3. Deploy updated `horizon/` files to leapto.co.uk

Trigger class anywhere: `trigger-pathmate-finder`

## Smoke test

From repo root:

```bash
python3 api/pathmate-matcher/scripts/smoke_test.py
```

Or:

```bash
cd api/pathmate-matcher
python3 scripts/smoke_test.py
# or
./smoke-test.sh
```

**Note:** the script lives in `api/pathmate-matcher/scripts/` — not under `schemas/`.

## Student intake fields

| Field | Required | Description |
|-------|----------|-------------|
| `destination_countries` | Yes | 1–5 countries (EN or FA names) |
| `field_of_study` | Yes | Leapto homepage field category |
| `target_degree` | Yes | `Bachelor`, `Master`, `PhD` |
| `current_status` | Yes | `student`, `graduate`, `working` |
| `origin_country` | No | Where they study now |
| `languages` | No | Spoken/test languages |
| `timeline` | No | When they plan to apply/start |
| `additional_notes` | No | Exams (IELTS, GRE, GMAT, CFA…), GPA, budget, etc. |

## Example request

```json
{
  "intake": {
    "destination_countries": ["Canada", "United Kingdom"],
    "field_of_study": "Computer Engineering & Computer Science",
    "target_degree": "Master",
    "current_status": "student",
    "origin_country": "Iran",
    "languages": ["Persian", "English"],
    "timeline": "September 2026",
    "additional_notes": "GPA 17/20, IELTS 7.0, interested in Data Science MSc."
  },
  "language": "fa",
  "limit": 5
}
```

## Leapto AI (v0.3)

Product docs: `docs/ai-product/README.md`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health/ai` | GET | Extractor + RAG status |
| `/ai/extract` | POST | Free text → structured intake + intent |
| `/ai/rag/programmes` | POST | Grounded programme Q&A with citations |

### Extract example

```bash
curl -s -X POST http://localhost:8080/ai/extract \
  -H 'Content-Type: application/json' \
  -d '{"text":"می‌خوام ارشد کامپیوتر برم آلمان و انگلیس","use_llm":false}' | python3 -m json.tool
```

### RAG example

```bash
curl -s -X POST http://localhost:8080/ai/rag/programmes \
  -H 'Content-Type: application/json' \
  -d '{"question":"UK MSc computer science IELTS 6.5 under £40000","language":"en"}' | python3 -m json.tool
```

### Evaluation (release gates)

```bash
cd api/pathmate-matcher
python3 eval/run_eval.py --suite all
```

Optional LLM: copy `.env.example` → `.env` and set `LEAPTO_AI_API_KEY`, then pass `"use_llm": true`.

## Next steps

- Wire widget to `POST /ai/extract`
- Embed widget on `leapto.co.uk`
- CI eval gate on pull requests
- Analytics events on intake funnel
