"""Portfolio match request/response models."""

from __future__ import annotations

from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field

from schemas.intake import StudentIntake

BucketName = Literal["reach", "match", "safety"]


class PortfolioMatchRequest(BaseModel):
    intake: StudentIntake
    language: Annotated[str, Field(default="fa", pattern="^(fa|en)$")] = "fa"
    limit_per_bucket: Annotated[int, Field(default=5, ge=1, le=10)] = 5


class ProgrammeMatch(BaseModel):
    programme_id: int
    university_en: str
    city_en: str = ""
    ranking_band: str = ""
    programme_title: str
    country_en: str
    field_tag_en: str = ""
    leapto_category: str = ""
    degree_level: str
    tuition_amount: Optional[float] = None
    currency: str = "GBP"
    living_cost_estimate: Optional[float] = None
    min_ielts_overall: Optional[float] = None
    min_gpa_20: Optional[float] = None
    programme_url: str
    start_term: Optional[str] = None
    application_deadline: Optional[str] = None
    requirements_confidence: str = "medium"
    bucket: BucketName
    score: float
    match_reasons: list[str] = Field(default_factory=list)


class PortfolioBuckets(BaseModel):
    reach: list[ProgrammeMatch] = Field(default_factory=list)
    match: list[ProgrammeMatch] = Field(default_factory=list)
    safety: list[ProgrammeMatch] = Field(default_factory=list)


class PortfolioMatchResponse(BaseModel):
    intake: StudentIntake
    buckets: PortfolioBuckets
    total_candidates: int
    total_eligible: int
    data_source: str = Field(description="postgres or json_cache")
