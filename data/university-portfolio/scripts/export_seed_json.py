#!/usr/bin/env python3
"""Build portfolio JSON cache from seed CSVs (no PostgreSQL required)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

SEED_DIR = Path(__file__).resolve().parents[1] / "seed"
OUT = Path(__file__).resolve().parents[1] / "cache" / "portfolio_gb_msc.json"


def read_csv(name: str) -> list[dict[str, str]]:
    path = SEED_DIR / name
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    unis = {(r["name_en"], r["country_code"]): r for r in read_csv("universities_import.csv")}
    tags = {r["slug"]: r for r in read_csv("leapto_field_tags.csv")}
    reqs = {
        (r["university_name_en"], r["programme_title_en"]): r
        for r in read_csv("programme_requirements_import.csv")
    }
    costs = {
        (r["university_name_en"], r["programme_title_en"]): r
        for r in read_csv("programme_costs_import.csv")
    }
    intakes = {
        (r["university_name_en"], r["programme_title_en"]): r for r in read_csv("intakes_import.csv")
    }

    programmes = []
    for i, row in enumerate(read_csv("programmes_import.csv"), start=1):
        uni = unis.get((row["university_name_en"], row["country_code"]), {})
        tag = tags.get(row.get("field_tag_slug", ""), {})
        key = (row["university_name_en"], row["title_en"])
        req = reqs.get(key, {})
        cost = costs.get(key, {})
        intake = intakes.get(key, {})

        programmes.append(
            {
                "programme_id": i,
                "country_en": "United Kingdom",
                "country_code": row["country_code"],
                "university_en": row["university_name_en"],
                "city_en": uni.get("city_en", ""),
                "ranking_band": uni.get("ranking_band", ""),
                "programme_title": row["title_en"],
                "degree_level": row["degree_level"],
                "field_tag_slug": row.get("field_tag_slug", ""),
                "field_tag_en": tag.get("label_en", ""),
                "leapto_category": tag.get("leapto_category", ""),
                "programme_url": row["programme_url"],
                "requirements_confidence": row.get("requirements_confidence", "medium"),
                "min_ielts_overall": float(req["min_ielts_overall"]) if req.get("min_ielts_overall") else None,
                "min_gpa_4": float(req["min_gpa_4"]) if req.get("min_gpa_4") else None,
                "min_gpa_20": float(req["min_gpa_20"]) if req.get("min_gpa_20") else None,
                "entry_notes_en": req.get("entry_notes_en", ""),
                "tuition_amount": float(cost["tuition_amount"]) if cost.get("tuition_amount") else None,
                "currency": cost.get("currency", "GBP"),
                "living_cost_estimate": float(cost["living_cost_estimate"])
                if cost.get("living_cost_estimate")
                else None,
                "start_term": intake.get("start_term"),
                "application_deadline": intake.get("application_deadline"),
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"programmes": programmes}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(programmes)} programmes to {OUT}")


if __name__ == "__main__":
    main()
