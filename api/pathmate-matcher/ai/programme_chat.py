"""Conversational programme advisor — LLM with grounded retrieval, rules fallback."""

from __future__ import annotations

import json
import re
from typing import Any, Literal

from ai.llm_client import chat_completion, llm_configured
from ai.query_intent import classify_programme_query, off_topic_message
from rag.portfolio_rag import RETRIEVAL_VERSION, retrieve_programmes
from schemas.ai_models import ChatProgrammesRequest, ChatProgrammesResponse, RagProgrammeCitation
from schemas.intake_extract import normalize_text

CHAT_VERSION = "chat-v1.1.0"

_ABSURD_LOCATION = re.compile(r"\bmars\b|moon|jupiter|زمین\s*دیگر", re.I)

SYSTEM_FA = """You are Leapto's study-abroad programme advisor (Persian UI).
You help users find MSc/Master programmes in our database (UK, Germany, Canada, etc.).

Rules:
- Do NOT invent programmes or universities — only cite data returned by search_programmes tool results.
- Do NOT give visa or immigration legal advice.
- If the message is NOT about university programmes, set action=off_topic.
- If the user is vague but on-topic, ask ONE short clarifying question (country, field, IELTS, or budget).
- If you have enough to search, set action=search and fill search_query in English for retrieval.
- Be warm and concise (2-4 sentences when clarifying).

Return ONLY JSON:
{
  "action": "search" | "clarify" | "off_topic",
  "search_query": "optional English query e.g. UK MSc computer science IELTS 6.5",
  "clarify_message": "Persian message if action=clarify",
  "off_topic_message": "Persian message if action=off_topic",
  "assistant_message": "optional Persian intro before listing results (search only)"
}"""

SYSTEM_EN = """You are Leapto's study-abroad programme advisor.
Help users find MSc programmes using our database only.
Do not invent programmes. No visa legal advice.
If not about programmes, action=off_topic. If vague but on-topic, clarify once. Else action=search.

Return ONLY JSON:
{
  "action": "search" | "clarify" | "off_topic",
  "search_query": "English retrieval query",
  "clarify_message": "English if clarify",
  "off_topic_message": "English if off_topic",
  "assistant_message": "optional intro before results"
}"""


def _intake_to_search_query(ctx: dict[str, Any] | None) -> str:
    if not ctx:
        return ""
    parts: list[str] = []
    countries = ctx.get("destination_countries") or ctx.get("countries") or []
    if countries:
        parts.append(" ".join(str(c) for c in countries[:3]))
    field = ctx.get("field_of_study") or ctx.get("field")
    if field:
        parts.append(str(field))
    degree = ctx.get("target_degree") or ctx.get("degree")
    if degree:
        parts.append(str(degree))
    ielts = ctx.get("ielts_overall") or ctx.get("ielts")
    if ielts is not None:
        parts.append(f"IELTS {ielts}")
    notes = ctx.get("additional_notes") or ctx.get("notes")
    if notes:
        parts.append(str(notes)[:200])
    return " ".join(parts).strip()


def _merge_query(user_message: str, search_query: str, intake_context: dict[str, Any] | None) -> str:
    base = search_query.strip() or user_message.strip()
    ctx_q = _intake_to_search_query(intake_context)
    if ctx_q and ctx_q.lower() not in base.lower():
        return f"{base} {ctx_q}".strip()
    return base


def _hits_to_citations(hits: list[dict[str, Any]]) -> list[RagProgrammeCitation]:
    return [
        RagProgrammeCitation(
            programme_id=int(h["programme_id"]),
            university_en=str(h["university_en"]),
            programme_title=str(h["programme_title"]),
            programme_url=h.get("programme_url"),
            tuition_amount=h.get("tuition_amount"),
            currency=h.get("currency"),
            min_ielts_overall=h.get("min_ielts_overall"),
        )
        for h in hits
    ]


def _uk_count(hits: list[dict[str, Any]]) -> int:
    return sum(1 for h in hits if h.get("country_code") == "GB")


def _format_listing(
    citations: list[RagProgrammeCitation],
    language: str,
    intro: str = "",
    *,
    uk_count: int = 0,
) -> str:
    if language == "fa":
        if not intro:
            if uk_count == len(citations) and uk_count > 0:
                intro = (
                    f"با توجه به شرایط شما، {len(citations)} برنامه در انگلیس پیدا کردم "
                    "(همه از پایگاه Leapto). خلاصه:"
                )
            else:
                intro = (
                    f"{len(citations)} گزینه از پایگاه Leapto پیدا شد. "
                    "چند مورد مناسب:"
                )
        lines = [intro]
        for i, c in enumerate(citations, 1):
            fee = f" — شهریه حدود {c.tuition_amount:,.0f} {c.currency}" if c.tuition_amount else ""
            ielts = f" — حداقل آیلتس {c.min_ielts_overall}" if c.min_ielts_overall else ""
            lines.append(f"{i}. {c.programme_title}، {c.university_en}{ielts}{fee}")
        lines.append(
            "اگر محدودیت بودجه یا آیلتس دارید بگویید تا دقیق‌تر فیلتر کنم. "
            "جزئیات رسمی را در لینک هر برنامه بررسی کنید."
        )
    else:
        if not intro:
            intro = f"I found {len(citations)} programmes in the Leapto database that may fit:"
        lines = [intro]
        for i, c in enumerate(citations, 1):
            fee = f" — tuition ~{c.tuition_amount:,.0f} {c.currency}" if c.tuition_amount else ""
            ielts = f" — min IELTS {c.min_ielts_overall}" if c.min_ielts_overall else ""
            lines.append(f"{i}. {c.programme_title}, {c.university_en}{ielts}{fee}")
        lines.append("Share budget or IELTS constraints to narrow further. Verify on each official link.")
    return "\n".join(lines)


def _rules_clarify(language: str, intake_context: dict[str, Any] | None) -> str:
    missing: list[str] = []
    ctx = intake_context or {}
    if not (ctx.get("destination_countries") or ctx.get("countries")):
        missing.append("کشور مقصد" if language == "fa" else "destination country")
    if not (ctx.get("field_of_study") or ctx.get("field")):
        missing.append("رشته" if language == "fa" else "field of study")
    if ctx.get("ielts_overall") is None and ctx.get("ielts") is None:
        missing.append("آیلتس" if language == "fa" else "IELTS score")

    if language == "fa":
        if missing:
            return (
                "حتماً — برای پیدا کردن دوره مناسب در پایگاه Leapto، "
                + "، ".join(missing)
                + " را بگویید. مثال: «ارشد کامپیوتر انگلیس، آیلتس ۶.۵، بودجه تا ۳۰ هزار پوند»."
            )
        return (
            "لطفاً سوالتان را مشخص‌تر کنید — کشور، رشته، بودجه یا آیلتس. "
            "مثلاً: «MSc Data Science در UK زیر ۲۵ هزار پوند»."
        )
    if missing:
        return (
            "Happy to help — please share your "
            + ", ".join(missing)
            + ". Example: UK MSc Computer Science, IELTS 6.5."
        )
    return "Please specify country, field, budget, or IELTS — e.g. UK MSc Data Science under £25k."


def _llm_plan(request: ChatProgrammesRequest) -> dict[str, Any]:
    system = SYSTEM_FA if request.language == "fa" else SYSTEM_EN
    history_lines = []
    for m in request.history[-8:]:
        history_lines.append(f"{m.role}: {m.content}")
    ctx = json.dumps(request.intake_context or {}, ensure_ascii=False)
    user_block = (
        f"Conversation:\n" + "\n".join(history_lines) + f"\n\nLatest user message: {request.message}\n"
        f"Known intake context (may be partial): {ctx}"
    )
    raw = chat_completion(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user_block},
        ],
        temperature=0.2,
        json_mode=True,
    )
    return json.loads(raw)


def _off_topic_response(request: ChatProgrammesRequest, llm_used: bool, plan: dict[str, Any] | None) -> ChatProgrammesResponse:
    msg = off_topic_message(request.language)
    if plan and plan.get("off_topic_message"):
        msg = str(plan["off_topic_message"])
    return ChatProgrammesResponse(
        answer=msg,
        abstain=True,
        citations=[],
        action="off_topic",
        llm_used=llm_used,
        retrieval_version=RETRIEVAL_VERSION,
        programmes_considered=0,
        chat_version=CHAT_VERSION,
    )


def chat_programmes(request: ChatProgrammesRequest) -> ChatProgrammesResponse:
    llm_used = False
    intent = classify_programme_query(request.message, request.language, request.intake_context)

    if intent == "off_topic":
        return _off_topic_response(request, False, None)

    merged_intake_query = _intake_to_search_query(request.intake_context)

    # Short on-topic follow-up — use wizard intake
    if len(request.message.strip()) < 20 and merged_intake_query and intent == "programme":
        hits, total = retrieve_programmes(merged_intake_query, request.max_results)
        if hits:
            citations = _hits_to_citations(hits)
            intro = (
                "با توجه به اطلاعاتی که قبلاً دادید، این برنامه‌ها را پیشنهاد می‌دهم:"
                if request.language == "fa"
                else "Based on your profile, these programmes may fit:"
            )
            return ChatProgrammesResponse(
                answer=_format_listing(
                    citations,
                    request.language,
                    intro,
                    uk_count=_uk_count(hits),
                ),
                abstain=False,
                citations=citations,
                action="search",
                llm_used=False,
                retrieval_version=RETRIEVAL_VERSION,
                programmes_considered=total,
                chat_version=CHAT_VERSION,
            )

    plan: dict[str, Any] | None = None
    if llm_configured():
        try:
            plan = _llm_plan(request)
            llm_used = True
            if plan.get("action") == "off_topic":
                return _off_topic_response(request, llm_used, plan)
        except Exception:  # noqa: BLE001
            plan = None
            llm_used = False

    if plan and plan.get("action") == "clarify":
        msg = str(plan.get("clarify_message") or _rules_clarify(request.language, request.intake_context))
        return ChatProgrammesResponse(
            answer=msg,
            abstain=False,
            citations=[],
            action="clarify",
            llm_used=llm_used,
            retrieval_version=RETRIEVAL_VERSION,
            programmes_considered=0,
            chat_version=CHAT_VERSION,
        )

    search_query = ""
    intro = ""
    if plan and plan.get("action") == "search":
        search_query = str(plan.get("search_query") or "")
        intro = str(plan.get("assistant_message") or "").strip()
    if not search_query:
        search_query = request.message

    query = _merge_query(request.message, search_query, request.intake_context)
    hits, total = retrieve_programmes(query, request.max_results)

    if not hits and merged_intake_query and merged_intake_query != query:
        hits, total = retrieve_programmes(merged_intake_query, request.max_results)

    if not hits:
        combined = normalize_text(f"{request.message} {query}")
        if _ABSURD_LOCATION.search(combined):
            msg = (
                "پایگاه Leapto فقط برنامه‌های دانشگاهی در کشورهای واقعی (انگلیس، آلمان، کانادا و …) را پوشش می‌دهد — "
                "نه مقاصد خارج از زمین!"
                if request.language == "fa"
                else "The Leapto database covers real-world university destinations (UK, Germany, Canada, etc.) — not other planets."
            )
            return ChatProgrammesResponse(
                answer=msg,
                abstain=True,
                citations=[],
                action="off_topic",
                llm_used=llm_used,
                retrieval_version=RETRIEVAL_VERSION,
                programmes_considered=total,
                chat_version=CHAT_VERSION,
            )
        if intent == "off_topic":
            return _off_topic_response(request, llm_used, plan)
        msg = _rules_clarify(request.language, request.intake_context)
        if llm_used and plan:
            msg = str(plan.get("clarify_message") or msg)
        return ChatProgrammesResponse(
            answer=msg,
            abstain=False,
            citations=[],
            action="clarify",
            llm_used=llm_used,
            retrieval_version=RETRIEVAL_VERSION,
            programmes_considered=total,
            chat_version=CHAT_VERSION,
        )

    citations = _hits_to_citations(hits)
    answer = _format_listing(citations, request.language, intro, uk_count=_uk_count(hits))

    if llm_used and llm_configured():
        try:
            facts = json.dumps([c.model_dump() for c in citations], ensure_ascii=False)
            polish_sys = (
                "Rewrite as a warm Persian programme advisor using ONLY these facts. "
                "Do not add programmes. Keep numbered list. End with one sentence inviting budget/IELTS follow-up. "
                'JSON: {"answer": "..."}'
                if request.language == "fa"
                else "Rewrite warmly in English using ONLY these facts. JSON: {\"answer\": \"...\"}"
            )
            polished = chat_completion(
                [
                    {"role": "system", "content": polish_sys},
                    {"role": "user", "content": f"Facts: {facts}\nDraft:\n{answer}"},
                ],
                temperature=0.3,
                json_mode=True,
            )
            answer = json.loads(polished).get("answer") or answer
        except Exception:  # noqa: BLE001
            pass

    return ChatProgrammesResponse(
        answer=answer,
        abstain=False,
        citations=citations,
        action="search",
        llm_used=llm_used,
        retrieval_version=RETRIEVAL_VERSION,
        programmes_considered=total,
        chat_version=CHAT_VERSION,
    )
