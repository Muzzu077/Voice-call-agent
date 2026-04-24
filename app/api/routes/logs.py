"""
Observability routes — conversations, actions, and stats for agents.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, func
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.db.database import get_db
from app.auth.dependencies import get_current_user, get_current_agent
from app.db.models import User, Agent, Conversation, ActionLog

router = APIRouter(tags=["Observability"])


class ConversationResponse(BaseModel):
    id: UUID
    user_message: str
    ai_response: str
    latency_ms: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class ActionResponse(BaseModel):
    id: UUID
    action_type: str
    action_data: Optional[dict]
    status: str
    result: Optional[str]
    latency_ms: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


@router.get(
    "/agents/{agent_id}/conversations",
    response_model=List[ConversationResponse],
)
async def get_agent_conversations(
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """Get paginated conversations for an agent."""
    offset = (page - 1) * limit
    stmt = (
        select(Conversation)
        .where(Conversation.agent_id == agent.id)
        .order_by(desc(Conversation.created_at))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get(
    "/agents/{agent_id}/actions",
    response_model=List[ActionResponse],
)
async def get_agent_actions(
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """Get paginated action log for an agent."""
    offset = (page - 1) * limit
    stmt = (
        select(ActionLog)
        .where(ActionLog.agent_id == agent.id)
        .order_by(desc(ActionLog.created_at))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/agents/{agent_id}/stats")
async def get_agent_stats(
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Get quick stats for an agent."""
    # Total conversations
    conv_count = await db.execute(
        select(func.count(Conversation.id)).where(
            Conversation.agent_id == agent.id
        )
    )
    total_conversations = conv_count.scalar_one()

    # Total actions
    action_count = await db.execute(
        select(func.count(ActionLog.id)).where(ActionLog.agent_id == agent.id)
    )
    total_actions = action_count.scalar_one()

    # Success rate
    success_count = await db.execute(
        select(func.count(ActionLog.id)).where(
            ActionLog.agent_id == agent.id, ActionLog.status == "success"
        )
    )
    successful_actions = success_count.scalar_one()

    # Average latency
    avg_latency = await db.execute(
        select(func.avg(Conversation.latency_ms)).where(
            Conversation.agent_id == agent.id,
            Conversation.latency_ms.isnot(None),
        )
    )
    avg_lat = avg_latency.scalar_one()

    return {
        "total_conversations": total_conversations,
        "total_actions": total_actions,
        "successful_actions": successful_actions,
        "failed_actions": total_actions - successful_actions,
        "success_rate": (
            round(successful_actions / total_actions * 100, 1)
            if total_actions > 0
            else 0
        ),
        "avg_latency_ms": round(avg_lat, 1) if avg_lat else None,
    }
