"""Student intake schema for Leapto path-mate and portfolio matching."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TargetDegree(str, Enum):
    BACHELOR = "Bachelor"
    MASTER = "Master"
    PHD = "PhD"


class CurrentStatus(str, Enum):
    STUDENT = "student"
    GRADUATE = "graduate"
    WORKING = "working"


class GpaScale(str, Enum):
    """Scale used for ``gpa`` (Iranian transcripts often use /20)."""

    SCALE_4 = "4.0"
    SCALE_20 = "20"
    SCALE_100 = "100"
    OTHER = "other"


class BudgetCurrency(str, Enum):
    GBP = "GBP"
    USD = "USD"
    EUR = "EUR"
    CAD = "CAD"
    AUD = "AUD"


class StudentIntake(BaseModel):
    """
    Candidate profile collected before path-mate or programme portfolio matching.

    Core fields are required for mentor matching. Academic scores and budget support
    programme hard-filters in ``POST /portfolio/match`` (Phase C).
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    destination_countries: Annotated[
        list[str],
        Field(
            min_length=1,
            max_length=5,
            description="One or more countries where the candidate wants to study or work.",
            json_schema_extra={
                "examples": [["United Kingdom", "Canada"]],
                "ui_label_en": "Where do you want to study/work?",
                "ui_label_fa": "کجا می‌خواهید تحصیل یا کار کنید؟",
            },
        ),
    ]
    field_of_study: Annotated[
        str,
        Field(
            min_length=2,
            max_length=200,
            description=(
                "Primary field of study. Prefer Leapto homepage categories, but free text is "
                "accepted — the matcher will map aliases and close/related fields."
            ),
            json_schema_extra={
                "examples": ["Computer Engineering & Computer Science"],
                "ui_label_en": "Field of study",
                "ui_label_fa": "رشته تحصیلی",
            },
        ),
    ]
    target_degree: Annotated[
        TargetDegree,
        Field(
            description="Degree level the candidate is aiming for.",
            json_schema_extra={
                "ui_label_en": "Target degree",
                "ui_label_fa": "مقطع هدف",
            },
        ),
    ]
    current_status: Annotated[
        CurrentStatus,
        Field(
            description="Current situation of the candidate.",
            json_schema_extra={
                "ui_label_en": "Current status",
                "ui_label_fa": "وضعیت فعلی",
            },
        ),
    ]

    origin_country: Annotated[
        Optional[str],
        Field(
            default=None,
            max_length=100,
            description="Country where the candidate studied or is studying now.",
            json_schema_extra={
                "examples": ["Iran", "India"],
                "ui_label_en": "Origin / current university country (optional)",
                "ui_label_fa": "کشور محل تحصیل فعلی (اختیاری)",
            },
        ),
    ] = None
    languages: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            max_length=10,
            description="Spoken or tested languages, e.g. English, Persian, French.",
            json_schema_extra={
                "examples": [["Persian", "English"]],
                "ui_label_en": "Languages (optional)",
                "ui_label_fa": "زبان‌ها (اختیاری)",
            },
        ),
    ] = None
    timeline: Annotated[
        Optional[str],
        Field(
            default=None,
            max_length=120,
            description="When they plan to apply or start, e.g. 'September 2026' or 'within 12 months'.",
            json_schema_extra={
                "examples": ["September 2026", "within 12 months"],
                "ui_label_en": "Timeline (optional)",
                "ui_label_fa": "زمان‌بندی (اختیاری)",
            },
        ),
    ] = None

    gpa: Annotated[
        Optional[float],
        Field(
            default=None,
            ge=0,
            description="Grade point average on the scale given by ``gpa_scale``.",
            json_schema_extra={
                "examples": [17.0, 3.6],
                "ui_label_en": "GPA",
                "ui_label_fa": "معدل",
            },
        ),
    ] = None
    gpa_scale: Annotated[
        Optional[GpaScale],
        Field(
            default=None,
            description="Scale for ``gpa``: 4.0, 20 (Iran), 100, or other.",
            json_schema_extra={
                "ui_label_en": "GPA scale",
                "ui_label_fa": "مقیاس معدل",
            },
        ),
    ] = None
    ielts_overall: Annotated[
        Optional[float],
        Field(
            default=None,
            ge=0,
            le=9,
            description="IELTS overall band score.",
            json_schema_extra={
                "examples": [7.0],
                "ui_label_en": "IELTS overall",
                "ui_label_fa": "نمره کلی آیلتس",
            },
        ),
    ] = None
    toefl_ibt: Annotated[
        Optional[int],
        Field(
            default=None,
            ge=0,
            le=120,
            description="TOEFL iBT total score.",
            json_schema_extra={"ui_label_en": "TOEFL iBT", "ui_label_fa": "تافل iBT"},
        ),
    ] = None
    gre_total: Annotated[
        Optional[int],
        Field(
            default=None,
            ge=260,
            le=340,
            description="GRE total score (verbal + quantitative).",
            json_schema_extra={"ui_label_en": "GRE total", "ui_label_fa": "GRE"},
        ),
    ] = None
    gmat_score: Annotated[
        Optional[int],
        Field(
            default=None,
            ge=200,
            le=800,
            description="GMAT total score.",
            json_schema_extra={"ui_label_en": "GMAT", "ui_label_fa": "GMAT"},
        ),
    ] = None
    budget_max_yearly: Annotated[
        Optional[float],
        Field(
            default=None,
            ge=0,
            description="Maximum affordable tuition + living cost per year.",
            json_schema_extra={
                "examples": [25000],
                "ui_label_en": "Max budget per year",
                "ui_label_fa": "حداکثر بودجه سالانه",
            },
        ),
    ] = None
    budget_currency: Annotated[
        Optional[BudgetCurrency],
        Field(
            default=None,
            description="Currency for ``budget_max_yearly``.",
            json_schema_extra={"ui_label_en": "Budget currency", "ui_label_fa": "واحد بودجه"},
        ),
    ] = None
    preferred_start: Annotated[
        Optional[str],
        Field(
            default=None,
            max_length=80,
            description="Preferred intake, e.g. 'September 2026'.",
            json_schema_extra={
                "examples": ["September 2026"],
                "ui_label_en": "Preferred start term",
                "ui_label_fa": "ترم شروع مد نظر",
            },
        ),
    ] = None

    additional_notes: Annotated[
        Optional[str],
        Field(
            default=None,
            max_length=2000,
            description=(
                "Free text for anything not covered above: spoken languages, standard exams "
                "(GMAT, GRE, CFA, IELTS, TOEFL, etc.), GPA, budget, or other context."
            ),
            json_schema_extra={
                "ui_label_en": "Describe your situation (2–3 sentences)",
                "ui_label_fa": "وضعیت خود را توضیح دهید (۲–۳ جمله)",
                "ui_placeholder_en": (
                    "Example: GPA 3.6, IELTS 7.0, interested in AI/ML MSc, budget around £25k/year..."
                ),
                "ui_placeholder_fa": (
                    "مثال: معدل ۱۷، آیلتس ۷، علاقه‌مند به کارشناسی ارشد هوش مصنوعی، بودجه حدود ..."
                ),
            },
        ),
    ] = None

    @field_validator("gpa_scale", mode="before")
    @classmethod
    def coerce_gpa_scale(cls, value: object) -> object:
        if value is None or value == "":
            return None
        if value == 20 or value == "20":
            return GpaScale.SCALE_20
        if value in (4, 4.0, "4", "4.0"):
            return GpaScale.SCALE_4
        if value in (100, "100"):
            return GpaScale.SCALE_100
        return value

    @field_validator("destination_countries")
    @classmethod
    def normalize_countries(cls, values: list[str]) -> list[str]:
        cleaned = [v.strip() for v in values if v and v.strip()]
        if not cleaned:
            raise ValueError("At least one destination country is required.")
        seen: set[str] = set()
        unique: list[str] = []
        for value in cleaned:
            key = value.casefold()
            if key not in seen:
                seen.add(key)
                unique.append(value)
        return unique

    @field_validator("languages")
    @classmethod
    def normalize_languages(cls, values: Optional[list[str]]) -> Optional[list[str]]:
        if values is None:
            return None
        cleaned = [v.strip() for v in values if v and v.strip()]
        return cleaned or None

    @field_validator("additional_notes", "preferred_start", "timeline")
    @classmethod
    def normalize_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def validate_gpa_against_scale(self) -> StudentIntake:
        if self.gpa is None:
            return self
        if self.gpa_scale is None:
            return self
        caps = {
            GpaScale.SCALE_4: 4.0,
            GpaScale.SCALE_20: 20.0,
            GpaScale.SCALE_100: 100.0,
        }
        cap = caps.get(self.gpa_scale)
        if cap is not None and self.gpa > cap:
            raise ValueError(f"gpa {self.gpa} exceeds scale maximum {cap} for {self.gpa_scale.value}.")
        return self

    @model_validator(mode="after")
    def default_budget_currency(self) -> StudentIntake:
        if self.budget_max_yearly is not None and self.budget_currency is None:
            self.budget_currency = BudgetCurrency.GBP
        return self


class MatchRequest(BaseModel):
    intake: StudentIntake
    language: Annotated[
        str,
        Field(default="fa", pattern="^(fa|en)$", description="Response language for match reasons."),
    ] = "fa"
    limit: Annotated[int, Field(default=5, ge=1, le=10)] = 5


class MentorMatch(BaseModel):
    id: str
    name: str
    name_en: str = ""
    current_country_en: str = ""
    current_city: str = ""
    degree_level: str = ""
    fields: list[str] = Field(default_factory=list)
    specializations: list[str] = Field(default_factory=list)
    profile_url: str = ""
    score: float
    field_match_level: str = Field(
        default="none",
        description="How the mentor's field relates to the request: exact, alias, close, specialization, token, weak, none",
    )
    match_reasons: list[str] = Field(default_factory=list)


class MatchResponse(BaseModel):
    intake: StudentIntake
    matches: list[MentorMatch]
    total_candidates_considered: int
    total_after_filters: int
