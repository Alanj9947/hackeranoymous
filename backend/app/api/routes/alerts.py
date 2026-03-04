"""Alert management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional, List

from app.core.database import get_db
from app.core.auth import get_company_id
from app.services.advanced_alert_service import (
    advanced_alert_service,
    AlertType,
    AlertSeverity,
    NotificationChannel
)

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.post("/check/error-rate")
async def check_error_rate(
    error_rate: float,
    threshold: float = 0.05,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(get_company_id)
):
    """
    Check error rate and create alert if exceeded.
    
    Args:
        error_rate: Current error rate (0-1)
        threshold: Error threshold (default 0.05 = 5%)
        db: Database session
        company_id: Company identifier
        
    Returns:
        Alert data if created
    """
    alert = await advanced_alert_service.check_error_rate(
        db,
        company_id,
        error_rate,
        threshold
    )
    
    return {"alert": alert, "checked": True}


@router.post("/check/budget")
async def check_budget(
    current_spend: float,
    budget_limit: float,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(get_company_id)
):
    """
    Check budget and create alert if exceeded.
    
    Args:
        current_spend: Current spend amount
        budget_limit: Monthly budget limit
        db: Database session
        company_id: Company identifier
        
    Returns:
        Alert data if created
    """
    alert = await advanced_alert_service.check_budget(
        db,
        company_id,
        current_spend,
        budget_limit
    )
    
    return {"alert": alert, "checked": True}


@router.post("/check/cost-spike")
async def check_cost_spike(
    current_cost: float,
    baseline_cost: float,
    threshold: float = 0.5,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(get_company_id)
):
    """
    Check for cost spike.
    
    Args:
        current_cost: Current period cost
        baseline_cost: Baseline cost
        threshold: Spike threshold (default 0.5 = 50%)
        db: Database session
        company_id: Company identifier
        
    Returns:
        Alert data if created
    """
    alert = await advanced_alert_service.check_cost_spike(
        db,
        company_id,
        current_cost,
        baseline_cost,
        threshold
    )
    
    return {"alert": alert, "checked": True}


@router.post("/check/agent-offline")
async def check_agent_offline(
    agent_id: str,
    offline_minutes: int = 30,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(get_company_id)
):
    """
    Check if agent is offline.
    
    Args:
        agent_id: Agent identifier
        offline_minutes: Minutes offline threshold
        db: Database session
        company_id: Company identifier
        
    Returns:
        Alert data
    """
    alert = await advanced_alert_service.check_agent_offline(
        db,
        company_id,
        agent_id,
        offline_minutes
    )
    
    return {"alert": alert, "checked": True}


@router.post("/check/quota")
async def check_quota(
    resource: str,
    current: int,
    limit: int,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(get_company_id)
):
    """
    Check quota limit.
    
    Args:
        resource: Resource type
        current: Current usage
        limit: Quota limit
        db: Database session
        company_id: Company identifier
        
    Returns:
        Alert data if created
    """
    alert = await advanced_alert_service.check_quota_limit(
        db,
        company_id,
        resource,
        current,
        limit
    )
    
    return {"alert": alert, "checked": True}


@router.post("/custom")
async def create_custom_alert(
    alert_type: str,
    severity: str,
    title: str,
    message: str,
    data: dict = None,
    channels: List[str] = None,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(get_company_id)
):
    """
    Create custom alert.
    
    Args:
        alert_type: Alert type
        severity: Severity level
        title: Alert title
        message: Alert message
        data: Additional data
        channels: Notification channels
        db: Database session
        company_id: Company identifier
        
    Returns:
        Alert data
    """
    try:
        alert_type_enum = AlertType(alert_type)
        severity_enum = AlertSeverity(severity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    channel_enums = []
    if channels:
        for channel in channels:
            try:
                channel_enums.append(NotificationChannel(channel))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid channel: {channel}")
    
    alert = await advanced_alert_service.create_alert(
        db,
        company_id,
        alert_type_enum,
        severity_enum,
        title,
        message,
        data,
        channel_enums or None
    )
    
    return {"alert": alert}


@router.get("/status")
async def get_alert_status(
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(get_company_id)
):
    """
    Get alert service status.
    
    Args:
        db: Database session
        company_id: Company identifier
        
    Returns:
        Service status
    """
    return {
        "service": "alerts",
        "status": "operational",
        "cooldown_minutes": advanced_alert_service.cooldown_minutes,
        "active_cooldowns": len(advanced_alert_service.alert_cooldowns),
        "timestamp": datetime.utcnow().isoformat()
    }
