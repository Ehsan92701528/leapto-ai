#!/bin/bash
# Start Leapto AI local dev: API (8080) + website (5500)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_DIR="$ROOT/api/pathmate-matcher"
WEB_DIR="$ROOT/horizon"
CACHE_SCRIPT="$ROOT/data/university-portfolio/scripts/build_global_portfolio_cache.py"

echo "== Leapto AI local dev =="
echo ""

# Ensure 320-programme cache exists
if [[ -f "$CACHE_SCRIPT" ]]; then
  python3 "$CACHE_SCRIPT"
  echo ""
fi

if lsof -i :8080 >/dev/null 2>&1; then
  echo "Port 8080 in use — API may already be running."
  echo "  Health: http://127.0.0.1:8080/health/portfolio (expect programmes: 320)"
  echo "  To restart: kill \$(lsof -t -i:8080) && rerun this script"
  echo ""
else
  echo "Starting API on http://127.0.0.1:8080 ..."
  (cd "$API_DIR" && python3 -m pip install -q -r requirements.txt && python3 -m uvicorn main:app --port 8080) &
  sleep 2
  curl -s http://127.0.0.1:8080/health/portfolio | python3 -m json.tool || true
  echo ""
fi

if lsof -i :5500 >/dev/null 2>&1; then
  echo "Port 5500 in use — website may already be running."
else
  echo "Starting website on http://localhost:5500/fa/index.html ..."
  (cd "$WEB_DIR" && python3 -m http.server 5500) &
  sleep 1
fi

echo ""
echo "Open: http://localhost:5500/fa/index.html"
echo "API docs: http://127.0.0.1:8080/docs"
echo "Eval: cd $API_DIR && python3 eval/run_eval.py --suite all"
echo ""
echo "Press Ctrl+C to stop (background jobs may keep running — use kill above if needed)."

wait
