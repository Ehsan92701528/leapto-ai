"""Leapto path-mate matching API."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from matcher import load_options, match_mentors
from portfolio_matcher import match_portfolio
from schemas.intake import MatchRequest, MatchResponse, StudentIntake
from schemas.intake_extract import enrich_intake_from_notes
from schemas.portfolio import PortfolioMatchRequest, PortfolioMatchResponse
from schemas.ai_models import (
    ChatProgrammesRequest,
    ChatProgrammesResponse,
    ExtractRequest,
    ExtractResponse,
    RagRequest,
    RagResponse,
)
from ai.extract_rules import extract_from_text, build_student_intake
from ai.extract_llm import extract_with_llm
from ai.llm_client import llm_configured
from ai.programme_chat import chat_programmes, CHAT_VERSION
from rag.portfolio_rag import answer_programme_question, RETRIEVAL_VERSION
from ai.extract_rules import EXTRACTOR_VERSION

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"

app = FastAPI(
    title="Leapto Path Mate Matcher",
    version="0.4.0",
    description="Path-mate matching, portfolio recommendations, and governed AI extraction/RAG.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/portfolio")
def health_portfolio() -> dict[str, object]:
    from portfolio_matcher import load_programmes

    rows, source = load_programmes()
    return {"status": "ok" if rows else "missing_data", "programmes": len(rows), "source": source}


@app.get("/health/ai")
def health_ai() -> dict[str, object]:
    return {
        "status": "ok",
        "rules_extractor": EXTRACTOR_VERSION,
        "rag_retrieval": RETRIEVAL_VERSION,
        "llm_configured": llm_configured(),
        "programme_chat": CHAT_VERSION,
    }


@app.post("/ai/extract", response_model=ExtractResponse)
def post_ai_extract(request: ExtractRequest) -> ExtractResponse:
    if request.use_llm:
        intake, meta = extract_with_llm(request.text)
        partial = None
    else:
        meta = extract_from_text(request.text)
        intake = None
        partial = meta.get("partial_intake")
        if meta["valid"]:
            intake, _build_meta = build_student_intake(request.text)
            partial = meta.get("partial_intake")

    return ExtractResponse(
        valid=bool(meta.get("valid")),
        reason=meta.get("reason"),
        path_intent=str(meta.get("path_intent", "unclear")),
        intake=intake,
        partial_intake=partial if intake is None else None,
        extractor=str(meta.get("extractor", EXTRACTOR_VERSION)),
        llm_used=bool(meta.get("llm_used", False)),
        confidence=float(meta.get("confidence", 0.0)),
        fallback_reason=meta.get("fallback_reason"),
        budget_focus=bool(meta.get("budget_focus", False)),
        needs_path_clarify=bool(meta.get("needs_path_clarify", False)),
    )


@app.post("/ai/rag/programmes", response_model=RagResponse)
def post_ai_rag_programmes(request: RagRequest) -> RagResponse:
    try:
        return answer_programme_question(request)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/ai/chat/programmes", response_model=ChatProgrammesResponse)
def post_ai_chat_programmes(request: ChatProgrammesRequest) -> ChatProgrammesResponse:
    try:
        return chat_programmes(request)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/options")
def get_form_options(lang: str = "fa") -> dict:
    """Form dropdown/checkbox options aligned with leapto.co.uk filters."""
    options = load_options()
    return {
        "language": lang,
        "destination_countries": options["destination_countries"],
        "fields_of_study": options["fields_of_study"],
        "target_degrees": options["target_degrees"],
        "current_statuses": options["current_statuses"],
        "common_exams_hint": options["common_exams_hint"],
        "intake_schema_url": "/schema/student-intake",
    }


@app.get("/schema/student-intake")
def get_intake_schema() -> dict:
    return StudentIntake.model_json_schema()


@app.post("/match", response_model=MatchResponse)
def post_match(request: MatchRequest) -> MatchResponse:
    intake = enrich_intake_from_notes(request.intake)
    try:
        matches, total, filtered = match_mentors(
            intake,
            lang=request.language,
            limit=request.limit,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=f"Mentor dataset missing: {exc}") from exc

    if not matches:
        return MatchResponse(
            intake=intake,
            matches=[],
            total_candidates_considered=total,
            total_after_filters=filtered,
        )

    return MatchResponse(
        intake=intake,
        matches=matches,
        total_candidates_considered=total,
        total_after_filters=filtered,
    )


@app.post("/portfolio/match", response_model=PortfolioMatchResponse)
def post_portfolio_match(request: PortfolioMatchRequest) -> PortfolioMatchResponse:
    intake = enrich_intake_from_notes(request.intake)
    try:
        result = match_portfolio(
            intake,
            lang=request.language,
            limit_per_bucket=request.limit_per_bucket,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if not (result.buckets.reach or result.buckets.match or result.buckets.safety):
        raise HTTPException(
            status_code=404,
            detail="No programmes matched. Try broadening countries, field, or budget.",
        )
    return result


@app.get("/demo")
def demo_form() -> FileResponse:
    form_path = STATIC_DIR / "intake-form.html"
    if not form_path.exists():
        raise HTTPException(status_code=404, detail="Demo form not found")
    return FileResponse(form_path)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
