"""
Integration tests for task cancellation endpoint.
"""

import pytest
from app.models.task import Task as TaskModel
from app.models.task import TaskStatus
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cancel_running_task(client: AsyncClient, db_session, auth_headers, sample_agent):
    """Test cancelling a running task."""
    # Create a running task
    task = TaskModel(
        id="cancel-test-1",
        agent_id=sample_agent.id,
        title="Running Task to Cancel",
        status=TaskStatus.RUNNING,
        celery_task_id="celery-123",
        input_data={},
    )
    db_session.add(task)
    await db_session.commit()

    # Cancel the task
    response = await client.post(f"/api/v1/tasks/{task.id}/cancel", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task.id
    assert data["status"] == "cancelled"
    assert data["completed_at"] is not None


@pytest.mark.asyncio
async def test_cancel_pending_task(client: AsyncClient, db_session, auth_headers, sample_agent):
    """Test cancelling a pending task."""
    # Create a pending task
    task = TaskModel(
        id="cancel-test-2",
        agent_id=sample_agent.id,
        title="Pending Task to Cancel",
        status=TaskStatus.PENDING,
        input_data={},
    )
    db_session.add(task)
    await db_session.commit()

    # Cancel the task
    response = await client.post(f"/api/v1/tasks/{task.id}/cancel", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cannot_cancel_completed_task(
    client: AsyncClient, db_session, auth_headers, sample_agent
):
    """Test that completed tasks cannot be cancelled."""
    # Create a completed task
    task = TaskModel(
        id="cancel-test-3",
        agent_id=sample_agent.id,
        title="Completed Task",
        status=TaskStatus.COMPLETED,
        input_data={},
    )
    db_session.add(task)
    await db_session.commit()

    # Attempt to cancel
    response = await client.post(f"/api/v1/tasks/{task.id}/cancel", headers=auth_headers)

    assert response.status_code == 400
    assert "Cannot cancel task with status completed" in response.json()["detail"]


@pytest.mark.asyncio
async def test_cannot_cancel_failed_task(
    client: AsyncClient, db_session, auth_headers, sample_agent
):
    """Test that failed tasks cannot be cancelled."""
    # Create a failed task
    task = TaskModel(
        id="cancel-test-4",
        agent_id=sample_agent.id,
        title="Failed Task",
        status=TaskStatus.FAILED,
        error_message="Task failed",
        input_data={},
    )
    db_session.add(task)
    await db_session.commit()

    # Attempt to cancel
    response = await client.post(f"/api/v1/tasks/{task.id}/cancel", headers=auth_headers)

    assert response.status_code == 400
    assert "Cannot cancel task with status failed" in response.json()["detail"]


@pytest.mark.asyncio
async def test_cannot_cancel_already_cancelled_task(
    client: AsyncClient, db_session, auth_headers, sample_agent
):
    """Test that already cancelled tasks cannot be cancelled again."""
    # Create a cancelled task
    task = TaskModel(
        id="cancel-test-5",
        agent_id=sample_agent.id,
        title="Already Cancelled Task",
        status=TaskStatus.CANCELLED,
        input_data={},
    )
    db_session.add(task)
    await db_session.commit()

    # Attempt to cancel again
    response = await client.post(f"/api/v1/tasks/{task.id}/cancel", headers=auth_headers)

    assert response.status_code == 400
    assert "Cannot cancel task with status cancelled" in response.json()["detail"]


@pytest.mark.asyncio
async def test_cancel_nonexistent_task(client: AsyncClient, auth_headers):
    """Test cancelling a task that doesn't exist."""
    response = await client.post("/api/v1/tasks/nonexistent-id/cancel", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


@pytest.mark.asyncio
async def test_cancel_task_revokes_celery_task(
    client: AsyncClient, db_session, auth_headers, sample_agent
):
    """Test that cancelling a task with celery_task_id revokes it."""
    from unittest.mock import MagicMock, patch

    # Create a running task with celery_task_id
    task = TaskModel(
        id="cancel-test-6",
        agent_id=sample_agent.id,
        title="Task with Celery ID",
        status=TaskStatus.RUNNING,
        celery_task_id="celery-456",
        input_data={},
    )
    db_session.add(task)
    await db_session.commit()

    # Mock Celery app control
    with patch("app.workers.celery_app.celery_app") as mock_celery:
        mock_control = MagicMock()
        mock_celery.control = mock_control

        # Cancel the task
        response = await client.post(f"/api/v1/tasks/{task.id}/cancel", headers=auth_headers)

        assert response.status_code == 200
        # Verify Celery revoke was called
        mock_control.revoke.assert_called_once_with("celery-456", terminate=True)


@pytest.mark.asyncio
async def test_cancel_task_broadcasts_websocket_event(
    client: AsyncClient, db_session, auth_headers, sample_agent
):
    """Test that cancelling a task broadcasts a WebSocket event."""
    from unittest.mock import AsyncMock, patch

    # Create a running task
    task = TaskModel(
        id="cancel-test-7",
        agent_id=sample_agent.id,
        title="Task for WebSocket Test",
        status=TaskStatus.RUNNING,
        input_data={},
    )
    db_session.add(task)
    await db_session.commit()

    # Mock broadcast_event
    with patch("app.routers.websocket.broadcast_event", new_callable=AsyncMock) as mock_broadcast:
        # Cancel the task
        response = await client.post(f"/api/v1/tasks/{task.id}/cancel", headers=auth_headers)

        assert response.status_code == 200

        # Verify broadcast was called
        mock_broadcast.assert_called_once()
        call_args = mock_broadcast.call_args
        assert call_args[0][0] == "task_cancelled"
        event_data = call_args[0][1]
        assert event_data["task_id"] == task.id
        assert event_data["agent_id"] == sample_agent.id
        assert event_data["title"] == "Task for WebSocket Test"
        assert event_data["status"] == "cancelled"
        assert "completed_at" in event_data
