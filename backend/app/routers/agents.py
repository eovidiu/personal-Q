"""
ABOUTME: Agent API endpoints with rate limiting for write operations.
ABOUTME: Agent creation and deletion are rate limited to prevent abuse.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.db.database import get_db
from app.schemas.agent import AgentCreate, AgentUpdate, AgentStatusUpdate, Agent, AgentList
from app.models.agent import AgentStatus, AgentType
from app.services.agent_service import AgentService
from app.middleware.rate_limit import limiter, get_rate_limit

router = APIRouter()


@router.post("/", response_model=Agent, status_code=201)
@limiter.limit(get_rate_limit("agent_create"))
async def create_agent(
    request: Request,
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new agent (rate limited)."""
    try:
        agent = await AgentService.create_agent(db, agent_data)
        return agent
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=AgentList)
async def list_agents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[AgentStatus] = Query(None, description="Filter by status"),
    agent_type: Optional[AgentType] = Query(None, description="Filter by type"),
    search: Optional[str] = Query(None, description="Search in name/description"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter"),
    db: AsyncSession = Depends(get_db)
):
    """
    List agents with filtering and pagination.

    Query parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - status: Filter by agent status (active, inactive, training, error, paused)
    - agent_type: Filter by agent type (conversational, analytical, creative, automation)
    - search: Search in agent name and description
    - tags: Comma-separated list of tags (e.g., "support,analytics")
    """
    skip = (page - 1) * page_size

    # Parse tags if provided
    tag_list = None
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

    agents, total = await AgentService.list_agents(
        db,
        skip=skip,
        limit=page_size,
        status=status,
        agent_type=agent_type,
        search=search,
        tags=tag_list
    )

    total_pages = (total + page_size - 1) // page_size

    return AgentList(
        agents=agents,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{agent_id}", response_model=Agent)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get agent details by ID."""
    agent = await AgentService.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/{agent_id}", response_model=Agent)
async def update_agent(
    agent_id: str,
    agent_data: AgentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update agent configuration."""
    try:
        agent = await AgentService.update_agent(db, agent_id, agent_data)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{agent_id}/status", response_model=Agent)
async def update_agent_status(
    agent_id: str,
    status_data: AgentStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update agent status (active/inactive/paused/etc.)."""
    agent = await AgentService.update_agent_status(db, agent_id, status_data)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.delete("/{agent_id}", status_code=204)
@limiter.limit(get_rate_limit("agent_delete"))
async def delete_agent(
    request: Request,
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete an agent (rate limited)."""
    deleted = await AgentService.delete_agent(db, agent_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found")
    return None
