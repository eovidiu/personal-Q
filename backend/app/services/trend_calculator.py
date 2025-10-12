"""Trend calculation service for dashboard metrics."""

from datetime import timedelta

from app.models.agent import Agent
from app.models.task import Task, TaskStatus
from app.utils.datetime_utils import utcnow
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class TrendCalculator:
    """Calculate trends for dashboard metrics."""

    @staticmethod
    async def calculate_agent_trend(db: AsyncSession) -> str:
        """
        Calculate change in total agents over the last week.
        Returns: "+X this week" or "-X this week" or "No change this week"
        """
        now = utcnow()
        seven_days_ago = now - timedelta(days=7)

        # Agents created in last 7 days
        recent_result = await db.execute(
            select(func.count(Agent.id)).where(Agent.created_at >= seven_days_ago)
        )
        recent_count = recent_result.scalar() or 0

        # For now, assume no deletions, just additions
        change = recent_count

        if change > 0:
            return f"+{change} this week"
        elif change < 0:
            return f"{change} this week"
        else:
            return "No change this week"

    @staticmethod
    async def calculate_tasks_trend(db: AsyncSession) -> str:
        """
        Calculate percentage change in tasks completed.
        Compares last 30 days vs. previous 30 days.
        Returns: "+X.X% from last month" or "-X.X% from last month"
        """
        now = utcnow()
        thirty_days_ago = now - timedelta(days=30)
        sixty_days_ago = now - timedelta(days=60)

        # Tasks completed in last 30 days
        this_month_result = await db.execute(
            select(func.count(Task.id)).where(
                Task.status == TaskStatus.COMPLETED, Task.completed_at >= thirty_days_ago
            )
        )
        this_month_count = this_month_result.scalar() or 0

        # Tasks completed in previous 30 days (30-60 days ago)
        last_month_result = await db.execute(
            select(func.count(Task.id)).where(
                Task.status == TaskStatus.COMPLETED,
                Task.completed_at >= sixty_days_ago,
                Task.completed_at < thirty_days_ago,
            )
        )
        last_month_count = last_month_result.scalar() or 0

        # Calculate percentage change
        if last_month_count == 0:
            if this_month_count > 0:
                return f"+{this_month_count} from last month (new baseline)"
            else:
                return "No data"

        percentage_change = ((this_month_count - last_month_count) / last_month_count) * 100

        if percentage_change > 0:
            return f"+{percentage_change:.1f}% from last month"
        elif percentage_change < 0:
            return f"{percentage_change:.1f}% from last month"
        else:
            return "No change from last month"

    @staticmethod
    async def calculate_success_rate_trend(db: AsyncSession) -> str:
        """
        Calculate change in success rate.
        Compares last 30 days vs. previous 30 days.
        Returns: "+X.X% from last month" or "-X.X% from last month"
        """
        now = utcnow()
        thirty_days_ago = now - timedelta(days=30)
        sixty_days_ago = now - timedelta(days=60)

        # Success rate for last 30 days
        this_month_completed = await db.execute(
            select(func.count(Task.id)).where(
                Task.status == TaskStatus.COMPLETED, Task.completed_at >= thirty_days_ago
            )
        )
        this_month_completed_count = this_month_completed.scalar() or 0

        this_month_failed = await db.execute(
            select(func.count(Task.id)).where(
                Task.status == TaskStatus.FAILED, Task.completed_at >= thirty_days_ago
            )
        )
        this_month_failed_count = this_month_failed.scalar() or 0

        this_month_total = this_month_completed_count + this_month_failed_count
        this_month_rate = (
            (this_month_completed_count / this_month_total * 100) if this_month_total > 0 else 0
        )

        # Success rate for previous 30 days (30-60 days ago)
        last_month_completed = await db.execute(
            select(func.count(Task.id)).where(
                Task.status == TaskStatus.COMPLETED,
                Task.completed_at >= sixty_days_ago,
                Task.completed_at < thirty_days_ago,
            )
        )
        last_month_completed_count = last_month_completed.scalar() or 0

        last_month_failed = await db.execute(
            select(func.count(Task.id)).where(
                Task.status == TaskStatus.FAILED,
                Task.completed_at >= sixty_days_ago,
                Task.completed_at < thirty_days_ago,
            )
        )
        last_month_failed_count = last_month_failed.scalar() or 0

        last_month_total = last_month_completed_count + last_month_failed_count
        last_month_rate = (
            (last_month_completed_count / last_month_total * 100) if last_month_total > 0 else 0
        )

        # Calculate percentage point change
        if last_month_total == 0:
            if this_month_total > 0:
                return f"{this_month_rate:.1f}% (new baseline)"
            else:
                return "No data"

        rate_change = this_month_rate - last_month_rate

        if rate_change > 0:
            return f"+{rate_change:.1f}% from last month"
        elif rate_change < 0:
            return f"{rate_change:.1f}% from last month"
        else:
            return "No change from last month"
