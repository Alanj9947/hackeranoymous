"""Analytics routes - Prediction endpoints."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_company_id
from app.services.prediction_service import PredictionService

router = APIRouter(prefix="/api/v1/predictions", tags=["predictions"])


@router.get("/call-volume")
async def get_call_volume_forecast(
    days_ahead: int = Query(7, ge=1, le=30),
    company_id: UUID = Depends(get_company_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get call volume forecast.

    Args:
        days_ahead: Days to forecast (1-30, default: 7)
        company_id: Company ID (from auth)
        db: Database session

    Returns:
        Forecast data with predictions and confidence
    """
    result = await PredictionService.get_call_volume_forecast(
        db, company_id, days_ahead
    )
    return result


@router.get("/costs")
async def get_cost_forecast(
    days_ahead: int = Query(30, ge=1, le=90),
    company_id: UUID = Depends(get_company_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get cost forecast for next N days.

    Args:
        days_ahead: Days to forecast (1-90, default: 30)
        company_id: Company ID (from auth)
        db: Database session

    Returns:
        Cost forecast with monthly projection
    """
    result = await PredictionService.get_cost_forecast(db, company_id, days_ahead)
    return result


@router.get("/agent-performance/{agent_id}")
async def get_agent_performance_forecast(
    agent_id: UUID,
    company_id: UUID = Depends(get_company_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get agent performance forecast and recommendations.

    Args:
        agent_id: Agent ID
        company_id: Company ID (from auth)
        db: Database session

    Returns:
        Agent performance metrics and trends
    """
    result = await PredictionService.get_agent_performance_forecast(
        db, company_id, agent_id
    )
    return result


@router.get("/anomalies")
async def detect_anomalies(
    company_id: UUID = Depends(get_company_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Detect anomalies in call patterns.

    Args:
        company_id: Company ID (from auth)
        db: Database session

    Returns:
        List of detected anomalies with severity levels
    """
    result = await PredictionService.detect_anomalies(db, company_id)
    return result
