"""
Agent service layer for business logic.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional, List
import uuid
from datetime import datetime

from app.models.agent import Agent, AgentStatus, AgentType
from app.models.activity import Activity, ActivityType, ActivityStatus
from app.schemas.agent import AgentCreate, AgentUpdate, AgentStatusUpdate
from app.utils.datetime_utils import utcnow
from app.services.cache_service import cache_service


class AgentService:
    """Service for agent operations."""

    @staticmethod
    async def create_agent(
        db: AsyncSession,
        agent_data: AgentCreate
    ) -> Agent:
        """
        Create a new agent.

        Args:
            db: Database session
            agent_data: Agent creation data

        Returns:
            Created agent

        Raises:
            ValueError: If agent name already exists
        """
        # Check if agent with same name exists
        result = await db.execute(
            select(Agent).where(Agent.name == agent_data.name)
        )
        existing_agent = result.scalar_one_or_none()
        if existing_agent:
            raise ValueError(f"Agent with name '{agent_data.name}' already exists")

        # Create agent
        agent = Agent(
            id=str(uuid.uuid4()),
            **agent_data.model_dump()
        )

        db.add(agent)
        await db.commit()
        await db.refresh(agent)

        # Log activity
        activity = Activity(
            id=str(uuid.uuid4()),
            agent_id=agent.id,
            activity_type=ActivityType.AGENT_CREATED,
            status=ActivityStatus.SUCCESS,
            title=f"Agent '{agent.name}' created",
            description=f"Created {agent.agent_type.value} agent"
        )
        db.add(activity)
        await db.commit()

        return agent

    @staticmethod
    async def get_agent(db: AsyncSession, agent_id: str) -> Optional[Agent]:
        """
        Get agent by ID with caching.
        
        Args:
            db: Database session
            agent_id: Agent ID
            
        Returns:
            Agent or None if not found
        """
        # Try cache first
        cache_key = f"agent:{agent_id}"
        cached_agent = await cache_service.get(cache_key)
        if cached_agent:
            return cached_agent
        
        # Fetch from database
        result = await db.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        agent = result.scalar_one_or_none()
        
        # Cache for 10 minutes
        if agent:
            await cache_service.set(cache_key, agent, ttl=600)
        
        return agent

    @staticmethod
    async def list_agents(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status: Optional[AgentStatus] = None,
        agent_type: Optional[AgentType] = None,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> tuple[List[Agent], int]:
        """
        List agents with filtering and pagination.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Filter by agent status
            agent_type: Filter by agent type
            search: Search in name, description, tags
            tags: Filter by tags (any match)

        Returns:
            Tuple of (agents list, total count)
        """
        query = select(Agent)

        # Apply filters
        if status:
            query = query.where(Agent.status == status)

        if agent_type:
            query = query.where(Agent.agent_type == agent_type)

        if search:
            search_filter = or_(
                Agent.name.ilike(f"%{search}%"),
                Agent.description.ilike(f"%{search}%")
            )
            query = query.where(search_filter)

        if tags:
            # Filter agents that have any of the specified tags
            tag_filters = []
            for tag in tags:
                tag_filters.append(Agent.tags.contains([tag]))
            if tag_filters:
                query = query.where(or_(*tag_filters))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination and ordering
        query = query.order_by(Agent.created_at.desc())
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        agents = result.scalars().all()

        return list(agents), total

    @staticmethod
    async def update_agent(
        db: AsyncSession,
        agent_id: str,
        agent_data: AgentUpdate
    ) -> Optional[Agent]:
        """
        Update agent.

        Args:
            db: Database session
            agent_id: Agent ID
            agent_data: Update data

        Returns:
            Updated agent or None if not found

        Raises:
            ValueError: If updated name conflicts with existing agent
        """
        agent = await AgentService.get_agent(db, agent_id)
        if not agent:
            return None

        # Check name uniqueness if name is being updated
        if agent_data.name and agent_data.name != agent.name:
            result = await db.execute(
                select(Agent).where(Agent.name == agent_data.name)
            )
            existing_agent = result.scalar_one_or_none()
            if existing_agent:
                raise ValueError(f"Agent with name '{agent_data.name}' already exists")

        # Update fields
        update_data = agent_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(agent, field, value)

        agent.updated_at = utcnow()

        await db.commit()
        await db.refresh(agent)

        # Log activity
        activity = Activity(
            id=str(uuid.uuid4()),
            agent_id=agent.id,
            activity_type=ActivityType.AGENT_UPDATED,
            status=ActivityStatus.SUCCESS,
            title=f"Agent '{agent.name}' updated",
            description="Agent configuration updated"
        )
        db.add(activity)
        await db.commit()

        # Invalidate cache
        await cache_service.delete(f"agent:{agent_id}")

        return agent

    @staticmethod
    async def update_agent_status(
        db: AsyncSession,
        agent_id: str,
        status_data: AgentStatusUpdate
    ) -> Optional[Agent]:
        """Update agent status."""
        agent = await AgentService.get_agent(db, agent_id)
        if not agent:
            return None

        old_status = agent.status
        agent.status = status_data.status
        agent.updated_at = utcnow()

        if status_data.status == AgentStatus.ACTIVE:
            agent.last_active = utcnow()

        await db.commit()
        await db.refresh(agent)

        # Log activity
        activity_type = {
            AgentStatus.ACTIVE: ActivityType.AGENT_STARTED,
            AgentStatus.INACTIVE: ActivityType.AGENT_STOPPED,
            AgentStatus.PAUSED: ActivityType.AGENT_STOPPED,
        }.get(status_data.status, ActivityType.AGENT_UPDATED)

        activity = Activity(
            id=str(uuid.uuid4()),
            agent_id=agent.id,
            activity_type=activity_type,
            status=ActivityStatus.SUCCESS,
            title=f"Agent '{agent.name}' status changed",
            description=f"Status changed from {old_status.value} to {status_data.status.value}"
        )
        db.add(activity)
        await db.commit()

        # Invalidate cache
        await cache_service.delete(f"agent:{agent_id}")

        return agent

    @staticmethod
    async def delete_agent(db: AsyncSession, agent_id: str) -> bool:
        """
        Delete agent.

        Args:
            db: Database session
            agent_id: Agent ID

        Returns:
            True if deleted, False if not found
        """
        agent = await AgentService.get_agent(db, agent_id)
        if not agent:
            return False

        agent_name = agent.name

        # Log activity before deletion
        activity = Activity(
            id=str(uuid.uuid4()),
            agent_id=None,  # Agent will be deleted
            activity_type=ActivityType.AGENT_DELETED,
            status=ActivityStatus.SUCCESS,
            title=f"Agent '{agent_name}' deleted",
            description="Agent removed from system"
        )
        db.add(activity)

        await db.delete(agent)
        await db.commit()

        # Invalidate cache
        await cache_service.delete(f"agent:{agent_id}")

        return True
