"""Ticketing system integration API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.auth import get_company_id
from app.services.ticketing_service import (
    ticketing_service,
    TicketingProvider,
    TicketStatus
)

router = APIRouter(prefix="/api/v1/ticketing", tags=["ticketing"])


@router.post("/configure/{provider}")
async def configure_ticketing(
    provider: str,
    api_key: str,
    api_url: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(get_company_id)
):
    """
    Configure ticketing provider.
    
    Args:
        provider: Ticketing provider (jira, zendesk)
        api_key: API key/token
        api_url: Optional API URL
        db: Database session
        company_id: Company identifier
        
    Returns:
        Configuration status
    """
    try:
        # Validate provider
        ticketing_provider = TicketingProvider(provider.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider: {provider}"
        )

    config = {"api_key": api_key}
    if api_url:
        config["api_url"] = api_url

    success = await ticketing_service.configure(company_id, ticketing_provider, config)

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Failed to configure ticketing system"
        )

    return {
        "provider": provider,
        "configured": True,
        "status": ticketing_service.get_status(company_id)
    }


@router.delete("/disconnect/{provider}")
async def disconnect_ticketing(
    provider: str,
    company_id: str = Depends(get_company_id)
):
    """
    Disconnect ticketing provider.
    
    Args:
        provider: Ticketing provider
        company_id: Company identifier
        
    Returns:
        Disconnection status
    """
    try:
        ticketing_provider = TicketingProvider(provider.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    success = await ticketing_service.disconnect(company_id, ticketing_provider)

    return {
        "provider": provider,
        "disconnected": success
    }


@router.get("/status")
async def get_ticketing_status(
    company_id: str = Depends(get_company_id)
):
    """
    Get ticketing integration status.
    
    Args:
        company_id: Company identifier
        
    Returns:
        Integration status
    """
    return ticketing_service.get_status(company_id)


@router.post("/tickets")
async def create_ticket(
    title: str,
    description: str,
    priority: str = "medium",
    metadata: dict = None,
    company_id: str = Depends(get_company_id)
):
    """
    Create ticket in ticketing system.
    
    Args:
        title: Ticket title
        description: Ticket description
        priority: Priority (low, medium, high, critical)
        metadata: Additional metadata
        company_id: Company identifier
        
    Returns:
        Created ticket info
    """
    ticket_id = await ticketing_service.create_ticket(
        company_id,
        title,
        description,
        priority,
        metadata
    )

    if not ticket_id:
        raise HTTPException(status_code=400, detail="Failed to create ticket")

    return {
        "ticket_id": ticket_id,
        "title": title,
        "status": "open",
        "created": True
    }


@router.get("/tickets")
async def list_tickets(
    limit: int = Query(20, ge=1, le=100),
    company_id: str = Depends(get_company_id)
):
    """
    List tickets from ticketing system.
    
    Args:
        limit: Result limit
        company_id: Company identifier
        
    Returns:
        List of tickets
    """
    tickets = await ticketing_service.list_tickets(company_id, limit)

    return {
        "tickets": [t.to_dict() for t in tickets],
        "count": len(tickets)
    }


@router.get("/tickets/{ticket_id}")
async def get_ticket(
    ticket_id: str,
    company_id: str = Depends(get_company_id)
):
    """
    Get specific ticket.
    
    Args:
        ticket_id: Ticket ID
        company_id: Company identifier
        
    Returns:
        Ticket details
    """
    ticket = await ticketing_service.get_ticket(company_id, ticket_id)

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return ticket.to_dict()


@router.patch("/tickets/{ticket_id}/status")
async def update_ticket_status(
    ticket_id: str,
    status: str,
    company_id: str = Depends(get_company_id)
):
    """
    Update ticket status.
    
    Args:
        ticket_id: Ticket ID
        status: New status (open, in_progress, resolved, closed, on_hold)
        company_id: Company identifier
        
    Returns:
        Update status
    """
    try:
        status_enum = TicketStatus(status.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    success = await ticketing_service.update_ticket_status(
        company_id,
        ticket_id,
        status_enum
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to update ticket")

    return {
        "ticket_id": ticket_id,
        "status": status,
        "updated": True
    }


@router.post("/tickets/{ticket_id}/comments")
async def add_ticket_comment(
    ticket_id: str,
    text: str,
    author: str = "AI Agent",
    is_internal: bool = False,
    company_id: str = Depends(get_company_id)
):
    """
    Add comment to ticket.
    
    Args:
        ticket_id: Ticket ID
        text: Comment text
        author: Comment author
        is_internal: Internal comment
        company_id: Company identifier
        
    Returns:
        Comment creation status
    """
    success = await ticketing_service.add_ticket_comment(
        company_id,
        ticket_id,
        author,
        text,
        is_internal
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to add comment")

    return {
        "ticket_id": ticket_id,
        "comment": text,
        "author": author,
        "created": True
    }


@router.post("/sync-call")
async def link_call_to_ticket(
    call_id: str,
    ticket_id: str,
    call_data: dict,
    company_id: str = Depends(get_company_id)
):
    """
    Link AI call to ticket or create ticket from call.
    
    Args:
        call_id: Call identifier
        ticket_id: Ticket ID (optional - if empty, create new)
        call_data: Call details
        company_id: Company identifier
        
    Returns:
        Linking status
    """
    # If no ticket ID, create one
    if not ticket_id:
        ticket_id = await ticketing_service.create_ticket(
            company_id,
            f"AI Call {call_id}",
            f"AI-generated support ticket from call {call_id}",
            "medium",
            {
                "call_id": call_id,
                "duration": call_data.get("duration"),
                "recording_url": call_data.get("recording_url")
            }
        )

        if not ticket_id:
            raise HTTPException(status_code=400, detail="Failed to create ticket")

    # Add call details as comment
    success = await ticketing_service.add_ticket_comment(
        company_id,
        ticket_id,
        "AI Agent",
        f"Call Recording: {call_data.get('recording_url', 'N/A')}\n\nTranscript:\n{call_data.get('transcript', 'N/A')}",
        is_internal=True
    )

    return {
        "call_id": call_id,
        "ticket_id": ticket_id,
        "linked": True
    }
