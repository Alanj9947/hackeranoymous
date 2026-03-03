"""
LLM service for generating conversational responses.
Supports OpenAI GPT-4 and Ollama via custom VPS server.
"""

from __future__ import annotations

from typing import List, Optional

import httpx
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


async def _get_custom_server_config():
    """Return the company-default custom server config if one is configured and enabled."""
    try:
        from app.core.database import async_session_factory
        from app.models.custom_server import CustomServerConfig
        from app.core.security import decrypt_value
        from sqlalchemy import select

        async with async_session_factory() as db:
            result = await db.execute(
                select(CustomServerConfig).where(
                    CustomServerConfig.enabled == True,  # noqa: E712
                    CustomServerConfig.agent_id == None,  # noqa: E711
                )
            )
            config = result.scalar_one_or_none()
            if config and config.endpoint:
                return {
                    "endpoint": config.endpoint.rstrip("/"),
                    "api_key": decrypt_value(config.api_key_encrypted) if config.api_key_encrypted else "",
                    "model_name": config.model_name or "llama3.1:8b",
                    "timeout": config.timeout_seconds or 120,
                }
    except Exception as e:
        logger.debug("custom_server_config_unavailable", error=str(e))
    return None


async def _custom_server_chat(
    endpoint: str,
    api_key: str,
    model_name: str,
    timeout: int,
    messages: List[dict],
    temperature: float,
    max_tokens: int,
) -> str:
    """Call the custom VPS AI server's /chat endpoint."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            f"{endpoint}/chat",
            json={
                "messages": messages,
                "model": model_name,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        data = response.json()
        return data.get("content", "")


async def get_llm_response(
    system_prompt: str,
    conversation_history: List[dict],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 300,
) -> str:
    """
    Get a conversational response from the LLM.
    Uses custom VPS Ollama server if configured, otherwise falls back to OpenAI.
    """
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history[-20:])  # Keep last 20 turns for context

    # Try custom VPS server (Ollama) first
    custom_config = await _get_custom_server_config()
    if custom_config:
        try:
            content = await _custom_server_chat(
                endpoint=custom_config["endpoint"],
                api_key=custom_config["api_key"],
                model_name=model or custom_config["model_name"],
                timeout=custom_config["timeout"],
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if content:
                logger.debug("llm_response_from_custom_server", length=len(content))
                return content
        except Exception as e:
            logger.warning("custom_server_llm_failed_falling_back", error=str(e))

    # Fallback to OpenAI
    try:
        client = _get_client()
        response = await client.chat.completions.create(
            model=model or settings.OPENAI_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )
        content = response.choices[0].message.content
        logger.debug("llm_response_from_openai", length=len(content) if content else 0)
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
