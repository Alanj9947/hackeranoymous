"""SMS integration service with Twilio support."""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class SMSProvider(str, Enum):
    """SMS providers."""
    TWILIO = "twilio"


class SMSMessage:
    """SMS message representation."""

    def __init__(
        self,
        message_id: str,
        phone_number: str,
        content: str,
        direction: str = "inbound",  # inbound, outbound
        status: str = "sent",
        metadata: Optional[Dict] = None
    ):
        """Initialize SMS message."""
        self.message_id = message_id
        self.phone_number = phone_number
        self.content = content
        self.direction = direction
        self.status = status
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "message_id": self.message_id,
            "phone_number": self.phone_number,
            "content": self.content,
            "direction": self.direction,
            "status": self.status,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class SMSConversation:
    """SMS conversation thread."""

    def __init__(
        self,
        conversation_id: str,
        phone_number: str,
        contact_name: Optional[str] = None
    ):
        """Initialize conversation."""
        self.conversation_id = conversation_id
        self.phone_number = phone_number
        self.contact_name = contact_name
        self.messages: List[SMSMessage] = []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def add_message(self, message: SMSMessage) -> None:
        """Add message to conversation."""
        self.messages.append(message)
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "conversation_id": self.conversation_id,
            "phone_number": self.phone_number,
            "contact_name": self.contact_name,
            "message_count": len(self.messages),
            "messages": [m.to_dict() for m in self.messages[-10:]],  # Last 10
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class SMSAdapter:
    """Base SMS adapter."""

    def __init__(self, config: Dict[str, str]):
        """Initialize adapter."""
        self.config = config
        self.connected = False

    async def connect(self) -> bool:
        """Connect to SMS provider."""
        pass

    async def disconnect(self) -> bool:
        """Disconnect from SMS provider."""
        pass

    async def send_sms(self, phone: str, message: str) -> Optional[str]:
        """Send SMS. Returns message ID."""
        pass

    async def receive_sms(self, message_id: str) -> Optional[SMSMessage]:
        """Receive/retrieve SMS."""
        pass


class TwilioSMSAdapter(SMSAdapter):
    """Twilio SMS adapter."""

    async def connect(self) -> bool:
        """Connect to Twilio."""
        try:
            # TODO: Import and initialize Twilio client
            # from twilio.rest import Client
            # self.client = Client(account_sid, auth_token)
            self.connected = True
            logger.info("Connected to Twilio SMS")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Twilio: {e}")
            return False

    async def disconnect(self) -> bool:
        """Disconnect from Twilio."""
        self.connected = False
        logger.info("Disconnected from Twilio SMS")
        return True

    async def send_sms(self, phone: str, message: str) -> Optional[str]:
        """Send SMS via Twilio."""
        try:
            # TODO: Send SMS via Twilio
            # message = self.client.messages.create(
            #     body=message,
            #     from_=self.config['phone_number'],
            #     to=phone
            # )
            # return message.sid
            logger.info(f"Sent SMS to {phone}")
            return "SM_" + phone  # Dummy ID
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return None

    async def receive_sms(self, message_id: str) -> Optional[SMSMessage]:
        """Retrieve SMS from Twilio."""
        try:
            # TODO: Retrieve message from Twilio
            # message = self.client.messages(message_id).fetch()
            return None
        except Exception as e:
            logger.error(f"Error retrieving SMS: {e}")
            return None


class SMSService:
    """Service for SMS communication."""

    def __init__(self):
        """Initialize SMS service."""
        self.adapter: Optional[SMSAdapter] = None
        self.conversations: Dict[str, SMSConversation] = {}
        self.active_provider: Optional[str] = None
        self.message_history: Dict[str, List[SMSMessage]] = {}

    async def configure(
        self,
        company_id: str,
        provider: SMSProvider,
        config: Dict[str, str]
    ) -> bool:
        """
        Configure SMS provider.
        
        Args:
            company_id: Company identifier
            provider: SMS provider
            config: Configuration
            
        Returns:
            Success status
        """
        try:
            if provider == SMSProvider.TWILIO:
                self.adapter = TwilioSMSAdapter(config)
            else:
                raise ValueError(f"Unknown provider: {provider}")

            # Test connection
            if not await self.adapter.connect():
                raise Exception("Failed to connect")

            self.active_provider = f"{company_id}:{provider.value}"
            logger.info(f"Configured SMS for {company_id}")
            return True
        except Exception as e:
            logger.error(f"Error configuring SMS: {e}")
            return False

    async def disconnect(self, company_id: str) -> bool:
        """Disconnect SMS provider."""
        if self.adapter:
            success = await self.adapter.disconnect()
            self.adapter = None
            self.active_provider = None
            return success
        return False

    async def send_sms(
        self,
        company_id: str,
        phone: str,
        message: str
    ) -> Optional[str]:
        """
        Send SMS.
        
        Args:
            company_id: Company identifier
            phone: Phone number
            message: Message content
            
        Returns:
            Message ID or None
        """
        if not self.adapter or not self.adapter.connected:
            logger.error("SMS adapter not connected")
            return None

        message_id = await self.adapter.send_sms(phone, message)

        if message_id:
            # Store in conversation
            conv_id = f"{company_id}:{phone}"
            if conv_id not in self.conversations:
                self.conversations[conv_id] = SMSConversation(conv_id, phone)

            sms_msg = SMSMessage(
                message_id,
                phone,
                message,
                direction="outbound",
                status="sent"
            )
            self.conversations[conv_id].add_message(sms_msg)

            # Track in history
            if phone not in self.message_history:
                self.message_history[phone] = []
            self.message_history[phone].append(sms_msg)

        return message_id

    async def receive_sms(
        self,
        company_id: str,
        phone: str,
        message: str,
        message_id: str = None
    ) -> SMSMessage:
        """
        Receive inbound SMS.
        
        Args:
            company_id: Company identifier
            phone: Phone number
            message: Message content
            message_id: Message ID
            
        Returns:
            SMS message object
        """
        import uuid
        msg_id = message_id or str(uuid.uuid4())

        sms_msg = SMSMessage(
            msg_id,
            phone,
            message,
            direction="inbound",
            status="received"
        )

        # Store in conversation
        conv_id = f"{company_id}:{phone}"
        if conv_id not in self.conversations:
            self.conversations[conv_id] = SMSConversation(conv_id, phone)

        self.conversations[conv_id].add_message(sms_msg)

        # Track in history
        if phone not in self.message_history:
            self.message_history[phone] = []
        self.message_history[phone].append(sms_msg)

        logger.info(f"Received SMS from {phone}")
        return sms_msg

    async def get_conversation(
        self,
        company_id: str,
        phone: str
    ) -> Optional[SMSConversation]:
        """Get SMS conversation."""
        conv_id = f"{company_id}:{phone}"
        return self.conversations.get(conv_id)

    async def list_conversations(
        self,
        company_id: str,
        limit: int = 20
    ) -> List[SMSConversation]:
        """List SMS conversations for company."""
        convs = [
            c for cid, c in self.conversations.items()
            if cid.startswith(company_id)
        ]
        return sorted(
            convs,
            key=lambda c: c.updated_at,
            reverse=True
        )[:limit]

    async def search_conversations(
        self,
        company_id: str,
        query: str,
        limit: int = 20
    ) -> List[SMSConversation]:
        """Search SMS conversations."""
        results = []
        
        for conv_id, conv in self.conversations.items():
            if not conv_id.startswith(company_id):
                continue

            # Search in phone number and messages
            if query.lower() in conv.phone_number.lower():
                results.append(conv)
                continue

            for msg in conv.messages:
                if query.lower() in msg.content.lower():
                    results.append(conv)
                    break

        return results[:limit]

    def get_status(self, company_id: str) -> Dict[str, Any]:
        """Get SMS integration status."""
        return {
            "provider": self.active_provider.split(":")[-1] if self.active_provider else None,
            "connected": self.adapter.connected if self.adapter else False,
            "conversations": len([
                c for cid in self.conversations
                if cid.startswith(company_id)
            ]),
            "timestamp": datetime.utcnow().isoformat()
        }


# Global instance
sms_service = SMSService()
