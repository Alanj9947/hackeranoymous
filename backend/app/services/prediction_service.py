"""Prediction Service - Forecasting and trend analysis."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.call import Call
from app.models.agent import Agent

logger = logging.getLogger(__name__)


class PredictionService:
    """Generate predictions for call volume, costs, and agent performance."""

    @staticmethod
    async def get_call_volume_forecast(
        db: AsyncSession,
        company_id: UUID,
        days_ahead: int = 7,
    ) -> dict:
        """
        Forecast call volume for next N days.

        Args:
            db: Database session
            company_id: Company ID
            days_ahead: Days to forecast (default: 7)

        Returns:
            Forecast data with predictions
        """
        try:
            # Get last 30 days of data
            now = datetime.now(timezone.utc)
            thirty_days_ago = now - timedelta(days=30)

            result = await db.execute(
                select(
                    func.date(Call.created_at).label("date"),
                    func.count(Call.id).label("call_count"),
                ).where(
                    and_(
                        Call.company_id == company_id,
                        Call.created_at >= thirty_days_ago,
                        Call.created_at <= now,
                    )
                )
                .group_by(func.date(Call.created_at))
                .order_by(func.date(Call.created_at))
            )

            historical_data = result.fetchall()

            if not historical_data:
                return {
                    "company_id": str(company_id),
                    "forecast_days": days_ahead,
                    "historical_days": 0,
                    "forecast": [],
                    "confidence": 0.0,
                    "message": "Insufficient historical data",
                }

            # Simple moving average forecast
            call_counts = [row.call_count for row in historical_data]
            avg_calls = sum(call_counts) / len(call_counts)
            trend = (call_counts[-1] - call_counts[0]) / len(call_counts)

            forecast = []
            for i in range(1, days_ahead + 1):
                forecast_date = now + timedelta(days=i)
                predicted_calls = max(
                    0, avg_calls + (trend * i)
                )  # Simple linear trend

                forecast.append(
                    {
                        "date": forecast_date.date().isoformat(),
                        "predicted_calls": round(predicted_calls),
                        "confidence": 0.75 if i <= 3 else 0.60,
                        "trend": "up" if trend > 0 else "down",
                    }
                )

            return {
                "company_id": str(company_id),
                "forecast_days": days_ahead,
                "historical_days": len(call_counts),
                "average_daily_calls": round(avg_calls, 2),
                "trend_per_day": round(trend, 2),
                "forecast": forecast,
                "confidence": 0.75,
                "timestamp": now.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error forecasting call volume: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "company_id": str(company_id),
            }

    @staticmethod
    async def get_cost_forecast(
        db: AsyncSession,
        company_id: UUID,
        days_ahead: int = 30,
    ) -> dict:
        """
        Forecast costs for next N days.

        Args:
            db: Database session
            company_id: Company ID
            days_ahead: Days to forecast (default: 30)

        Returns:
            Cost forecast data
        """
        try:
            # Get last 30 days of cost data
            now = datetime.now(timezone.utc)
            thirty_days_ago = now - timedelta(days=30)

            result = await db.execute(
                select(
                    func.date(Call.created_at).label("date"),
                    func.sum(Call.ai_cost_usd).label("daily_cost"),
                    func.count(Call.id).label("call_count"),
                ).where(
                    and_(
                        Call.company_id == company_id,
                        Call.created_at >= thirty_days_ago,
                        Call.created_at <= now,
                    )
                )
                .group_by(func.date(Call.created_at))
                .order_by(func.date(Call.created_at))
            )

            historical_data = result.fetchall()

            if not historical_data:
                return {
                    "company_id": str(company_id),
                    "forecast_days": days_ahead,
                    "forecast": [],
                    "message": "Insufficient historical data",
                }

            # Calculate costs
            daily_costs = [float(row.daily_cost or 0) for row in historical_data]
            daily_calls = [row.call_count for row in historical_data]

            avg_daily_cost = sum(daily_costs) / len(daily_costs)
            avg_cost_per_call = (
                sum(daily_costs) / sum(daily_calls) if sum(daily_calls) > 0 else 0
            )
            cost_trend = (daily_costs[-1] - daily_costs[0]) / len(daily_costs)

            forecast = []
            for i in range(1, days_ahead + 1):
                forecast_date = now + timedelta(days=i)
                predicted_cost = max(
                    0, avg_daily_cost + (cost_trend * i)
                )

                forecast.append(
                    {
                        "date": forecast_date.date().isoformat(),
                        "predicted_daily_cost": round(predicted_cost, 2),
                        "confidence": 0.75 if i <= 7 else 0.60,
                    }
                )

            # Calculate monthly projection
            monthly_projection = avg_daily_cost * 30

            return {
                "company_id": str(company_id),
                "forecast_days": days_ahead,
                "average_daily_cost": round(avg_daily_cost, 2),
                "average_cost_per_call": round(avg_cost_per_call, 4),
                "monthly_projection": round(monthly_projection, 2),
                "cost_trend_per_day": round(cost_trend, 2),
                "forecast": forecast,
                "confidence": 0.75,
                "timestamp": now.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error forecasting costs: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "company_id": str(company_id),
            }

    @staticmethod
    async def get_agent_performance_forecast(
        db: AsyncSession,
        company_id: UUID,
        agent_id: UUID,
    ) -> dict:
        """
        Forecast agent performance trends.

        Args:
            db: Database session
            company_id: Company ID
            agent_id: Agent ID

        Returns:
            Agent performance forecast
        """
        try:
            # Get agent's last 30 days
            now = datetime.now(timezone.utc)
            thirty_days_ago = now - timedelta(days=30)

            result = await db.execute(
                select(
                    func.count(Call.id).label("total_calls"),
                    func.sum(
                        func.case(
                            (Call.status == "completed", 1),
                            else_=0,
                        )
                    ).label("successful_calls"),
                    func.avg(Call.duration_seconds).label("avg_duration"),
                    func.sum(Call.ai_cost_usd).label("total_cost"),
                ).where(
                    and_(
                        Call.company_id == company_id,
                        Call.agent_id == agent_id,
                        Call.created_at >= thirty_days_ago,
                        Call.created_at <= now,
                    )
                )
            )

            stats = result.first()

            if not stats or stats.total_calls == 0:
                return {
                    "company_id": str(company_id),
                    "agent_id": str(agent_id),
                    "forecast": None,
                    "message": "Insufficient data for this agent",
                }

            # Calculate metrics
            success_rate = (stats.successful_calls or 0) / stats.total_calls
            avg_duration = stats.avg_duration or 0
            total_cost = stats.total_cost or 0
            cost_per_call = total_cost / stats.total_calls

            # Trend analysis (simplified)
            trend = "stable"
            if success_rate > 0.85:
                trend = "excellent"
            elif success_rate > 0.75:
                trend = "good"
            elif success_rate > 0.60:
                trend = "fair"
            else:
                trend = "needs_improvement"

            return {
                "company_id": str(company_id),
                "agent_id": str(agent_id),
                "period": "last_30_days",
                "total_calls": stats.total_calls,
                "successful_calls": stats.successful_calls or 0,
                "success_rate": round(success_rate, 3),
                "average_duration_seconds": round(avg_duration, 2),
                "total_cost": round(total_cost, 2),
                "cost_per_call": round(cost_per_call, 4),
                "trend": trend,
                "recommendation": PredictionService._get_recommendation(
                    success_rate, avg_duration
                ),
                "confidence": 0.85,
                "timestamp": now.isoformat(),
            }

        except Exception as e:
            logger.error(
                f"Error forecasting agent performance: {str(e)}", exc_info=True
            )
            return {
                "error": str(e),
                "agent_id": str(agent_id),
            }

    @staticmethod
    def _get_recommendation(success_rate: float, avg_duration: float) -> str:
        """Get performance recommendation based on metrics."""
        recommendations = []

        if success_rate < 0.75:
            recommendations.append(
                "Focus on improving call success rate through coaching"
            )
        if avg_duration > 600:  # > 10 minutes
            recommendations.append("Consider efficiency training to reduce call duration")
        if success_rate > 0.90:
            recommendations.append("Excellent performance - consider as a mentor")

        if not recommendations:
            recommendations.append("Continue current performance level")

        return recommendations[0] if recommendations else "No specific recommendation"

    @staticmethod
    async def detect_anomalies(
        db: AsyncSession,
        company_id: UUID,
    ) -> dict:
        """
        Detect anomalies in call patterns.

        Args:
            db: Database session
            company_id: Company ID

        Returns:
            List of detected anomalies
        """
        try:
            # Get today's stats
            now = datetime.now(timezone.utc)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

            today_result = await db.execute(
                select(
                    func.count(Call.id).label("total_calls"),
                    func.sum(
                        func.case(
                            (
                                Call.status.in_(["failed", "no-answer", "busy"]),
                                1,
                            ),
                            else_=0,
                        )
                    ).label("error_count"),
                ).where(
                    and_(
                        Call.company_id == company_id,
                        Call.created_at >= today_start,
                        Call.created_at <= now,
                    )
                )
            )

            today_stats = today_result.first()

            # Get yesterday's stats for comparison
            yesterday_start = today_start - timedelta(days=1)
            yesterday_end = today_start

            yesterday_result = await db.execute(
                select(
                    func.count(Call.id).label("total_calls"),
                    func.sum(
                        func.case(
                            (
                                Call.status.in_(["failed", "no-answer", "busy"]),
                                1,
                            ),
                            else_=0,
                        )
                    ).label("error_count"),
                ).where(
                    and_(
                        Call.company_id == company_id,
                        Call.created_at >= yesterday_start,
                        Call.created_at < yesterday_end,
                    )
                )
            )

            yesterday_stats = yesterday_result.first()

            anomalies = []

            # Compare today vs yesterday
            today_calls = today_stats.total_calls or 0
            yesterday_calls = yesterday_stats.total_calls or 0

            if yesterday_calls > 0:
                call_change_percent = ((today_calls - yesterday_calls) / yesterday_calls) * 100

                if abs(call_change_percent) > 50:
                    anomalies.append(
                        {
                            "type": "volume_spike",
                            "severity": "warning" if call_change_percent > 0 else "info",
                            "message": f"Call volume changed by {abs(call_change_percent):.1f}%",
                            "percent_change": round(call_change_percent, 1),
                        }
                    )

            # Check error rate
            if today_calls > 0:
                today_error_rate = (today_stats.error_count or 0) / today_calls
                if today_error_rate > 0.10:  # > 10% error rate
                    anomalies.append(
                        {
                            "type": "high_error_rate",
                            "severity": "critical",
                            "message": f"Error rate is {today_error_rate*100:.1f}%",
                            "error_rate": round(today_error_rate, 3),
                        }
                    )

            return {
                "company_id": str(company_id),
                "anomaly_count": len(anomalies),
                "anomalies": anomalies,
                "timestamp": now.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "company_id": str(company_id),
                "anomalies": [],
            }
