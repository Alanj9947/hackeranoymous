"""Custom workflow API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.auth import get_company_id
from app.services.workflow_service import (
    workflow_engine,
    TriggerType,
    WorkflowStatus
)

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])


@router.post("")
async def create_workflow(
    name: str,
    triggers: list,
    actions: list,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(get_company_id)
):
    """
    Create new workflow.
    
    Args:
        name: Workflow name
        triggers: List of trigger definitions
        actions: List of action definitions
        db: Database session
        company_id: Company identifier
        
    Returns:
        Created workflow
    """
    workflow = await workflow_engine.create_workflow(
        company_id,
        name,
        triggers,
        actions
    )

    if not workflow:
        raise HTTPException(status_code=400, detail="Failed to create workflow")

    return workflow.to_dict()


@router.get("")
async def list_workflows(
    company_id: str = Depends(get_company_id)
):
    """
    List workflows for company.
    
    Args:
        company_id: Company identifier
        
    Returns:
        List of workflows
    """
    workflows = await workflow_engine.list_workflows(company_id)

    return {
        "workflows": [w.to_dict() for w in workflows],
        "count": len(workflows)
    }


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    company_id: str = Depends(get_company_id)
):
    """Get specific workflow."""
    workflow = workflow_engine.workflows.get(workflow_id)

    if not workflow or workflow.company_id != company_id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return workflow.to_dict()


@router.put("/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    name: Optional[str] = None,
    status: Optional[str] = None,
    triggers: Optional[list] = None,
    actions: Optional[list] = None,
    company_id: str = Depends(get_company_id)
):
    """
    Update workflow.
    
    Args:
        workflow_id: Workflow identifier
        name: New name
        status: New status
        triggers: Updated triggers
        actions: Updated actions
        company_id: Company identifier
        
    Returns:
        Update status
    """
    workflow = workflow_engine.workflows.get(workflow_id)
    if not workflow or workflow.company_id != company_id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    status_enum = None
    if status:
        try:
            status_enum = WorkflowStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    success = await workflow_engine.update_workflow(
        workflow_id,
        name,
        status_enum,
        triggers,
        actions
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to update workflow")

    return workflow_engine.workflows[workflow_id].to_dict()


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    company_id: str = Depends(get_company_id)
):
    """Delete workflow."""
    workflow = workflow_engine.workflows.get(workflow_id)
    if not workflow or workflow.company_id != company_id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    success = await workflow_engine.delete_workflow(workflow_id)

    return {"deleted": success}


@router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    trigger_type: str,
    context: dict,
    company_id: str = Depends(get_company_id)
):
    """
    Manually execute workflow.
    
    Args:
        workflow_id: Workflow identifier
        trigger_type: Trigger type (manual, call_completed, etc.)
        context: Context data
        company_id: Company identifier
        
    Returns:
        Execution result
    """
    workflow = workflow_engine.workflows.get(workflow_id)
    if not workflow or workflow.company_id != company_id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    try:
        trigger = TriggerType(trigger_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid trigger: {trigger_type}")

    execution = await workflow_engine.execute_workflow(
        workflow_id,
        trigger,
        context
    )

    if not execution:
        raise HTTPException(status_code=400, detail="Failed to execute workflow")

    return {
        "execution_id": execution.execution_id,
        "workflow_id": workflow_id,
        "status": execution.status,
        "actions_executed": execution.actions_executed,
        "actions_failed": execution.actions_failed
    }


@router.get("/{workflow_id}/executions")
async def get_execution_history(
    workflow_id: str,
    limit: int = Query(20, ge=1, le=100),
    company_id: str = Depends(get_company_id)
):
    """Get execution history for workflow."""
    workflow = workflow_engine.workflows.get(workflow_id)
    if not workflow or workflow.company_id != company_id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    executions = await workflow_engine.get_execution_history(workflow_id, limit)

    return {
        "workflow_id": workflow_id,
        "executions": [
            {
                "execution_id": e.execution_id,
                "triggered_by": e.triggered_by.value,
                "status": e.status,
                "started_at": e.started_at.isoformat(),
                "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                "actions_executed": e.actions_executed,
                "actions_failed": e.actions_failed
            }
            for e in executions
        ],
        "count": len(executions)
    }


@router.post("/{workflow_id}/enable")
async def enable_workflow(
    workflow_id: str,
    company_id: str = Depends(get_company_id)
):
    """Enable (activate) workflow."""
    workflow = workflow_engine.workflows.get(workflow_id)
    if not workflow or workflow.company_id != company_id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    success = await workflow_engine.update_workflow(
        workflow_id,
        status=WorkflowStatus.ACTIVE
    )

    return {"enabled": success}


@router.post("/{workflow_id}/disable")
async def disable_workflow(
    workflow_id: str,
    company_id: str = Depends(get_company_id)
):
    """Disable (pause) workflow."""
    workflow = workflow_engine.workflows.get(workflow_id)
    if not workflow or workflow.company_id != company_id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    success = await workflow_engine.update_workflow(
        workflow_id,
        status=WorkflowStatus.PAUSED
    )

    return {"disabled": success}


@router.get("/templates")
async def get_workflow_templates():
    """Get workflow templates."""
    return {
        "templates": [
            {
                "id": "escalate_failed_calls",
                "name": "Escalate Failed Calls",
                "description": "Create ticket when call fails",
                "triggers": [{"type": "call_failed"}],
                "actions": [{"type": "create_ticket"}]
            },
            {
                "id": "notify_high_cost",
                "name": "Notify on High Cost",
                "description": "Send SMS when cost exceeds threshold",
                "triggers": [{"type": "cost_threshold", "condition": {"threshold": 100}}],
                "actions": [{"type": "send_sms"}]
            },
            {
                "id": "low_satisfaction",
                "name": "Low Satisfaction Handling",
                "description": "Create ticket and log activity on low satisfaction",
                "triggers": [{"type": "sentiment_low"}],
                "actions": [
                    {"type": "create_ticket"},
                    {"type": "log_activity"}
                ]
            },
            {
                "id": "agent_offline_alert",
                "name": "Agent Offline Alert",
                "description": "Notify and escalate when agent goes offline",
                "triggers": [{"type": "agent_offline"}],
                "actions": [
                    {"type": "notify_agent"},
                    {"type": "escalate"}
                ]
            },
            {
                "id": "call_duration_report",
                "name": "Long Call Report",
                "description": "Generate report for calls over 15 minutes",
                "triggers": [{"type": "call_duration", "condition": {"min": 900}}],
                "actions": [{"type": "generate_report"}]
            }
        ]
    }
