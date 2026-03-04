"""Advanced alert service with email, Slack, and SMS notifications."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class AlertType(str, Enum):
    """Types of alerts."""
    ERROR_RATE = "error_rate"
    BUDGET_EXCEEDED = "budget_exceeded"
    COST_SPIKE = "cost_spike"
    AGENT_OFFLINE = "agent_offline"
    CALL_FAILURE = "call_failure"
    SYSTEM_DOWN = "system_down"
    QUOTA_LIMIT = "quota_limit"


class NotificationChannel(str, Enum):
    """Notification channels."""
    EMAIL = "email"
    SLACK = "slack"
    SMS = "sms"
    WEBHOOK = "webhook"


class AdvancedAlertService:
    """Service for managing alerts and notifications."""

    def __init__(self):
        """Initialize alert service."""
        self.alert_cooldowns = {}  # Track cooldowns by alert key
        self.cooldown_minutes = 15  # Minimum time between similar alerts

    async def create_alert(
        self,
        db: AsyncSession,
        company_id: str,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str,
        data: dict = None,
        channels: List[NotificationChannel] = None
    ) -> dict:
        """
        Create and send an alert.
        
        Args:
            db: Database session
            company_id: Company identifier
            alert_type: Type of alert
            severity: Severity level
            title: Alert title
            message: Alert message
            data: Additional context data
            channels: Notification channels to use
            
        Returns:
            Alert data
        """
        alert_key = f"{company_id}:{alert_type.value}"
        
        # Check cooldown
        if self._is_on_cooldown(alert_key):
            logger.info(f"Alert {alert_key} is on cooldown, skipping")
            return None
        
        # Mark cooldown
        self.alert_cooldowns[alert_key] = datetime.utcnow()
        
        alert = {
            "company_id": company_id,
            "alert_type": alert_type.value,
            "severity": severity.value,
            "title": title,
            "message": message,
            "data": data or {},
            "created_at": datetime.utcnow().isoformat(),
            "status": "new"
        }
        
        # Send to channels
        if channels:
            for channel in channels:
                await self._send_to_channel(channel, alert)
        else:
            # Send to default channels based on severity
            if severity == AlertSeverity.CRITICAL:
                await self._send_to_channel(NotificationChannel.EMAIL, alert)
                await self._send_to_channel(NotificationChannel.SLACK, alert)
                await self._send_to_channel(NotificationChannel.SMS, alert)
            elif severity == AlertSeverity.WARNING:
                await self._send_to_channel(NotificationChannel.EMAIL, alert)
                await self._send_to_channel(NotificationChannel.SLACK, alert)
            else:
                await self._send_to_channel(NotificationChannel.SLACK, alert)
        
        logger.info(f"Alert created: {alert_type.value} - {severity.value}")
        return alert

    async def _send_to_channel(
        self,
        channel: NotificationChannel,
        alert: dict
    ):
        """
        Send alert to specific channel.
        
        Args:
            channel: Notification channel
            alert: Alert data
        """
        try:
            if channel == NotificationChannel.EMAIL:
                await self._send_email_alert(alert)
            elif channel == NotificationChannel.SLACK:
                await self._send_slack_alert(alert)
            elif channel == NotificationChannel.SMS:
                await self._send_sms_alert(alert)
            elif channel == NotificationChannel.WEBHOOK:
                await self._send_webhook_alert(alert)
        except Exception as e:
            logger.error(f"Failed to send alert via {channel.value}: {e}")

    async def _send_email_alert(self, alert: dict):
        """
        Send email notification.
        
        Args:
            alert: Alert data
        """
        # TODO: Implement email service integration
        # Use: SendGrid, AWS SES, or SMTP
        logger.info(f"Email alert: {alert['title']}")

    async def _send_slack_alert(self, alert: dict):
        """
        Send Slack notification.
        
        Args:
            alert: Alert data
        """
        # TODO: Implement Slack webhook integration
        # POST to SLACK_WEBHOOK_URL with formatted message
        
        severity_colors = {
            "critical": "#ff0000",  # Red
            "warning": "#ffaa00",   # Orange
            "info": "#0099ff"       # Blue
        }
        
        payload = {
            "attachments": [{
                "color": severity_colors.get(alert["severity"], "#999999"),
                "title": alert["title"],
                "text": alert["message"],
                "fields": [
                    {
                        "title": "Type",
                        "value": alert["alert_type"],
                        "short": True
                    },
                    {
                        "title": "Severity",
                        "value": alert["severity"].upper(),
                        "short": True
                    },
                    {
                        "title": "Time",
                        "value": alert["created_at"],
                        "short": False
                    }
                ]
            }]
        }
        
        logger.info(f"Slack alert sent: {alert['title']}")

    async def _send_sms_alert(self, alert: dict):
        """
        Send SMS notification via Twilio.
        
        Args:
            alert: Alert data
        """
        # TODO: Implement SMS via Twilio
        # Use TwilioService to send SMS with alert summary
        
        message = f"[{alert['severity'].upper()}] {alert['title']}: {alert['message']}"
        logger.info(f"SMS alert: {message}")

    async def _send_webhook_alert(self, alert: dict):
        """
        Send webhook notification.
        
        Args:
            alert: Alert data
        """
        # TODO: Implement custom webhook delivery
        # POST to configured webhook endpoints
        logger.info(f"Webhook alert: {alert['title']}")

    def _is_on_cooldown(self, alert_key: str) -> bool:
        """
        Check if alert is on cooldown.
        
        Args:
            alert_key: Alert key
            
        Returns:
            True if on cooldown
        """
        if alert_key not in self.alert_cooldowns:
            return False
        
        last_sent = self.alert_cooldowns[alert_key]
        return datetime.utcnow() < last_sent + timedelta(minutes=self.cooldown_minutes)

    async def check_error_rate(
        self,
        db: AsyncSession,
        company_id: str,
        error_rate: float,
        threshold: float = 0.05
    ) -> Optional[dict]:
        """
        Check error rate and create alert if exceeded.
        
        Args:
            db: Database session
            company_id: Company identifier
            error_rate: Current error rate (0-1)
            threshold: Error rate threshold (default 5%)
            
        Returns:
            Alert data if created
        """
        if error_rate > threshold:
            severity = AlertSeverity.CRITICAL if error_rate > 0.10 else AlertSeverity.WARNING
            
            return await self.create_alert(
                db,
                company_id,
                AlertType.ERROR_RATE,
                severity,
                f"High Error Rate ({error_rate*100:.1f}%)",
                f"Error rate exceeded {threshold*100:.0f}% threshold. Current: {error_rate*100:.1f}%",
                {"error_rate": error_rate, "threshold": threshold},
                [NotificationChannel.EMAIL, NotificationChannel.SLACK]
            )
        
        return None

    async def check_budget(
        self,
        db: AsyncSession,
        company_id: str,
        current_spend: float,
        budget_limit: float
    ) -> Optional[dict]:
        """
        Check budget and create alert if exceeded.
        
        Args:
            db: Database session
            company_id: Company identifier
            current_spend: Current spend amount
            budget_limit: Monthly budget limit
            
        Returns:
            Alert data if created
        """
        percentage = (current_spend / budget_limit) * 100 if budget_limit > 0 else 0
        
        if percentage >= 95:
            return await self.create_alert(
                db,
                company_id,
                AlertType.BUDGET_EXCEEDED,
                AlertSeverity.CRITICAL,
                f"Budget Almost Exhausted ({percentage:.0f}%)",
                f"You've spent {percentage:.1f}% of your {budget_limit} budget",
                {"current_spend": current_spend, "budget_limit": budget_limit},
                [NotificationChannel.EMAIL, NotificationChannel.SMS]
            )
        elif percentage >= 80:
            return await self.create_alert(
                db,
                company_id,
                AlertType.BUDGET_EXCEEDED,
                AlertSeverity.WARNING,
                f"Budget Warning ({percentage:.0f}%)",
                f"You've spent {percentage:.1f}% of your {budget_limit} budget",
                {"current_spend": current_spend, "budget_limit": budget_limit},
                [NotificationChannel.EMAIL, NotificationChannel.SLACK]
            )
        
        return None

    async def check_cost_spike(
        self,
        db: AsyncSession,
        company_id: str,
        current_cost: float,
        baseline_cost: float,
        threshold: float = 0.5
    ) -> Optional[dict]:
        """
        Check for cost spike and create alert.
        
        Args:
            db: Database session
            company_id: Company identifier
            current_cost: Current period cost
            baseline_cost: Baseline cost
            threshold: Spike threshold (default 50%)
            
        Returns:
            Alert data if created
        """
        if baseline_cost == 0:
            return None
        
        increase = (current_cost - baseline_cost) / baseline_cost
        
        if increase > threshold:
            return await self.create_alert(
                db,
                company_id,
                AlertType.COST_SPIKE,
                AlertSeverity.WARNING,
                f"Cost Spike Detected (+{increase*100:.0f}%)",
                f"Current costs are {increase*100:.1f}% higher than baseline",
                {"current_cost": current_cost, "baseline_cost": baseline_cost, "increase": increase},
                [NotificationChannel.EMAIL, NotificationChannel.SLACK]
            )
        
        return None

    async def check_agent_offline(
        self,
        db: AsyncSession,
        company_id: str,
        agent_id: str,
        offline_minutes: int = 30
    ) -> Optional[dict]:
        """
        Check if agent is offline and create alert.
        
        Args:
            db: Database session
            company_id: Company identifier
            agent_id: Agent identifier
            offline_minutes: Minutes offline threshold
            
        Returns:
            Alert data if created
        """
        return await self.create_alert(
            db,
            company_id,
            AlertType.AGENT_OFFLINE,
            AlertSeverity.WARNING,
            f"Agent Offline: {agent_id}",
            f"Agent has been offline for {offline_minutes} minutes",
            {"agent_id": agent_id, "offline_minutes": offline_minutes},
            [NotificationChannel.SLACK, NotificationChannel.EMAIL]
        )

    async def check_quota_limit(
        self,
        db: AsyncSession,
        company_id: str,
        resource: str,
        current: int,
        limit: int
    ) -> Optional[dict]:
        """
        Check quota limits.
        
        Args:
            db: Database session
            company_id: Company identifier
            resource: Resource type (phone_numbers, agents, etc.)
            current: Current usage
            limit: Quota limit
            
        Returns:
            Alert data if created
        """
        percentage = (current / limit) * 100 if limit > 0 else 0
        
        if percentage >= 95:
            return await self.create_alert(
                db,
                company_id,
                AlertType.QUOTA_LIMIT,
                AlertSeverity.WARNING,
                f"Quota Limit: {resource}",
                f"You've used {percentage:.0f}% of your {resource} quota",
                {"resource": resource, "current": current, "limit": limit},
                [NotificationChannel.EMAIL]
            )
        
        return None


# Global instance
advanced_alert_service = AdvancedAlertService()
