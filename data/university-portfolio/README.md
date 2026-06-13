# University portfolio data

## Global cache — 320 programmes (GB, DE, CA, AU)

```bash
python3 scripts/build_global_portfolio_cache.py
```

Writes `cache/portfolio_global_msc.json` (80 programmes × 4 countries). The API prefers this file over the legacy 50-row UK cache.

To reach **many more** courses: import verified CSVs via `import_programmes.py`, or extend the builder script with US, NL, ES, etc.

---

# Phase B — University portfolio (UK MSc MVP)

## What's included

- **PostgreSQL schema** — `schema.sql`
- **50 UK MSc programmes** — 5 fields × 10 programmes (`seed/` CSVs)
- **Import tooling** — load CSVs into Postgres + export JSON cache
- **API** — `POST /portfolio/match` → reach / match / safety buckets

## Quick start

```bash
cd data/university-portfolio
chmod +x scripts/setup_phase_b.sh
./scripts/setup_phase_b.sh
```

This will:

1. Generate `seed/*.csv` (50 programmes, 20 universities)
2. Start Postgres on **port 5433** (`docker compose`)
3. Apply schema + load data
4. Export `cache/portfolio_gb_msc.json` (API fallback without Docker)

## API

```bash
cd api/pathmate-matcher
pip3 install -r requirements.txt
python3 -m uvicorn main:app --reload --host 127.0.0.1 --port 8080
```

Health:

```bash
curl http://127.0.0.1:8080/health/portfolio
```

Portfolio match:

```bash
curl -s -X POST http://127.0.0.1:8080/portfolio/match \
  -H 'Content-Type: application/json' \
  -d '{
    "intake": {
      "destination_countries": ["United Kingdom"],
      "field_of_study": "Computer Engineering & Computer Science",
      "target_degree": "Master",
      "current_status": "student",
      "gpa": 17,
      "gpa_scale": "20",
      "ielts_overall": 7.0,
      "budget_max_yearly": 40000
    },
    "language": "fa",
    "limit_per_bucket": 5
  }' | python3 -m json.tool
```

Smoke test (no server):

```bash
python3 api/pathmate-matcher/scripts/portfolio_smoke_test.py
```

## Environment

| Variable | Default |
|----------|---------|
| `DATABASE_URL` | `postgresql://leapto:leapto@127.0.0.1:5433/leapto_portfolio` |

Copy `.env.example` if you need a custom connection string.

## Manual commands

```bash
# Regenerate seed only
python3 scripts/generate_uk_msc_seed.py

# Validate CSVs
python3 scripts/import_programmes.py --dry-run --data-dir seed

# Reload DB
python3 scripts/import_programmes.py --apply-schema --load --data-dir seed

# Export JSON cache
python3 scripts/import_programmes.py --export-json cache/portfolio_gb_msc.json
```

## Matching rules (v1)

Hard filters from DB:

- destination country
- degree level (Master)
- field ↔ Leapto category
- IELTS ≥ minimum (if provided)
- GPA ≥ minimum /20 (if provided)
- tuition ≤ budget (if provided)

Buckets:

- **reach** — top-ranked uni, profile near minimum requirements
- **match** — good fit
- **safety** — comfortable margin on requirements

## Next (Phase C / widget)

- Tab «دانشگاه و دوره» in pathmate-finder.js
- Link programmes → path-mates at same university
- Back-navigation in chat (still pending)
