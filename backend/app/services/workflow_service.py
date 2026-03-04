"""Custom workflow engine with trigger/action automation."""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import uuid

logger = logging.getLogger(__name__)


class TriggerType(str, Enum):
    """Workflow trigger types."""
    CALL_COMPLETED = "call_completed"
    CALL_FAILED = "call_failed"
    CALL_DURATION = "call_duration"
    AGENT_OFFLINE = "agent_offline"
    COST_THRESHOLD = "cost_threshold"
    SENTIMENT_LOW = "sentiment_low"
    CUSTOMER_FEEDBACK = "customer_feedback"
    MANUAL = "manual"


class ActionType(str, Enum):
    """Workflow action types."""
    SEND_SMS = "send_sms"
    SEND_EMAIL = "send_email"
    CREATE_TICKET = "create_ticket"
    LOG_ACTIVITY = "log_activity"
    UPDATE_CRM = "update_crm"
    ESCALATE = "escalate"
    NOTIFY_AGENT = "notify_agent"
    GENERATE_REPORT = "generate_report"
    TRIGGER_FORECAST = "trigger_forecast"
    ARCHIVE_CALL = "archive_call"


class WorkflowStatus(str, Enum):
    """Workflow status."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


@dataclass
class Trigger:
    """Workflow trigger definition."""
    trigger_type: TriggerType
    condition: Dict[str, Any]
    metadata: Optional[Dict] = None


@dataclass
class Action:
    """Workflow action definition."""
    action_type: ActionType
    config: Dict[str, Any]
    on_error: str = "continue"  # continue, stop, retry
    max_retries: int = 3
    metadata: Optional[Dict] = None


@dataclass
class WorkflowExecution:
    """Record of workflow execution."""
    execution_id: str
    workflow_id: str
    triggered_by: TriggerType
    started_at: datetime
    completed_at: Optional[datetime] = None
    actions_executed: int = 0
    actions_failed: int = 0
    status: str = "in_progress"
    logs: List[Dict] = None

    def __post_init__(self):
        if self.logs is None:
            self.logs = []


class Workflow:
    """Workflow definition."""

    def __init__(
        self,
        workflow_id: str,
        name: str,
        company_id: str,
        triggers: List[Trigger],
        actions: List[Action],
        status: WorkflowStatus = WorkflowStatus.DRAFT,
        metadata: Optional[Dict] = None
    ):
        """Initialize workflow."""
        self.workflow_id = workflow_id
        self.name = name
        self.company_id = company_id
        self.triggers = triggers
        self.actions = actions
        self.status = status
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.execution_count = 0
        self.last_execution = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "company_id": self.company_id,
            "status": self.status.value,
            "triggers": [
                {
                    "type": t.trigger_type.value,
                    "condition": t.condition,
                    "metadata": t.metadata
                }
                for t in self.triggers
            ],
            "actions": [
                {
                    "type": a.action_type.value,
                    "config": a.config,
                    "on_error": a.on_error,
                    "max_retries": a.max_retries
                }
                for a in self.actions
            ],
            "execution_count": self.execution_count,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class WorkflowEngine:
    """Workflow execution engine."""

    def __init__(self):
        """Initialize workflow engine."""
        self.workflows: Dict[str, Workflow] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.action_handlers: Dict[ActionType, Callable] = {}
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register default action handlers."""
        self.action_handlers = {
            ActionType.SEND_SMS: self._handle_send_sms,
            ActionType.SEND_EMAIL: self._handle_send_email,
            ActionType.CREATE_TICKET: self._handle_create_ticket,
            ActionType.LOG_ACTIVITY: self._handle_log_activity,
            ActionType.UPDATE_CRM: self._handle_update_crm,
            ActionType.ESCALATE: self._handle_escalate,
            ActionType.NOTIFY_AGENT: self._handle_notify_agent,
            ActionType.GENERATE_REPORT: self._handle_generate_report,
            ActionType.TRIGGER_FORECAST: self._handle_trigger_forecast,
            ActionType.ARCHIVE_CALL: self._handle_archive_call,
        }

    async def create_workflow(
        self,
        company_id: str,
        name: str,
        triggers: List[Dict],
        actions: List[Dict],
        metadata: Optional[Dict] = None
    ) -> Optional[Workflow]:
        """
        Create new workflow.
        
        Args:
            company_id: Company identifier
            name: Workflow name
            triggers: List of trigger definitions
            actions: List of action definitions
            metadata: Additional metadata
            
        Returns:
            Created workflow or None
        """
        try:
            workflow_id = str(uuid.uuid4())

            # Parse triggers
            parsed_triggers = []
            for trig in triggers:
                trigger_type = TriggerType(trig["type"])
                parsed_triggers.append(
                    Trigger(trigger_type, trig.get("condition", {}))
                )

            # Parse actions
            parsed_actions = []
            for act in actions:
                action_type = ActionType(act["type"])
                parsed_actions.append(
                    Action(
                        action_type,
                        act.get("config", {}),
                        on_error=act.get("on_error", "continue"),
                        max_retries=act.get("max_retries", 3)
                    )
                )

            workflow = Workflow(
                workflow_id,
                name,
                company_id,
                parsed_triggers,
                parsed_actions,
                metadata=metadata
            )

            self.workflows[workflow_id] = workflow
            logger.info(f"Created workflow {workflow_id} for {company_id}")
            return workflow
        except Exception as e:
            logger.error(f"Error creating workflow: {e}")
            return None

    async def execute_workflow(
        self,
        workflow_id: str,
        trigger_type: TriggerType,
        context: Dict[str, Any]
    ) -> Optional[WorkflowExecution]:
        """
        Execute workflow.
        
        Args:
            workflow_id: Workflow identifier
            trigger_type: Trigger that fired
            context: Context data
            
        Returns:
            Execution record or None
        """
        try:
            workflow = self.workflows.get(workflow_id)
            if not workflow or workflow.status != WorkflowStatus.ACTIVE:
                logger.warning(f"Workflow {workflow_id} not active")
                return None

            # Check if trigger matches
            trigger_match = False
            for trigger in workflow.triggers:
                if trigger.trigger_type == trigger_type:
                    if self._check_trigger_condition(trigger, context):
                        trigger_match = True
                        break

            if not trigger_match:
                logger.info(f"Trigger {trigger_type} not matched for workflow {workflow_id}")
                return None

            # Create execution record
            execution = WorkflowExecution(
                execution_id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                triggered_by=trigger_type,
                started_at=datetime.utcnow()
            )

            # Execute actions
            for action in workflow.actions:
                success = False
                retries = 0

                while retries < action.max_retries:
                    try:
                        handler = self.action_handlers.get(action.action_type)
                        if handler:
                            await handler(action, context)
                            execution.actions_executed += 1
                            success = True
                            break
                        else:
                            logger.warning(f"No handler for {action.action_type}")
                            success = True
                            break
                    except Exception as e:
                        retries += 1
                        logger.warning(f"Action failed (retry {retries}): {e}")

                if not success:
                    execution.actions_failed += 1
                    if action.on_error == "stop":
                        break

            # Update execution
            execution.completed_at = datetime.utcnow()
            execution.status = "completed"
            self.executions[execution.execution_id] = execution

            # Update workflow
            workflow.execution_count += 1
            workflow.last_execution = datetime.utcnow()

            logger.info(f"Completed workflow execution {execution.execution_id}")
            return execution
        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            return None

    async def update_workflow(
        self,
        workflow_id: str,
        name: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
        triggers: Optional[List[Dict]] = None,
        actions: Optional[List[Dict]] = None
    ) -> bool:
        """Update workflow."""
        try:
            workflow = self.workflows.get(workflow_id)
            if not workflow:
                return False

            if name:
                workflow.name = name
            if status:
                workflow.status = status
            if triggers:
                parsed = []
                for t in triggers:
                    trigger_type = TriggerType(t["type"])
                    parsed.append(Trigger(trigger_type, t.get("condition", {})))
                workflow.triggers = parsed
            if actions:
                parsed = []
                for a in actions:
                    action_type = ActionType(a["type"])
                    parsed.append(
                        Action(action_type, a.get("config", {}))
                    )
                workflow.actions = parsed

            workflow.updated_at = datetime.utcnow()
            logger.info(f"Updated workflow {workflow_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating workflow: {e}")
            return False

    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete workflow."""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            logger.info(f"Deleted workflow {workflow_id}")
            return True
        return False

    async def list_workflows(self, company_id: str) -> List[Workflow]:
        """List workflows for company."""
        return [
            w for w in self.workflows.values()
            if w.company_id == company_id
        ]

    async def get_execution_history(
        self,
        workflow_id: str,
        limit: int = 20
    ) -> List[WorkflowExecution]:
        """Get execution history for workflow."""
        execs = [
            e for e in self.executions.values()
            if e.workflow_id == workflow_id
        ]
        return sorted(
            execs,
            key=lambda x: x.started_at,
            reverse=True
        )[:limit]

    def _check_trigger_condition(self, trigger: Trigger, context: Dict) -> bool:
        """Check if trigger condition matches context."""
        condition = trigger.condition

        # Simple condition checking
        for key, expected in condition.items():
            if key not in context:
                return False
            if isinstance(expected, dict):
                # Range check: {"min": 100, "max": 200}
                if "min" in expected and context[key] < expected["min"]:
                    return False
                if "max" in expected and context[key] > expected["max"]:
                    return False
            else:
                # Exact match
                if context[key] != expected:
                    return False

        return True

    async def _handle_send_sms(self, action: Action, context: Dict) -> None:
        """Handle send SMS action."""
        # TODO: Integrate with SMS service
        logger.info(f"Send SMS: {action.config}")

    async def _handle_send_email(self, action: Action, context: Dict) -> None:
        """Handle send email action."""
        # TODO: Integrate with email service
        logger.info(f"Send email: {action.config}")

    async def _handle_create_ticket(self, action: Action, context: Dict) -> None:
        """Handle create ticket action."""
        # TODO: Integrate with ticketing service
        logger.info(f"Create ticket: {action.config}")

    async def _handle_log_activity(self, action: Action, context: Dict) -> None:
        """Handle log activity action."""
        logger.info(f"Log activity: {action.config}")

    async def _handle_update_crm(self, action: Action, context: Dict) -> None:
        """Handle update CRM action."""
        # TODO: Integrate with CRM service
        logger.info(f"Update CRM: {action.config}")

    async def _handle_escalate(self, action: Action, context: Dict) -> None:
        """Handle escalation action."""
        logger.info(f"Escalate: {action.config}")

    async def _handle_notify_agent(self, action: Action, context: Dict) -> None:
        """Handle agent notification."""
        logger.info(f"Notify agent: {action.config}")

    async def _handle_generate_report(self, action: Action, context: Dict) -> None:
        """Handle report generation."""
        # TODO: Integrate with reporting service
        logger.info(f"Generate report: {action.config}")

    async def _handle_trigger_forecast(self, action: Action, context: Dict) -> None:
        """Handle forecast triggering."""
        # TODO: Integrate with forecasting service
        logger.info(f"Trigger forecast: {action.config}")

    async def _handle_archive_call(self, action: Action, context: Dict) -> None:
        """Handle call archival."""
        logger.info(f"Archive call: {action.config}")


# Global instance
workflow_engine = WorkflowEngine()
