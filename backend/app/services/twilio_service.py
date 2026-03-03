"""
Twilio service for managing Voice API calls.
"""

from __future__ import annotations

from twilio.rest import Client as TwilioClient

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class TwilioService:
    def __init__(self):
        self.client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.phone_number = settings.TWILIO_PHONE_NUMBER
        self.webhook_base_url = settings.TWILIO_WEBHOOK_BASE_URL

    def initiate_outbound_call(self, call_id: str, to_number: str, agent_id: str) -> str:
        """Start an outbound call via Twilio Voice API. Returns Call SID."""
        logger.info("initiate_outbound_call", call_id=call_id, to=to_number)

        call = self.client.calls.create(
            to=to_number,
            from_=self.phone_number,
            url=f"{self.webhook_base_url}/webhooks/twilio/voice",
            status_callback=f"{self.webhook_base_url}/webhooks/twilio/status",
            status_callback_event=["initiated", "ringing", "answered", "completed"],
            record=True,
            recording_status_callback=f"{self.webhook_base_url}/webhooks/twilio/recording",
            machine_detection="Enable",
            async_amd=True,
            timeout=30,
        )

        logger.info("outbound_call_created", call_sid=call.sid)
        return call.sid

    def end_call(self, call_sid: str) -> None:
        """End an active call."""
        logger.info("end_call", call_sid=call_sid)
        self.client.calls(call_sid).update(status="completed")

    def transfer_call(self, call_sid: str, transfer_to: str) -> None:
        """Transfer a call to another number."""
        logger.info("transfer_call", call_sid=call_sid, transfer_to=transfer_to)
        twiml = f"""
        <Response>
            <Dial>{transfer_to}</Dial>
        </Response>
        """
        self.client.calls(call_sid).update(twiml=twiml)
