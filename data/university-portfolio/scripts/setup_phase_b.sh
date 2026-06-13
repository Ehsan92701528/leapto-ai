#!/usr/bin/env bash
# Phase B one-shot setup: PostgreSQL + 50 UK MSc seed rows + JSON cache for API fallback
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Generating seed CSVs (50 UK MSc programmes)"
python3 scripts/generate_uk_msc_seed.py

echo "==> Building JSON cache (works without Postgres)"
python3 scripts/export_seed_json.py

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker not found — skipped PostgreSQL load. JSON cache is ready for API."
  exit 0
fi

echo "==> Starting PostgreSQL (docker compose)"
docker compose up -d

echo "==> Waiting for database..."
for i in {1..30}; do
  if docker compose exec -T postgres pg_isready -U leapto -d leapto_portfolio >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

export DATABASE_URL="${DATABASE_URL:-postgresql://leapto:leapto@127.0.0.1:5433/leapto_portfolio}"

echo "==> Applying schema and loading seed data"
python3 scripts/import_programmes.py --apply-schema --load --data-dir seed

echo "==> Exporting JSON cache for API fallback"
python3 scripts/import_programmes.py --export-json cache/portfolio_gb_msc.json --data-dir seed

echo ""
echo "Phase B ready."
echo "  PostgreSQL: $DATABASE_URL"
echo "  JSON cache: $ROOT/cache/portfolio_gb_msc.json"
echo ""
echo "Test API:"
echo "  cd ../../api/pathmate-matcher && pip3 install -r requirements.txt"
echo "  python3 -m uvicorn main:app --reload --port 8080"
echo "  curl -s http://127.0.0.1:8080/health/portfolio | python3 -m json.tool"
