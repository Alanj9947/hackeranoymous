"""Call quality scoring API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional, List

from app.core.database import get_db
from app.core.auth import get_company_id
from app.services.quality_service import call_quality_service

router = APIRouter(prefix="/api/v1/quality", tags=["quality"])


@router.post("/score")
async def score_call(
    call_id: str,
    duration_seconds: int,
    success: bool,
    sentiment_score: Optional[float] = None,
    transcript_length: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(get_company_id)
):
    """
    Calculate quality score for a call.
    
    Args:
        call_id: Call identifier
        duration_seconds: Call duration in seconds
        success: Was call successful
        sentiment_score: Sentiment score (0-1)
        transcript_length: Transcript word count
        db: Database session
        company_id: Company identifier
        
    Returns:
        Quality score data
    """
    score = await call_quality_service.calculate_call_quality(
        db,
        call_id,
        duration_seconds,
        success,
        sentiment_score,
        transcript_length
    )
    
    return score


@router.post("/score-batch")
async def score_calls_batch(
    calls: List[dict],
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(get_company_id)
):
    """
    Score multiple calls in batch.
    
    Args:
        calls: List of call data
        db: Database session
        company_id: Company identifier
        
    Returns:
        List of scored calls
    """
    scores = await call_quality_service.batch_score_calls(db, calls)
    
    return {
        "total_calls": len(scores),
        "scores": scores,
        "summary": call_quality_service.get_quality_stats_summary(scores)
    }


@router.get("/agent/{agent_id}/metrics")
async def get_agent_quality_metrics(
    agent_id: str,
    days: int = Query(7, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(get_company_id)
):
    """
    Get quality metrics for an agent.
    
    Args:
        agent_id: Agent identifier
        days: Number of days to analyze
        db: Database session
        company_id: Company identifier
        
    Returns:
        Agent quality metrics
    """
    metrics = await call_quality_service.get_agent_quality_metrics(
        db,
        agent_id,
        days
    )
    
    return metrics


@router.get("/agent/{agent_id}/trend")
async def get_agent_quality_trend(
    agent_id: str,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(get_company_id)
):
    """
    Get quality score trend for an agent.
    
    Args:
        agent_id: Agent identifier
        days: Number of days to analyze
        db: Database session
        company_id: Company identifier
        
    Returns:
        Trend data points
    """
    trend = await call_quality_service.get_quality_trend(
        db,
        agent_id,
        days
    )
    
    return {
        "agent_id": agent_id,
        "period_days": days,
        "trend": trend
    }


@router.get("/stats")
async def get_quality_service_status(
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(get_company_id)
):
    """
    Get quality service status.
    
    Args:
        db: Database session
        company_id: Company identifier
        
    Returns:
        Service status
    """
    return {
        "service": "quality_scoring",
        "status": "operational",
        "scoring_weights": call_quality_service.weights,
        "quality_levels": {
            "excellent": "Score >= 85",
            "good": "Score >= 70",
            "fair": "Score >= 55",
            "poor": "Score < 55"
        },
        "timestamp": datetime.utcnow().isoformat()
    }
