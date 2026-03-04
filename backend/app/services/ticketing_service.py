"""Ticketing system integration service with Jira and Zendesk adapters."""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class TicketingProvider(str, Enum):
    """Supported ticketing providers."""
    JIRA = "jira"
    ZENDESK = "zendesk"


class TicketStatus(str, Enum):
    """Ticket status values."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ON_HOLD = "on_hold"


class Ticket:
    """Ticket representation."""
    
    def __init__(
        self,
        external_id: str,
        title: str,
        description: str,
        status: TicketStatus,
        priority: str = "medium",
        assignee: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Initialize ticket."""
        self.external_id = external_id
        self.title = title
        self.description = description
        self.status = status
        self.priority = priority
        self.assignee = assignee
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "external_id": self.external_id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority,
            "assignee": self.assignee,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class TicketComment:
    """Ticket comment/update."""
    
    def __init__(
        self,
        ticket_id: str,
        author: str,
        text: str,
        is_internal: bool = False
    ):
        """Initialize comment."""
        self.ticket_id = ticket_id
        self.author = author
        self.text = text
        self.is_internal = is_internal
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "ticket_id": self.ticket_id,
            "author": self.author,
            "text": self.text,
            "is_internal": self.is_internal,
            "timestamp": self.timestamp.isoformat()
        }


class TicketingAdapter(ABC):
    """Base class for ticketing adapters."""

    def __init__(self, config: Dict[str, str]):
        """
        Initialize adapter.
        
        Args:
            config: Configuration dictionary with API credentials
        """
        self.config = config
        self.connected = False

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to ticketing system."""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from ticketing system."""
        pass

    @abstractmethod
    async def create_ticket(self, ticket: Ticket) -> Optional[str]:
        """Create ticket. Returns external ID."""
        pass

    @abstractmethod
    async def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Get ticket by ID."""
        pass

    @abstractmethod
    async def list_tickets(self, limit: int = 20) -> List[Ticket]:
        """List recent tickets."""
        pass

    @abstractmethod
    async def update_ticket(self, ticket_id: str, status: TicketStatus) -> bool:
        """Update ticket status."""
        pass

    @abstractmethod
    async def add_comment(self, comment: TicketComment) -> bool:
        """Add comment to ticket."""
        pass


class JiraAdapter(TicketingAdapter):
    """Jira ticketing adapter."""

    async def connect(self) -> bool:
        """Connect to Jira."""
        try:
            # TODO: Implement Jira connection
            # Use: jira-python or atlassian-python-api
            self.connected = True
            logger.info("Connected to Jira")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Jira: {e}")
            return False

    async def disconnect(self) -> bool:
        """Disconnect from Jira."""
        self.connected = False
        logger.info("Disconnected from Jira")
        return True

    async def create_ticket(self, ticket: Ticket) -> Optional[str]:
        """Create issue in Jira."""
        try:
            # TODO: Create issue
            # POST /rest/api/3/issues
            logger.info(f"Created Jira ticket: {ticket.title}")
            return "JIRA-12345"  # Example ID
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            return None

    async def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Get issue from Jira."""
        try:
            # TODO: Retrieve issue
            # GET /rest/api/3/issues/{issueIdOrKey}
            return None
        except Exception as e:
            logger.error(f"Error retrieving ticket: {e}")
            return None

    async def list_tickets(self, limit: int = 20) -> List[Ticket]:
        """List Jira issues."""
        try:
            # TODO: Search issues
            # GET /rest/api/3/search?jql=...
            return []
        except Exception as e:
            logger.error(f"Error listing tickets: {e}")
            return []

    async def update_ticket(self, ticket_id: str, status: TicketStatus) -> bool:
        """Update Jira issue status."""
        try:
            # TODO: Transition issue
            # POST /rest/api/3/issues/{issueIdOrKey}/transitions
            logger.info(f"Updated ticket {ticket_id} to {status.value}")
            return True
        except Exception as e:
            logger.error(f"Error updating ticket: {e}")
            return False

    async def add_comment(self, comment: TicketComment) -> bool:
        """Add comment to Jira issue."""
        try:
            # TODO: Add comment
            # POST /rest/api/3/issues/{issueIdOrKey}/comments
            logger.info(f"Added comment to {comment.ticket_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding comment: {e}")
            return False


class ZendeskAdapter(TicketingAdapter):
    """Zendesk ticketing adapter."""

    async def connect(self) -> bool:
        """Connect to Zendesk."""
        try:
            # TODO: Implement Zendesk connection
            # Use: zendesk or requests
            self.connected = True
            logger.info("Connected to Zendesk")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Zendesk: {e}")
            return False

    async def disconnect(self) -> bool:
        """Disconnect from Zendesk."""
        self.connected = False
        logger.info("Disconnected from Zendesk")
        return True

    async def create_ticket(self, ticket: Ticket) -> Optional[str]:
        """Create ticket in Zendesk."""
        try:
            # TODO: Create ticket
            # POST /api/v2/tickets.json
            logger.info(f"Created Zendesk ticket: {ticket.title}")
            return "12345"  # Example ID
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            return None

    async def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Get ticket from Zendesk."""
        try:
            # TODO: Retrieve ticket
            # GET /api/v2/tickets/{id}.json
            return None
        except Exception as e:
            logger.error(f"Error retrieving ticket: {e}")
            return None

    async def list_tickets(self, limit: int = 20) -> List[Ticket]:
        """List Zendesk tickets."""
        try:
            # TODO: Search tickets
            # GET /api/v2/search.json?query=...
            return []
        except Exception as e:
            logger.error(f"Error listing tickets: {e}")
            return []

    async def update_ticket(self, ticket_id: str, status: TicketStatus) -> bool:
        """Update Zendesk ticket status."""
        try:
            # TODO: Update ticket
            # PUT /api/v2/tickets/{id}.json
            logger.info(f"Updated ticket {ticket_id} to {status.value}")
            return True
        except Exception as e:
            logger.error(f"Error updating ticket: {e}")
            return False

    async def add_comment(self, comment: TicketComment) -> bool:
        """Add comment to Zendesk ticket."""
        try:
            # TODO: Add comment
            # POST /api/v2/tickets/{id}/comments.json
            logger.info(f"Added comment to {comment.ticket_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding comment: {e}")
            return False


class TicketingService:
    """Service for managing ticketing integrations."""

    def __init__(self):
        """Initialize ticketing service."""
        self.adapters: Dict[str, TicketingAdapter] = {}
        self.active_provider: Optional[str] = None
        self.ticket_cache: Dict[str, Ticket] = {}

    async def configure(
        self,
        company_id: str,
        provider: TicketingProvider,
        config: Dict[str, str]
    ) -> bool:
        """
        Configure ticketing provider.
        
        Args:
            company_id: Company identifier
            provider: Ticketing provider
            config: Configuration with API credentials
            
        Returns:
            Success status
        """
        try:
            if provider == TicketingProvider.JIRA:
                adapter = JiraAdapter(config)
            elif provider == TicketingProvider.ZENDESK:
                adapter = ZendeskAdapter(config)
            else:
                raise ValueError(f"Unknown provider: {provider}")

            # Test connection
            if not await adapter.connect():
                raise Exception("Failed to connect")

            # Store adapter
            adapter_key = f"{company_id}:{provider.value}"
            self.adapters[adapter_key] = adapter
            self.active_provider = adapter_key

            logger.info(f"Configured {provider.value} for {company_id}")
            return True
        except Exception as e:
            logger.error(f"Error configuring ticketing: {e}")
            return False

    async def disconnect(self, company_id: str, provider: TicketingProvider) -> bool:
        """Disconnect ticketing provider."""
        adapter_key = f"{company_id}:{provider.value}"
        if adapter_key in self.adapters:
            adapter = self.adapters[adapter_key]
            success = await adapter.disconnect()
            del self.adapters[adapter_key]
            if self.active_provider == adapter_key:
                self.active_provider = None
            return success
        return False

    async def create_ticket(
        self,
        company_id: str,
        title: str,
        description: str,
        priority: str = "medium",
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Create ticket in active system.
        
        Args:
            company_id: Company identifier
            title: Ticket title
            description: Ticket description
            priority: Priority level
            metadata: Additional metadata
            
        Returns:
            External ticket ID or None
        """
        adapter = self._get_active_adapter(company_id)
        if not adapter:
            return None

        ticket = Ticket(
            external_id="",  # Will be set by adapter
            title=title,
            description=description,
            status=TicketStatus.OPEN,
            priority=priority,
            metadata=metadata or {}
        )

        return await adapter.create_ticket(ticket)

    async def get_ticket(
        self,
        company_id: str,
        ticket_id: str
    ) -> Optional[Ticket]:
        """
        Get ticket from active system.
        
        Args:
            company_id: Company identifier
            ticket_id: Ticket ID
            
        Returns:
            Ticket object or None
        """
        adapter = self._get_active_adapter(company_id)
        if not adapter:
            return None

        return await adapter.get_ticket(ticket_id)

    async def list_tickets(
        self,
        company_id: str,
        limit: int = 20
    ) -> List[Ticket]:
        """
        List tickets from active system.
        
        Args:
            company_id: Company identifier
            limit: Result limit
            
        Returns:
            List of tickets
        """
        adapter = self._get_active_adapter(company_id)
        if not adapter:
            return []

        return await adapter.list_tickets(limit)

    async def update_ticket_status(
        self,
        company_id: str,
        ticket_id: str,
        status: TicketStatus
    ) -> bool:
        """
        Update ticket status.
        
        Args:
            company_id: Company identifier
            ticket_id: Ticket ID
            status: New status
            
        Returns:
            Success status
        """
        adapter = self._get_active_adapter(company_id)
        if not adapter:
            return False

        return await adapter.update_ticket(ticket_id, status)

    async def add_ticket_comment(
        self,
        company_id: str,
        ticket_id: str,
        author: str,
        text: str,
        is_internal: bool = False
    ) -> bool:
        """
        Add comment to ticket.
        
        Args:
            company_id: Company identifier
            ticket_id: Ticket ID
            author: Comment author
            text: Comment text
            is_internal: Internal comment
            
        Returns:
            Success status
        """
        adapter = self._get_active_adapter(company_id)
        if not adapter:
            return False

        comment = TicketComment(ticket_id, author, text, is_internal)
        return await adapter.add_comment(comment)

    def _get_active_adapter(self, company_id: str) -> Optional[TicketingAdapter]:
        """Get active ticketing adapter for company."""
        if not self.active_provider:
            return None

        if self.active_provider.startswith(company_id):
            return self.adapters.get(self.active_provider)

        return None

    def get_status(self, company_id: str) -> Dict[str, Any]:
        """Get ticketing integration status."""
        adapter_key = self.active_provider
        if adapter_key and adapter_key.startswith(company_id):
            provider = adapter_key.split(":")[-1]
            adapter = self.adapters.get(adapter_key)
            return {
                "provider": provider,
                "connected": adapter.connected if adapter else False,
                "timestamp": datetime.utcnow().isoformat()
            }

        return {
            "provider": None,
            "connected": False,
            "timestamp": datetime.utcnow().isoformat()
        }


# Global instance
ticketing_service = TicketingService()
