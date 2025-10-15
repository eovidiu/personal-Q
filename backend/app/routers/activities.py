"""
Activity log API endpoints.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, Dict

from app.db.database import get_db
from app.schemas.activity import Activity, ActivityList
from app.models.activity import Activity as ActivityModel, ActivityType, ActivityStatus
from app.dependencies.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=ActivityList)
async def list_activities(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    agent_id: Optional[str] = Query(None),
    activity_type: Optional[ActivityType] = Query(None),
    status: Optional[ActivityStatus] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """List activities with filtering and pagination (requires authentication)."""
    query = select(ActivityModel)

    if agent_id:
        query = query.where(ActivityModel.agent_id == agent_id)

    if activity_type:
        query = query.where(ActivityModel.activity_type == activity_type)

    if status:
        query = query.where(ActivityModel.status == status)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    skip = (page - 1) * page_size
    query = query.order_by(ActivityModel.created_at.desc()).offset(skip).limit(page_size)

    result = await db.execute(query)
    activities = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size

    return ActivityList(
        activities=list(activities),
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
