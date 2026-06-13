"""Rule-based free-text intake extraction (deterministic, no LLM)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

from ai.intent import detect_path_intent
from schemas.intake import CurrentStatus, GpaScale, StudentIntake, TargetDegree
from schemas.intake_extract import (
    enrich_intake_from_notes,
    extract_gpa,
    extract_ielts,
    normalize_text,
)

EXTRACTOR_VERSION = "rules-v1.0.0"

APP_DIR = Path(__file__).resolve().parent.parent
OPTIONS_PATH = APP_DIR / "reference_options.json"

FIELD_HINTS: dict[str, str] = {
    "computer science": "Computer Engineering & Computer Science",
    "software": "Computer Engineering & Computer Science",
    "data science": "Computer Engineering & Computer Science",
    "هوش مصنوعی": "Computer Engineering & Computer Science",
    "business": "Management, Business & Industrial Engineering",
    "mba": "Management, Business & Industrial Engineering",
    "civil": "Civil Engineering & Architechture",
    "mechanical": "Mechanical, Material & Mining Engineering",
    "مکانیک": "Mechanical, Material & Mining Engineering",
    "electrical": "Electrical Engineering",
    "medicine": "Life Sciences & Medicine",
    "law": "Law Studies",
}

COUNTRY_ALIASES: list[tuple[str, str]] = [
    (r"\buk\b|england|britain|انگلیس|انگستان", "United Kingdom"),
    (r"canada|کانادا|کanada|کانada", "Canada"),
    (r"germany|آلمان", "Germany"),
    (r"usa|united states|\bus\b|آمریکا", "United States"),
    (r"spain|اسپانیا", "Spain"),
    (r"australia|استرالیا", "Australia"),
    (r"italy|ایتالیا", "Italy"),
    (r"sweden|سوئد", "Sweden"),
]


def load_options() -> dict[str, Any]:
    return json.loads(OPTIONS_PATH.read_text(encoding="utf-8"))


def _extract_countries(text: str, options: dict[str, Any]) -> list[str]:
    n = normalize_text(text)
    found: list[str] = []
    for c in options.get("destination_countries", []):
        en = normalize_text(c["en"])
        fa = normalize_text(c.get("fa", ""))
        if en in n or (fa and fa in n):
            if c["en"] not in found:
                found.append(c["en"])
    for pattern, canonical in COUNTRY_ALIASES:
        if re.search(pattern, n) and canonical not in found:
            found.append(canonical)
    return found[:5]


def _extract_field(text: str, options: dict[str, Any]) -> Optional[str]:
    n = normalize_text(text)
    # Prefer longer / more specific field names first
    fields = sorted(options.get("fields_of_study", []), key=len, reverse=True)
    for field in fields:
        if normalize_text(field) in n:
            return field
    for hint, canonical in FIELD_HINTS.items():
        if hint in n:
            return canonical
    if re.search(r"data science|ai\b", n) and "computer" not in n:
        return "Computer Engineering & Computer Science"
    return None


def _extract_degree(text: str) -> TargetDegree:
    n = normalize_text(text)
    if re.search(r"\bphd\b|دکتری", n):
        return TargetDegree.PHD
    if re.search(r"master|msc|\bma\b|کارشناسی ارشد|ارشد|data science", n):
        return TargetDegree.MASTER
    if re.search(r"bachelor|کارشناسی", n):
        return TargetDegree.BACHELOR
    return TargetDegree.MASTER


def _extract_status(text: str) -> CurrentStatus:
    n = normalize_text(text)
    if re.search(r"شاغل|working|employed|شاغلم", n):
        return CurrentStatus.WORKING
    if re.search(r"فارغ|graduate|فارغ‌التحصیل", n):
        return CurrentStatus.GRADUATE
    if re.search(r"دانشجو", n):
        return CurrentStatus.STUDENT
    return CurrentStatus.STUDENT


def _extract_origin(text: str) -> Optional[str]:
    n = normalize_text(text)
    if re.search(r"از\s*ایران|from\s*iran|ایرانی\s*هستم|ایران\s*به", n):
        return "Iran"
    if re.search(r"from\s*india|هند\s*به|از\s*هند", n):
        return "India"
    return None


def _budget_focus(text: str) -> bool:
    n = normalize_text(text)
    return bool(re.search(r"budget|بودجه|ارزون|ارزان|cheap|affordable|low cost", n))


def validate_free_text(text: str) -> tuple[bool, Optional[str]]:
    trimmed = text.strip()
    if not trimmed:
        return False, "too_short"
    if len(trimmed) < 8 and len(trimmed.split()) < 2:
        return False, "too_short"

    intent = detect_path_intent(trimmed)
    if intent != "unclear":
        return True, None

    options = load_options()
    countries = _extract_countries(trimmed, options)
    field = _extract_field(trimmed, options)
    if countries or field:
        return True, None

    if _budget_focus(trimmed) or _extract_origin(trimmed):
        return True, None

    if re.search(r"study|work|تحصیل|کار|مهاجرت|خارج|برم|mba|master|phd", normalize_text(trimmed)):
        return True, None

    return False, "irrelevant"


def extract_from_text(text: str) -> dict[str, Any]:
    """
    Parse free text into partial intake + metadata.

    Returns dict with keys: valid, reason, path_intent, partial_intake, extractor, confidence.
    """
    valid, reason = validate_free_text(text)
    if not valid:
        return {
            "valid": False,
            "reason": reason,
            "path_intent": detect_path_intent(text),
            "partial_intake": None,
            "extractor": EXTRACTOR_VERSION,
            "confidence": 0.0,
        }

    options = load_options()
    path_intent = detect_path_intent(text)
    countries = _extract_countries(text, options)
    field = _extract_field(text, options)
    gpa, gpa_scale = extract_gpa(text)
    ielts = extract_ielts(text)

    partial: dict[str, Any] = {
        "destination_countries": countries,
        "field_of_study": field or "Computer Engineering & Computer Science",
        "target_degree": _extract_degree(text).value,
        "current_status": _extract_status(text).value,
        "additional_notes": text.strip(),
    }
    if gpa is not None:
        partial["gpa"] = gpa
    if gpa_scale is not None:
        partial["gpa_scale"] = gpa_scale.value if isinstance(gpa_scale, GpaScale) else gpa_scale
    if ielts is not None:
        partial["ielts_overall"] = ielts
    origin = _extract_origin(text)
    if origin:
        partial["origin_country"] = origin

    # Confidence heuristic for routing (LLM vs rules-only)
    signals = sum(
        [
            bool(countries),
            bool(field),
            gpa is not None,
            ielts is not None,
            path_intent != "unclear",
        ]
    )
    confidence = min(1.0, 0.35 + signals * 0.15)

    return {
        "valid": True,
        "reason": None,
        "path_intent": path_intent,
        "budget_focus": _budget_focus(text),
        "needs_path_clarify": path_intent
        in ("alternatives_to_study", "emigration_explore", "work_abroad", "unclear"),
        "partial_intake": partial,
        "extractor": EXTRACTOR_VERSION,
        "confidence": round(confidence, 2),
    }


def build_student_intake(text: str) -> tuple[Optional[StudentIntake], dict[str, Any]]:
    """Full extraction result; returns (StudentIntake|None, metadata)."""
    meta = extract_from_text(text)
    if not meta["valid"]:
        return None, meta

    partial = meta["partial_intake"]
    assert partial is not None

    # StudentIntake requires at least one country — use placeholder if missing (chat will ask)
    countries = partial.get("destination_countries") or ["United Kingdom"]

    intake = StudentIntake(
        destination_countries=countries,
        field_of_study=partial["field_of_study"],
        target_degree=TargetDegree(partial["target_degree"]),
        current_status=CurrentStatus(partial["current_status"]),
        additional_notes=partial.get("additional_notes"),
        gpa=partial.get("gpa"),
        gpa_scale=partial.get("gpa_scale"),
        ielts_overall=partial.get("ielts_overall"),
        origin_country=partial.get("origin_country"),
    )
    intake = enrich_intake_from_notes(intake)
    meta["intake_complete"] = len(partial.get("destination_countries") or []) > 0
    return intake, meta
