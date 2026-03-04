"""API endpoints for analytics and insights."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.api.deps import get_company_id
from app.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/calls/summary")
async def get_calls_summary(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_session),
    company_id: UUID = Depends(get_company_id),
):
    """
    Get overall call statistics.

    Query params:
    - date_from: ISO format date (default: 7 days ago)
    - date_to: ISO format date (default: now)

    Returns:
    - total_calls, success_rate, avg_duration, total_cost, etc.
    """
    try:
        date_from_dt = None
        date_to_dt = None

        if date_from:
            date_from_dt = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
        if date_to:
            date_to_dt = datetime.fromisoformat(date_to.replace("Z", "+00:00"))

        stats = await AnalyticsService.get_call_stats(
            db=db,
            company_id=company_id,
            date_from=date_from_dt,
            date_to=date_to_dt,
        )

        return stats

    except Exception as e:
        logger.error(f"Error getting calls summary: {str(e)}")
        raise


@router.get("/calls/by-agent")
async def get_calls_by_agent(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_async_session),
    company_id: UUID = Depends(get_company_id),
):
    """Get per-agent call statistics."""
    try:
        date_from_dt = None
        date_to_dt = None

        if date_from:
            date_from_dt = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
        if date_to:
            date_to_dt = datetime.fromisoformat(date_to.replace("Z", "+00:00"))

        agents = await AnalyticsService.get_calls_by_agent(
            db=db,
            company_id=company_id,
            date_from=date_from_dt,
            date_to=date_to_dt,
            limit=limit,
        )

        return {
            "count": len(agents),
            "agents": agents,
        }

    except Exception as e:
        logger.error(f"Error getting calls by agent: {str(e)}")
        raise


@router.get("/calls/by-phone")
async def get_calls_by_phone(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_async_session),
    company_id: UUID = Depends(get_company_id),
):
    """Get per-phone-number call statistics."""
    try:
        date_from_dt = None
        date_to_dt = None

        if date_from:
            date_from_dt = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
        if date_to:
            date_to_dt = datetime.fromisoformat(date_to.replace("Z", "+00:00"))

        phones = await AnalyticsService.get_calls_by_phone(
            db=db,
            company_id=company_id,
            date_from=date_from_dt,
            date_to=date_to_dt,
            limit=limit,
        )

        return {
            "count": len(phones),
            "phones": phones,
        }

    except Exception as e:
        logger.error(f"Error getting calls by phone: {str(e)}")
        raise


@router.get("/calls/trend")
async def get_call_trends(
    bucket: str = Query("day", regex="^(day|week|month)$"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_async_session),
    company_id: UUID = Depends(get_company_id),
):
    """
    Get call volume trends.

    Query params:
    - bucket: 'day', 'week', or 'month'
    - date_from: ISO format date
    - date_to: ISO format date
    """
    try:
        date_from_dt = None
        date_to_dt = None

        if date_from:
            date_from_dt = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
        if date_to:
            date_to_dt = datetime.fromisoformat(date_to.replace("Z", "+00:00"))

        trends = await AnalyticsService.get_call_trends(
            db=db,
            company_id=company_id,
            bucket=bucket,
            date_from=date_from_dt,
            date_to=date_to_dt,
            limit=limit,
        )

        return {
            "bucket": bucket,
            "count": len(trends),
            "trends": trends,
        }

    except Exception as e:
        logger.error(f"Error getting call trends: {str(e)}")
        raise


@router.get("/agents/{agent_id}/metrics")
async def get_agent_metrics(
    agent_id: UUID,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_session),
    company_id: UUID = Depends(get_company_id),
):
    """Get metrics for a specific agent."""
    try:
        date_from_dt = None
        date_to_dt = None

        if date_from:
            date_from_dt = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
        if date_to:
            date_to_dt = datetime.fromisoformat(date_to.replace("Z", "+00:00"))

        metrics = await AnalyticsService.get_agent_metrics(
            db=db,
            agent_id=agent_id,
            date_from=date_from_dt,
            date_to=date_to_dt,
        )

        if not metrics:
            return {"error": "Agent not found"}

        return metrics

    except Exception as e:
        logger.error(f"Error getting agent metrics: {str(e)}")
        raise


@router.get("/agents/ranking")
async def get_agent_ranking(
    metric: str = Query("calls", regex="^(calls|duration|success_rate|cost)$"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_async_session),
    company_id: UUID = Depends(get_company_id),
):
    """Get agents ranked by metric."""
    try:
        date_from_dt = None
        date_to_dt = None

        if date_from:
            date_from_dt = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
        if date_to:
            date_to_dt = datetime.fromisoformat(date_to.replace("Z", "+00:00"))

        agents = await AnalyticsService.get_calls_by_agent(
            db=db,
            company_id=company_id,
            date_from=date_from_dt,
            date_to=date_to_dt,
            limit=limit,
        )

        # Sort by metric
        if metric == "calls":
            agents.sort(key=lambda x: x["total_calls"], reverse=True)
        elif metric == "duration":
            agents.sort(key=lambda x: x["avg_duration_seconds"], reverse=True)
        elif metric == "success_rate":
            agents.sort(key=lambda x: x["success_rate"], reverse=True)
        elif metric == "cost":
            agents.sort(key=lambda x: x["total_cost_usd"], reverse=True)

        # Add ranking
        for i, agent in enumerate(agents, 1):
            agent["rank"] = i

        return {
            "metric": metric,
            "count": len(agents),
            "agents": agents,
        }

    except Exception as e:
        logger.error(f"Error getting agent ranking: {str(e)}")
        raise


@router.get("/costs/summary")
async def get_costs_summary(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_session),
    company_id: UUID = Depends(get_company_id),
):
    """Get cost breakdown by service."""
    try:
        date_from_dt = None
        date_to_dt = None

        if date_from:
            date_from_dt = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
        if date_to:
            date_to_dt = datetime.fromisoformat(date_to.replace("Z", "+00:00"))

        costs = await AnalyticsService.get_costs_summary(
            db=db,
            company_id=company_id,
            date_from=date_from_dt,
            date_to=date_to_dt,
        )

        return costs

    except Exception as e:
        logger.error(f"Error getting costs summary: {str(e)}")
        raise


@router.get("/costs/trend")
async def get_cost_trends(
    bucket: str = Query("day", regex="^(day|week|month)$"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_async_session),
    company_id: UUID = Depends(get_company_id),
):
    """Get cost trends over time."""
    try:
        date_from_dt = None
        date_to_dt = None

        if date_from:
            date_from_dt = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
        if date_to:
            date_to_dt = datetime.fromisoformat(date_to.replace("Z", "+00:00"))

        trends = await AnalyticsService.get_call_trends(
            db=db,
            company_id=company_id,
            bucket=bucket,
            date_from=date_from_dt,
            date_to=date_to_dt,
            limit=limit,
        )

        return {
            "bucket": bucket,
            "count": len(trends),
            "trends": trends,
        }

    except Exception as e:
        logger.error(f"Error getting cost trends: {str(e)}")
        raise


@router.get("/health")
async def get_system_health(
    db: AsyncSession = Depends(get_async_session),
    company_id: UUID = Depends(get_company_id),
):
    """Get system health metrics."""
    try:
        health = await AnalyticsService.get_system_health(
            db=db,
            company_id=company_id,
        )

        return health

    except Exception as e:
        logger.error(f"Error getting system health: {str(e)}")
        raise
