"""SMS integration API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.auth import get_company_id
from app.services.sms_service import (
    sms_service,
    SMSProvider
)

router = APIRouter(prefix="/api/v1/sms", tags=["sms"])


@router.post("/configure/{provider}")
async def configure_sms(
    provider: str,
    account_sid: str,
    auth_token: str,
    phone_number: str,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(get_company_id)
):
    """
    Configure SMS provider.
    
    Args:
        provider: SMS provider (twilio)
        account_sid: Account SID/API Key
        auth_token: Auth token
        phone_number: SMS phone number
        db: Database session
        company_id: Company identifier
        
    Returns:
        Configuration status
    """
    try:
        sms_provider = SMSProvider(provider.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider: {provider}"
        )

    config = {
        "account_sid": account_sid,
        "auth_token": auth_token,
        "phone_number": phone_number
    }

    success = await sms_service.configure(company_id, sms_provider, config)

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Failed to configure SMS"
        )

    return {
        "provider": provider,
        "configured": True,
        "status": sms_service.get_status(company_id)
    }


@router.delete("/disconnect")
async def disconnect_sms(
    company_id: str = Depends(get_company_id)
):
    """Disconnect SMS provider."""
    success = await sms_service.disconnect(company_id)

    return {
        "disconnected": success
    }


@router.get("/status")
async def get_sms_status(
    company_id: str = Depends(get_company_id)
):
    """Get SMS integration status."""
    return sms_service.get_status(company_id)


@router.post("/send")
async def send_sms(
    phone: str,
    message: str,
    company_id: str = Depends(get_company_id)
):
    """
    Send SMS.
    
    Args:
        phone: Phone number
        message: Message content
        company_id: Company identifier
        
    Returns:
        Send status
    """
    message_id = await sms_service.send_sms(company_id, phone, message)

    if not message_id:
        raise HTTPException(status_code=400, detail="Failed to send SMS")

    return {
        "message_id": message_id,
        "phone": phone,
        "status": "sent"
    }


@router.post("/receive")
async def receive_sms(
    phone: str,
    message: str,
    message_id: Optional[str] = None,
    company_id: str = Depends(get_company_id)
):
    """
    Receive inbound SMS (webhook from Twilio).
    
    Args:
        phone: Sender phone number
        message: Message content
        message_id: Message ID
        company_id: Company identifier
        
    Returns:
        Receive status
    """
    sms_msg = await sms_service.receive_sms(company_id, phone, message, message_id)

    return {
        "message_id": sms_msg.message_id,
        "phone": phone,
        "status": "received"
    }


@router.get("/conversations")
async def list_conversations(
    limit: int = Query(20, ge=1, le=100),
    company_id: str = Depends(get_company_id)
):
    """
    List SMS conversations.
    
    Args:
        limit: Result limit
        company_id: Company identifier
        
    Returns:
        List of conversations
    """
    conversations = await sms_service.list_conversations(company_id, limit)

    return {
        "conversations": [c.to_dict() for c in conversations],
        "count": len(conversations)
    }


@router.get("/conversations/{phone}")
async def get_conversation(
    phone: str,
    company_id: str = Depends(get_company_id)
):
    """
    Get SMS conversation with phone number.
    
    Args:
        phone: Phone number
        company_id: Company identifier
        
    Returns:
        Conversation details
    """
    conversation = await sms_service.get_conversation(company_id, phone)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation.to_dict()


@router.get("/search")
async def search_conversations(
    query: str,
    limit: int = Query(20, ge=1, le=100),
    company_id: str = Depends(get_company_id)
):
    """
    Search SMS conversations.
    
    Args:
        query: Search query
        limit: Result limit
        company_id: Company identifier
        
    Returns:
        Search results
    """
    conversations = await sms_service.search_conversations(company_id, query, limit)

    return {
        "query": query,
        "conversations": [c.to_dict() for c in conversations],
        "count": len(conversations)
    }
