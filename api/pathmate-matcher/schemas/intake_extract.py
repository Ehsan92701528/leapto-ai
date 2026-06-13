"""Extract structured scores from free-text intake notes (shared by API and portfolio matcher)."""

from __future__ import annotations

import re
from typing import Any, Optional

from schemas.intake import BudgetCurrency, GpaScale, StudentIntake

_PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


def normalize_text(text: str) -> str:
    return text.translate(_PERSIAN_DIGITS).lower().strip()


def extract_gpa(text: str) -> tuple[Optional[float], Optional[GpaScale]]:
    n = normalize_text(text)
    patterns = [
        r"معدل\s*[:：]?\s*(\d+(?:\.\d+)?)",
        r"gpa\s*[:：]?\s*(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)\s*/\s*20",
        r"(\d+(?:\.\d+)?)\s*/\s*4(?:\.0)?",
    ]
    for pat in patterns:
        m = re.search(pat, n)
        if not m:
            continue
        value = float(m.group(1))
        if "/20" in pat or value > 4.5:
            return value, GpaScale.SCALE_20
        if value <= 4.5:
            return value, GpaScale.SCALE_4
        if value <= 100:
            return value, GpaScale.SCALE_100
    return None, None


def extract_ielts(text: str) -> Optional[float]:
    n = normalize_text(text)
    m = re.search(r"(?:ielts|آیلتس)\s*[:：]?\s*(\d+(?:\.\d+)?)", n)
    if m:
        return float(m.group(1))
    return None


def extract_toefl(text: str) -> Optional[int]:
    n = normalize_text(text)
    m = re.search(r"(?:toefl|تافل)\s*[:：]?\s*(\d+)", n)
    return int(m.group(1)) if m else None


def extract_gre(text: str) -> Optional[int]:
    n = normalize_text(text)
    m = re.search(r"gre\s*[:：]?\s*(\d{3})", n)
    return int(m.group(1)) if m else None


def extract_gmat(text: str) -> Optional[int]:
    n = normalize_text(text)
    m = re.search(r"gmat\s*[:：]?\s*(\d{3})", n)
    return int(m.group(1)) if m else None


def extract_budget(text: str) -> tuple[Optional[float], Optional[BudgetCurrency]]:
    n = normalize_text(text)
    currency = None
    if "£" in text or "gbp" in n or "پوند" in n:
        currency = BudgetCurrency.GBP
    elif "€" in text or "eur" in n or "یورو" in n:
        currency = BudgetCurrency.EUR
    elif "$" in text or "usd" in n or "دلار" in n:
        currency = BudgetCurrency.USD
    elif "cad" in n or "کanada" in n:
        currency = BudgetCurrency.CAD

    m = re.search(r"(?:بودجه|budget)[^\d]{0,20}(\d[\d,]*)", n)
    if not m:
        m = re.search(r"£\s*(\d[\d,]*)", normalize_text(text))
    if m:
        amount = float(m.group(1).replace(",", ""))
        return amount, currency or BudgetCurrency.GBP
    return None, None


def enrich_intake_from_notes(intake: StudentIntake) -> StudentIntake:
    """Fill optional score fields from ``additional_notes`` when not already set."""
    notes = intake.additional_notes or ""
    if not notes.strip():
        return intake

    updates: dict[str, Any] = {}
    if intake.gpa is None:
        gpa, scale = extract_gpa(notes)
        if gpa is not None:
            updates["gpa"] = gpa
            updates["gpa_scale"] = scale
    if intake.ielts_overall is None:
        ielts = extract_ielts(notes)
        if ielts is not None:
            updates["ielts_overall"] = ielts
    if intake.toefl_ibt is None:
        toefl = extract_toefl(notes)
        if toefl is not None:
            updates["toefl_ibt"] = toefl
    if intake.gre_total is None:
        gre = extract_gre(notes)
        if gre is not None:
            updates["gre_total"] = gre
    if intake.gmat_score is None:
        gmat = extract_gmat(notes)
        if gmat is not None:
            updates["gmat_score"] = gmat
    if intake.budget_max_yearly is None:
        budget, curr = extract_budget(notes)
        if budget is not None:
            updates["budget_max_yearly"] = budget
            updates["budget_currency"] = curr

    if updates:
        return intake.model_copy(update=updates)
    return intake
