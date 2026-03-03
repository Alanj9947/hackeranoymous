"""
WebSocket endpoint for frontend real-time call status updates.
Clients connect here to receive live events for a specific call.

NOTE: The _connections dict is in-memory and not shared across workers.
In a multi-worker production deployment (multiple Uvicorn/Gunicorn processes),
broadcast_to_call() will only reach clients on the same worker. For multi-worker
setups, replace this with a Redis pub/sub fan-out (see REDIS_URL in config).
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Set
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger
from app.core.security import decode_token

logger = get_logger(__name__)

router = APIRouter(tags=["Conversation"])

# In-memory registry: call_id -> set of connected WebSockets.
# Not shared across worker processes (see module docstring).
_connections: Dict[str, Set[WebSocket]] = {}


async def _validate_token(token: str) -> bool:
    """Validate JWT access token. Returns True if valid."""
    if not token:
        return False
    try:
        payload = decode_token(token)
        return payload.get("type") == "access"
    except Exception:
        return False


async def broadcast_to_call(call_id: str, event: dict) -> None:
    """Broadcast an event to all WebSocket clients watching a call."""
    sockets = _connections.get(call_id, set())
    if not sockets:
        return
    dead: Set[WebSocket] = set()
    message = json.dumps(event)
    for ws in list(sockets):
        try:
            await ws.send_text(message)
        except Exception:
            dead.add(ws)
    for ws in dead:
        sockets.discard(ws)


@router.websocket("/ws/calls/{call_id}")
async def call_websocket(websocket: WebSocket, call_id: str, token: str = ""):
    """
    WebSocket endpoint for receiving real-time events for a call.
    The frontend connects here with ?token=<jwt> to get live updates.
    """
    # Accept the WebSocket upgrade first so we can send a proper close frame.
    # The WebSocket protocol requires the handshake to complete before control
    # frames (including Close) can be sent to the client. Any unauthenticated
    # connection is immediately closed with code 4001 before any data is exchanged.
    await websocket.accept()
    if not await _validate_token(token):
        await websocket.close(code=4001)
        return
    logger.info("ws_call_connected", call_id=call_id)

    # Register connection
    if call_id not in _connections:
        _connections[call_id] = set()
    _connections[call_id].add(websocket)

    # Send initial connected event
    await websocket.send_text(
        json.dumps({
            "type": "connected",
            "call_id": call_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    )

    try:
        # Keep alive: echo pings and wait for disconnect
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                msg = json.loads(data)
                # Handle ping/pong
                if msg.get("type") == "ping":
                    await websocket.send_text(
                        json.dumps({"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()})
                    )
            except asyncio.TimeoutError:
                # Send a heartbeat so the connection stays alive
                await websocket.send_text(
                    json.dumps({"type": "heartbeat", "timestamp": datetime.now(timezone.utc).isoformat()})
                )
    except WebSocketDisconnect:
        logger.info("ws_call_disconnected", call_id=call_id)
    except Exception as e:
        logger.error("ws_call_error", call_id=call_id, error=str(e))
    finally:
        _connections.get(call_id, set()).discard(websocket)
        if not _connections.get(call_id):
            _connections.pop(call_id, None)
        logger.info("ws_call_closed", call_id=call_id)
