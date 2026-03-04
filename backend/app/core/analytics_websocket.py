"""Real-time analytics WebSocket connection manager for live dashboard updates."""

import asyncio
import json
from typing import Callable, Dict, Set
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AnalyticsConnectionManager:
    """Manages WebSocket connections for real-time analytics streaming."""

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Dict[str, Set] = {}  # company_id -> set of connections
        self.update_tasks: Dict[str, asyncio.Task] = {}  # company_id -> broadcast task

    async def connect(self, company_id: str, send_callable: Callable):
        """
        Register a new analytics WebSocket connection.
        
        Args:
            company_id: Company identifier
            send_callable: Async function to send messages to client
        """
        if company_id not in self.active_connections:
            self.active_connections[company_id] = set()
        
        self.active_connections[company_id].add(send_callable)
        
        # Start broadcast task if not running
        if company_id not in self.update_tasks or self.update_tasks[company_id].done():
            self.update_tasks[company_id] = asyncio.create_task(
                self._broadcast_updates(company_id)
            )
        
        logger.info(f"Analytics WS client connected for company {company_id}")

    async def disconnect(self, company_id: str, send_callable: Callable):
        """
        Unregister a WebSocket connection.
        
        Args:
            company_id: Company identifier
            send_callable: Async function to remove
        """
        if company_id in self.active_connections:
            self.active_connections[company_id].discard(send_callable)
            
            # Clean up empty sets
            if not self.active_connections[company_id]:
                del self.active_connections[company_id]
                if company_id in self.update_tasks:
                    self.update_tasks[company_id].cancel()
                    del self.update_tasks[company_id]
        
        logger.info(f"Analytics WS client disconnected for company {company_id}")

    async def broadcast_update(
        self,
        company_id: str,
        update_type: str,
        data: dict,
        timestamp: datetime = None
    ):
        """
        Broadcast an update to all connected clients for a company.
        
        Args:
            company_id: Company identifier
            update_type: Type of update (metrics, alerts, etc.)
            data: Update data payload
            timestamp: Event timestamp (default: now)
        """
        if company_id not in self.active_connections:
            return
        
        message = {
            "type": update_type,
            "timestamp": (timestamp or datetime.utcnow()).isoformat(),
            "data": data
        }
        
        # Send to all connected clients for this company
        disconnected = []
        for send_callable in self.active_connections.get(company_id, set()):
            try:
                await send_callable(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending update to client: {e}")
                disconnected.append(send_callable)
        
        # Clean up disconnected clients
        for send_callable in disconnected:
            await self.disconnect(company_id, send_callable)

    async def _broadcast_updates(self, company_id: str):
        """
        Continuously broadcast updated metrics every 30 seconds.
        
        Args:
            company_id: Company identifier
        """
        while company_id in self.active_connections and self.active_connections[company_id]:
            try:
                await asyncio.sleep(30)  # 30-second refresh interval
                
                # Send heartbeat with current timestamp
                await self.broadcast_update(
                    company_id,
                    "heartbeat",
                    {"status": "connected", "clients": len(self.active_connections.get(company_id, set()))}
                )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in broadcast task: {e}")
                await asyncio.sleep(5)

    async def send_metrics_update(
        self,
        company_id: str,
        calls_summary: dict,
        by_agent: list,
        by_phone: list,
        costs: dict,
        health: dict
    ):
        """
        Send comprehensive metrics update to all clients.
        
        Args:
            company_id: Company identifier
            calls_summary: Summary metrics
            by_agent: Per-agent breakdown
            by_phone: Per-phone breakdown
            costs: Cost summary
            health: System health
        """
        await self.broadcast_update(
            company_id,
            "metrics_update",
            {
                "calls_summary": calls_summary,
                "by_agent": by_agent,
                "by_phone": by_phone,
                "costs": costs,
                "health": health
            }
        )

    async def send_alert(
        self,
        company_id: str,
        alert_type: str,
        severity: str,
        message: str,
        data: dict = None
    ):
        """
        Send an alert to all connected clients.
        
        Args:
            company_id: Company identifier
            alert_type: Type of alert (error_rate, budget, cost_spike, etc.)
            severity: Severity level (critical, warning, info)
            message: Alert message
            data: Additional alert data
        """
        await self.broadcast_update(
            company_id,
            "alert",
            {
                "alert_type": alert_type,
                "severity": severity,
                "message": message,
                "data": data or {}
            }
        )

    async def send_prediction_update(
        self,
        company_id: str,
        prediction_type: str,
        data: dict
    ):
        """
        Send prediction update to all connected clients.
        
        Args:
            company_id: Company identifier
            prediction_type: Type of prediction (call_volume, costs, etc.)
            data: Prediction data
        """
        await self.broadcast_update(
            company_id,
            "prediction_update",
            {
                "prediction_type": prediction_type,
                "data": data
            }
        )

    def get_active_clients(self, company_id: str) -> int:
        """Get number of active clients for a company."""
        return len(self.active_connections.get(company_id, set()))

    def get_all_connected_companies(self) -> list:
        """Get list of companies with active connections."""
        return list(self.active_connections.keys())


# Global instance
analytics_connection_manager = AnalyticsConnectionManager()
