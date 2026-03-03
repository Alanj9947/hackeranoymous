"""
LLM service for generating conversational responses (OpenAI GPT-4).
"""

from __future__ import annotations

from typing import List, Optional

import openai

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

_client = None


def _get_client() -> openai.AsyncOpenAI:
    global _client
    if _client is None:
        _client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


async def get_llm_response(
    system_prompt: str,
    conversation_history: List[dict],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 300,
) -> str:
    """
    Get a conversational response from the LLM.
    Used for real-time voice conversation.
    """
    try:
        client = _get_client()

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history[-20:])  # Keep last 20 turns for context

        response = await client.chat.completions.create(
            model=model or settings.OPENAI_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )

        content = response.choices[0].message.content
        logger.debug("llm_response", length=len(content) if content else 0)
        return content or ""

    except Exception as e:
        logger.error("llm_error", error=str(e))
        return "I apologize, I'm having a moment. Could you repeat that?"


async def extract_data_with_openai(
    transcript: str,
    extraction_prompt: str,
    fields: dict,
    model: str = "gpt-4",
) -> dict:
    """
    Use OpenAI GPT-4 for data extraction (fallback when custom server is down).
    """
    try:
        client = _get_client()
        import json

        prompt = f"""{extraction_prompt}

TRANSCRIPT:
{transcript}

EXTRACTION INSTRUCTIONS:
{json.dumps(fields, indent=2)}

Return ONLY valid JSON matching the requested fields. No markdown, no explanation."""

        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise data extraction assistant. Return only valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=2000,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        return json.loads(content)

    except Exception as e:
        logger.error("openai_extraction_error", error=str(e))
        return {"error": str(e)}
