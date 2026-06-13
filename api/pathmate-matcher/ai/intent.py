"""Path intent detection — Python mirror of pathmate-finder.js logic."""

from __future__ import annotations

import re

from schemas.intake_extract import normalize_text

PathIntent = str  # study_abroad | work_abroad | alternatives_to_study | emigration_explore | unclear


def _has_study_intent(text: str) -> bool:
    n = normalize_text(text)
    return bool(
        re.search(
            r"study|university|master|msc|phd|bachelor|mba|"
            r"تحصیل|دانشگاه|ارشد|دکتری|کارشناسی",
            n,
        )
    )


def _has_work_intent(text: str) -> bool:
    n = normalize_text(text)
    return bool(
        re.search(
            r"work|job|career|employment|skilled worker|شغل|کاری|کار\s*در|مهاجرت\s*کاری|ویزای\s*کار",
            n,
        )
    )


def _has_mobility_intent(text: str) -> bool:
    n = normalize_text(text)
    return bool(
        re.search(
            r"abroad|overseas|immigr|emigrat|خارج|برم|بریم|مهاجرت|رفتن\s*به",
            n,
        )
    )


def _rejects_study_path(text: str) -> bool:
    n = normalize_text(text)
    return bool(
        re.search(
            r"without\s*stud|no\s*stud|don't\s*want\s*to\s*stud|بدون\s*تحصیل|تحصیل\s*نمی",
            n,
        )
    )


def detect_path_intent(text: str) -> PathIntent:
    n = normalize_text(text)
    if _rejects_study_path(text):
        return "alternatives_to_study"
    if re.search(
        r"any other way|other ways|another way|get out of|leave the country|"
        r"leave my country|راه\s*دیگر|چطور\s*برم\s*خارج|از\s*کشور\s*برم|برم\s*خارج",
        n,
    ):
        return "emigration_explore"
    if re.search(
        r"work visa|skilled worker|find a job|job abroad|employment|"
        r"کار\s*در\s*خارج|ویزای\s*کار|مهاجرت\s*کاری",
        n,
    ):
        return "work_abroad"
    if _has_work_intent(text) and _has_mobility_intent(text):
        return "work_abroad"
    if _has_work_intent(text):
        return "work_abroad"
    if _has_study_intent(text) and not _rejects_study_path(text):
        return "study_abroad"
    if _has_mobility_intent(text) and re.search(r"mba|master|msc|phd|ارشد|دکتری|تحصیل", normalize_text(text)):
        return "study_abroad"
    if re.search(r"work|job|شغل|career|کاری", n):
        return "work_abroad"
    if re.search(r"emigrat|immigrat|مهاجرت|خروج\s*از\s*کشور", n):
        return "emigration_explore"
    return "unclear"
