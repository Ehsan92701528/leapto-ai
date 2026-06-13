"""Shared OpenAI-compatible LLM client."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx


def llm_configured() -> bool:
    return bool(os.getenv("LEAPTO_AI_API_KEY", "").strip())


def client_config() -> tuple[str, str, str]:
    api_key = os.environ["LEAPTO_AI_API_KEY"]
    base_url = os.getenv("LEAPTO_AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("LEAPTO_AI_MODEL", "gpt-4o-mini")
    return api_key, base_url, model


def chat_completion(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.3,
    json_mode: bool = False,
    timeout: float = 45.0,
) -> str:
    api_key, base_url, model = client_config()
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    with httpx.Client(timeout=timeout) as client:
        resp = client.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
