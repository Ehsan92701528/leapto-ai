#!/usr/bin/env python3
"""Tests for the verified 2027 catalogue publishing gate."""

from __future__ import annotations

import csv
import importlib.util
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

SCRIPT = Path(__file__).with_name("verify_uk_masters_2027.py")
SPEC = importlib.util.spec_from_file_location("verify_uk_masters_2027", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

ROOT = Path(__file__).resolve().parents[1] / "verified_2027"


def write_csv(path: Path, fieldnames: list[str], row: dict[str, str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(row)


class VerifiedCatalogueTests(unittest.TestCase):
    def make_catalogue(self, root: Path, *, programme_url: str, deadline: str) -> None:
        root.mkdir()
        write_csv(
            root / "programmes.csv",
            ["university_name_en", "title_en", "subject_family", "leapto_category", "programme_url", "duration_months", "delivery_mode", "last_verified_at"],
            {
                "university_name_en": "University of Manchester",
                "title_en": "MSc Data Science",
                "subject_family": "computing-data-ai",
                "leapto_category": "Computer Engineering & Computer Science",
                "programme_url": programme_url,
                "duration_months": "12",
                "delivery_mode": "on_campus",
                "last_verified_at": "2026-08-15",
            },
        )
        write_csv(
            root / "requirements.csv",
            ["university_name_en", "programme_title_en", "min_ielts_overall", "min_toefl_ibt", "min_gpa_4", "min_gpa_20", "work_experience_years_min", "entry_notes_en", "source_url", "last_verified_at"],
            {
                "university_name_en": "University of Manchester",
                "programme_title_en": "MSc Data Science",
                "min_ielts_overall": "6.5",
                "entry_notes_en": "Relevant quantitative degree; international equivalencies must be checked on the official page.",
                "source_url": "https://www.manchester.ac.uk/study/masters/courses/list/00000/msc-data-science/entry-requirements/",
                "last_verified_at": "2026-08-15",
            },
        )
        write_csv(
            root / "costs.csv",
            ["university_name_en", "programme_title_en", "academic_year", "tuition_amount", "currency", "source_url", "last_verified_at"],
            {
                "university_name_en": "University of Manchester",
                "programme_title_en": "MSc Data Science",
                "academic_year": "2027/28",
                "tuition_amount": "35000",
                "currency": "GBP",
                "source_url": "https://www.manchester.ac.uk/study/masters/courses/list/00000/msc-data-science/fees-and-funding/",
                "last_verified_at": "2026-08-15",
            },
        )
        write_csv(
            root / "intakes.csv",
            ["university_name_en", "programme_title_en", "start_term", "application_deadline", "is_rolling", "source_url", "last_verified_at"],
            {
                "university_name_en": "University of Manchester",
                "programme_title_en": "MSc Data Science",
                "start_term": "September 2027",
                "application_deadline": deadline,
                "is_rolling": "false",
                "source_url": "https://www.manchester.ac.uk/study/masters/courses/list/00000/msc-data-science/application-and-selection/",
                "last_verified_at": "2026-08-15",
            },
        )

    def validate(self, data_dir: Path):
        return MODULE.validate(
            data_dir,
            ROOT / "university_sources.csv",
            ROOT / "catalogue_policy.json",
            as_of=date(2026, 8, 15),
            minimum_programmes=1,
        )

    def test_valid_complete_record_is_publishable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "incoming"
            self.make_catalogue(
                data_dir,
                programme_url="https://www.manchester.ac.uk/study/masters/courses/list/00000/msc-data-science/",
                deadline="2027-07-31",
            )
            result = self.validate(data_dir)
            self.assertEqual([], result.errors)
            self.assertEqual(1, len(result.rows))
            self.assertEqual("September 2027", result.rows[0]["start_term"])

    def test_wrong_domain_and_expired_deadline_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "incoming"
            self.make_catalogue(
                data_dir,
                programme_url="https://example.com/fake-course",
                deadline="2026-07-31",
            )
            result = self.validate(data_dir)
            joined = "\n".join(result.errors)
            self.assertIn("programme URL is not a specific page", joined)
            self.assertIn("application deadline is not in the future", joined)


if __name__ == "__main__":
    unittest.main()
