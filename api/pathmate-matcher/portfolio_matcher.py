"""Rule-based UK/international programme portfolio matcher (Phase B)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from field_matching import FieldFit, assess_field_fit, normalize_text, resolve_canonical_field
from portfolio_db import fetch_programme_rows
from schemas.intake import GpaScale, StudentIntake
from schemas.portfolio import PortfolioBuckets, PortfolioMatchResponse, ProgrammeMatch

REPO_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = REPO_ROOT / "data" / "university-portfolio" / "cache"
GLOBAL_CACHE_PATH = CACHE_DIR / "portfolio_global_msc.json"
LEGACY_CACHE_PATH = CACHE_DIR / "portfolio_gb_msc.json"

COUNTRY_ALIASES = {
    "united kingdom": "GB",
    "uk": "GB",
    "england": "GB",
    "great britain": "GB",
    "انگلیس": "GB",
    "britain": "GB",
    "germany": "DE",
    "deutschland": "DE",
    "آلمان": "DE",
    "canada": "CA",
    "کانادا": "CA",
    "australia": "AU",
    "استرالیا": "AU",
    "united states": "US",
    "usa": "US",
    "آمریکا": "US",
    "spain": "ES",
    "اسپانیا": "ES",
    "italy": "IT",
    "ایتالیا": "IT",
    "netherlands": "NL",
    "holland": "NL",
    "هلند": "NL",
}


def gpa_on_20(intake: StudentIntake) -> Optional[float]:
    if intake.gpa is None:
        return None
    scale = intake.gpa_scale
    if scale == GpaScale.SCALE_20 or scale is None:
        return float(intake.gpa)
    if scale == GpaScale.SCALE_4:
        return float(intake.gpa) / 4.0 * 20.0
    if scale == GpaScale.SCALE_100:
        return float(intake.gpa) / 100.0 * 20.0
    return float(intake.gpa)


def destination_country_codes(intake: StudentIntake) -> set[str]:
    codes: set[str] = set()
    for country in intake.destination_countries:
        key = normalize_text(country)
        if key in COUNTRY_ALIASES:
            codes.add(COUNTRY_ALIASES[key])
        elif len(country.strip()) == 2:
            codes.add(country.strip().upper())
    return codes


def _load_json_cache(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("programmes", [])


def load_programmes() -> tuple[list[dict[str, Any]], str]:
    rows = fetch_programme_rows()
    if rows:
        return rows, "postgres"
    if GLOBAL_CACHE_PATH.exists():
        return _load_json_cache(GLOBAL_CACHE_PATH), "json_cache_global"
    if LEGACY_CACHE_PATH.exists():
        return _load_json_cache(LEGACY_CACHE_PATH), "json_cache_gb"
    return [], "none"


def category_field_fit(user_field: str, leapto_category: str) -> FieldFit:
    return assess_field_fit(
        user_field,
        {"fields": [leapto_category], "specializations": [], "search_text": ""},
    )


def programme_field_matches(intake_field: str, leapto_category: Optional[str]) -> bool:
    if not leapto_category:
        return True
    canonical = resolve_canonical_field(intake_field)
    if normalize_text(canonical) == normalize_text(leapto_category):
        return True
    fit = category_field_fit(intake_field, leapto_category)
    return fit.level in ("exact", "alias", "close", "specialization", "token")


def passes_hard_filters(row: dict[str, Any], intake: StudentIntake) -> bool:
    dest_codes = destination_country_codes(intake)
    if dest_codes and row.get("country_code") not in dest_codes:
        return False
    if intake.target_degree.value != row.get("degree_level"):
        return False
    if not programme_field_matches(intake.field_of_study, row.get("leapto_category")):
        return False

    min_ielts = row.get("min_ielts_overall")
    if intake.ielts_overall is not None and min_ielts is not None:
        if float(intake.ielts_overall) < float(min_ielts):
            return False

    gpa20 = gpa_on_20(intake)
    min_gpa20 = row.get("min_gpa_20")
    if gpa20 is not None and min_gpa20 is not None:
        if gpa20 < float(min_gpa20):
            return False

    tuition = row.get("tuition_amount")
    if intake.budget_max_yearly is not None and tuition is not None:
        if float(tuition) > float(intake.budget_max_yearly):
            return False

    return True


def prestige_score(ranking_band: Optional[str]) -> float:
    return {"top100": 3.0, "top200": 2.0}.get(ranking_band or "", 1.0)


def margin_score(row: dict[str, Any], intake: StudentIntake) -> float:
    gpa20 = gpa_on_20(intake)
    min_gpa20 = float(row.get("min_gpa_20") or 14.0)
    gpa_gap = (gpa20 - min_gpa20) if gpa20 is not None else 1.0

    ielts = float(intake.ielts_overall) if intake.ielts_overall is not None else None
    min_ielts = float(row.get("min_ielts_overall") or 6.5)
    ielts_gap = (ielts - min_ielts) if ielts is not None else 0.5

    return gpa_gap * 0.35 + ielts_gap * 2.0


def assign_bucket(row: dict[str, Any], intake: StudentIntake, margin: float) -> str:
    prestige = prestige_score(row.get("ranking_band"))
    if prestige >= 3.0 and margin < 2.0:
        return "reach"
    if margin >= 3.0:
        return "safety"
    if prestige <= 1.5 and margin >= 1.5:
        return "safety"
    return "match"


def build_reasons(row: dict[str, Any], intake: StudentIntake, bucket: str, lang: str) -> list[str]:
    fa = lang == "fa"
    reasons: list[str] = []
    country = row.get("country_en", "")
    uni = row.get("university_en", "")
    title = row.get("programme_title", "")

    if fa:
        reasons.append(f"{title} در {uni} ({country})")
        if row.get("min_ielts_overall") is not None:
            reasons.append(f"حداقل آیلتس: {row['min_ielts_overall']}")
        if row.get("tuition_amount") is not None:
            reasons.append(f"شهریه تقریبی: £{int(row['tuition_amount']):,}")
        if bucket == "reach":
            reasons.append("سطح رقابتی بالاتر — گزینه reach")
        elif bucket == "safety":
            reasons.append("نیازمندی‌ها با پروفایل شما فاصله مناسب دارد — گزینه safety")
        else:
            reasons.append("تطابق خوب با پروفایل — گزینه match")
    else:
        reasons.append(f"{title} at {uni} ({country})")
        if row.get("min_ielts_overall") is not None:
            reasons.append(f"Min IELTS: {row['min_ielts_overall']}")
        if row.get("tuition_amount") is not None:
            reasons.append(f"Approx. tuition: £{int(row['tuition_amount']):,}")
        reasons.append(f"Bucket: {bucket}")
    return reasons


def score_programme(row: dict[str, Any], intake: StudentIntake) -> float:
    margin = margin_score(row, intake)
    prestige = prestige_score(row.get("ranking_band"))
    fit = category_field_fit(intake.field_of_study, row.get("leapto_category") or "")
    field_points = {"exact": 30, "alias": 28, "close": 24, "specialization": 20, "token": 15, "weak": 8}.get(
        fit.level, 5
    )
    return field_points + margin * 4 + prestige * 3


def match_portfolio(
    intake: StudentIntake,
    lang: str = "fa",
    limit_per_bucket: int = 5,
) -> PortfolioMatchResponse:
    rows, source = load_programmes()
    if not rows:
        raise FileNotFoundError(
            "Portfolio dataset missing. Run Phase B setup: "
            "data/university-portfolio/scripts/setup_phase_b.sh"
        )

    eligible: list[tuple[str, ProgrammeMatch]] = []
    for row in rows:
        if not passes_hard_filters(row, intake):
            continue
        margin = margin_score(row, intake)
        bucket = assign_bucket(row, intake, margin)
        score = score_programme(row, intake)
        eligible.append(
            (
                bucket,
                ProgrammeMatch(
                    programme_id=int(row["programme_id"]),
                    university_en=row.get("university_en", ""),
                    city_en=row.get("city_en") or "",
                    ranking_band=row.get("ranking_band") or "",
                    programme_title=row.get("programme_title", ""),
                    country_en=row.get("country_en", ""),
                    field_tag_en=row.get("field_tag_en") or "",
                    leapto_category=row.get("leapto_category") or "",
                    degree_level=row.get("degree_level", ""),
                    tuition_amount=row.get("tuition_amount"),
                    currency=row.get("currency") or "GBP",
                    living_cost_estimate=row.get("living_cost_estimate"),
                    min_ielts_overall=row.get("min_ielts_overall"),
                    min_gpa_20=row.get("min_gpa_20"),
                    programme_url=row.get("programme_url", ""),
                    start_term=row.get("start_term"),
                    application_deadline=row.get("application_deadline"),
                    requirements_confidence=row.get("requirements_confidence") or "medium",
                    bucket=bucket,  # type: ignore[arg-type]
                    score=round(score, 1),
                    match_reasons=build_reasons(row, intake, bucket, lang),
                ),
            )
        )

    buckets = PortfolioBuckets()
    for bucket_name in ("reach", "match", "safety"):
        items = [pm for b, pm in eligible if b == bucket_name]
        items.sort(key=lambda x: x.score, reverse=True)
        setattr(buckets, bucket_name, items[:limit_per_bucket])

    return PortfolioMatchResponse(
        intake=intake,
        buckets=buckets,
        total_candidates=len(rows),
        total_eligible=len(eligible),
        data_source=source,
    )
