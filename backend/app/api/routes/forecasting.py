"""ML Forecasting API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_company_id
from app.services.forecasting_service import (
    forecasting_service,
    ForecastMetric,
    ForecastModel
)

router = APIRouter(prefix="/api/v1/forecasting", tags=["forecasting"])


@router.post("/data-point")
async def add_data_point(
    metric: str,
    value: float,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(get_company_id)
):
    """
    Add data point for forecasting.
    
    Args:
        metric: Metric type (call_volume, cost, etc.)
        value: Data value
        db: Database session
        company_id: Company identifier
        
    Returns:
        Addition status
    """
    try:
        metric_enum = ForecastMetric(metric.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown metric: {metric}")

    success = await forecasting_service.add_data_point(
        company_id,
        metric_enum,
        value,
        timestamp=datetime.utcnow()
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to add data point")

    return {
        "metric": metric,
        "value": value,
        "added": True
    }


@router.get("/forecast/{metric}")
async def get_forecast(
    metric: str,
    horizon_days: int = Query(30, ge=1, le=90),
    model: str = Query("exponential_smoothing"),
    company_id: str = Depends(get_company_id)
):
    """
    Generate forecast for metric.
    
    Args:
        metric: Metric to forecast
        horizon_days: Forecast horizon (1-90 days)
        model: Forecasting model
        company_id: Company identifier
        
    Returns:
        Forecast results
    """
    try:
        metric_enum = ForecastMetric(metric.lower())
        model_enum = ForecastModel(model.lower())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    forecast = await forecasting_service.forecast(
        company_id,
        metric_enum,
        horizon_days,
        model_enum
    )

    if not forecast:
        raise HTTPException(status_code=400, detail="Unable to generate forecast")

    return {
        "metric": metric,
        "model": model,
        "horizon_days": horizon_days,
        "trend": forecast.trend,
        "accuracy": forecast.accuracy_score,
        "predictions": [
            {"timestamp": ts.isoformat(), "value": val}
            for ts, val in forecast.predictions
        ],
        "confidence_intervals": [
            {"lower": lower, "upper": upper}
            for lower, upper in forecast.confidence_intervals
        ],
        "metadata": forecast.metadata
    }


@router.post("/scenario")
async def what_if_scenario(
    metric: str,
    adjustment_percent: float = Query(0, ge=-100, le=100),
    horizon_days: int = Query(30, ge=1, le=90),
    company_id: str = Depends(get_company_id)
):
    """
    Generate what-if scenario forecast.
    
    Args:
        metric: Metric to forecast
        adjustment_percent: Adjustment percentage (-100 to +100)
        horizon_days: Forecast horizon
        company_id: Company identifier
        
    Returns:
        Adjusted forecast
    """
    try:
        metric_enum = ForecastMetric(metric.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown metric: {metric}")

    forecast = await forecasting_service.what_if_scenario(
        company_id,
        metric_enum,
        adjustment_percent,
        horizon_days
    )

    if not forecast:
        raise HTTPException(status_code=400, detail="Unable to generate scenario")

    return {
        "metric": metric,
        "scenario": "what_if",
        "adjustment_percent": adjustment_percent,
        "horizon_days": horizon_days,
        "predictions": [
            {"timestamp": ts.isoformat(), "value": val}
            for ts, val in forecast.predictions
        ],
        "confidence_intervals": [
            {"lower": lower, "upper": upper}
            for lower, upper in forecast.confidence_intervals
        ]
    }


@router.get("/anomalies/{metric}")
async def detect_anomalies(
    metric: str,
    threshold: float = Query(2.0, ge=1.0, le=5.0),
    company_id: str = Depends(get_company_id)
):
    """
    Detect anomalies in metric data.
    
    Args:
        metric: Metric to analyze
        threshold: Standard deviation threshold
        company_id: Company identifier
        
    Returns:
        Detected anomalies
    """
    try:
        metric_enum = ForecastMetric(metric.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown metric: {metric}")

    anomalies = await forecasting_service.detect_anomalies(
        company_id,
        metric_enum,
        threshold
    )

    return {
        "metric": metric,
        "threshold": threshold,
        "anomalies": anomalies,
        "count": len(anomalies)
    }


@router.get("/trends")
async def get_trends(
    company_id: str = Depends(get_company_id)
):
    """
    Get trend analysis for all metrics.
    
    Args:
        company_id: Company identifier
        
    Returns:
        Trend information
    """
    trends = {}

    for metric in ForecastMetric:
        forecast = await forecasting_service.get_recent_forecast(company_id, metric)
        if forecast:
            trends[metric.value] = {
                "trend": forecast.trend,
                "accuracy": forecast.accuracy_score,
                "last_updated": forecast.timestamp.isoformat(),
                "last_value": forecast.metadata.get("last_value"),
                "avg_value": forecast.metadata.get("avg_value")
            }

    return {
        "company_id": company_id,
        "trends": trends
    }


@router.get("/model-comparison/{metric}")
async def compare_models(
    metric: str,
    horizon_days: int = Query(30, ge=1, le=90),
    company_id: str = Depends(get_company_id)
):
    """
    Compare forecasting models for metric.
    
    Args:
        metric: Metric to analyze
        horizon_days: Forecast horizon
        company_id: Company identifier
        
    Returns:
        Model comparison results
    """
    try:
        metric_enum = ForecastMetric(metric.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown metric: {metric}")

    results = {}

    for model in ForecastModel:
        forecast = await forecasting_service.forecast(
            company_id,
            metric_enum,
            horizon_days,
            model
        )

        if forecast:
            results[model.value] = {
                "accuracy": forecast.accuracy_score,
                "trend": forecast.trend,
                "latest_prediction": forecast.predictions[-1][1] if forecast.predictions else None
            }

    return {
        "metric": metric,
        "horizon_days": horizon_days,
        "models": results
    }
