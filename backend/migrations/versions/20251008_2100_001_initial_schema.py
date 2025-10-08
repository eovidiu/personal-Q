"""initial schema

Revision ID: 001
Revises:
Create Date: 2025-10-08 21:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create agents table
    op.create_table(
        'agents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('agent_type', sa.Enum('CONVERSATIONAL', 'ANALYTICAL', 'CREATIVE', 'AUTOMATION', name='agenttype'), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'TRAINING', 'ERROR', 'PAUSED', name='agentstatus'), nullable=False),
        sa.Column('model', sa.String(), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('max_tokens', sa.Integer(), nullable=True),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('tasks_completed', sa.Integer(), nullable=True),
        sa.Column('tasks_failed', sa.Integer(), nullable=True),
        sa.Column('last_active', sa.DateTime(), nullable=True),
        sa.Column('tools_config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_agents_id'), 'agents', ['id'], unique=False)
    op.create_index(op.f('ix_agents_name'), 'agents', ['name'], unique=True)

    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', name='taskstatus'), nullable=False),
        sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'URGENT', name='taskpriority'), nullable=False),
        sa.Column('input_data', sa.JSON(), nullable=True),
        sa.Column('output_data', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('celery_task_id', sa.String(), nullable=True),
        sa.Column('execution_time_seconds', sa.Integer(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_agent_id'), 'tasks', ['agent_id'], unique=False)
    op.create_index(op.f('ix_tasks_celery_task_id'), 'tasks', ['celery_task_id'], unique=False)
    op.create_index(op.f('ix_tasks_id'), 'tasks', ['id'], unique=False)

    # Create activities table
    op.create_table(
        'activities',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=True),
        sa.Column('task_id', sa.String(), nullable=True),
        sa.Column('activity_type', sa.Enum('AGENT_CREATED', 'AGENT_UPDATED', 'AGENT_DELETED', 'AGENT_STARTED', 'AGENT_STOPPED', 'TASK_CREATED', 'TASK_STARTED', 'TASK_COMPLETED', 'TASK_FAILED', 'TASK_CANCELLED', 'INTEGRATION_CONNECTED', 'INTEGRATION_ERROR', name='activitytype'), nullable=False),
        sa.Column('status', sa.Enum('SUCCESS', 'ERROR', 'INFO', 'WARNING', name='activitystatus'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activities_activity_type'), 'activities', ['activity_type'], unique=False)
    op.create_index(op.f('ix_activities_agent_id'), 'activities', ['agent_id'], unique=False)
    op.create_index(op.f('ix_activities_created_at'), 'activities', ['created_at'], unique=False)
    op.create_index(op.f('ix_activities_id'), 'activities', ['id'], unique=False)
    op.create_index(op.f('ix_activities_task_id'), 'activities', ['task_id'], unique=False)

    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('service_name', sa.String(), nullable=False),
        sa.Column('api_key', sa.Text(), nullable=True),
        sa.Column('access_token', sa.Text(), nullable=True),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('client_id', sa.String(), nullable=True),
        sa.Column('client_secret', sa.Text(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('config', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_validated', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('service_name')
    )
    op.create_index(op.f('ix_api_keys_id'), 'api_keys', ['id'], unique=False)
    op.create_index(op.f('ix_api_keys_service_name'), 'api_keys', ['service_name'], unique=True)

    # Create schedules table
    op.create_table(
        'schedules',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cron_expression', sa.String(), nullable=False),
        sa.Column('task_config', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_run', sa.DateTime(), nullable=True),
        sa.Column('next_run', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schedules_agent_id'), 'schedules', ['agent_id'], unique=False)
    op.create_index(op.f('ix_schedules_id'), 'schedules', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_schedules_id'), table_name='schedules')
    op.drop_index(op.f('ix_schedules_agent_id'), table_name='schedules')
    op.drop_table('schedules')

    op.drop_index(op.f('ix_api_keys_service_name'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_id'), table_name='api_keys')
    op.drop_table('api_keys')

    op.drop_index(op.f('ix_activities_task_id'), table_name='activities')
    op.drop_index(op.f('ix_activities_id'), table_name='activities')
    op.drop_index(op.f('ix_activities_created_at'), table_name='activities')
    op.drop_index(op.f('ix_activities_agent_id'), table_name='activities')
    op.drop_index(op.f('ix_activities_activity_type'), table_name='activities')
    op.drop_table('activities')

    op.drop_index(op.f('ix_tasks_id'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_celery_task_id'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_agent_id'), table_name='tasks')
    op.drop_table('tasks')

    op.drop_index(op.f('ix_agents_name'), table_name='agents')
    op.drop_index(op.f('ix_agents_id'), table_name='agents')
    op.drop_table('agents')
