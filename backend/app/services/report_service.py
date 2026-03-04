"""Report generation and scheduling service."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from enum import Enum
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

logger = logging.getLogger(__name__)


class ReportType(str, Enum):
    """Report types."""
    SUMMARY = "summary"
    DETAILED = "detailed"
    EXECUTIVE = "executive"
    AGENT_PERFORMANCE = "agent_performance"
    COST_ANALYSIS = "cost_analysis"
    TREND_ANALYSIS = "trend_analysis"


class ReportFormat(str, Enum):
    """Report output formats."""
    PDF = "pdf"
    CSV = "csv"
    JSON = "json"
    HTML = "html"


class ReportFrequency(str, Enum):
    """Report scheduling frequency."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class ReportTemplate:
    """Report template configuration."""

    def __init__(
        self,
        name: str,
        report_type: ReportType,
        sections: List[str],
        include_charts: bool = True,
        include_recommendations: bool = True
    ):
        """
        Initialize report template.
        
        Args:
            name: Template name
            report_type: Type of report
            sections: Report sections to include
            include_charts: Include visualizations
            include_recommendations: Include recommendations
        """
        self.name = name
        self.report_type = report_type
        self.sections = sections
        self.include_charts = include_charts
        self.include_recommendations = include_recommendations

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "report_type": self.report_type.value,
            "sections": self.sections,
            "include_charts": self.include_charts,
            "include_recommendations": self.include_recommendations
        }


class ReportBuilder:
    """Service for building and generating reports."""

    def __init__(self):
        """Initialize report builder."""
        self.templates = self._create_default_templates()
        self.scheduled_reports = {}

    def _create_default_templates(self) -> Dict[str, ReportTemplate]:
        """Create default report templates."""
        return {
            "executive_summary": ReportTemplate(
                name="Executive Summary",
                report_type=ReportType.EXECUTIVE,
                sections=[
                    "key_metrics",
                    "calls_summary",
                    "cost_summary",
                    "top_agents",
                    "alerts",
                    "recommendations"
                ]
            ),
            "detailed": ReportTemplate(
                name="Detailed Report",
                report_type=ReportType.DETAILED,
                sections=[
                    "calls_summary",
                    "calls_by_agent",
                    "calls_by_phone",
                    "cost_breakdown",
                    "trends",
                    "performance_metrics",
                    "alerts",
                    "recommendations"
                ]
            ),
            "agent_performance": ReportTemplate(
                name="Agent Performance",
                report_type=ReportType.AGENT_PERFORMANCE,
                sections=[
                    "agent_rankings",
                    "individual_metrics",
                    "coaching_insights",
                    "improvement_areas",
                    "top_performers"
                ]
            ),
            "cost_analysis": ReportTemplate(
                name="Cost Analysis",
                report_type=ReportType.COST_ANALYSIS,
                sections=[
                    "cost_summary",
                    "cost_by_agent",
                    "cost_by_phone",
                    "cost_trends",
                    "budget_tracking",
                    "optimization_opportunities"
                ]
            )
        }

    async def generate_report(
        self,
        db: AsyncSession,
        company_id: str,
        template_name: str,
        start_date: datetime,
        end_date: datetime,
        format: ReportFormat = ReportFormat.PDF
    ) -> dict:
        """
        Generate report from template.
        
        Args:
            db: Database session
            company_id: Company identifier
            template_name: Template name
            start_date: Report start date
            end_date: Report end date
            format: Output format
            
        Returns:
            Generated report data
        """
        if template_name not in self.templates:
            raise ValueError(f"Unknown template: {template_name}")
        
        template = self.templates[template_name]
        
        # Gather data for each section
        report_data = {
            "metadata": {
                "company_id": company_id,
                "template": template_name,
                "report_type": template.report_type.value,
                "generated_at": datetime.utcnow().isoformat(),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "format": format.value
            },
            "sections": {}
        }
        
        # Build sections
        for section in template.sections:
            try:
                section_data = await self._build_section(
                    db,
                    company_id,
                    section,
                    start_date,
                    end_date
                )
                if section_data:
                    report_data["sections"][section] = section_data
            except Exception as e:
                logger.error(f"Error building section {section}: {e}")
                report_data["sections"][section] = {"error": str(e)}
        
        # Convert to requested format
        formatted_report = await self._format_report(report_data, format)
        
        return formatted_report

    async def _build_section(
        self,
        db: AsyncSession,
        company_id: str,
        section: str,
        start_date: datetime,
        end_date: datetime
    ) -> dict:
        """
        Build individual report section.
        
        Args:
            db: Database session
            company_id: Company identifier
            section: Section name
            start_date: Start date
            end_date: End date
            
        Returns:
            Section data
        """
        if section == "key_metrics":
            return await self._build_key_metrics(db, company_id, start_date, end_date)
        elif section == "calls_summary":
            return await self._build_calls_summary(db, company_id, start_date, end_date)
        elif section == "cost_summary":
            return await self._build_cost_summary(db, company_id, start_date, end_date)
        elif section == "calls_by_agent":
            return await self._build_calls_by_agent(db, company_id, start_date, end_date)
        elif section == "calls_by_phone":
            return await self._build_calls_by_phone(db, company_id, start_date, end_date)
        elif section == "cost_breakdown":
            return await self._build_cost_breakdown(db, company_id, start_date, end_date)
        elif section == "trends":
            return await self._build_trends(db, company_id, start_date, end_date)
        elif section == "agent_rankings":
            return await self._build_agent_rankings(db, company_id, start_date, end_date)
        elif section == "coaching_insights":
            return await self._build_coaching_insights(db, company_id, start_date, end_date)
        elif section == "recommendations":
            return await self._build_recommendations(db, company_id, start_date, end_date)
        elif section == "alerts":
            return await self._build_alerts_section(db, company_id, start_date, end_date)
        else:
            return None

    async def _build_key_metrics(self, db, company_id, start_date, end_date) -> dict:
        """Build key metrics section."""
        return {
            "title": "Key Metrics",
            "metrics": {
                "total_calls": 0,
                "success_rate": 0.0,
                "avg_duration": 0.0,
                "total_cost": 0.0
            }
        }

    async def _build_calls_summary(self, db, company_id, start_date, end_date) -> dict:
        """Build calls summary section."""
        return {
            "title": "Call Summary",
            "data": {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 0.0,
                "avg_duration": 0.0
            }
        }

    async def _build_cost_summary(self, db, company_id, start_date, end_date) -> dict:
        """Build cost summary section."""
        return {
            "title": "Cost Summary",
            "data": {
                "total_cost": 0.0,
                "cost_per_call": 0.0,
                "openai_cost": 0.0,
                "elevenlabs_cost": 0.0,
                "twilio_cost": 0.0
            }
        }

    async def _build_calls_by_agent(self, db, company_id, start_date, end_date) -> dict:
        """Build calls by agent section."""
        return {
            "title": "Calls by Agent",
            "data": []
        }

    async def _build_calls_by_phone(self, db, company_id, start_date, end_date) -> dict:
        """Build calls by phone section."""
        return {
            "title": "Calls by Phone Number",
            "data": []
        }

    async def _build_cost_breakdown(self, db, company_id, start_date, end_date) -> dict:
        """Build cost breakdown section."""
        return {
            "title": "Cost Breakdown",
            "data": {
                "by_service": {},
                "by_agent": {},
                "by_phone": {}
            }
        }

    async def _build_trends(self, db, company_id, start_date, end_date) -> dict:
        """Build trends section."""
        return {
            "title": "Trends",
            "data": {
                "calls_trend": [],
                "cost_trend": [],
                "success_rate_trend": []
            }
        }

    async def _build_agent_rankings(self, db, company_id, start_date, end_date) -> dict:
        """Build agent rankings section."""
        return {
            "title": "Agent Rankings",
            "data": {
                "by_calls": [],
                "by_success_rate": [],
                "by_efficiency": []
            }
        }

    async def _build_coaching_insights(self, db, company_id, start_date, end_date) -> dict:
        """Build coaching insights section."""
        return {
            "title": "Coaching Insights",
            "data": {
                "top_performers": [],
                "needs_coaching": [],
                "improvement_areas": []
            }
        }

    async def _build_recommendations(self, db, company_id, start_date, end_date) -> dict:
        """Build recommendations section."""
        return {
            "title": "Recommendations",
            "data": {
                "cost_optimization": [],
                "performance_improvement": [],
                "resource_allocation": []
            }
        }

    async def _build_alerts_section(self, db, company_id, start_date, end_date) -> dict:
        """Build alerts section."""
        return {
            "title": "Recent Alerts",
            "data": []
        }

    async def _format_report(
        self,
        report_data: dict,
        format: ReportFormat
    ) -> dict:
        """
        Format report for output.
        
        Args:
            report_data: Report data
            format: Output format
            
        Returns:
            Formatted report
        """
        if format == ReportFormat.JSON:
            return report_data
        elif format == ReportFormat.CSV:
            return await self._format_as_csv(report_data)
        elif format == ReportFormat.HTML:
            return await self._format_as_html(report_data)
        elif format == ReportFormat.PDF:
            return await self._format_as_pdf(report_data)
        else:
            return report_data

    async def _format_as_csv(self, report_data: dict) -> dict:
        """Format report as CSV."""
        return {
            "format": "csv",
            "content": "CSV content would be generated here",
            "metadata": report_data["metadata"]
        }

    async def _format_as_html(self, report_data: dict) -> dict:
        """Format report as HTML."""
        return {
            "format": "html",
            "content": "<html>HTML report content</html>",
            "metadata": report_data["metadata"]
        }

    async def _format_as_pdf(self, report_data: dict) -> dict:
        """Format report as PDF."""
        return {
            "format": "pdf",
            "content_base64": "PDF content would be base64 encoded",
            "metadata": report_data["metadata"]
        }

    def create_schedule(
        self,
        company_id: str,
        template_name: str,
        frequency: ReportFrequency,
        recipients: List[str],
        format: ReportFormat = ReportFormat.PDF
    ) -> dict:
        """
        Create scheduled report.
        
        Args:
            company_id: Company identifier
            template_name: Template name
            frequency: Schedule frequency
            recipients: Email recipients
            format: Output format
            
        Returns:
            Schedule data
        """
        schedule_id = f"{company_id}:{template_name}:{int(datetime.utcnow().timestamp())}"
        
        schedule = {
            "schedule_id": schedule_id,
            "company_id": company_id,
            "template": template_name,
            "frequency": frequency.value,
            "recipients": recipients,
            "format": format.value,
            "created_at": datetime.utcnow().isoformat(),
            "next_run": self._calculate_next_run(frequency),
            "status": "active"
        }
        
        self.scheduled_reports[schedule_id] = schedule
        logger.info(f"Created schedule: {schedule_id}")
        
        return schedule

    def _calculate_next_run(self, frequency: ReportFrequency) -> str:
        """Calculate next run time."""
        now = datetime.utcnow()
        
        if frequency == ReportFrequency.DAILY:
            next_run = now + timedelta(days=1)
        elif frequency == ReportFrequency.WEEKLY:
            next_run = now + timedelta(weeks=1)
        elif frequency == ReportFrequency.MONTHLY:
            next_run = now + timedelta(days=30)
        else:
            next_run = now + timedelta(hours=1)
        
        return next_run.isoformat()

    def get_templates(self) -> Dict[str, dict]:
        """Get all available templates."""
        return {
            name: template.to_dict()
            for name, template in self.templates.items()
        }

    def get_schedules(self, company_id: str) -> List[dict]:
        """Get company schedules."""
        return [
            schedule
            for schedule in self.scheduled_reports.values()
            if schedule["company_id"] == company_id
        ]

    def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule."""
        if schedule_id in self.scheduled_reports:
            del self.scheduled_reports[schedule_id]
            logger.info(f"Deleted schedule: {schedule_id}")
            return True
        return False


# Global instance
report_builder = ReportBuilder()
