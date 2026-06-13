"""Grounded programme RAG — retrieve from portfolio corpus, answer with citations."""

from __future__ import annotations

import re
from typing import Any

from portfolio_matcher import load_programmes
from schemas.ai_models import RagProgrammeCitation, RagRequest, RagResponse
from schemas.intake_extract import normalize_text

RETRIEVAL_VERSION = "rag-rules-v1.0.0"


def _parse_ielts_cap(question: str) -> float | None:
    n = normalize_text(question)
    m = re.search(r"(?:ielts|آیلتس)\s*[:：]?\s*(\d+(?:\.\d+)?)", n)
    if m:
        return float(m.group(1))
    m = re.search(r"(\d+(?:\.\d+)?)\s*ielts", n)
    return float(m.group(1)) if m else None


def _parse_budget_cap(question: str) -> float | None:
    n = normalize_text(question)
    m = re.search(r"£\s*(\d[\d,]*)", question)
    if m:
        return float(m.group(1).replace(",", ""))
    m = re.search(r"(\d[\d,]*)\s*(?:gbp|pound|پوند)", n)
    if m:
        return float(m.group(1).replace(",", ""))
    m = re.search(r"under\s*(\d[\d,]*)", n)
    if m:
        return float(m.group(1).replace(",", ""))
    return None


def _detect_country_filters(question: str) -> set[str]:
    n = normalize_text(question)
    codes: set[str] = set()
    mapping = [
        (r"uk|united kingdom|england|britain|انگلیس|انگستان", "GB"),
        (r"germany|deutschland|آلمان", "DE"),
        (r"canada|کانادا", "CA"),
        (r"australia|استرالیا", "AU"),
        (r"united states|\busa\b|\bus\b|آمریکا", "US"),
        (r"spain|españa|اسپانیا", "ES"),
        (r"italy|italia|ایتالیا", "IT"),
        (r"netherlands|holland|هلند", "NL"),
    ]
    for pattern, code in mapping:
        if re.search(pattern, n):
            codes.add(code)
    return codes


def _field_keywords(question: str) -> list[str]:
    n = normalize_text(question)
    keys: list[str] = []
    if re.search(r"computer|cs\b|software|data science|ai\b|هوش مصنوعی|کامپیوتر|نرم.?افزار|داده", n):
        keys.extend(["cs", "computer", "data science", "artificial intelligence", "software"])
    if re.search(r"business|mba|management|مدیریت|کسب.?و.?کار", n):
        keys.extend(["business", "management", "mba"])
    if re.search(r"engineering|مهندسی", n):
        keys.extend(["engineering"])
    if re.search(r"finance|اقتصاد|مالی", n):
        keys.extend(["finance", "economics"])
    return keys


def _score_row(row: dict[str, Any], question: str, ielts_cap: float | None, budget_cap: float | None) -> float:
    score = 0.0
    n = normalize_text(question)
    title = normalize_text(str(row.get("programme_title", "")))
    field = normalize_text(str(row.get("field_tag_en", "")))
    category = normalize_text(str(row.get("leapto_category", "")))

    for kw in _field_keywords(question):
        if kw in title or kw in field or kw in category:
            score += 2.0

    min_ielts = row.get("min_ielts_overall")
    if ielts_cap is not None and min_ielts is not None:
        if float(min_ielts) <= ielts_cap + 0.5:
            score += 3.0
        else:
            score -= 5.0

    tuition = row.get("tuition_amount")
    if budget_cap is not None and tuition is not None:
        if float(tuition) <= budget_cap:
            score += 3.0
        else:
            score -= 4.0

    country_codes = _detect_country_filters(question)
    if country_codes and row.get("country_code") in country_codes:
        score += 2.0

    if re.search(r"msc|master|ارشد", n) and row.get("degree_level") == "Master":
        score += 1.0

    return score


def retrieve_programmes(question: str, max_results: int = 5) -> tuple[list[dict[str, Any]], int]:
    rows, _source = load_programmes()
    if not rows:
        return [], 0

    n = normalize_text(question)
    if re.search(r"\bmars\b|moon|jupiter|زمین\s*دیگر", n):
        return [], len(rows)

    ielts_cap = _parse_ielts_cap(question)
    budget_cap = _parse_budget_cap(question)
    field_keys = _field_keywords(question)

    country_codes = _detect_country_filters(question)
    has_domain_signal = (
        bool(field_keys) or bool(country_codes) or ielts_cap is not None or budget_cap is not None
    )
    if not has_domain_signal:
        return [], len(rows)

    scored = [( _score_row(r, question, ielts_cap, budget_cap), r) for r in rows]
    min_score = 1.0 if (field_keys or country_codes) else 2.0
    scored = [(s, r) for s, r in scored if s >= min_score]
    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored:
        return [], len(rows)

    return [r for _, r in scored[:max_results]], len(rows)


def answer_programme_question(request: RagRequest) -> RagResponse:
    """Legacy RAG endpoint — delegates to conversational programme chat."""
    from ai.programme_chat import chat_programmes
    from schemas.ai_models import ChatProgrammesRequest

    chat_resp = chat_programmes(
        ChatProgrammesRequest(
            message=request.question,
            language=request.language,
            max_results=request.max_results,
        )
    )
    return RagResponse(
        answer=chat_resp.answer,
        abstain=chat_resp.abstain,
        citations=chat_resp.citations,
        retrieval_version=chat_resp.retrieval_version,
        programmes_considered=chat_resp.programmes_considered,
    )
