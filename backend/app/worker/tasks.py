"""
Celery tasks for async processing:
- Call initiation
- Post-call processing (transcription, extraction)
- Data exports
- Health checks
- Scheduled exports
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import UUID

from app.worker.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)


def _run_async(coro):
    """Helper to run async code in sync Celery tasks."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ── Call Tasks ───────────────────────────────────────────────────

@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def initiate_outbound_call(self, call_id: str):
    """Initiate an outbound call via Twilio."""
    try:
        from app.services.twilio_service import TwilioService
        from app.core.database import async_session_factory
        from app.models.call import Call
        from sqlalchemy import select

        async def _do():
            async with async_session_factory() as db:
                result = await db.execute(select(Call).where(Call.id == UUID(call_id)))
                call = result.scalar_one_or_none()
                if not call:
                    logger.error("call_not_found", call_id=call_id)
                    return

                twilio = TwilioService()
                call_sid = twilio.initiate_outbound_call(
                    call_id=call_id,
                    to_number=call.to_number,
                    agent_id=str(call.agent_id),
                )
                call.twilio_call_sid = call_sid
                call.status = "ringing"
                call.started_at = datetime.now(timezone.utc).isoformat()
                await db.commit()

        _run_async(_do())
        logger.info("outbound_call_initiated", call_id=call_id)

    except Exception as exc:
        logger.error("outbound_call_failed", call_id=call_id, error=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=10)
def post_call_processing(self, call_id: str):
    """Post-call processing: check transcript, trigger extraction."""
    try:
        from app.core.database import async_session_factory
        from app.models.call import Call, CallTranscript
        from app.models.agent import Agent
        from app.models.extraction import DataExtractionJob
        from sqlalchemy import select

        async def _do():
            async with async_session_factory() as db:
                # Load call
                result = await db.execute(select(Call).where(Call.id == UUID(call_id)))
                call = result.scalar_one_or_none()
                if not call:
                    return

                # Check if transcript exists
                transcript_result = await db.execute(
                    select(CallTranscript).where(CallTranscript.call_id == call.id)
                )
                transcript = transcript_result.scalar_one_or_none()

                if not transcript:
                    logger.info("no_transcript_yet", call_id=call_id)
                    return

                # Check if agent has extraction enabled
                agent_result = await db.execute(select(Agent).where(Agent.id == call.agent_id))
                agent = agent_result.scalar_one_or_none()
                if not agent:
                    return

                extraction_config = agent.data_extraction or {}
                if not extraction_config.get("enabled", False):
                    logger.info("extraction_not_enabled", agent_id=str(agent.id))
                    return

                # Create extraction job
                job = DataExtractionJob(
                    call_id=call.id,
                    company_id=call.company_id,
                    status="queued",
                )
                db.add(job)
                await db.commit()

                # Trigger extraction
                process_extraction.delay(str(job.id))

        _run_async(_do())

    except Exception as exc:
        logger.error("post_call_processing_failed", call_id=call_id, error=str(exc))
        raise self.retry(exc=exc)


# ── Extraction Tasks ────────────────────────────────────────────

@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def process_extraction(self, job_id: str):
    """Process a data extraction job."""
    try:
        from app.core.database import async_session_factory
        from app.services.extraction_service import DataExtractionService

        async def _do():
            async with async_session_factory() as db:
                service = DataExtractionService()
                await service.process_extraction(job_id, db)
                await db.commit()

        _run_async(_do())
        logger.info("extraction_task_completed", job_id=job_id)

    except Exception as exc:
        logger.error("extraction_task_failed", job_id=job_id, error=str(exc))
        raise self.retry(exc=exc)


# ── Export Tasks ─────────────────────────────────────────────────

@celery_app.task(bind=True, max_retries=2, default_retry_delay=10)
def export_to_excel_task(self, history_id: str, call_ids: list, template: str, filename: str | None):
    """Export extracted data to Excel file."""
    try:
        from app.core.database import async_session_factory
        from app.models.extraction import ExtractedCallData
        from app.models.export import ExportHistory
        from app.services.excel_export import ExcelExportService
        from sqlalchemy import select
        import time

        async def _do():
            start = time.monotonic()
            async with async_session_factory() as db:
                # Load extracted data
                result = await db.execute(
                    select(ExtractedCallData).where(
                        ExtractedCallData.call_id.in_([UUID(c) for c in call_ids])
                    )
                )
                extractions = result.scalars().all()

                data_rows = []
                for ext in extractions:
                    row = {
                        "created_at": str(ext.created_at),
                        "confidence_score": ext.confidence_score,
                        "extraction_method": ext.extraction_method,
                        **(ext.extracted_data or {}),
                    }
                    data_rows.append(row)

                # Generate Excel
                service = ExcelExportService()
                filepath = service.export_to_excel(data_rows, template, filename)

                # Update history
                hist_result = await db.execute(
                    select(ExportHistory).where(ExportHistory.id == UUID(history_id))
                )
                history = hist_result.scalar_one()
                history.status = "success"
                history.file_path = filepath
                history.rows_exported = len(data_rows)
                history.duration_ms = int((time.monotonic() - start) * 1000)
                history.completed_at = datetime.now(timezone.utc).isoformat()

                import os
                history.file_size = os.path.getsize(filepath)

                await db.commit()

        _run_async(_do())
        logger.info("excel_export_completed", history_id=history_id)

    except Exception as exc:
        logger.error("excel_export_failed", history_id=history_id, error=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=10)
def export_to_sheets_task(
    self,
    history_id: str,
    call_ids: list,
    spreadsheet_id: str | None,
    template: str,
    share_with: list | None,
):
    """Export extracted data to Google Sheets."""
    try:
        from app.core.database import async_session_factory
        from app.models.extraction import ExtractedCallData
        from app.models.export import ExportHistory
        from app.services.sheets_export import GoogleSheetsExportService
        from sqlalchemy import select
        import time

        async def _do():
            start = time.monotonic()
            async with async_session_factory() as db:
                result = await db.execute(
                    select(ExtractedCallData).where(
                        ExtractedCallData.call_id.in_([UUID(c) for c in call_ids])
                    )
                )
                extractions = result.scalars().all()

                data_rows = []
                for ext in extractions:
                    row = {
                        "created_at": str(ext.created_at),
                        "confidence_score": ext.confidence_score,
                        **(ext.extracted_data or {}),
                    }
                    data_rows.append(row)

                service = GoogleSheetsExportService()
                result_data = service.export_data(spreadsheet_id, data_rows, template)

                # Share if requested
                if share_with:
                    for email in share_with:
                        service.share_spreadsheet(result_data["spreadsheet_id"], email)

                # Update history
                hist_result = await db.execute(
                    select(ExportHistory).where(ExportHistory.id == UUID(history_id))
                )
                history = hist_result.scalar_one()
                history.status = "success"
                history.rows_exported = result_data["rows_added"]
                history.duration_ms = int((time.monotonic() - start) * 1000)
                history.completed_at = datetime.now(timezone.utc).isoformat()
                history.file_path = result_data["spreadsheet_url"]

                await db.commit()

        _run_async(_do())
        logger.info("sheets_export_completed", history_id=history_id)

    except Exception as exc:
        logger.error("sheets_export_failed", history_id=history_id, error=str(exc))
        raise self.retry(exc=exc)


# ── Recording Tasks ──────────────────────────────────────────────

@celery_app.task(bind=True, max_retries=3, default_retry_delay=15)
def upload_recording_to_s3(self, call_id: str, recording_url: str):
    """Download recording from Twilio and upload to S3/MinIO."""
    try:
        import httpx
        import boto3
        from app.core.config import get_settings
        from app.core.database import async_session_factory
        from app.models.call import Call
        from sqlalchemy import select

        settings = get_settings()

        async def _do():
            # Download from Twilio
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.get(recording_url)
                resp.raise_for_status()
                audio_data = resp.content

            # Upload to S3/MinIO
            s3 = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION,
            )
            key = f"recordings/{call_id}.mp3"
            s3.put_object(
                Bucket=settings.S3_BUCKET_RECORDINGS,
                Key=key,
                Body=audio_data,
                ContentType="audio/mpeg",
            )

            # Update call record
            async with async_session_factory() as db:
                result = await db.execute(select(Call).where(Call.id == UUID(call_id)))
                call = result.scalar_one_or_none()
                if call:
                    call.recording_s3_key = key
                    await db.commit()

        _run_async(_do())
        logger.info("recording_uploaded", call_id=call_id)

    except Exception as exc:
        logger.error("recording_upload_failed", call_id=call_id, error=str(exc))
        raise self.retry(exc=exc)


# ── Health Check Tasks ───────────────────────────────────────────

@celery_app.task
def check_custom_server_health(config_id: str):
    """Check health of a specific custom AI server."""
    from app.core.database import async_session_factory
    from app.models.custom_server import CustomServerConfig
    from app.clients.custom_server import CustomServerClient
    from sqlalchemy import select

    async def _do():
        async with async_session_factory() as db:
            result = await db.execute(
                select(CustomServerConfig).where(CustomServerConfig.id == UUID(config_id))
            )
            config = result.scalar_one_or_none()
            if not config:
                return

            try:
                client = CustomServerClient(config)
                health = await client.health()
                config.health_status = "healthy"
                config.last_response_time_ms = health.get("response_time")
            except Exception:
                config.health_status = "unhealthy"

            config.last_health_check = datetime.now(timezone.utc).isoformat()
            await db.commit()

    _run_async(_do())


@celery_app.task
def periodic_health_check():
    """Periodically check all configured custom servers."""
    from app.core.database import async_session_factory
    from app.models.custom_server import CustomServerConfig
    from sqlalchemy import select

    async def _do():
        async with async_session_factory() as db:
            result = await db.execute(
                select(CustomServerConfig).where(CustomServerConfig.enabled == True)  # noqa: E712
            )
            configs = result.scalars().all()
            for config in configs:
                check_custom_server_health.delay(str(config.id))

    _run_async(_do())


@celery_app.task
def run_scheduled_exports():
    """Check and run due scheduled exports."""
    from app.core.database import async_session_factory
    from app.models.export import ScheduledExport
    from app.models.extraction import ExtractedCallData
    from sqlalchemy import select

    async def _do():
        now = datetime.now(timezone.utc)
        async with async_session_factory() as db:
            result = await db.execute(
                select(ScheduledExport).where(
                    ScheduledExport.enabled == True,  # noqa: E712
                )
            )
            schedules = result.scalars().all()

            for sched in schedules:
                # Simple check: compare scheduled_time with current time
                if sched.scheduled_time:
                    sched_hour, sched_min = sched.scheduled_time.split(":")
                    if now.hour == int(sched_hour) and now.minute == int(sched_min):
                        # Check frequency
                        if sched.frequency == "daily":
                            _trigger_scheduled_export(sched)
                        elif sched.frequency == "weekly" and sched.days_of_week:
                            if now.weekday() in sched.days_of_week:
                                _trigger_scheduled_export(sched)
                        elif sched.frequency == "monthly" and sched.day_of_month:
                            if now.day == sched.day_of_month:
                                _trigger_scheduled_export(sched)

    _run_async(_do())


def _trigger_scheduled_export(sched):
    """Trigger a scheduled export job."""
    logger.info("triggering_scheduled_export", schedule_id=str(sched.id), name=sched.name)
    # This would load the most recent unexported data and trigger the appropriate export task
    # Implementation depends on the specific filter/destination config
