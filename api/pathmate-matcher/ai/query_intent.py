"""Classify programme-chat queries: on-topic search vs off-topic vs needs clarification."""

from __future__ import annotations

import re
from typing import Any, Literal

from schemas.intake_extract import normalize_text

QueryIntent = Literal["programme", "off_topic", "clarify"]

# Exact or near-exact junk / meta messages (Persian + English)
_OFF_TOPIC_EXACT = {
    "پرسیدن",
    "سوال",
    "سؤال",
    "سلام",
    "hello",
    "hi",
    "hey",
    "test",
    "testing",
    "asking",
    "ask",
    "کمک",
    "؟",
    "?",
    "who are you",
    "what is this",
    "thanks",
    "thank you",
    "ممنون",
    "مرسی",
    "چطوری",
    "how are you",
}

_OFF_TOPIC_PATTERNS = [
    re.compile(r"^(سلام|درود)\s*[!.؟?]*$", re.I),
    re.compile(r"^who\s+are\s+you", re.I),
    re.compile(r"^what\s+(is|are)\s+(this|leapto)", re.I),
    re.compile(r"^(tell me a joke|joke)$", re.I),
    re.compile(r"^(weather|forecast)", re.I),
    re.compile(r"^(visa\s+only|only\s+visa)", re.I),
    re.compile(r"^\W+$"),
]

_PROGRAMME_SIGNAL = re.compile(
    r"msc|master|mba|phd|bachelor|"
    r"programme|program|course|degree|university|uni\b|"
    r"tuition|fee|scholarship|"
    r"ielts|toefl|آیلتس|"
    r"computer|software|data\s*science|engineering|business|finance|mba|"
    r"کامپیوتر|مهندسی|مدیریت|ارشد|کارشناسی|دوره|دانشگاه|رشته|"
    r"uk|united kingdom|england|britain|انگلیس|انگستان|"
    r"germany|canada|australia|آلمان|کانادا|استرالیا|"
    r"spain|italy|netherlands|"
    r"£|\€|\$|gbp|eur|pound|پوند|یورو|بودجه|شهریه",
    re.I,
)


def _intake_has_signals(ctx: dict[str, Any] | None) -> bool:
    if not ctx:
        return False
    if ctx.get("destination_countries") or ctx.get("countries"):
        return True
    if ctx.get("field_of_study") or ctx.get("field"):
        return True
    if ctx.get("ielts_overall") is not None or ctx.get("ielts") is not None:
        return True
    return False


def classify_programme_query(
    message: str,
    language: str = "fa",
    intake_context: dict[str, Any] | None = None,
) -> QueryIntent:
    raw = message.strip()
    n = normalize_text(raw)
    if not n:
        return "clarify"

    if n in _OFF_TOPIC_EXACT or raw.strip() in _OFF_TOPIC_EXACT:
        return "off_topic"

    for pat in _OFF_TOPIC_PATTERNS:
        if pat.search(raw.strip()) or pat.search(n):
            return "off_topic"

    if _PROGRAMME_SIGNAL.search(n) or _PROGRAMME_SIGNAL.search(raw):
        return "programme"

    if _intake_has_signals(intake_context):
        # Vague follow-up in an ongoing programme conversation, e.g. "more options"
        if re.search(r"more|بیشتر|دیگر|another|else|گزینه", n):
            return "programme"
        # Short message but we know their profile — treat as search intent
        if len(n) <= 24:
            return "programme"

    # Long text without programme signals — likely off-topic
    if len(n.split()) >= 4 and not _PROGRAMME_SIGNAL.search(n):
        return "off_topic"

    # Very short, no signals, no intake
    if len(n) <= 16:
        return "off_topic"

    return "clarify"


def off_topic_message(language: str) -> str:
    if language == "fa":
        return (
            "به نظر می‌رسد این پیام درباره دوره‌ها یا برنامه‌های تحصیلی نیست.\n"
            "این بخش فقط برای جستجوی MSc و مقایسه برنامه‌های دانشگاهی Leapto است — "
            "مثلاً «ارشد کامپیوتر انگلیس با آیلتس ۶.۵».\n"
            "برای سوالات عمومی درباره مهاجرت، هم‌مسیران یا پشتیبانی، "
            "از چت اصلی «پیدا کردن هم‌مسیر من» یا تماس با پشتیبانی Leapto استفاده کنید."
        )
    return (
        "That message doesn't look like a question about university programmes.\n"
        "This chat is only for searching MSc courses in the Leapto database — "
        "e.g. \"UK MSc Computer Science, IELTS 6.5\".\n"
        "For general immigration, mentor, or support questions, use the main path-mate chat "
        "or contact Leapto support."
    )
