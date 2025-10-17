"""
ABOUTME: Agent API endpoints with rate limiting for write operations.
ABOUTME: Agent creation and deletion are rate limited to prevent abuse.
"""

from typing import Dict, List, Optional

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.middleware.rate_limit import get_rate_limit, limiter
from app.models.agent import AgentStatus, AgentType
from app.schemas.agent import Agent, AgentCreate, AgentList, AgentStatusUpdate, AgentUpdate
from app.services.agent_service import AgentService
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/", response_model=Agent, status_code=201)
@limiter.limit(get_rate_limit("agent_create"))
async def create_agent(
    request: Request,
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """Create a new agent (rate limited, requires authentication)."""
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
    search: Optional[str] = Query(None, max_length=100, description="Search in name/description"),
    tags: Optional[str] = Query(None, max_length=500, description="Comma-separated tags to filter"),
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """
    List agents with filtering and pagination (requires authentication).

    Query parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - status: Filter by agent status (active, inactive, training, error, paused)
    - agent_type: Filter by agent type (conversational, analytical, creative, automation)
    - search: Search in agent name and description
    - tags: Comma-separated list of tags (e.g., "support,analytics")
    """
    skip = (page - 1) * page_size

    # Sanitize search query
    if search:
        search = search.strip()[:100]  # Enforce max length

    # Parse tags if provided
    tag_list = None
    if tags:
        tag_list = [tag.strip()[:50] for tag in tags.split(",") if tag.strip()][
            :20
        ]  # Max 20 tags, 50 chars each

    agents, total = await AgentService.list_agents(
        db,
        skip=skip,
        limit=page_size,
        status=status,
        agent_type=agent_type,
        search=search,
        tags=tag_list,
    )

    total_pages = (total + page_size - 1) // page_size

    return AgentList(
        agents=agents, total=total, page=page, page_size=page_size, total_pages=total_pages
    )


@router.get("/{agent_id}", response_model=Agent)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """Get agent details by ID (requires authentication)."""
    agent = await AgentService.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/{agent_id}", response_model=Agent)
async def update_agent(
    agent_id: str,
    agent_data: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """Update agent configuration (requires authentication)."""
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
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """Update agent status (requires authentication)."""
    agent = await AgentService.update_agent_status(db, agent_id, status_data)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.delete("/{agent_id}", status_code=204)
@limiter.limit(get_rate_limit("agent_delete"))
async def delete_agent(
    request: Request,
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """Delete an agent (rate limited, requires authentication)."""
    deleted = await AgentService.delete_agent(db, agent_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found")
    return None
