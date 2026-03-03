"""
Twilio webhook routes for handling inbound/outbound calls.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.agent import Agent
from app.models.call import Call

logger = get_logger(__name__)

router = APIRouter(prefix="/webhooks/twilio", tags=["Twilio Webhooks"])


@router.post("/voice")
async def twilio_voice_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    CallSid: str = Form(""),
    From: str = Form(""),
    To: str = Form(""),
    CallStatus: str = Form(""),
    Direction: str = Form(""),
):
    """
    Handle incoming Twilio voice webhook.
    Twilio POSTs here when a call connects.
    Returns TwiML to establish a WebSocket media stream.
    """
    logger.info("twilio_voice_webhook", call_sid=CallSid, from_=From, to=To, status=CallStatus)

    # Find agent assigned to this phone number
    result = await db.execute(
        select(Agent).where(Agent.phone_numbers.any(To), Agent.status == "active")
    )
    agent = result.scalar_one_or_none()

    if not agent:
        logger.warning("no_agent_for_number", to_number=To)
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say>Sorry, no agent is available for this number.</Say>
            <Hangup/>
        </Response>"""
        return Response(content=twiml, media_type="application/xml")

    # Create call record
    call = Call(
        company_id=agent.company_id,
        agent_id=agent.id,
        twilio_call_sid=CallSid,
        direction="inbound",
        from_number=From,
        to_number=To,
        status="ringing",
    )
    db.add(call)
    await db.flush()

    # Return TwiML to connect to our media stream WebSocket
    ws_url = f"wss://{request.headers.get('host', 'localhost')}/ws/media-stream/{call.id}"
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Connect>
            <Stream url="{ws_url}">
                <Parameter name="call_id" value="{call.id}"/>
                <Parameter name="agent_id" value="{agent.id}"/>
            </Stream>
        </Connect>
    </Response>"""

    return Response(content=twiml, media_type="application/xml")


@router.post("/status")
async def twilio_status_callback(
    CallSid: str = Form(""),
    CallStatus: str = Form(""),
    CallDuration: str = Form("0"),
    RecordingUrl: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    """Handle call status updates from Twilio."""
    logger.info("twilio_status_callback", call_sid=CallSid, status=CallStatus)

    result = await db.execute(select(Call).where(Call.twilio_call_sid == CallSid))
    call = result.scalar_one_or_none()
    if not call:
        logger.warning("status_callback_unknown_call", call_sid=CallSid)
        return {"status": "ignored"}

    call.status = CallStatus
    if CallDuration:
        call.duration_seconds = int(CallDuration)
    if RecordingUrl:
        call.recording_url = RecordingUrl

    if CallStatus in ("completed", "failed", "no-answer", "busy"):
        from datetime import datetime, timezone

        call.ended_at = datetime.now(timezone.utc).isoformat()

        # Trigger data extraction if call completed and extraction enabled
        if CallStatus == "completed":
            from app.worker.tasks import post_call_processing

            post_call_processing.delay(str(call.id))

    return {"status": "ok"}


@router.post("/recording")
async def twilio_recording_callback(
    CallSid: str = Form(""),
    RecordingUrl: str = Form(""),
    RecordingSid: str = Form(""),
    RecordingDuration: str = Form("0"),
    db: AsyncSession = Depends(get_db),
):
    """Handle recording completion from Twilio."""
    logger.info("twilio_recording_callback", call_sid=CallSid, recording_sid=RecordingSid)

    result = await db.execute(select(Call).where(Call.twilio_call_sid == CallSid))
    call = result.scalar_one_or_none()
    if call:
        call.recording_url = f"{RecordingUrl}.mp3"
        # Optionally upload to S3
        from app.worker.tasks import upload_recording_to_s3

        upload_recording_to_s3.delay(str(call.id), call.recording_url)

    return {"status": "ok"}
