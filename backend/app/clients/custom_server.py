"""
HTTP client for the Custom AI Model Server (VPS).
Handles requests, retries, timeouts, and fallback.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

import httpx

from app.core.logging import get_logger
from app.core.security import decrypt_value

logger = get_logger(__name__)


class CustomServerClient:
    """Client for communicating with the custom AI extraction server on VPS."""

    def __init__(self, config):
        """
        config: CustomServerConfig model instance or dict-like with
            endpoint, api_key_encrypted, timeout_seconds, max_retries
        """
        self.endpoint = config.endpoint.rstrip("/")
        self.api_key = decrypt_value(config.api_key_encrypted) if config.api_key_encrypted else ""
        self.timeout = config.timeout_seconds or 120
        self.max_retries = config.max_retries or 2

    async def extract_data(
        self,
        transcript: str,
        extraction_prompt: str,
        fields: Dict[str, str],
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send transcript to the custom AI server for data extraction.
        Returns structured extraction result.
        """
        payload = {
            "transcript": transcript,
            "extraction_prompt": extraction_prompt,
            "fields": fields,
            "request_id": request_id or "",
        }

        last_error = None
        for attempt in range(1, self.max_retries + 2):  # +1 for initial attempt
            try:
                start = time.monotonic()
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.endpoint}/extract-data",
                        json=payload,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                    )
                elapsed_ms = int((time.monotonic() - start) * 1000)

                if response.status_code == 200:
                    result = response.json()
                    logger.info(
                        "custom_server_extraction_success",
                        request_id=request_id,
                        elapsed_ms=elapsed_ms,
                        attempt=attempt,
                    )
                    return result
                else:
                    last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                    logger.warning(
                        "custom_server_extraction_http_error",
                        status=response.status_code,
                        attempt=attempt,
                    )

            except httpx.TimeoutException:
                last_error = f"Timeout after {self.timeout}s"
                logger.warning("custom_server_timeout", attempt=attempt, timeout=self.timeout)
            except httpx.ConnectError as e:
                last_error = f"Connection error: {str(e)}"
                logger.warning("custom_server_connect_error", attempt=attempt, error=str(e))
            except Exception as e:
                last_error = str(e)
                logger.error("custom_server_unexpected_error", attempt=attempt, error=str(e))

            # Exponential backoff between retries
            if attempt <= self.max_retries:
                import asyncio
                delay = 2 ** (attempt - 1)
                await asyncio.sleep(delay)

        raise CustomServerError(f"All {self.max_retries + 1} attempts failed. Last error: {last_error}")

    async def sentiment_analysis(self, transcript: str) -> Dict[str, Any]:
        """Analyze sentiment of a transcript."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.endpoint}/sentiment-analysis",
                    json={"transcript": transcript},
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error("sentiment_analysis_error", error=str(e))
            raise CustomServerError(f"Sentiment analysis failed: {e}")

    async def health(self) -> Dict[str, Any]:
        """Check the health of the custom AI server."""
        try:
            start = time.monotonic()
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.endpoint}/health",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                response.raise_for_status()
                result = response.json()
                result["response_time"] = int((time.monotonic() - start) * 1000)
                return result
        except Exception as e:
            logger.error("health_check_error", endpoint=self.endpoint, error=str(e))
            raise CustomServerError(f"Health check failed: {e}")

    async def batch_extract(
        self, requests: list[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Submit batch extraction job."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout * 2) as client:
                response = await client.post(
                    f"{self.endpoint}/batch-extract",
                    json=requests,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error("batch_extract_error", error=str(e))
            raise CustomServerError(f"Batch extraction failed: {e}")


class CustomServerError(Exception):
    """Raised when communication with the custom AI server fails."""
    pass
