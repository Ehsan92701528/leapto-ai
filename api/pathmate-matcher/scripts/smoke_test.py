#!/usr/bin/env python3
"""Export StudentIntake JSON Schema and run a sample match."""

from __future__ import annotations

import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR))

from matcher import match_mentors
from schemas.intake import GpaScale, StudentIntake, TargetDegree, CurrentStatus


def export_schema() -> Path:
    out = APP_DIR / "schemas" / "student_intake.schema.json"
    out.write_text(
        json.dumps(StudentIntake.model_json_schema(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return out


def sample_match() -> None:
    print("=== Exact platform field ===")
    _run_match(
        StudentIntake(
            destination_countries=["Canada", "United Kingdom"],
            field_of_study="Computer Engineering & Computer Science",
            target_degree=TargetDegree.MASTER,
            current_status=CurrentStatus.STUDENT,
            origin_country="Iran",
            languages=["Persian", "English"],
            timeline="September 2026",
            gpa=17.0,
            gpa_scale=GpaScale.SCALE_20,
            ielts_overall=7.0,
            preferred_start="September 2026",
            additional_notes="Interested in Data Science and AI MSc programmes.",
        )
    )

    print("=== Free-text close field (not on dropdown) ===")
    _run_match(
        StudentIntake(
            destination_countries=["Germany"],
            field_of_study="Artificial Intelligence",
            target_degree=TargetDegree.MASTER,
            current_status=CurrentStatus.GRADUATE,
            additional_notes="Background in robotics, GRE 320.",
        )
    )


def _run_match(intake: StudentIntake) -> None:
    matches, total, filtered = match_mentors(intake, lang="fa", limit=3)
    print(f"Field requested: {intake.field_of_study}")
    print(f"Considered {total} mentors, {filtered} passed filters\n")
    for m in matches:
        print(f"- {m.name} ({m.name_en}) score={m.score} field_match={m.field_match_level}")
        for reason in m.match_reasons:
            print(f"    • {reason}")
        print()


if __name__ == "__main__":
    schema_path = export_schema()
    print(f"Wrote {schema_path}\n")
    sample_match()
