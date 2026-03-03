"""
Custom AI Server management routes.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_id, get_current_active_user
from app.core.database import get_db
from app.core.security import encrypt_value
from app.models.custom_server import CustomServerConfig
from app.schemas.custom_server import (
    CustomServerConfigCreate,
    CustomServerConfigResponse,
    CustomServerHealthResponse,
)

router = APIRouter(prefix="/custom-server", tags=["Custom AI Server"])


@router.post("/config", response_model=CustomServerConfigResponse)
async def configure_server(
    body: CustomServerConfigCreate,
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
):
    """Configure or update custom AI server settings."""
    # Check for existing config
    result = await db.execute(
        select(CustomServerConfig).where(
            CustomServerConfig.company_id == company_id,
            CustomServerConfig.agent_id == body.agent_id,
        )
    )
    config = result.scalar_one_or_none()

    if config:
        # Update existing
        config.endpoint = body.endpoint
        config.api_key_encrypted = encrypt_value(body.api_key) if body.api_key else config.api_key_encrypted
        config.model_name = body.model_name
        config.timeout_seconds = body.timeout_seconds
        config.max_retries = body.max_retries
        config.enabled = body.enabled
        config.fallback_to_openai = body.fallback_to_openai
    else:
        config = CustomServerConfig(
            company_id=company_id,
            agent_id=body.agent_id,
            endpoint=body.endpoint,
            api_key_encrypted=encrypt_value(body.api_key) if body.api_key else None,
            model_name=body.model_name,
            timeout_seconds=body.timeout_seconds,
            max_retries=body.max_retries,
            enabled=body.enabled,
            fallback_to_openai=body.fallback_to_openai,
        )
        db.add(config)

    await db.flush()

    # Trigger health check
    from app.worker.tasks import check_custom_server_health

    check_custom_server_health.delay(str(config.id))

    return CustomServerConfigResponse.model_validate(config)


@router.get("/health", response_model=CustomServerHealthResponse)
async def get_server_health(
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
):
    """Get health status of the custom AI server."""
    result = await db.execute(
        select(CustomServerConfig).where(
            CustomServerConfig.company_id == company_id,
            CustomServerConfig.agent_id == None,  # noqa: E711 — company default
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="No custom server configured")

    # Try a live health check
    from app.clients.custom_server import CustomServerClient

    client = CustomServerClient(config)
    try:
        health = await client.health()
        return CustomServerHealthResponse(
            status=health.get("status", "healthy"),
            endpoint=config.endpoint,
            last_check=config.last_health_check,
            response_time=health.get("response_time"),
            # VPS Ollama-specific fields
            ollama_connected=health.get("ollama_connected"),
            model_loaded=health.get("model_loaded"),
            model_name=health.get("model_name"),
            active_requests=health.get("active_requests"),
            # Generic fields
            models_available=health.get("models_available"),
            gpu_available=health.get("gpu_available"),
            gpu_memory_usage=health.get("gpu_memory_usage"),
            request_queue_depth=health.get("request_queue_depth"),
            uptime=health.get("uptime"),
        )
    except Exception as e:
        logger.warning("custom_server_health_check_failed", endpoint=config.endpoint, error=str(e))
        return CustomServerHealthResponse(
            status="unhealthy",
            endpoint=config.endpoint,
            last_check=config.last_health_check,
            response_time=None,
        )


@router.get("/config", response_model=CustomServerConfigResponse)
async def get_server_config(
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
):
    """Get current custom server configuration."""
    result = await db.execute(
        select(CustomServerConfig).where(
            CustomServerConfig.company_id == company_id,
            CustomServerConfig.agent_id == None,  # noqa: E711
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="No custom server configured")
    return CustomServerConfigResponse.model_validate(config)
