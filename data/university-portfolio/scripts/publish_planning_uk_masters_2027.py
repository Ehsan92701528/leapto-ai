#!/usr/bin/env python3
"""Publish the latest-official UK Master's planning inventory for local matching."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PORTFOLIO_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PORTFOLIO_DIR / "planning_2027" / "discovered_programmes.csv"
DEFAULT_OUTPUT = PORTFOLIO_DIR / "cache" / "portfolio_gb_msc_planning_2027.json"
DEFAULT_REPORT = PORTFOLIO_DIR / "planning_2027" / "completeness_report.json"
OUT_OF_SCOPE_RE = re.compile(
    r"\b(online|distance learning|bahrain|china|dubai|hong kong|malaysia|oman|qatar|singapore|uae)\b",
    re.I,
)


def number(value: str) -> float | None:
    value = (value or "").strip().replace(",", "")
    try:
        return float(value) if value else None
    except ValueError:
        return None


def row_in_scope(row: dict[str, str]) -> bool:
    scope_text = " ".join((row.get("title_en", ""), row.get("programme_url", "").replace("-", " ")))
    return row.get("delivery_mode", "on_campus") == "on_campus" and not OUT_OF_SCOPE_RE.search(scope_text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    with args.input.open(encoding="utf-8-sig", newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    unique: dict[tuple[str, str], dict[str, str]] = {}
    for row in source_rows:
        if not row_in_scope(row):
            continue
        key = (row["university_name_en"].strip(), row["title_en"].strip().lower())
        unique.setdefault(key, row)

    programmes = []
    for programme_id, row in enumerate(sorted(unique.values(), key=lambda item: (item["university_name_en"], item["title_en"])), start=700001):
        tuition = (
            number(row.get("international_tuition_gbp", ""))
            if row.get("tuition_evidence_status", "").strip() == "official_international_verified"
            else None
        )
        ielts = number(row.get("min_ielts_overall", ""))
        programmes.append({
            "programme_id": programme_id,
            "country_en": "United Kingdom",
            "country_code": "GB",
            "university_en": row["university_name_en"].strip(),
            "city_en": row.get("city_en", "").strip(),
            "ranking_band": "",
            "programme_title": row["title_en"].strip(),
            "degree_level": "Master",
            "field_tag_slug": row.get("subject_family", "").strip(),
            "field_tag_en": row.get("subject_family", "").replace("-", " ").title(),
            "leapto_category": row.get("leapto_category", "").strip(),
            "programme_url": row.get("programme_url", "").strip(),
            "requirements_confidence": "medium" if ielts is not None else "low",
            "min_ielts_overall": ielts,
            "min_gpa_4": None,
            "min_gpa_20": None,
            "entry_notes_en": "Check the official course page for current country-specific entry requirements.",
            "tuition_amount": tuition,
            "currency": "GBP",
            "living_cost_estimate": None,
            "start_term": row.get("published_start_term", "").strip() or None,
            "application_deadline": row.get("application_deadline", "").strip() or None,
            "source_academic_year": row.get("source_academic_year", "").strip() or None,
            "planning_target_intake": "September 2027",
            "data_quality": "latest-published-planning",
            "last_verified_at": row.get("last_checked_at", "").strip() or None,
        })

    generated_at = datetime.now(timezone.utc).isoformat()
    payload = {
        "catalogue": "uk-taught-masters-planning-2027",
        "generated_at": generated_at,
        "quality": "latest-published-planning",
        "disclaimer": "Uses the latest official university pages available; values are not confirmed for 2027 unless the source says so.",
        "programmes": programmes,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    report = {
        "generated_at": generated_at,
        "programmes": len(programmes),
        "universities": len({row["university_en"] for row in programmes}),
        "with_verified_international_tuition": sum(row["tuition_amount"] is not None for row in programmes),
        "with_unreviewed_tuition_candidate": sum(bool(number(row.get("international_tuition_gbp", ""))) for row in unique.values()),
        "with_ielts": sum(row["min_ielts_overall"] is not None for row in programmes),
        "with_published_start_term": sum(row["start_term"] is not None for row in programmes),
        "subject_family_counts": dict(Counter(row["field_tag_slug"] for row in programmes)),
        "university_counts": dict(sorted(Counter(row["university_en"] for row in programmes).items())),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if programmes else 1


if __name__ == "__main__":
    raise SystemExit(main())
