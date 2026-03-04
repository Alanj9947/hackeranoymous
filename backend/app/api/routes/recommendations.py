"""Recommendations engine API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.auth import get_company_id
from app.services.recommendations_service import (
    recommendations_engine,
    RecommendationPriority
)

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


@router.post("/analyze-agent/{agent_id}")
async def analyze_agent(
    agent_id: str,
    accuracy: float,
    avg_handle_time: float,
    customer_satisfaction: float,
    team_avg_handle_time: float = None,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(get_company_id)
):
    """
    Analyze agent and generate recommendations.
    
    Args:
        agent_id: Agent identifier
        accuracy: Call accuracy percentage (0-100)
        avg_handle_time: Average handle time in seconds
        customer_satisfaction: Satisfaction score (0-5)
        team_avg_handle_time: Team average handle time
        db: Database session
        company_id: Company identifier
        
    Returns:
        List of recommendations
    """
    metrics = {
        "accuracy": accuracy,
        "avg_handle_time": avg_handle_time,
        "customer_satisfaction": customer_satisfaction,
        "team_avg_handle_time": team_avg_handle_time or avg_handle_time
    }

    recommendations = await recommendations_engine.analyze_agent(
        company_id,
        agent_id,
        metrics
    )

    return {
        "agent_id": agent_id,
        "recommendations": [
            {
                "id": r.recommendation_id,
                "type": r.type.value,
                "priority": r.priority.value,
                "title": r.title,
                "description": r.description,
                "impact_score": r.impact_score,
                "estimated_benefit": r.estimated_benefit,
                "action_items": r.action_items
            }
            for r in recommendations
        ],
        "count": len(recommendations)
    }


@router.post("/analyze-team")
async def analyze_team(
    agents_metrics: dict,
    company_id: str = Depends(get_company_id)
):
    """
    Analyze team and generate team-wide recommendations.
    
    Args:
        agents_metrics: Dict of agent metrics
        company_id: Company identifier
        
    Returns:
        List of team recommendations
    """
    recommendations = await recommendations_engine.analyze_team(
        company_id,
        agents_metrics
    )

    return {
        "team_recommendations": [
            {
                "id": r.recommendation_id,
                "type": r.type.value,
                "priority": r.priority.value,
                "title": r.title,
                "description": r.description,
                "impact_score": r.impact_score,
                "estimated_benefit": r.estimated_benefit
            }
            for r in recommendations
        ],
        "count": len(recommendations)
    }


@router.get("/agent/{agent_id}")
async def get_agent_recommendations(
    agent_id: str,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    company_id: str = Depends(get_company_id)
):
    """Get recommendations for agent."""
    priority_enum = None
    if priority:
        try:
            priority_enum = RecommendationPriority(priority)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid priority: {priority}")

    recommendations = await recommendations_engine.get_recommendations(
        company_id,
        agent_id,
        priority_enum,
        status
    )

    return {
        "agent_id": agent_id,
        "recommendations": [
            {
                "id": r.recommendation_id,
                "type": r.type.value,
                "priority": r.priority.value,
                "title": r.title,
                "status": r.status,
                "impact_score": r.impact_score
            }
            for r in recommendations
        ],
        "count": len(recommendations)
    }


@router.post("/{recommendation_id}/accept")
async def accept_recommendation(
    recommendation_id: str,
    agent_id: str,
    company_id: str = Depends(get_company_id)
):
    """Accept a recommendation."""
    success = await recommendations_engine.accept_recommendation(
        recommendation_id,
        agent_id,
        company_id
    )

    if not success:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    return {"accepted": True}


@router.post("/{recommendation_id}/reject")
async def reject_recommendation(
    recommendation_id: str,
    agent_id: str,
    reason: Optional[str] = None,
    company_id: str = Depends(get_company_id)
):
    """Reject a recommendation."""
    success = await recommendations_engine.reject_recommendation(
        recommendation_id,
        agent_id,
        company_id,
        reason
    )

    if not success:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    return {"rejected": True}


@router.get("/agent/{agent_id}/impact")
async def get_impact_score(
    agent_id: str,
    company_id: str = Depends(get_company_id)
):
    """
    Get potential impact score for agent.
    
    Shows current vs potential productivity with implementation of recommendations.
    """
    impact = await recommendations_engine.get_impact_score(company_id, agent_id)

    return {
        "agent_id": agent_id,
        "current_productivity": impact["current_productivity"],
        "potential_productivity": impact["potential_productivity"],
        "improvement_potential": impact["improvement_potential"],
        "estimated_roi": impact["estimated_roi"]
    }
