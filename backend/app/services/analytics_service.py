"""Analytics Service - Core analytics calculations and aggregations."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.call import Call, CallTranscript
from app.models.agent import Agent
from app.models.phone_number import PhoneNumber

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Calculate and aggregate call, agent, and cost metrics."""

    @staticmethod
    async def get_call_stats(
        db: AsyncSession,
        company_id: UUID,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> dict:
        """
        Get overall call statistics for company.

        Args:
            db: Database session
            company_id: Company ID
            date_from: Start date (default: 7 days ago)
            date_to: End date (default: now)

        Returns:
            {
                total_calls: int,
                successful_calls: int,
                failed_calls: int,
                success_rate: float,
                avg_duration_seconds: float,
                total_duration_seconds: int,
                total_cost_usd: float,
                calls_by_status: {status: count, ...}
            }
        """
        try:
            # Set defaults
            if not date_to:
                date_to = datetime.now(timezone.utc)
            if not date_from:
                date_from = date_to - timedelta(days=7)

            # Query calls
            result = await db.execute(
                select(
                    func.count(Call.id).label("total"),
                    func.sum(
                        func.case(
                            (Call.status == "completed", 1),
                            else_=0,
                        )
                    ).label("successful"),
                    func.sum(
                        func.case(
                            (Call.status.in_(["failed", "no-answer", "busy"]), 1),
                            else_=0,
                        )
                    ).label("failed"),
                    func.avg(Call.duration_seconds).label("avg_duration"),
                    func.sum(Call.duration_seconds).label("total_duration"),
                    func.sum(Call.ai_cost_usd).label("total_cost"),
                ).where(
                    and_(
                        Call.company_id == company_id,
                        Call.created_at >= date_from,
                        Call.created_at <= date_to,
                    )
                )
            )
            row = result.first()

            total_calls = row.total or 0
            successful = row.successful or 0
            failed = row.failed or 0
            avg_duration = row.avg_duration or 0
            total_duration = row.total_duration or 0
            total_cost = row.total_cost or 0.0

            success_rate = (successful / total_calls * 100) if total_calls > 0 else 0

            # Get status breakdown
            result = await db.execute(
                select(Call.status, func.count(Call.id).label("count")).where(
                    and_(
                        Call.company_id == company_id,
                        Call.created_at >= date_from,
                        Call.created_at <= date_to,
                    )
                ).group_by(Call.status)
            )
            status_breakdown = {row.status: row.count for row in result.all()}

            return {
                "total_calls": total_calls,
                "successful_calls": successful,
                "failed_calls": failed,
                "success_rate": round(success_rate, 2),
                "avg_duration_seconds": round(float(avg_duration), 2),
                "total_duration_seconds": int(total_duration) if total_duration else 0,
                "total_cost_usd": round(float(total_cost), 2),
                "calls_by_status": status_breakdown,
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting call stats: {str(e)}", exc_info=True)
            return {}

    @staticmethod
    async def get_calls_by_agent(
        db: AsyncSession,
        company_id: UUID,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[dict]:
        """Get per-agent statistics."""
        try:
            if not date_to:
                date_to = datetime.now(timezone.utc)
            if not date_from:
                date_from = date_to - timedelta(days=7)

            result = await db.execute(
                select(
                    Agent.id,
                    Agent.name,
                    func.count(Call.id).label("total_calls"),
                    func.sum(
                        func.case((Call.status == "completed", 1), else_=0)
                    ).label("successful_calls"),
                    func.avg(Call.duration_seconds).label("avg_duration"),
                    func.sum(Call.ai_cost_usd).label("total_cost"),
                )
                .join(Call, Call.agent_id == Agent.id)
                .where(
                    and_(
                        Call.company_id == company_id,
                        Call.created_at >= date_from,
                        Call.created_at <= date_to,
                    )
                )
                .group_by(Agent.id, Agent.name)
                .order_by(func.count(Call.id).desc())
                .limit(limit)
            )

            agents = []
            for row in result.all():
                total = row.total_calls or 0
                successful = row.successful_calls or 0
                success_rate = (successful / total * 100) if total > 0 else 0

                agents.append(
                    {
                        "agent_id": str(row.id),
                        "agent_name": row.name,
                        "total_calls": total,
                        "successful_calls": successful,
                        "success_rate": round(success_rate, 2),
                        "avg_duration_seconds": round(float(row.avg_duration or 0), 2),
                        "total_cost_usd": round(float(row.total_cost or 0), 2),
                    }
                )

            return agents

        except Exception as e:
            logger.error(f"Error getting calls by agent: {str(e)}", exc_info=True)
            return []

    @staticmethod
    async def get_calls_by_phone(
        db: AsyncSession,
        company_id: UUID,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[dict]:
        """Get per-phone-number statistics."""
        try:
            if not date_to:
                date_to = datetime.now(timezone.utc)
            if not date_from:
                date_from = date_to - timedelta(days=7)

            result = await db.execute(
                select(
                    PhoneNumber.id,
                    PhoneNumber.phone_number,
                    func.count(Call.id).label("total_calls"),
                    func.sum(
                        func.case((Call.status == "completed", 1), else_=0)
                    ).label("successful_calls"),
                    func.avg(Call.duration_seconds).label("avg_duration"),
                )
                .join(Call, Call.to_number == PhoneNumber.phone_number)
                .where(
                    and_(
                        PhoneNumber.company_id == company_id,
                        Call.created_at >= date_from,
                        Call.created_at <= date_to,
                    )
                )
                .group_by(PhoneNumber.id, PhoneNumber.phone_number)
                .order_by(func.count(Call.id).desc())
                .limit(limit)
            )

            phones = []
            for row in result.all():
                total = row.total_calls or 0
                successful = row.successful_calls or 0
                success_rate = (successful / total * 100) if total > 0 else 0

                phones.append(
                    {
                        "phone_number_id": str(row.id),
                        "phone_number": row.phone_number,
                        "total_calls": total,
                        "successful_calls": successful,
                        "success_rate": round(success_rate, 2),
                        "avg_duration_seconds": round(float(row.avg_duration or 0), 2),
                    }
                )

            return phones

        except Exception as e:
            logger.error(f"Error getting calls by phone: {str(e)}", exc_info=True)
            return []

    @staticmethod
    async def get_call_trends(
        db: AsyncSession,
        company_id: UUID,
        bucket: str = "day",
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[dict]:
        """
        Get call volume trends over time.

        Args:
            db: Database session
            company_id: Company ID
            bucket: 'day', 'week', or 'month'
            date_from: Start date
            date_to: End date

        Returns:
            List of {date, count, duration, cost}
        """
        try:
            if not date_to:
                date_to = datetime.now(timezone.utc)
            if not date_from:
                date_from = date_to - timedelta(days=30)

            # Determine grouping based on bucket
            if bucket == "day":
                date_trunc = func.date(Call.created_at)
            elif bucket == "week":
                date_trunc = func.date_trunc("week", Call.created_at)
            else:  # month
                date_trunc = func.date_trunc("month", Call.created_at)

            result = await db.execute(
                select(
                    date_trunc.label("period"),
                    func.count(Call.id).label("count"),
                    func.avg(Call.duration_seconds).label("avg_duration"),
                    func.sum(Call.ai_cost_usd).label("total_cost"),
                )
                .where(
                    and_(
                        Call.company_id == company_id,
                        Call.created_at >= date_from,
                        Call.created_at <= date_to,
                    )
                )
                .group_by(date_trunc)
                .order_by(date_trunc)
                .limit(limit)
            )

            trends = []
            for row in result.all():
                trends.append(
                    {
                        "date": row.period.isoformat() if row.period else None,
                        "call_count": row.count or 0,
                        "avg_duration_seconds": round(float(row.avg_duration or 0), 2),
                        "total_cost_usd": round(float(row.total_cost or 0), 2),
                    }
                )

            return trends

        except Exception as e:
            logger.error(f"Error getting call trends: {str(e)}", exc_info=True)
            return []

    @staticmethod
    async def get_agent_metrics(
        db: AsyncSession,
        agent_id: UUID,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> dict:
        """Get detailed metrics for a specific agent."""
        try:
            if not date_to:
                date_to = datetime.now(timezone.utc)
            if not date_from:
                date_from = date_to - timedelta(days=30)

            # Get agent basic info
            result = await db.execute(select(Agent).where(Agent.id == agent_id))
            agent = result.scalar_one_or_none()

            if not agent:
                return {}

            # Get call stats
            result = await db.execute(
                select(
                    func.count(Call.id).label("total"),
                    func.sum(
                        func.case((Call.status == "completed", 1), else_=0)
                    ).label("successful"),
                    func.avg(Call.duration_seconds).label("avg_duration"),
                    func.sum(Call.duration_seconds).label("total_duration"),
                    func.sum(Call.ai_cost_usd).label("total_cost"),
                ).where(
                    and_(
                        Call.agent_id == agent_id,
                        Call.created_at >= date_from,
                        Call.created_at <= date_to,
                    )
                )
            )
            row = result.first()

            total_calls = row.total or 0
            successful = row.successful or 0
            success_rate = (successful / total_calls * 100) if total_calls > 0 else 0

            return {
                "agent_id": str(agent.id),
                "agent_name": agent.name,
                "total_calls": total_calls,
                "successful_calls": successful,
                "success_rate": round(success_rate, 2),
                "avg_duration_seconds": round(float(row.avg_duration or 0), 2),
                "total_duration_seconds": int(row.total_duration or 0),
                "total_cost_usd": round(float(row.total_cost or 0), 2),
            }

        except Exception as e:
            logger.error(f"Error getting agent metrics: {str(e)}", exc_info=True)
            return {}

    @staticmethod
    async def get_costs_summary(
        db: AsyncSession,
        company_id: UUID,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> dict:
        """Get cost breakdown by service."""
        try:
            if not date_to:
                date_to = datetime.now(timezone.utc)
            if not date_from:
                date_from = date_to - timedelta(days=30)

            # Total costs
            result = await db.execute(
                select(func.sum(Call.ai_cost_usd).label("total")).where(
                    and_(
                        Call.company_id == company_id,
                        Call.created_at >= date_from,
                        Call.created_at <= date_to,
                    )
                )
            )
            total_cost = result.scalar() or 0.0

            # Get call count for cost per call
            result = await db.execute(
                select(func.count(Call.id).label("count")).where(
                    and_(
                        Call.company_id == company_id,
                        Call.created_at >= date_from,
                        Call.created_at <= date_to,
                        Call.status == "completed",
                    )
                )
            )
            completed_calls = result.scalar() or 1

            cost_per_call = total_cost / completed_calls if completed_calls > 0 else 0

            # Estimate service breakdown (approximate)
            # Assuming: 40% OpenAI (STT + LLM), 30% ElevenLabs (TTS), 30% Twilio
            return {
                "total_cost_usd": round(float(total_cost), 2),
                "cost_per_call": round(float(cost_per_call), 2),
                "completed_calls": completed_calls,
                "estimated_breakdown": {
                    "openai_usd": round(float(total_cost * 0.4), 2),
                    "elevenlabs_usd": round(float(total_cost * 0.3), 2),
                    "twilio_usd": round(float(total_cost * 0.3), 2),
                },
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting costs summary: {str(e)}", exc_info=True)
            return {}

    @staticmethod
    async def get_system_health(
        db: AsyncSession,
        company_id: UUID,
    ) -> dict:
        """Get system health metrics."""
        try:
            # Get last 24 hours error rate
            result = await db.execute(
                select(
                    func.count(Call.id).label("total"),
                    func.sum(
                        func.case(
                            (
                                Call.status.in_(["failed", "no-answer", "busy"]),
                                1,
                            ),
                            else_=0,
                        )
                    ).label("errors"),
                ).where(
                    and_(
                        Call.company_id == company_id,
                        Call.created_at
                        >= datetime.now(timezone.utc) - timedelta(hours=24),
                    )
                )
            )
            row = result.first()

            total = row.total or 0
            errors = row.errors or 0
            error_rate = (errors / total * 100) if total > 0 else 0

            # Uptime (assume 100% if no data)
            uptime_percent = 100.0 if error_rate < 5 else max(95.0, 100 - error_rate)

            return {
                "error_rate_percent": round(error_rate, 2),
                "uptime_percent": round(uptime_percent, 2),
                "calls_last_24h": total,
                "errors_last_24h": errors,
                "status": "healthy" if error_rate < 5 else "degraded",
            }

        except Exception as e:
            logger.error(f"Error getting system health: {str(e)}", exc_info=True)
            return {}
