"""Coaching Service - Agent performance coaching and recommendations."""

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


class CoachingService:
    """Generate coaching insights and recommendations for agents."""

    @staticmethod
    async def get_agent_coaching_insights(
        db: AsyncSession,
        company_id: UUID,
        agent_id: UUID,
    ) -> dict:
        """
        Get comprehensive coaching insights for an agent.

        Args:
            db: Database session
            company_id: Company ID
            agent_id: Agent ID

        Returns:
            Coaching insights with recommendations
        """
        try:
            # Get agent info
            agent_result = await db.execute(
                select(Agent).where(
                    and_(
                        Agent.id == agent_id,
                        Agent.company_id == company_id,
                    )
                )
            )
            agent = agent_result.scalar()

            if not agent:
                return {
                    "error": "Agent not found",
                    "agent_id": str(agent_id),
                }

            # Get last 30 days data
            now = datetime.now(timezone.utc)
            thirty_days_ago = now - timedelta(days=30)

            call_result = await db.execute(
                select(
                    func.count(Call.id).label("total_calls"),
                    func.sum(
                        func.case(
                            (Call.status == "completed", 1),
                            else_=0,
                        )
                    ).label("successful_calls"),
                    func.sum(
                        func.case(
                            (
                                Call.status.in_(["failed", "no-answer", "busy"]),
                                1,
                            ),
                            else_=0,
                        )
                    ).label("failed_calls"),
                    func.avg(Call.duration_seconds).label("avg_duration"),
                    func.min(Call.duration_seconds).label("min_duration"),
                    func.max(Call.duration_seconds).label("max_duration"),
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

            stats = call_result.first()

            if not stats or stats.total_calls == 0:
                return {
                    "agent_id": str(agent_id),
                    "agent_name": agent.name,
                    "message": "Insufficient data for coaching",
                    "days_analyzed": 30,
                }

            # Calculate metrics
            success_rate = stats.successful_calls / stats.total_calls
            failed_rate = stats.failed_calls / stats.total_calls
            avg_duration = stats.avg_duration or 0
            cost_per_call = stats.total_cost / stats.total_calls if stats.total_cost else 0

            # Generate scores
            success_score = int(success_rate * 100)
            efficiency_score = CoachingService._calculate_efficiency_score(
                avg_duration
            )
            quality_score = CoachingService._calculate_quality_score(
                success_rate, avg_duration
            )
            overall_score = int((success_score + efficiency_score + quality_score) / 3)

            # Generate insights and recommendations
            insights = CoachingService._generate_insights(
                success_rate, failed_rate, avg_duration, cost_per_call, stats.total_calls
            )

            # Generate coaching recommendations
            recommendations = CoachingService._generate_recommendations(
                success_rate, avg_duration, cost_per_call, insights
            )

            return {
                "agent_id": str(agent_id),
                "agent_name": agent.name,
                "period": "last_30_days",
                "days_analyzed": 30,
                "total_calls": stats.total_calls,
                "successful_calls": stats.successful_calls or 0,
                "failed_calls": stats.failed_calls or 0,
                "success_rate": round(success_rate, 3),
                "failed_rate": round(failed_rate, 3),
                "average_call_duration_seconds": round(avg_duration, 2),
                "min_duration_seconds": int(stats.min_duration or 0),
                "max_duration_seconds": int(stats.max_duration or 0),
                "total_cost": round(stats.total_cost or 0, 2),
                "cost_per_call": round(cost_per_call, 4),
                "scores": {
                    "success_score": success_score,
                    "efficiency_score": efficiency_score,
                    "quality_score": quality_score,
                    "overall_score": overall_score,
                },
                "performance_level": CoachingService._get_performance_level(
                    overall_score
                ),
                "insights": insights,
                "recommendations": recommendations,
                "timestamp": now.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting coaching insights: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "agent_id": str(agent_id),
            }

    @staticmethod
    async def get_team_coaching_report(
        db: AsyncSession,
        company_id: UUID,
    ) -> dict:
        """
        Get coaching report for entire team.

        Args:
            db: Database session
            company_id: Company ID

        Returns:
            Team coaching insights and comparisons
        """
        try:
            # Get all agents
            agent_result = await db.execute(
                select(Agent).where(Agent.company_id == company_id)
            )
            agents = agent_result.scalars().all()

            if not agents:
                return {
                    "company_id": str(company_id),
                    "agent_count": 0,
                    "report": [],
                }

            # Get metrics for each agent
            now = datetime.now(timezone.utc)
            thirty_days_ago = now - timedelta(days=30)

            team_report = []
            for agent in agents:
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
                    ).where(
                        and_(
                            Call.company_id == company_id,
                            Call.agent_id == agent.id,
                            Call.created_at >= thirty_days_ago,
                            Call.created_at <= now,
                        )
                    )
                )

                stats = result.first()

                if stats and stats.total_calls > 0:
                    success_rate = stats.successful_calls / stats.total_calls
                    overall_score = int(
                        (
                            success_rate * 100
                            + CoachingService._calculate_efficiency_score(
                                stats.avg_duration or 0
                            )
                            + CoachingService._calculate_quality_score(
                                success_rate, stats.avg_duration or 0
                            )
                        )
                        / 3
                    )

                    team_report.append(
                        {
                            "agent_id": str(agent.id),
                            "agent_name": agent.name,
                            "total_calls": stats.total_calls,
                            "success_rate": round(success_rate, 3),
                            "avg_duration": round(stats.avg_duration or 0, 2),
                            "overall_score": overall_score,
                            "performance_level": CoachingService._get_performance_level(
                                overall_score
                            ),
                        }
                    )

            # Sort by overall score
            team_report.sort(key=lambda x: x["overall_score"], reverse=True)

            # Calculate team averages
            avg_success = (
                sum(a["success_rate"] for a in team_report) / len(team_report)
                if team_report
                else 0
            )
            avg_score = (
                sum(a["overall_score"] for a in team_report) / len(team_report)
                if team_report
                else 0
            )

            return {
                "company_id": str(company_id),
                "period": "last_30_days",
                "agent_count": len(agents),
                "team_average_success_rate": round(avg_success, 3),
                "team_average_score": int(avg_score),
                "top_performer": team_report[0] if team_report else None,
                "needs_attention": team_report[-1] if team_report else None,
                "report": team_report,
                "timestamp": now.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting team coaching report: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "company_id": str(company_id),
            }

    @staticmethod
    def _calculate_efficiency_score(avg_duration: float) -> int:
        """Calculate efficiency score based on call duration."""
        # Optimal duration: 3-5 minutes (180-300 seconds)
        if avg_duration == 0:
            return 0

        if avg_duration < 180:  # Too quick
            return max(0, 100 - int((180 - avg_duration) / 10))
        elif avg_duration <= 300:  # Optimal
            return 100
        else:  # Too long
            return max(0, 100 - int((avg_duration - 300) / 10))

    @staticmethod
    def _calculate_quality_score(success_rate: float, avg_duration: float) -> int:
        """Calculate quality score based on success rate and duration."""
        quality_from_success = success_rate * 100
        quality_from_duration = CoachingService._calculate_efficiency_score(
            avg_duration
        )
        return int((quality_from_success + quality_from_duration) / 2)

    @staticmethod
    def _get_performance_level(score: int) -> str:
        """Get performance level based on score."""
        if score >= 90:
            return "exceptional"
        elif score >= 80:
            return "excellent"
        elif score >= 70:
            return "good"
        elif score >= 60:
            return "fair"
        else:
            return "needs_improvement"

    @staticmethod
    def _generate_insights(
        success_rate: float,
        failed_rate: float,
        avg_duration: float,
        cost_per_call: float,
        total_calls: int,
    ) -> list[str]:
        """Generate insights based on metrics."""
        insights = []

        # Success insights
        if success_rate > 0.90:
            insights.append("Excellent success rate - consistently closing calls")
        elif success_rate > 0.75:
            insights.append("Good success rate with room for improvement")
        elif success_rate > 0.60:
            insights.append("Success rate below team average - needs coaching")
        else:
            insights.append("Critical: Success rate significantly below expectations")

        # Duration insights
        if avg_duration < 180:
            insights.append(
                "Calls are very quick - verify quality isn't being sacrificed"
            )
        elif avg_duration > 600:
            insights.append("Average call duration is high - focus on efficiency")
        else:
            insights.append("Call duration is within optimal range")

        # Volume insights
        if total_calls > 100:
            insights.append("High call volume - experience and skills are solid")
        elif total_calls < 20:
            insights.append("Limited call volume - insufficient data for coaching")

        # Cost insights
        if cost_per_call > 0.50:
            insights.append("Cost per call is elevated - optimization needed")
        elif cost_per_call < 0.10:
            insights.append("Cost per call is efficient")

        return insights

    @staticmethod
    def _generate_recommendations(
        success_rate: float,
        avg_duration: float,
        cost_per_call: float,
        insights: list[str],
    ) -> list[dict]:
        """Generate coaching recommendations."""
        recommendations = []

        if success_rate < 0.75:
            recommendations.append(
                {
                    "priority": "high",
                    "category": "success_rate",
                    "recommendation": "Focus on call handling techniques to improve success rate",
                    "action_items": [
                        "Review recent failed calls for patterns",
                        "Practice objection handling",
                        "Study top performer calls",
                    ],
                }
            )

        if avg_duration > 600:
            recommendations.append(
                {
                    "priority": "high",
                    "category": "efficiency",
                    "recommendation": "Improve call efficiency and time management",
                    "action_items": [
                        "Set time targets for different call types",
                        "Use call scripts for common scenarios",
                        "Practice time management techniques",
                    ],
                }
            )

        if avg_duration < 180 and success_rate < 0.80:
            recommendations.append(
                {
                    "priority": "high",
                    "category": "quality",
                    "recommendation": "Balance speed with quality - improve call completeness",
                    "action_items": [
                        "Ensure all customer needs are addressed",
                        "Take time to understand customer requirements",
                        "Follow proper call closure procedures",
                    ],
                }
            )

        if cost_per_call > 0.50:
            recommendations.append(
                {
                    "priority": "medium",
                    "category": "cost",
                    "recommendation": "Reduce operational costs per call",
                    "action_items": [
                        "Identify cost drivers in your calls",
                        "Optimize AI model usage",
                        "Review service selection",
                    ],
                }
            )

        if not recommendations:
            recommendations.append(
                {
                    "priority": "low",
                    "category": "development",
                    "recommendation": "Maintain current performance and develop new skills",
                    "action_items": [
                        "Explore advanced call scenarios",
                        "Mentor newer team members",
                        "Pursue continuous improvement",
                    ],
                }
            )

        return recommendations
