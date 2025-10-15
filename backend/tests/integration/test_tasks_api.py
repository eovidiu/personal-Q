"""
Integration tests for Tasks API.
"""

import pytest
from httpx import AsyncClient
import sys
import os




@pytest.mark.asyncio
async def test_create_task_endpoint(test_app):
    """Test POST /tasks endpoint."""
    # First create an agent
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        agent_response = await client.post(
            "/api/v1/agents",
            json={
                "name": "Task Test Agent",
                "description": "Agent for task testing",
                "agent_type": "conversational",
                "model": "claude-3-5-sonnet-20241022",
                "system_prompt": "Test agent."
            }
        )
        agent_id = agent_response.json()["id"]

        # Create task
        response = await client.post(
            "/api/v1/tasks",
            json={
                "agent_id": agent_id,
                "title": "Test Task",
                "description": "Task description",
                "priority": "high",
                "input_data": {"key": "value"}
            }
        )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["agent_id"] == agent_id
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_list_tasks_endpoint(test_app):
    """Test GET /tasks endpoint."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        response = await client.get("/api/v1/tasks")

    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_task_endpoint(test_app):
    """Test GET /tasks/{id} endpoint."""
    # Create task first
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        agent_response = await client.post(
            "/api/v1/agents",
            json={
                "name": "Get Task Agent",
                "description": "Test",
                "agent_type": "analytical",
                "model": "claude-3-5-sonnet-20241022",
                "system_prompt": "Test."
            }
        )
        agent_id = agent_response.json()["id"]

        create_response = await client.post(
            "/api/v1/tasks",
            json={
                "agent_id": agent_id,
                "title": "Get Test Task",
                "description": "Test"
            }
        )
        task_id = create_response.json()["id"]

        # Get task
        response = await client.get(f"/api/v1/tasks/{task_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id


@pytest.mark.asyncio
async def test_update_task_endpoint(test_app):
    """Test PATCH /tasks/{id} endpoint."""
    # Create task first
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        agent_response = await client.post(
            "/api/v1/agents",
            json={
                "name": "Update Task Agent",
                "description": "Test",
                "agent_type": "creative",
                "model": "claude-3-5-sonnet-20241022",
                "system_prompt": "Test."
            }
        )
        agent_id = agent_response.json()["id"]

        create_response = await client.post(
            "/api/v1/tasks",
            json={
                "agent_id": agent_id,
                "title": "Update Task",
                "description": "Original"
            }
        )
        task_id = create_response.json()["id"]

        # Update task
        response = await client.patch(
            f"/api/v1/tasks/{task_id}",
            json={"description": "Updated"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated"
