#!/bin/bash
# Run from anywhere: ./api/pathmate-matcher/smoke-test.sh
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
python3 scripts/smoke_test.py
