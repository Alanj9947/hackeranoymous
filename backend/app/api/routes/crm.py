"""CRM integration API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.auth import get_company_id
from app.services.crm_service import crm_service, CRMProvider

router = APIRouter(prefix="/api/v1/crm", tags=["crm"])


@router.post("/configure/{provider}")
async def configure_crm(
    provider: str,
    api_key: str,
    api_url: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(get_company_id)
):
    """
    Configure CRM provider.
    
    Args:
        provider: CRM provider (salesforce, hubspot)
        api_key: API key/token
        api_url: Optional API URL for Salesforce
        db: Database session
        company_id: Company identifier
        
    Returns:
        Configuration status
    """
    try:
        # Validate provider
        crm_provider = CRMProvider(provider.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider: {provider}"
        )

    config = {"api_key": api_key}
    if api_url:
        config["api_url"] = api_url

    success = await crm_service.configure(company_id, crm_provider, config)

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Failed to configure CRM"
        )

    return {
        "provider": provider,
        "configured": True,
        "status": crm_service.get_status(company_id)
    }


@router.delete("/disconnect/{provider}")
async def disconnect_crm(
    provider: str,
    company_id: str = Depends(get_company_id)
):
    """
    Disconnect CRM provider.
    
    Args:
        provider: CRM provider
        company_id: Company identifier
        
    Returns:
        Disconnection status
    """
    try:
        crm_provider = CRMProvider(provider.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    success = await crm_service.disconnect(company_id, crm_provider)

    return {
        "provider": provider,
        "disconnected": success
    }


@router.get("/status")
async def get_crm_status(
    company_id: str = Depends(get_company_id)
):
    """
    Get CRM integration status.
    
    Args:
        company_id: Company identifier
        
    Returns:
        Integration status
    """
    return crm_service.get_status(company_id)


@router.get("/contacts")
async def search_contacts(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    company_id: str = Depends(get_company_id)
):
    """
    Search contacts in CRM.
    
    Args:
        query: Search query
        limit: Result limit
        company_id: Company identifier
        
    Returns:
        List of contacts
    """
    contacts = await crm_service.search_contacts(company_id, query, limit)

    return {
        "query": query,
        "results": [c.to_dict() for c in contacts],
        "count": len(contacts)
    }


@router.get("/contacts/{contact_id}")
async def get_contact(
    contact_id: str,
    company_id: str = Depends(get_company_id)
):
    """
    Get specific contact.
    
    Args:
        contact_id: Contact ID in CRM
        company_id: Company identifier
        
    Returns:
        Contact details
    """
    contact = await crm_service.get_contact(company_id, contact_id)

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    return contact.to_dict()


@router.post("/contacts/{contact_id}/activity")
async def log_activity(
    contact_id: str,
    activity_type: str,
    description: str,
    metadata: dict = None,
    company_id: str = Depends(get_company_id)
):
    """
    Log activity for contact.
    
    Args:
        contact_id: Contact ID
        activity_type: Type of activity (call, email, etc.)
        description: Activity description
        metadata: Additional metadata
        company_id: Company identifier
        
    Returns:
        Activity logging status
    """
    success = await crm_service.log_activity(
        company_id,
        contact_id,
        activity_type,
        description,
        metadata
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to log activity")

    return {
        "contact_id": contact_id,
        "activity_type": activity_type,
        "logged": True
    }


@router.post("/sync")
async def sync_call_to_crm(
    call_id: str,
    contact_id: str,
    call_data: dict,
    company_id: str = Depends(get_company_id)
):
    """
    Sync call data to CRM.
    
    Args:
        call_id: Call identifier
        contact_id: Contact in CRM
        call_data: Call details to sync
        company_id: Company identifier
        
    Returns:
        Sync status
    """
    success = await crm_service.log_activity(
        company_id,
        contact_id,
        "call",
        f"AI call {call_id}",
        {
            "call_id": call_id,
            "duration": call_data.get("duration"),
            "recording_url": call_data.get("recording_url"),
            "transcript": call_data.get("transcript")
        }
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to sync call")

    return {
        "call_id": call_id,
        "contact_id": contact_id,
        "synced": True
    }
