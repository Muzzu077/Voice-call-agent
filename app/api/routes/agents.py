"""
Agent management routes for creating and configuring AI agents.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel

from app.db.database import get_db
from app.auth.dependencies import get_current_user, get_current_agent
from app.db.models import User, Agent

router = APIRouter(prefix="/agents", tags=["Agents"])


class AgentCreate(BaseModel):
    name: str
    personality: Optional[str] = None
    voice: Optional[str] = "default"
    tools_enabled: Optional[list[str]] = ["open_app", "search_browser"]


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    personality: Optional[str] = None
    voice: Optional[str] = None
    tools_enabled: Optional[list[str]] = None
    is_active: Optional[bool] = None


class AgentResponse(BaseModel):
    id: UUID
    name: str
    personality: Optional[str]
    voice: str
    tools_enabled: list[str]
    is_active: bool

    class Config:
        from_attributes = True


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_in: AgentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new voice agent."""
    new_agent = Agent(
        user_id=current_user.id,
        name=agent_in.name,
        personality=agent_in.personality,
        voice=agent_in.voice,
        tools_enabled=agent_in.tools_enabled,
    )
    db.add(new_agent)
    await db.commit()
    await db.refresh(new_agent)
    return new_agent


@router.get("", response_model=List[AgentResponse])
async def list_agents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all agents belonging to the current user."""
    stmt = select(Agent).where(Agent.user_id == current_user.id, Agent.is_active == True)
    result = await db.execute(stmt)
    agents = result.scalars().all()
    return agents


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent: Agent = Depends(get_current_agent)
):
    """Get details of a specific agent."""
    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_in: AgentUpdate,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Update agent configuration."""
    update_data = agent_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(agent, key, value)
        
    await db.commit()
    await db.refresh(agent)
    return agent


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete an agent."""
    agent.is_active = False
    await db.commit()
    return None
