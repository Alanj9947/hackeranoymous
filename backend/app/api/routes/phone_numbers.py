"""API endpoints for phone number management."""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.config import get_settings
from app.api.deps import get_company_id
from app.models import PhoneNumber, Agent
from app.services.twilio_service import TwilioService

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/phone-numbers", tags=["phone-numbers"])

# Initialize Twilio service
try:
    twilio_service = TwilioService(
        account_sid=settings.TWILIO_ACCOUNT_SID,
        auth_token=settings.TWILIO_AUTH_TOKEN,
    )
except Exception as e:
    logger.warning(f"Twilio service not initialized: {str(e)}")
    twilio_service = None


@router.get("/available")
async def get_available_numbers(
    country: str = Query("US"),
    area_code: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    company_id: UUID = Depends(get_company_id),
):
    """
    Get available phone numbers from Twilio.

    Args:
        country: Country code (US, CA, GB, AU)
        area_code: Area code filter (US only)
        limit: Maximum results
        company_id: Company ID (for authorization)

    Returns:
        List of available numbers
    """
    if not twilio_service:
        raise HTTPException(status_code=503, detail="Twilio service unavailable")

    try:
        logger.info(f"Searching available numbers: country={country}, area_code={area_code}")

        numbers = await twilio_service.get_available_numbers(
            country=country,
            area_code=area_code,
            limit=limit,
        )

        return {
            "country": country,
            "area_code": area_code,
            "count": len(numbers),
            "numbers": numbers,
        }

    except Exception as e:
        logger.error(f"Error getting available numbers: {str(e)}")
        raise HTTPException(status_code=500, detail="Error searching numbers")


@router.post("/")
async def provision_phone_number(
    phone_number: str = Query(...),
    agent_id: UUID = Query(...),
    db: AsyncSession = Depends(get_async_session),
    company_id: UUID = Depends(get_company_id),
):
    """
    Provision a phone number for an agent.

    Args:
        phone_number: Phone number to provision
        agent_id: Agent to assign to
        db: Database session
        company_id: Company ID (for authorization)

    Returns:
        Provisioning result
    """
    if not twilio_service:
        raise HTTPException(status_code=503, detail="Twilio service unavailable")

    try:
        # Validate agent exists and belongs to company
        result = await db.execute(
            select(Agent).where(
                Agent.id == agent_id,
                Agent.company_id == company_id,
            )
        )
        agent = result.scalar_one_or_none()

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Validate phone number
        if not twilio_service.validate_phone_number(phone_number):
            raise HTTPException(status_code=400, detail="Invalid phone number format")

        # Check if already provisioned
        result = await db.execute(
            select(PhoneNumber).where(PhoneNumber.phone_number == phone_number)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Number already provisioned")

        # Build webhook URL
        webhook_url = f"{settings.API_URL}/webhooks/twilio/voice"

        # Provision the number
        logger.info(f"Provisioning number {phone_number} for agent {agent_id}")

        twilio_result = await twilio_service.provision_phone_number(
            phone_number=phone_number,
            company_id=str(company_id),
            agent_id=str(agent_id),
            webhook_url=webhook_url,
        )

        # Save to database
        db_phone_number = PhoneNumber(
            company_id=company_id,
            agent_id=agent_id,
            phone_number=phone_number,
            twilio_phone_sid=twilio_result["twilio_phone_sid"],
            friendly_name=twilio_result.get("friendly_name"),
            country_code="US",  # Extract from phone number if needed
            webhook_url=webhook_url,
            webhook_configured_at=twilio_result.get("webhook_configured_at"),
            provisioned_at=twilio_result.get("provisioned_at"),
            status="active",
            monthly_cost=twilio_result.get("monthly_cost", 1.00),
        )

        db.add(db_phone_number)
        await db.commit()
        await db.refresh(db_phone_number)

        logger.info(f"Number provisioned and saved: {phone_number}")

        return {
            "id": str(db_phone_number.id),
            "phone_number": db_phone_number.phone_number,
            "agent_id": str(db_phone_number.agent_id),
            "status": db_phone_number.status,
            "provisioned_at": db_phone_number.provisioned_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error provisioning number: {str(e)}")
        raise HTTPException(status_code=500, detail="Error provisioning number")


@router.get("/")
async def list_phone_numbers(
    agent_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_session),
    company_id: UUID = Depends(get_company_id),
):
    """
    List phone numbers for the company.

    Args:
        agent_id: Filter by agent (optional)
        status: Filter by status (optional)
        db: Database session
        company_id: Company ID

    Returns:
        List of phone numbers
    """
    try:
        query = select(PhoneNumber).where(PhoneNumber.company_id == company_id)

        if agent_id:
            query = query.where(PhoneNumber.agent_id == agent_id)

        if status:
            query = query.where(PhoneNumber.status == status)

        result = await db.execute(query)
        numbers = result.scalars().all()

        return {
            "count": len(numbers),
            "numbers": [
                {
                    "id": str(n.id),
                    "phone_number": n.phone_number,
                    "agent_id": str(n.agent_id) if n.agent_id else None,
                    "agent_name": n.agent.name if n.agent else None,
                    "status": n.status,
                    "monthly_cost": n.monthly_cost,
                    "provisioned_at": n.provisioned_at,
                    "call_count": n.call_count,
                }
                for n in numbers
            ],
        }

    except Exception as e:
        logger.error(f"Error listing phone numbers: {str(e)}")
        raise HTTPException(status_code=500, detail="Error listing numbers")


@router.get("/{phone_number_id}")
async def get_phone_number(
    phone_number_id: UUID,
    db: AsyncSession = Depends(get_async_session),
    company_id: UUID = Depends(get_company_id),
):
    """
    Get details for a specific phone number.

    Args:
        phone_number_id: Phone number ID
        db: Database session
        company_id: Company ID

    Returns:
        Phone number details
    """
    try:
        result = await db.execute(
            select(PhoneNumber).where(
                PhoneNumber.id == phone_number_id,
                PhoneNumber.company_id == company_id,
            )
        )
        phone_number = result.scalar_one_or_none()

        if not phone_number:
            raise HTTPException(status_code=404, detail="Phone number not found")

        return {
            "id": str(phone_number.id),
            "phone_number": phone_number.phone_number,
            "agent_id": str(phone_number.agent_id) if phone_number.agent_id else None,
            "agent_name": phone_number.agent.name if phone_number.agent else None,
            "status": phone_number.status,
            "country_code": phone_number.country_code,
            "area_code": phone_number.area_code,
            "monthly_cost": phone_number.monthly_cost,
            "inbound_enabled": phone_number.inbound_enabled,
            "outbound_enabled": phone_number.outbound_enabled,
            "provisioned_at": phone_number.provisioned_at,
            "call_count": phone_number.call_count,
            "last_call_at": phone_number.last_call_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting phone number: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving number")


@router.delete("/{phone_number_id}")
async def release_phone_number(
    phone_number_id: UUID,
    db: AsyncSession = Depends(get_async_session),
    company_id: UUID = Depends(get_company_id),
):
    """
    Release (delete) a phone number.

    Args:
        phone_number_id: Phone number ID to release
        db: Database session
        company_id: Company ID

    Returns:
        Success message
    """
    if not twilio_service:
        raise HTTPException(status_code=503, detail="Twilio service unavailable")

    try:
        # Get phone number
        result = await db.execute(
            select(PhoneNumber).where(
                PhoneNumber.id == phone_number_id,
                PhoneNumber.company_id == company_id,
            )
        )
        phone_number = result.scalar_one_or_none()

        if not phone_number:
            raise HTTPException(status_code=404, detail="Phone number not found")

        # Release from Twilio
        logger.info(f"Releasing phone number {phone_number.phone_number}")

        try:
            await twilio_service.release_phone_number(phone_number.twilio_phone_sid)
        except Exception as e:
            logger.warning(f"Error releasing from Twilio: {str(e)}")
            # Continue to delete from DB anyway

        # Update database status
        phone_number.status = "inactive"
        phone_number.released_at = phone_number.released_at or str(__import__("datetime").datetime.utcnow().isoformat())
        await db.commit()

        logger.info(f"Phone number released: {phone_number.phone_number}")

        return {"message": "Phone number released successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error releasing phone number: {str(e)}")
        raise HTTPException(status_code=500, detail="Error releasing number")
