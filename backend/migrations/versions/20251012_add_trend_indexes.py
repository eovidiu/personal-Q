"""add trend calculation indexes

Revision ID: 002
Revises: 001
Create Date: 2025-10-12 12:00:00

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add indexes for trend calculation queries."""
    # Index for agent creation trends (last 7 days queries)
    op.create_index("ix_agents_created_at", "agents", ["created_at"], unique=False)

    # Index for task completion trends (last 30/60 days queries)
    op.create_index("ix_tasks_completed_at", "tasks", ["completed_at"], unique=False)

    # Composite index for task status + completion date (for success rate trends)
    op.create_index(
        "ix_tasks_status_completed_at", "tasks", ["status", "completed_at"], unique=False
    )


def downgrade() -> None:
    """Remove trend calculation indexes."""
    op.drop_index("ix_tasks_status_completed_at", table_name="tasks")
    op.drop_index("ix_tasks_completed_at", table_name="tasks")
    op.drop_index("ix_agents_created_at", table_name="agents")
