"""
Phone number management routes.
Supports listing, provisioning, and releasing Twilio phone numbers.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_id, get_current_active_user
from app.core.database import get_db
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.agent import Agent
from app.models.user import User
from pydantic import BaseModel
from sqlalchemy import select

logger = get_logger(__name__)
router = APIRouter(prefix="/phone-numbers", tags=["Phone Numbers"])
settings = get_settings()


class PhoneNumberResponse(BaseModel):
    sid: str
    phone_number: str
    friendly_name: str
    capabilities: dict
    date_created: Optional[str] = None
    assigned_agent_id: Optional[str] = None


class PhoneNumberSearchResult(BaseModel):
    phone_number: str
    friendly_name: str
    region: Optional[str] = None
    postal_code: Optional[str] = None
    monthly_cost: Optional[str] = None


class AssignPhoneNumberRequest(BaseModel):
    agent_id: UUID


@router.get("", response_model=List[PhoneNumberResponse])
async def list_phone_numbers(
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
):
    """List all Twilio phone numbers for the account."""
    if not settings.TWILIO_ACCOUNT_SID:
        raise HTTPException(status_code=503, detail="Twilio not configured")

    try:
        from twilio.rest import Client as TwilioClient

        client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        incoming_numbers = client.incoming_phone_numbers.list()

        # Load agent assignments
        agents_result = await db.execute(select(Agent).where(Agent.company_id == company_id))
        agents = agents_result.scalars().all()

        # Build a map: phone_number -> agent_id
        number_to_agent: dict[str, str] = {}
        for agent in agents:
            for num in (agent.phone_numbers or []):
                number_to_agent[num] = str(agent.id)

        result = []
        for num in incoming_numbers:
            result.append(
                PhoneNumberResponse(
                    sid=num.sid,
                    phone_number=num.phone_number,
                    friendly_name=num.friendly_name or num.phone_number,
                    capabilities={
                        "voice": num.capabilities.get("voice", False),
                        "sms": num.capabilities.get("SMS", False),
                        "mms": num.capabilities.get("MMS", False),
                    },
                    date_created=str(num.date_created) if num.date_created else None,
                    assigned_agent_id=number_to_agent.get(num.phone_number),
                )
            )
        return result
    except Exception as e:
        logger.error("list_phone_numbers_error", error=str(e))
        raise HTTPException(status_code=502, detail=f"Twilio error: {str(e)}")


@router.get("/search", response_model=List[PhoneNumberSearchResult])
async def search_available_numbers(
    area_code: Optional[str] = Query(None, description="US area code to search"),
    country: str = Query("US", description="ISO country code"),
    limit: int = Query(10, ge=1, le=20),
    _: UUID = Depends(get_company_id),
):
    """Search for available phone numbers to purchase."""
    if not settings.TWILIO_ACCOUNT_SID:
        raise HTTPException(status_code=503, detail="Twilio not configured")

    try:
        from twilio.rest import Client as TwilioClient

        client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        kwargs = {"limit": limit, "voice_enabled": True}
        if area_code:
            kwargs["area_code"] = area_code

        numbers = client.available_phone_numbers(country).local.list(**kwargs)
        return [
            PhoneNumberSearchResult(
                phone_number=n.phone_number,
                friendly_name=n.friendly_name or n.phone_number,
                region=getattr(n, "region", None),
                postal_code=getattr(n, "postal_code", None),
            )
            for n in numbers
        ]
    except Exception as e:
        logger.error("search_numbers_error", error=str(e))
        raise HTTPException(status_code=502, detail=f"Twilio error: {str(e)}")


@router.post("/{phone_number_sid}/assign", status_code=status.HTTP_204_NO_CONTENT)
async def assign_phone_number(
    phone_number_sid: str,
    body: AssignPhoneNumberRequest,
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
):
    """Assign a Twilio phone number to an agent and configure its webhook."""
    if not settings.TWILIO_ACCOUNT_SID:
        raise HTTPException(status_code=503, detail="Twilio not configured")

    # Verify agent belongs to company
    agent_result = await db.execute(
        select(Agent).where(Agent.id == body.agent_id, Agent.company_id == company_id)
    )
    agent = agent_result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    try:
        from twilio.rest import Client as TwilioClient

        client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        # Get the phone number's actual number string
        num_resource = client.incoming_phone_numbers(phone_number_sid).fetch()
        phone_number = num_resource.phone_number

        # Configure webhook to our platform
        webhook_url = f"{settings.TWILIO_WEBHOOK_BASE_URL}/webhooks/twilio/voice"
        status_callback = f"{settings.TWILIO_WEBHOOK_BASE_URL}/webhooks/twilio/status"
        client.incoming_phone_numbers(phone_number_sid).update(
            voice_url=webhook_url,
            voice_method="POST",
            status_callback=status_callback,
            status_callback_method="POST",
        )

        # Update agent's phone_numbers list
        numbers = list(agent.phone_numbers or [])
        if phone_number not in numbers:
            numbers.append(phone_number)
            agent.phone_numbers = numbers
            await db.commit()

        logger.info("phone_number_assigned", number=phone_number, agent_id=str(agent.id))
    except Exception as e:
        logger.error("assign_number_error", error=str(e))
        raise HTTPException(status_code=502, detail=f"Twilio error: {str(e)}")


@router.delete("/{phone_number_sid}/assign", status_code=status.HTTP_204_NO_CONTENT)
async def unassign_phone_number(
    phone_number_sid: str,
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
):
    """Remove agent assignment from a phone number."""
    if not settings.TWILIO_ACCOUNT_SID:
        raise HTTPException(status_code=503, detail="Twilio not configured")

    try:
        from twilio.rest import Client as TwilioClient

        client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        num_resource = client.incoming_phone_numbers(phone_number_sid).fetch()
        phone_number = num_resource.phone_number

        # Remove from all agents
        agents_result = await db.execute(select(Agent).where(Agent.company_id == company_id))
        for agent in agents_result.scalars().all():
            numbers = list(agent.phone_numbers or [])
            if phone_number in numbers:
                numbers.remove(phone_number)
                agent.phone_numbers = numbers

        await db.commit()
        logger.info("phone_number_unassigned", number=phone_number)
    except Exception as e:
        logger.error("unassign_number_error", error=str(e))
        raise HTTPException(status_code=502, detail=f"Twilio error: {str(e)}")
