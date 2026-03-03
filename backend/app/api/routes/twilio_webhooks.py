"""
Enhanced Twilio webhook handlers for voice calls.
Handles incoming calls, status updates, and recording completions.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.config import get_settings
from app.models.call import Call
from app.models.agent import Agent
from app.models.phone_number import PhoneNumber
from app.services.phone_call_service import PhoneCallService

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/webhooks/twilio", tags=["Twilio Webhooks"])


@router.post("/voice")
async def handle_inbound_call(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    CallSid: str = Form(""),
    From: str = Form(""),
    To: str = Form(""),
    CallStatus: str = Form(""),
    Direction: str = Form("inbound"),
):
    """
    Handle incoming Twilio voice call.

    Twilio POSTs here when:
    1. Inbound call arrives
    2. Call connects
    3. Other call events

    Returns TwiML to:
    1. Acknowledge the call
    2. Connect to WebSocket for media stream
    3. Play hold music if needed
    """
    logger.info(
        f"Inbound call webhook: CallSid={CallSid}, From={From}, To={To}",
        extra={"direction": Direction, "status": CallStatus},
    )

    try:
        # Create call record and find agent
        call, agent, error = await PhoneCallService.create_inbound_call(
            db=db,
            twilio_call_sid=CallSid,
            from_number=From,
            to_number=To,
        )

        # Handle errors
        if error:
            logger.warning(f"Call creation error: {error}")
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Say>{error}</Say>
                <Hangup/>
            </Response>"""
            return Response(content=twiml, media_type="application/xml")

        if not call or not agent:
            logger.error("Call or agent is None")
            twiml = """<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Say>Sorry, we are unable to process your call at this time.</Say>
                <Hangup/>
            </Response>"""
            return Response(content=twiml, media_type="application/xml")

        # Update call status
        call.status = "ringing"
        call.started_at = datetime.now(timezone.utc).isoformat()
        await db.commit()

        logger.info(
            f"Call accepted and routed to agent",
            extra={
                "call_id": str(call.id),
                "call_sid": CallSid,
                "agent_id": str(agent.id),
                "agent_name": agent.name,
            },
        )

        # Build WebSocket URL for media stream
        # Uses HTTPS/WSS from request context
        host = request.headers.get("Host", "localhost")
        protocol = "wss" if request.headers.get("X-Forwarded-Proto") == "https" else "ws"
        ws_url = f"{protocol}://{host}/ws/media-stream/{call.id}"

        # Return TwiML to establish WebSocket connection
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Connect>
                <Stream url="{ws_url}" track="inbound_track">
                    <Parameter name="call_id" value="{call.id}"/>
                    <Parameter name="agent_id" value="{agent.id}"/>
                </Stream>
            </Connect>
        </Response>"""

        return Response(content=twiml, media_type="application/xml")

    except Exception as e:
        logger.error(f"Error handling inbound call: {str(e)}", exc_info=True)
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say>Sorry, an error occurred. Please try again later.</Say>
            <Hangup/>
        </Response>"""
        return Response(content=twiml, media_type="application/xml")


@router.post("/status")
async def handle_call_status(
    CallSid: str = Form(""),
    CallStatus: str = Form(""),
    CallDuration: str = Form("0"),
    RecordingUrl: str = Form(""),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Handle call status callbacks from Twilio.

    Called when:
    - Call completes
    - Call fails
    - No answer
    - Busy signal
    - Call is transferred
    """
    logger.info(
        f"Call status update: CallSid={CallSid}, Status={CallStatus}",
        extra={"duration": CallDuration},
    )

    try:
        # Update call in database
        success = await PhoneCallService.update_call_status(
            db=db,
            twilio_call_sid=CallSid,
            status=CallStatus,
            duration_seconds=int(CallDuration) if CallDuration else None,
            recording_url=RecordingUrl if RecordingUrl else None,
        )

        if not success:
            logger.warning(f"Call not found for status update: {CallSid}")
            return {"status": "ignored"}

        # If call completed, trigger post-processing
        if CallStatus == "completed":
            # Queue data extraction job
            from app.worker.tasks import post_call_processing

            result = await db.execute(select(Call).where(Call.twilio_call_sid == CallSid))
            call = result.scalar_one_or_none()

            if call:
                logger.info(f"Queuing post-processing for call: {call.id}")
                post_call_processing.delay(str(call.id))

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Error handling call status: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}


@router.post("/recording")
async def handle_recording_complete(
    CallSid: str = Form(""),
    RecordingUrl: str = Form(""),
    RecordingSid: str = Form(""),
    RecordingDuration: str = Form("0"),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Handle recording completion from Twilio.

    Called when Twilio finishes recording a call.
    """
    logger.info(
        f"Recording complete: CallSid={CallSid}, RecordingSid={RecordingSid}",
        extra={"duration": RecordingDuration},
    )

    try:
        result = await db.execute(select(Call).where(Call.twilio_call_sid == CallSid))
        call = result.scalar_one_or_none()

        if not call:
            logger.warning(f"Recording callback for unknown call: {CallSid}")
            return {"status": "ignored"}

        # Update recording URL
        call.recording_url = f"{RecordingUrl}.mp3"
        await db.commit()

        logger.info(
            f"Recording saved: {call.id}",
            extra={"url": call.recording_url},
        )

        # Optionally upload to S3
        if settings.AWS_S3_BUCKET:
            from app.worker.tasks import upload_recording_to_s3

            logger.info(f"Queuing S3 upload for: {call.id}")
            upload_recording_to_s3.delay(str(call.id), call.recording_url)

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Error handling recording: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}


@router.post("/fallback")
async def fallback_error(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Handle fallback/error webhooks from Twilio.

    Called when Twilio encounters an error processing webhook.
    """
    try:
        body = await request.json()
        logger.warning(f"Twilio fallback/error webhook", extra=body)
        return {"status": "received"}
    except Exception as e:
        logger.error(f"Error in fallback webhook: {str(e)}", exc_info=True)
        return {"status": "error"}
