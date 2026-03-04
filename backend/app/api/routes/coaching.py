"""Coaching routes - Agent performance coaching endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_company_id
from app.services.coaching_service import CoachingService

router = APIRouter(prefix="/api/v1/coaching", tags=["coaching"])


@router.get("/agents/{agent_id}/insights")
async def get_agent_insights(
    agent_id: UUID,
    company_id: UUID = Depends(get_company_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get coaching insights for a specific agent.

    Args:
        agent_id: Agent ID
        company_id: Company ID (from auth)
        db: Database session

    Returns:
        Coaching insights including scores and recommendations
    """
    result = await CoachingService.get_agent_coaching_insights(
        db, company_id, agent_id
    )
    return result


@router.get("/team-report")
async def get_team_coaching_report(
    company_id: UUID = Depends(get_company_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get coaching report for entire team.

    Args:
        company_id: Company ID (from auth)
        db: Database session

    Returns:
        Team coaching report with rankings and comparisons
    """
    result = await CoachingService.get_team_coaching_report(db, company_id)
    return result
