"""Alert Service - System alerts and notifications."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.call import Call
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AlertType:
    """Alert type constants."""

    HIGH_ERROR_RATE = "high_error_rate"
    API_FAILURE = "api_failure"
    BUDGET_EXCEEDED = "budget_exceeded"
    AGENT_OFFLINE = "agent_offline"
    QUEUE_BACKLOG = "queue_backlog"
    COST_SPIKE = "cost_spike"


class AlertSeverity:
    """Alert severity levels."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class AlertService:
    """Monitor system health and generate alerts."""

    @staticmethod
    async def check_high_error_rate(
        db: AsyncSession,
        company_id: UUID,
        threshold_percent: float = 5.0,
    ) -> Optional[dict]:
        """
        Check if error rate exceeds threshold (last 24 hours).

        Args:
            db: Database session
            company_id: Company ID
            threshold_percent: Alert threshold (default: 5%)

        Returns:
            Alert dict or None if healthy
        """
        try:
            # Get calls from last 24 hours
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

            total_calls = row.total or 0
            error_count = row.errors or 0

            if total_calls == 0:
                return None

            error_rate = (error_count / total_calls) * 100

            if error_rate > threshold_percent:
                return {
                    "type": AlertType.HIGH_ERROR_RATE,
                    "severity": AlertSeverity.CRITICAL,
                    "title": "High Error Rate Detected",
                    "message": f"Error rate is {error_rate:.1f}% (threshold: {threshold_percent}%)",
                    "details": {
                        "total_calls": total_calls,
                        "error_count": error_count,
                        "error_rate_percent": round(error_rate, 2),
                        "threshold_percent": threshold_percent,
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            return None

        except Exception as e:
            logger.error(f"Error checking error rate: {str(e)}", exc_info=True)
            return None

    @staticmethod
    async def check_budget_exceeded(
        db: AsyncSession,
        company_id: UUID,
        monthly_budget: float,
    ) -> Optional[dict]:
        """
        Check if monthly costs exceed budget.

        Args:
            db: Database session
            company_id: Company ID
            monthly_budget: Monthly budget in USD

        Returns:
            Alert dict or None if within budget
        """
        try:
            # Get current month's costs
            now = datetime.now(timezone.utc)
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            result = await db.execute(
                select(func.sum(Call.ai_cost_usd).label("total")).where(
                    and_(
                        Call.company_id == company_id,
                        Call.created_at >= month_start,
                        Call.created_at <= now,
                    )
                )
            )
            current_cost = result.scalar() or 0.0

            if current_cost > monthly_budget:
                percent_over = ((current_cost - monthly_budget) / monthly_budget) * 100

                return {
                    "type": AlertType.BUDGET_EXCEEDED,
                    "severity": AlertSeverity.WARNING,
                    "title": "Budget Exceeded",
                    "message": f"Monthly spending ({current_cost:.2f}) exceeds budget ({monthly_budget:.2f})",
                    "details": {
                        "current_cost": round(current_cost, 2),
                        "monthly_budget": monthly_budget,
                        "percent_over": round(percent_over, 1),
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            return None

        except Exception as e:
            logger.error(f"Error checking budget: {str(e)}", exc_info=True)
            return None

    @staticmethod
    async def check_cost_spike(
        db: AsyncSession,
        company_id: UUID,
        spike_percent: float = 30.0,
    ) -> Optional[dict]:
        """
        Check for sudden cost spike compared to previous day.

        Args:
            db: Database session
            company_id: Company ID
            spike_percent: Alert threshold (default: 30% increase)

        Returns:
            Alert dict or None if normal
        """
        try:
            now = datetime.now(timezone.utc)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday_start = today_start - timedelta(days=1)

            # Get today's cost
            result = await db.execute(
                select(func.sum(Call.ai_cost_usd).label("total")).where(
                    and_(
                        Call.company_id == company_id,
                        Call.created_at >= today_start,
                        Call.created_at <= now,
                    )
                )
            )
            today_cost = result.scalar() or 0.0

            # Get yesterday's cost
            result = await db.execute(
                select(func.sum(Call.ai_cost_usd).label("total")).where(
                    and_(
                        Call.company_id == company_id,
                        Call.created_at >= yesterday_start,
                        Call.created_at < today_start,
                    )
                )
            )
            yesterday_cost = result.scalar() or 0.0

            if yesterday_cost == 0:
                return None

            percent_increase = ((today_cost - yesterday_cost) / yesterday_cost) * 100

            if percent_increase > spike_percent:
                return {
                    "type": AlertType.COST_SPIKE,
                    "severity": AlertSeverity.WARNING,
                    "title": "Cost Spike Detected",
                    "message": f"Today's cost is {percent_increase:.1f}% higher than yesterday",
                    "details": {
                        "today_cost": round(today_cost, 2),
                        "yesterday_cost": round(yesterday_cost, 2),
                        "percent_increase": round(percent_increase, 1),
                        "threshold_percent": spike_percent,
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            return None

        except Exception as e:
            logger.error(f"Error checking cost spike: {str(e)}", exc_info=True)
            return None

    @staticmethod
    async def check_all_alerts(
        db: AsyncSession,
        company_id: UUID,
        monthly_budget: Optional[float] = None,
    ) -> list[dict]:
        """
        Run all alert checks and return active alerts.

        Args:
            db: Database session
            company_id: Company ID
            monthly_budget: Monthly budget (optional)

        Returns:
            List of active alerts
        """
        alerts = []

        # Check error rate
        error_alert = await AlertService.check_high_error_rate(db, company_id)
        if error_alert:
            alerts.append(error_alert)

        # Check budget if provided
        if monthly_budget:
            budget_alert = await AlertService.check_budget_exceeded(
                db, company_id, monthly_budget
            )
            if budget_alert:
                alerts.append(budget_alert)

        # Check cost spike
        spike_alert = await AlertService.check_cost_spike(db, company_id)
        if spike_alert:
            alerts.append(spike_alert)

        return alerts

    @staticmethod
    async def send_alert(
        alert_type: str,
        severity: str,
        title: str,
        message: str,
        details: Optional[dict] = None,
    ) -> bool:
        """
        Send alert notification.

        Args:
            alert_type: Type of alert
            severity: Alert severity
            title: Alert title
            message: Alert message
            details: Additional details

        Returns:
            True if sent successfully
        """
        try:
            logger.warning(
                f"ALERT [{severity.upper()}]: {title}",
                extra={
                    "alert_type": alert_type,
                    "message": message,
                    "details": details,
                },
            )

            # TODO: Implement notification channels
            # - Email
            # - Slack
            # - SMS
            # - In-app notifications

            return True

        except Exception as e:
            logger.error(f"Error sending alert: {str(e)}", exc_info=True)
            return False
