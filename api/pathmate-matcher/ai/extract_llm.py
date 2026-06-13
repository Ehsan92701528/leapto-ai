"""Optional LLM extraction — OpenAI-compatible API with schema validation."""

from __future__ import annotations

import json
from typing import Any, Optional

from ai.extract_rules import EXTRACTOR_VERSION, extract_from_text
from ai.llm_client import chat_completion, client_config, llm_configured
from schemas.intake import StudentIntake

LLM_EXTRACTOR_VERSION = "llm-v1.0.0"

SYSTEM_PROMPT = """You extract structured student intake for an international education platform.
Return ONLY valid JSON matching this shape (no markdown):
{
  "destination_countries": ["United Kingdom"],
  "field_of_study": "Computer Engineering & Computer Science",
  "target_degree": "Master",
  "current_status": "student",
  "origin_country": null,
  "gpa": null,
  "gpa_scale": null,
  "ielts_overall": null,
  "path_intent": "study_abroad",
  "additional_notes": "<original user text>"
}
Use English country names from: Germany, United States, Spain, Australia, United Kingdom, Canada, Italy, etc.
path_intent one of: study_abroad, work_abroad, alternatives_to_study, emigration_explore, unclear.
Do NOT provide visa or legal advice. Do NOT invent countries not mentioned."""


def extract_with_llm(text: str) -> tuple[Optional[StudentIntake], dict[str, Any]]:
    """
    Call LLM; validate with Pydantic; fallback to rules on any failure.
    """
    rules_meta = extract_from_text(text)
    if not rules_meta["valid"]:
        return None, {**rules_meta, "llm_used": False, "fallback_reason": "validation_failed"}

    if not llm_configured():
        intake, meta = _from_rules(text, rules_meta)
        return intake, {**meta, "llm_used": False, "fallback_reason": "no_api_key"}

    _, _, model = client_config()

    try:
        content = chat_completion(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0,
            json_mode=True,
        )
        data = json.loads(content)
        intake = StudentIntake.model_validate(data)
        return intake, {
            "valid": True,
            "path_intent": data.get("path_intent", rules_meta["path_intent"]),
            "extractor": LLM_EXTRACTOR_VERSION,
            "llm_used": True,
            "model": model,
            "confidence": 0.85,
            "fallback_reason": None,
        }
    except Exception as exc:  # noqa: BLE001 — fallback path
        intake, meta = _from_rules(text, rules_meta)
        return intake, {
            **meta,
            "llm_used": False,
            "fallback_reason": str(exc)[:200],
        }


def _from_rules(text: str, rules_meta: dict[str, Any]) -> tuple[Optional[StudentIntake], dict[str, Any]]:
    from ai.extract_rules import build_student_intake

    intake, meta = build_student_intake(text)
    return intake, {**meta, "extractor": EXTRACTOR_VERSION, "rules_snapshot": rules_meta}
