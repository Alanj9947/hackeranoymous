"""
Agent CRUD routes.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_id, get_current_active_user
from app.core.database import get_db
from app.models.agent import Agent
from app.models.user import User
from app.schemas.agent import (
    AgentCreate,
    AgentListResponse,
    AgentResponse,
    AgentUpdate,
)

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("", response_model=AgentListResponse)
async def list_agents(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
):
    """List agents for the current company."""
    query = select(Agent).where(Agent.company_id == company_id)
    count_query = select(func.count()).select_from(Agent).where(Agent.company_id == company_id)

    if status_filter:
        query = query.where(Agent.status == status_filter)
        count_query = count_query.where(Agent.status == status_filter)

    query = query.order_by(Agent.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    agents = result.scalars().all()
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    return AgentListResponse(
        agents=[AgentResponse.model_validate(a) for a in agents],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    body: AgentCreate,
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
):
    """Create a new voice agent."""
    agent = Agent(
        company_id=company_id,
        name=body.name,
        description=body.description,
        system_prompt=body.system_prompt.model_dump() if body.system_prompt else {},
        voice_settings=body.voice_settings.model_dump() if body.voice_settings else {},
        call_settings=body.call_settings.model_dump() if body.call_settings else {},
        data_extraction=body.data_extraction.model_dump() if body.data_extraction else {},
        phone_numbers=body.phone_numbers or [],
    )
    db.add(agent)
    await db.flush()
    return AgentResponse.model_validate(agent)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
):
    """Get a single agent by ID."""
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.company_id == company_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentResponse.model_validate(agent)


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: UUID,
    body: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
):
    """Update an existing agent."""
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.company_id == company_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)

    await db.flush()
    return AgentResponse.model_validate(agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
):
    """Delete an agent."""
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.company_id == company_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    await db.delete(agent)
