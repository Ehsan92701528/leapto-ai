#!/usr/bin/env python3
"""Tests for planning-catalogue discovery and publication safeguards."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


def load_script(name: str):
    path = Path(__file__).with_name(name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


DISCOVERY = load_script("discover_official_uk_masters")
PUBLISHER = load_script("publish_planning_uk_masters_2027")
UNIVERSITY = {
    "university_name_en": "King's College London",
    "city_en": "London",
}


class PlanningCatalogueTests(unittest.TestCase):
    def test_catalogue_title_supplies_award_missing_from_h1(self) -> None:
        html = """
        <html><h1>Advanced Computing</h1><p>IELTS Academic: 6.5.</p>
        <p>International tuition fees £38,000 for 2026/27.</p></html>
        """
        row = DISCOVERY.extract_course(
            html,
            "https://www.kcl.ac.uk/study/postgraduate-taught/courses/advanced-computing-msc",
            UNIVERSITY,
            "2026-08-15T00:00:00+00:00",
            "Advanced Computing MSc",
        )
        self.assertIsNotNone(row)
        assert row
        self.assertEqual("Advanced Computing MSc", row["title_en"])
        self.assertEqual("38000", row["international_tuition_gbp"])
        self.assertEqual("unreviewed_regex", row["tuition_evidence_status"])

    def test_home_fee_is_not_mistaken_for_international_fee(self) -> None:
        html = """
        <html><h1>Data Science MSc</h1>
        <p>Home tuition fees £15,000. International tuition fees £35,000.</p></html>
        """
        row = DISCOVERY.extract_course(
            html,
            "https://example.ac.uk/study/postgraduate/data-science-msc",
            {"university_name_en": "Example University", "city_en": "Example"},
            "2026-08-15T00:00:00+00:00",
        )
        self.assertIsNotNone(row)
        assert row
        self.assertEqual("35000", row["international_tuition_gbp"])

    def test_online_and_overseas_courses_are_not_published(self) -> None:
        base = {"delivery_mode": "on_campus", "programme_url": "https://example.ac.uk/course"}
        self.assertFalse(PUBLISHER.row_in_scope({**base, "title_en": "Cyber Security Online MSc"}))
        self.assertFalse(PUBLISHER.row_in_scope({**base, "title_en": "Management MSc", "programme_url": "https://example.ac.uk/dubai/management-msc"}))
        self.assertFalse(PUBLISHER.row_in_scope({**base, "title_en": "Strategic FinTech MSc (Bahrain)"}))
        self.assertTrue(PUBLISHER.row_in_scope({**base, "title_en": "Cyber Security MSc"}))


if __name__ == "__main__":
    unittest.main()
