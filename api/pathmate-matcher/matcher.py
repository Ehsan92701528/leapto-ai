"""Rule-based path-mate matching from student intake + mentor dataset."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from field_matching import assess_field_fit, field_fit_reason, load_field_relations
from schemas.intake import MentorMatch, StudentIntake, TargetDegree

ROOT = Path(__file__).resolve().parent.parent.parent
MENTORS_FA_PATH = ROOT / "data" / "mentors.fa.json"
MENTORS_EN_PATH = ROOT / "data" / "mentors.en.json"
MENTORS_PATH = MENTORS_FA_PATH  # backwards compat
OPTIONS_PATH = Path(__file__).resolve().parent / "reference_options.json"

DEGREE_RANK = {"Bachelor": 1, "Master": 2, "PhD": 3}

EXAM_KEYWORDS = (
    "ielts",
    "toefl",
    "gre",
    "gmat",
    "cfa",
    "pte",
    "duolingo",
    "gpa",
    "moi",
)

NOTE_STOPWORDS = {
    "and",
    "the",
    "for",
    "with",
    "from",
    "that",
    "this",
    "have",
    "are",
    "was",
    "you",
    "your",
    "about",
    "around",
    "interested",
    "programmes",
    "programs",
}


@dataclass
class ScoredMentor:
    mentor: dict
    score: float
    reasons: list[str]
    field_match_level: str = "none"


@lru_cache(maxsize=1)
def load_options() -> dict:
    return json.loads(OPTIONS_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=2)
def load_mentors(lang: str = "fa") -> list[dict]:
    path = MENTORS_EN_PATH if lang == "en" and MENTORS_EN_PATH.exists() else MENTORS_FA_PATH
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [m for m in payload["mentors"] if m.get("active")]


def mentor_display_name(mentor: dict, lang: str) -> str:
    if lang == "en":
        return (mentor.get("name_en") or mentor.get("name") or "").strip()
    return (mentor.get("name") or mentor.get("name_en") or "").strip()


def mentor_profile_url(mentor: dict, lang: str) -> str:
    if lang == "en":
        return (mentor.get("profile_url_en") or mentor.get("profile_url") or "").strip()
    return (mentor.get("profile_url") or "").strip()


def _country_aliases() -> dict[str, str]:
    aliases: dict[str, str] = {}
    for item in load_options()["destination_countries"]:
        canonical = item["en"]
        aliases[item["en"].casefold()] = canonical
        aliases[item["fa"].casefold()] = canonical
        aliases[item["code"].casefold()] = canonical
    extras = {
        "uk": "United Kingdom",
        "england": "United Kingdom",
        "britain": "United Kingdom",
        "usa": "United States",
        "america": "United States",
        "u.s.": "United States",
        "u.s.a.": "United States",
        "korea": "South Korea",
        "south korea": "South Korea",
    }
    for key, value in extras.items():
        aliases[key] = value
    return aliases


def normalize_country(name: str) -> str:
    return _country_aliases().get(name.strip().casefold(), name.strip())


def normalize_countries(names: list[str]) -> set[str]:
    return {normalize_country(n) for n in names}


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip().casefold()


def min_field_score() -> float:
    return float(load_field_relations().get("min_field_score_to_include", 12))


def degree_compatible(mentor_degree: str, target: TargetDegree) -> bool:
    mentor_rank = DEGREE_RANK.get(mentor_degree, 0)
    target_rank = DEGREE_RANK.get(target.value, 0)
    if mentor_rank == 0:
        return True
    return mentor_rank >= target_rank


def meaningful_tokens(text: str) -> list[str]:
    tokens = re.findall(r"[\w\u0600-\u06FF]+", text)
    return [
        t
        for t in tokens
        if len(t) >= 4 and not t.isdigit() and t.casefold() not in NOTE_STOPWORDS
    ]


def token_hits(text: str, tokens: list[str]) -> list[str]:
    lowered = normalize_text(text)
    hits: list[str] = []
    for token in tokens:
        t = normalize_text(token)
        if t and t in lowered:
            hits.append(token)
    return hits


def score_mentor(mentor: dict, intake: StudentIntake, lang: str) -> ScoredMentor | None:
    reasons: list[str] = []
    score = 0.0

    target_countries = normalize_countries(intake.destination_countries)
    mentor_country = normalize_country(mentor.get("current_country_en") or mentor.get("current_country_fa") or "")

    if mentor_country not in target_countries:
        return None
    score += 40
    if lang == "fa":
        reasons.append(f"اکنون در {mentor.get('current_country_fa') or mentor_country} زندگی می‌کند")
    else:
        reasons.append(f"Currently based in {mentor_country}")

    field_fit = assess_field_fit(intake.field_of_study, mentor)
    if field_fit.score < min_field_score():
        return None
    score += field_fit.score
    fit_reason = field_fit_reason(field_fit, lang)
    if fit_reason:
        reasons.append(fit_reason)

    mentor_degree = mentor.get("degree_level") or ""
    if mentor_degree:
        if degree_compatible(mentor_degree, intake.target_degree):
            score += 15
            if lang == "fa":
                reasons.append(f"مسیر {mentor_degree} نزدیک به هدف {intake.target_degree.value} شماست")
            else:
                reasons.append(f"{mentor_degree} path aligns with your {intake.target_degree.value} goal")
        else:
            score -= 10

    specs = mentor.get("specializations") or []
    if specs and field_fit.level not in ("exact", "specialization"):
        score += 3
        if lang == "fa":
            reasons.append(f"گرایش: {', '.join(specs[:2])}")
        else:
            reasons.append(f"Specialization: {', '.join(specs[:2])}")

    search_blob = mentor.get("search_text") or ""
    if intake.languages:
        lang_hits = token_hits(search_blob, intake.languages)
        if lang_hits:
            score += min(5, len(lang_hits) * 2)
            if lang == "fa":
                reasons.append(f"زبان مشترک: {', '.join(lang_hits[:3])}")
            else:
                reasons.append(f"Shared languages: {', '.join(lang_hits[:3])}")

    notes_blob = " ".join(
        filter(
            None,
            [
                intake.additional_notes or "",
                intake.timeline or "",
                intake.origin_country or "",
            ],
        )
    )
    if notes_blob:
        exam_hits = [kw.upper() for kw in EXAM_KEYWORDS if kw in normalize_text(notes_blob)]
        spec_hits = token_hits(search_blob, meaningful_tokens(notes_blob))
        if exam_hits:
            score += min(4, len(exam_hits))
        if spec_hits:
            score += min(6, len(spec_hits) * 2)
            if lang == "fa":
                reasons.append(f"هم‌خوانی با توضیحات شما: {', '.join(spec_hits[:2])}")
            else:
                reasons.append(f"Matches your notes: {', '.join(spec_hits[:2])}")

    if intake.current_status.value == "working" and mentor.get("work_experience"):
        score += 3
        if lang == "fa":
            reasons.append("سابقه کاری قابل استفاده برای وضعیت شغلی شما")
        else:
            reasons.append("Work experience relevant for working professionals")

    return ScoredMentor(
        mentor=mentor,
        score=score,
        reasons=reasons,
        field_match_level=field_fit.level,
    )


def match_mentors(intake: StudentIntake, *, lang: str = "fa", limit: int = 5) -> tuple[list[MentorMatch], int, int]:
    mentors = load_mentors(lang)
    total = len(mentors)
    scored: list[ScoredMentor] = []

    for mentor in mentors:
        result = score_mentor(mentor, intake, lang)
        if result:
            scored.append(result)

    scored.sort(key=lambda item: (-item.score, item.mentor.get("card_index", 9999)))

    matches: list[MentorMatch] = []
    for item in scored[:limit]:
        m = item.mentor
        matches.append(
            MentorMatch(
                id=m["id"],
                name=mentor_display_name(m, lang),
                name_en=m.get("name_en") or m.get("name", ""),
                current_country_en=m.get("current_country_en", ""),
                current_city=m.get("current_city", ""),
                degree_level=m.get("degree_level", ""),
                fields=m.get("fields", []),
                specializations=m.get("specializations", []),
                profile_url=mentor_profile_url(m, lang),
                score=round(item.score, 1),
                field_match_level=item.field_match_level,
                match_reasons=item.reasons,
            )
        )

    return matches, total, len(scored)
