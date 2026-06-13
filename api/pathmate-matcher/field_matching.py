"""Fuzzy and related-field matching for student intake vs mentor profiles."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
RELATIONS_PATH = APP_DIR / "field_relations.json"
OPTIONS_PATH = APP_DIR / "reference_options.json"

FIELD_STOPWORDS = {
    "and",
    "the",
    "studies",
    "engineering",
    "science",
    "sciences",
    "study",
    "field",
    "programme",
    "program",
    "degree",
    "major",
}


@dataclass(frozen=True)
class FieldFit:
    level: str  # exact | alias | close | specialization | token | weak | none
    score: float
    detail: str
    canonical_field: str = ""


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip().casefold()


def field_tokens(value: str) -> set[str]:
    raw = re.findall(r"[\w\u0600-\u06FF]+", normalize_text(value))
    return {t for t in raw if len(t) >= 3 and t not in FIELD_STOPWORDS}


@lru_cache(maxsize=1)
def load_field_relations() -> dict:
    return json.loads(RELATIONS_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def canonical_fields() -> tuple[str, ...]:
    options = json.loads(OPTIONS_PATH.read_text(encoding="utf-8"))
    return tuple(options["fields_of_study"])


@lru_cache(maxsize=1)
def alias_map() -> dict[str, str]:
    relations = load_field_relations()
    mapping: dict[str, str] = {}
    for alias, canonical in relations.get("aliases", {}).items():
        mapping[normalize_text(alias)] = canonical
    return mapping


@lru_cache(maxsize=1)
def field_to_group() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for group in load_field_relations().get("related_groups", []):
        group_id = group["id"]
        for field in group["fields"]:
            mapping[field] = group_id
    return mapping


def resolve_canonical_field(user_field: str) -> str:
    """Map free-text / alias input to a platform category when possible."""
    normalized = normalize_text(user_field)
    if not normalized:
        return user_field

    aliases = alias_map()
    if normalized in aliases:
        return aliases[normalized]

    for canonical in canonical_fields():
        if normalize_text(canonical) == normalized:
            return canonical

    best_canonical = ""
    best_ratio = 0.0
    for canonical in canonical_fields():
        ratio = SequenceMatcher(None, normalized, normalize_text(canonical)).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_canonical = canonical

    if best_ratio >= 0.72:
        return best_canonical

    for alias, canonical in aliases.items():
        if alias in normalized or normalized in alias:
            return canonical

    return user_field


def mentor_field_blob(mentor: dict) -> str:
    parts = mentor.get("fields", []) + mentor.get("specializations", [])
    return normalize_text(" ".join(parts))


def same_related_group(field_a: str, field_b: str) -> bool:
    groups = field_to_group()
    ga = groups.get(field_a)
    gb = groups.get(field_b)
    return bool(ga and gb and ga == gb)


def token_overlap_score(user_tokens: set[str], mentor_tokens: set[str]) -> float:
    if not user_tokens or not mentor_tokens:
        return 0.0
    shared = user_tokens & mentor_tokens
    if not shared:
        return 0.0
    coverage = len(shared) / max(len(user_tokens), 1)
    return min(18.0, 8.0 + coverage * 10.0)


def assess_field_fit(user_field: str, mentor: dict) -> FieldFit:
    canonical = resolve_canonical_field(user_field)
    user_norm = normalize_text(user_field)
    canonical_norm = normalize_text(canonical)
    user_tokens = field_tokens(user_field) | field_tokens(canonical)
    mentor_fields = mentor.get("fields") or []
    mentor_specs = mentor.get("specializations") or []
    blob = mentor_field_blob(mentor)
    search_blob = normalize_text(mentor.get("search_text") or "")

    # 1) Exact match on mentor category
    for mf in mentor_fields:
        if normalize_text(mf) == canonical_norm or normalize_text(mf) == user_norm:
            return FieldFit("exact", 35.0, mf, canonical)

    # 2) User input was an alias; mentor is in resolved canonical family
    if canonical != user_field:
        for mf in mentor_fields:
            if normalize_text(mf) == normalize_text(canonical):
                return FieldFit("alias", 30.0, mf, canonical)

    # 3) Substring / near-text on mentor categories
    for mf in mentor_fields:
        mf_norm = normalize_text(mf)
        if user_norm in mf_norm or mf_norm in user_norm:
            return FieldFit("close", 24.0, mf, canonical)
        ratio = SequenceMatcher(None, user_norm, mf_norm).ratio()
        if ratio >= 0.68:
            return FieldFit("close", 22.0, mf, canonical)

    # 4) Related platform group (e.g. CS ↔ Electrical Engineering)
    for mf in mentor_fields:
        if same_related_group(canonical, mf) or same_related_group(user_field, mf):
            return FieldFit("close", 20.0, mf, canonical)

    # 5) Specialization overlap (e.g. user says "Data Science", mentor spec matches)
    for spec in mentor_specs:
        spec_norm = normalize_text(spec)
        if user_norm == spec_norm or user_norm in spec_norm or spec_norm in user_norm:
            return FieldFit("specialization", 26.0, spec, canonical)
        spec_tokens = field_tokens(spec)
        overlap = user_tokens & spec_tokens
        if overlap:
            return FieldFit(
                "specialization",
                min(24.0, 16.0 + len(overlap) * 3.0),
                spec,
                canonical,
            )

    # 6) Token overlap across mentor field blob
    mentor_tokens = field_tokens(blob)
    overlap_score = token_overlap_score(user_tokens, mentor_tokens)
    if overlap_score >= 12.0:
        shared = sorted(user_tokens & mentor_tokens)
        return FieldFit(
            "token",
            overlap_score,
            ", ".join(shared[:3]) or blob[:80],
            canonical,
        )

    # 7) Weak signal in full profile text (future custom fields, bios)
    search_tokens = field_tokens(search_blob)
    weak_score = token_overlap_score(user_tokens, search_tokens)
    if weak_score >= 10.0:
        return FieldFit("weak", min(14.0, weak_score), user_field, canonical)

    return FieldFit("none", 0.0, "", canonical)


def field_fit_reason(fit: FieldFit, lang: str) -> str:
    if fit.level == "exact":
        return (
            f"رشته دقیقاً منطبق: {fit.detail}"
            if lang == "fa"
            else f"Exact field match: {fit.detail}"
        )
    if fit.level == "alias":
        return (
            f"رشته نزدیک (معادل {fit.canonical_field}): {fit.detail}"
            if lang == "fa"
            else f"Close field (mapped to {fit.canonical_field}): {fit.detail}"
        )
    if fit.level == "close":
        return (
            f"رشته مرتبط: {fit.detail}"
            if lang == "fa"
            else f"Related field: {fit.detail}"
        )
    if fit.level == "specialization":
        return (
            f"گرایش نزدیک به درخواست شما: {fit.detail}"
            if lang == "fa"
            else f"Specialization close to your request: {fit.detail}"
        )
    if fit.level == "token":
        return (
            f"هم‌پوشانی موضوعی: {fit.detail}"
            if lang == "fa"
            else f"Topic overlap: {fit.detail}"
        )
    if fit.level == "weak":
        return (
            "ارتباط ضعیف‌تر در پروفایل؛ پیشنهاد جایگزین"
            if lang == "fa"
            else "Weaker profile overlap; suggested alternative"
        )
    return ""
