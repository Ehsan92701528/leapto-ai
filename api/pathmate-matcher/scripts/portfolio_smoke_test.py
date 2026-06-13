#!/usr/bin/env python3
"""Smoke test for POST /portfolio/match."""

from __future__ import annotations

import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR))

from portfolio_matcher import match_portfolio
from schemas.intake import CurrentStatus, GpaScale, StudentIntake, TargetDegree


def main() -> None:
    intake = StudentIntake(
        destination_countries=["United Kingdom"],
        field_of_study="Computer Engineering & Computer Science",
        target_degree=TargetDegree.MASTER,
        current_status=CurrentStatus.STUDENT,
        origin_country="Iran",
        gpa=17.0,
        gpa_scale=GpaScale.SCALE_20,
        ielts_overall=7.0,
        budget_max_yearly=40000,
    )
    result = match_portfolio(intake, lang="fa", limit_per_bucket=3)
    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
    print(
        f"\nSource={result.data_source} eligible={result.total_eligible}/{result.total_candidates}"
    )
    print(
        f"reach={len(result.buckets.reach)} match={len(result.buckets.match)} "
        f"safety={len(result.buckets.safety)}"
    )


if __name__ == "__main__":
    main()
