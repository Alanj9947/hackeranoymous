"""Report generation and scheduling API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional, List

from app.core.database import get_db
from app.core.auth import get_company_id
from app.services.report_service import (
    report_builder,
    ReportType,
    ReportFormat,
    ReportFrequency
)

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/templates")
async def get_templates(
    company_id: str = Depends(get_company_id)
):
    """
    Get available report templates.
    
    Args:
        company_id: Company identifier
        
    Returns:
        Available templates
    """
    return {
        "templates": report_builder.get_templates(),
        "count": len(report_builder.templates)
    }


@router.post("/generate")
async def generate_report(
    template: str = Query(..., description="Template name"),
    format: str = Query("pdf", description="Output format"),
    days: int = Query(7, description="Days to include in report"),
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(get_company_id)
):
    """
    Generate report from template.
    
    Args:
        template: Template name (executive_summary, detailed, etc.)
        format: Output format (pdf, csv, json, html)
        days: Number of days to include (default 7)
        db: Database session
        company_id: Company identifier
        
    Returns:
        Generated report
    """
    try:
        # Validate inputs
        if template not in report_builder.templates:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown template: {template}"
            )
        
        try:
            format_enum = ReportFormat(format.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format: {format}"
            )
        
        # Set date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Generate report
        report = await report_builder.generate_report(
            db,
            company_id,
            template,
            start_date,
            end_date,
            format_enum
        )
        
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedules")
async def create_schedule(
    template: str,
    frequency: str,
    recipients: List[str],
    format: str = "pdf",
    company_id: str = Depends(get_company_id)
):
    """
    Create scheduled report.
    
    Args:
        template: Template name
        frequency: Schedule frequency (daily, weekly, monthly)
        recipients: Email recipients
        format: Output format
        company_id: Company identifier
        
    Returns:
        Schedule data
    """
    try:
        template_check = report_builder.templates.get(template)
        if not template_check:
            raise HTTPException(status_code=400, detail=f"Unknown template: {template}")
        
        frequency_enum = ReportFrequency(frequency.lower())
        format_enum = ReportFormat(format.lower())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    schedule = report_builder.create_schedule(
        company_id,
        template,
        frequency_enum,
        recipients,
        format_enum
    )
    
    return schedule


@router.get("/schedules")
async def list_schedules(
    company_id: str = Depends(get_company_id)
):
    """
    List scheduled reports.
    
    Args:
        company_id: Company identifier
        
    Returns:
        List of schedules
    """
    schedules = report_builder.get_schedules(company_id)
    return {
        "schedules": schedules,
        "count": len(schedules)
    }


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    company_id: str = Depends(get_company_id)
):
    """
    Delete scheduled report.
    
    Args:
        schedule_id: Schedule identifier
        company_id: Company identifier
        
    Returns:
        Delete status
    """
    # Verify ownership
    schedules = report_builder.get_schedules(company_id)
    if not any(s["schedule_id"] == schedule_id for s in schedules):
        raise HTTPException(
            status_code=403,
            detail="Schedule not found or access denied"
        )
    
    deleted = report_builder.delete_schedule(schedule_id)
    
    return {
        "deleted": deleted,
        "schedule_id": schedule_id
    }


@router.get("/status")
async def get_report_service_status(
    company_id: str = Depends(get_company_id)
):
    """
    Get report service status.
    
    Args:
        company_id: Company identifier
        
    Returns:
        Service status
    """
    schedules = report_builder.get_schedules(company_id)
    
    return {
        "service": "reports",
        "status": "operational",
        "templates_available": len(report_builder.templates),
        "schedules_active": len([s for s in schedules if s["status"] == "active"]),
        "timestamp": datetime.utcnow().isoformat()
    }
