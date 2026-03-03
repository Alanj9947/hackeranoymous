"""
Data Extraction Service.
Orchestrates extraction pipeline: custom server → fallback → store.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.custom_server import CustomServerClient, CustomServerError
from app.core.logging import get_logger
from app.models.agent import Agent
from app.models.call import Call, CallTranscript
from app.models.custom_server import CustomServerConfig
from app.models.extraction import DataExtractionJob, ExtractedCallData
from app.services.voice.llm import extract_data_with_openai

logger = get_logger(__name__)


class DataExtractionService:
    """Handles the full data extraction pipeline for completed calls."""

    async def process_extraction(self, job_id: str, db: AsyncSession) -> None:
        """Process a data extraction job."""
        # Load job
        result = await db.execute(
            select(DataExtractionJob).where(DataExtractionJob.id == UUID(job_id))
        )
        job = result.scalar_one_or_none()
        if not job:
            logger.error("extraction_job_not_found", job_id=job_id)
            return

        job.status = "processing"
        job.started_at = datetime.now(timezone.utc).isoformat()
        await db.flush()

        try:
            # Load call + transcript + agent
            call_result = await db.execute(select(Call).where(Call.id == job.call_id))
            call = call_result.scalar_one()

            transcript_result = await db.execute(
                select(CallTranscript).where(CallTranscript.call_id == job.call_id)
            )
            transcript = transcript_result.scalar_one_or_none()
            if not transcript:
                raise ValueError("No transcript available for this call")

            agent_result = await db.execute(select(Agent).where(Agent.id == call.agent_id))
            agent = agent_result.scalar_one()

            # Get extraction config from agent
            extraction_config = agent.data_extraction or {}
            if not extraction_config.get("enabled", False):
                logger.info("extraction_disabled", agent_id=str(agent.id))
                job.status = "completed"
                job.completed_at = datetime.now(timezone.utc).isoformat()
                await db.flush()
                return

            extraction_prompt = extraction_config.get(
                "extractionPrompt",
                "Extract customer details, main issue, resolution, and sentiment from this call.",
            )
            fields = extraction_config.get("fieldsToExtract", {})

            # Try custom server first, then fallback
            start_time = time.monotonic()
            extracted_data, method, model = await self._extract_with_fallback(
                transcript=transcript.full_text,
                extraction_prompt=extraction_prompt,
                fields=fields,
                agent_config=extraction_config,
                company_id=job.company_id,
                call_id=str(job.call_id),
                db=db,
            )
            processing_time = int((time.monotonic() - start_time) * 1000)

            # Store extracted data
            extracted = ExtractedCallData(
                call_id=job.call_id,
                agent_id=call.agent_id,
                company_id=job.company_id,
                extraction_method=method,
                model_used=model,
                processing_time_ms=processing_time,
                confidence_score=extracted_data.get("confidence", 0.9),
                extracted_data=extracted_data,
            )
            db.add(extracted)
            await db.flush()

            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc).isoformat()
            job.result_id = extracted.id
            await db.flush()

            logger.info(
                "extraction_completed",
                job_id=job_id,
                method=method,
                model=model,
                time_ms=processing_time,
            )

        except Exception as e:
            logger.error("extraction_failed", job_id=job_id, error=str(e))
            job.status = "failed"
            job.error_message = str(e)
            job.retry_count += 1
            await db.flush()

    async def _extract_with_fallback(
        self,
        transcript: str,
        extraction_prompt: str,
        fields: dict,
        agent_config: dict,
        company_id: UUID,
        call_id: str,
        db: AsyncSession,
    ) -> tuple[dict, str, str]:
        """
        Try custom server first; fall back to OpenAI if enabled.
        Returns (extracted_data, method, model_used).
        """
        custom_server_config = agent_config.get("customServer", {})
        use_custom = custom_server_config.get("enabled", False)

        if use_custom:
            # Load server config
            server_result = await db.execute(
                select(CustomServerConfig).where(
                    CustomServerConfig.company_id == company_id,
                    CustomServerConfig.enabled == True,  # noqa: E712
                )
            )
            server_config = server_result.scalar_one_or_none()

            if server_config and server_config.health_status != "unhealthy":
                try:
                    client = CustomServerClient(server_config)
                    result = await client.extract_data(
                        transcript=transcript,
                        extraction_prompt=extraction_prompt,
                        fields=fields,
                        request_id=call_id,
                    )
                    data = result.get("extracted_data", result)
                    model = result.get("model_used", server_config.model_name or "custom")
                    return data, "custom_server", model
                except CustomServerError as e:
                    logger.warning("custom_server_failed_fallback", error=str(e))

        # Fallback to OpenAI
        fallback = agent_config.get("fallbackToOpenAI", True)
        if fallback or not use_custom:
            data = await extract_data_with_openai(
                transcript=transcript,
                extraction_prompt=extraction_prompt,
                fields=fields,
            )
            return data, "openai", "gpt-4"

        raise ValueError("Custom server failed and fallback is disabled")
