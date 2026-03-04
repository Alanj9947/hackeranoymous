"""Analytics WebSocket endpoint for real-time dashboard updates."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.database import get_db
from app.core.auth import get_company_id
from app.core.analytics_websocket import analytics_connection_manager
from app.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ws", tags=["analytics"])


@router.websocket("/analytics/{company_id}")
async def websocket_analytics(
    websocket: WebSocket,
    company_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time analytics streaming.
    
    Clients connect and receive continuous metric updates every 30 seconds.
    
    Args:
        websocket: WebSocket connection
        company_id: Company identifier
        db: Database session
    """
    await websocket.accept()
    
    try:
        # Register connection
        await analytics_connection_manager.connect(
            company_id,
            websocket.send_text
        )
        
        # Send initial metrics
        service = AnalyticsService()
        calls_summary = await service.get_calls_summary(db, company_id)
        by_agent = await service.get_calls_by_agent(db, company_id)
        by_phone = await service.get_calls_by_phone(db, company_id)
        costs = await service.get_costs_summary(db, company_id)
        health = await service.get_health(db)
        
        await analytics_connection_manager.send_metrics_update(
            company_id,
            calls_summary,
            by_agent,
            by_phone,
            costs,
            health
        )
        
        # Keep connection open and listen for client messages
        while True:
            data = await websocket.receive_text()
            
            # Handle client messages (e.g., ping, custom requests)
            if data == "ping":
                await websocket.send_json({"type": "pong", "status": "connected"})
            elif data.startswith("update:"):
                # Client requesting immediate update
                calls_summary = await service.get_calls_summary(db, company_id)
                by_agent = await service.get_calls_by_agent(db, company_id)
                by_phone = await service.get_calls_by_phone(db, company_id)
                costs = await service.get_costs_summary(db, company_id)
                health = await service.get_health(db)
                
                await analytics_connection_manager.send_metrics_update(
                    company_id,
                    calls_summary,
                    by_agent,
                    by_phone,
                    costs,
                    health
                )
    
    except WebSocketDisconnect:
        await analytics_connection_manager.disconnect(company_id, websocket.send_text)
        logger.info(f"Analytics WebSocket disconnected for company {company_id}")
    except Exception as e:
        logger.error(f"Analytics WebSocket error: {e}")
        await analytics_connection_manager.disconnect(company_id, websocket.send_text)
