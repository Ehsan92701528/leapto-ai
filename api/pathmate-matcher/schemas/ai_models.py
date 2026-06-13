"""API models for Leapto AI endpoints."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from schemas.intake import StudentIntake


class ExtractRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)
    use_llm: bool = False
    language: str = "fa"


class ExtractResponse(BaseModel):
    valid: bool
    reason: Optional[str] = None
    path_intent: str
    intake: Optional[StudentIntake] = None
    partial_intake: Optional[dict[str, Any]] = None
    extractor: str
    llm_used: bool = False
    confidence: float = 0.0
    fallback_reason: Optional[str] = None
    budget_focus: bool = False
    needs_path_clarify: bool = False


class RagProgrammeCitation(BaseModel):
    programme_id: int
    university_en: str
    programme_title: str
    programme_url: Optional[str] = None
    tuition_amount: Optional[float] = None
    currency: Optional[str] = None
    min_ielts_overall: Optional[float] = None


class RagRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    language: str = "fa"
    max_results: int = Field(default=5, ge=1, le=10)


class RagResponse(BaseModel):
    answer: str
    abstain: bool
    citations: list[RagProgrammeCitation]
    retrieval_version: str
    programmes_considered: int


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatProgrammesRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    language: str = "fa"
    max_results: int = Field(default=5, ge=1, le=10)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)
    intake_context: Optional[dict[str, Any]] = None


class ChatProgrammesResponse(BaseModel):
    answer: str
    abstain: bool = False
    citations: list[RagProgrammeCitation]
    action: Literal["search", "clarify", "answer", "off_topic"] = "answer"
    llm_used: bool = False
    retrieval_version: str
    programmes_considered: int
    chat_version: str
