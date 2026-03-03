"""
WebSocket connection manager for real-time communication.
Manages bidirectional communication between browser and backend.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List
from uuid import UUID

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and message routing."""

    def __init__(self):
        """Initialize connection manager."""
        # Store active connections: {conversation_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # Store conversation history: {conversation_id: [messages]}
        self.conversation_history: Dict[str, List[Dict[str, Any]]] = {}

    async def connect(self, websocket: WebSocket, conversation_id: str) -> None:
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: FastAPI WebSocket connection
            conversation_id: Unique conversation identifier
        """
        await websocket.accept()
        self.active_connections[conversation_id] = websocket
        self.conversation_history[conversation_id] = []
        logger.info(f"Client connected: {conversation_id}")

    def disconnect(self, conversation_id: str) -> None:
        """
        Unregister and cleanup a WebSocket connection.

        Args:
            conversation_id: Unique conversation identifier
        """
        if conversation_id in self.active_connections:
            del self.active_connections[conversation_id]
            logger.info(f"Client disconnected: {conversation_id}")

    async def send_json(
        self, conversation_id: str, data: Dict[str, Any]
    ) -> None:
        """
        Send JSON data to a specific client.

        Args:
            conversation_id: Target conversation ID
            data: Dictionary to send as JSON
        """
        if conversation_id not in self.active_connections:
            logger.warning(f"Attempted to send to disconnected client: {conversation_id}")
            return

        try:
            websocket = self.active_connections[conversation_id]
            await websocket.send_json(data)
            logger.debug(f"Sent JSON to {conversation_id}: {data.get('type', 'unknown')}")
        except Exception as e:
            logger.error(f"Error sending JSON to {conversation_id}: {str(e)}")
            self.disconnect(conversation_id)

    async def send_bytes(
        self, conversation_id: str, data: bytes
    ) -> None:
        """
        Send binary data (audio) to a specific client.

        Args:
            conversation_id: Target conversation ID
            data: Binary data to send
        """
        if conversation_id not in self.active_connections:
            logger.warning(f"Attempted to send bytes to disconnected client: {conversation_id}")
            return

        try:
            websocket = self.active_connections[conversation_id]
            await websocket.send_bytes(data)
            logger.debug(f"Sent {len(data)} bytes to {conversation_id}")
        except Exception as e:
            logger.error(f"Error sending bytes to {conversation_id}: {str(e)}")
            self.disconnect(conversation_id)

    async def receive_bytes(self, conversation_id: str) -> bytes | None:
        """
        Receive binary data from a specific client.

        Args:
            conversation_id: Source conversation ID

        Returns:
            Binary data or None if disconnected
        """
        if conversation_id not in self.active_connections:
            logger.warning(f"Attempted to receive from disconnected client: {conversation_id}")
            return None

        try:
            websocket = self.active_connections[conversation_id]
            data = await websocket.receive_bytes()
            logger.debug(f"Received {len(data)} bytes from {conversation_id}")
            return data
        except Exception as e:
            logger.error(f"Error receiving bytes from {conversation_id}: {str(e)}")
            self.disconnect(conversation_id)
            return None

    def add_to_history(
        self,
        conversation_id: str,
        speaker: str,
        message: str,
        message_type: str = "text",
    ) -> None:
        """
        Add a message to conversation history.

        Args:
            conversation_id: Conversation identifier
            speaker: Who sent the message ('user' or 'agent')
            message: Message content
            message_type: Type of message ('text', 'audio', etc)
        """
        if conversation_id not in self.conversation_history:
            self.conversation_history[conversation_id] = []

        self.conversation_history[conversation_id].append(
            {
                "speaker": speaker,
                "message": message,
                "type": message_type,
            }
        )
        logger.debug(
            f"Added to history for {conversation_id}: {speaker} - {message_type}"
        )

    def get_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history.

        Args:
            conversation_id: Conversation identifier

        Returns:
            List of messages in conversation
        """
        return self.conversation_history.get(conversation_id, [])

    def is_connected(self, conversation_id: str) -> bool:
        """
        Check if a conversation is currently connected.

        Args:
            conversation_id: Conversation identifier

        Returns:
            True if connected, False otherwise
        """
        return conversation_id in self.active_connections

    def clear_history(self, conversation_id: str) -> None:
        """
        Clear conversation history (after storing to database).

        Args:
            conversation_id: Conversation identifier
        """
        if conversation_id in self.conversation_history:
            del self.conversation_history[conversation_id]
            logger.debug(f"Cleared history for {conversation_id}")


# Global instance
connection_manager = ConnectionManager()
