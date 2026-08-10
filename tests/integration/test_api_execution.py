"""
Integration Tests for ERDIS REST API Layer (Phase 6).
Tests asynchronous task execution, state polling, HITL approval resumption, rejection flow, and secret leakage prevention.
Uses AsyncClient to yield event loop execution to background tasks cleanly.
"""

import asyncio
import pytest
import httpx
from app.main import app


async def _wait_for_task(client: httpx.AsyncClient, task_id: str, target_statuses: set, timeout_seconds: float = 15.0):
    """Helper function yielding loop control while polling task status."""
    start_time = asyncio.get_event_loop().time()
    last_data = {}
    while (asyncio.get_event_loop().time() - start_time) < timeout_seconds:
        res = await client.get(f"/api/v1/tasks/{task_id}")
        assert res.status_code == 200
        last_data = res.json()
        if last_data["status"] in target_statuses:
            return last_data
        await asyncio.sleep(0.1)
    return last_data


@pytest.mark.asyncio
async def test_integration_api_task_lifecycle_sql_path():
    """Tests end-to-end task creation, asynchronous graph execution, and result retrieval for SQL path."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        create_res = await client.post(
            "/api/v1/tasks",
            json={"query": "What is total Midwest customer refund payout amount?"},
        )
        assert create_res.status_code == 201
        data = create_res.json()
        task_id = data["task_id"]
        assert task_id.startswith("TASK-")

        # Poll status yielding loop execution
        task_data = await _wait_for_task(client, task_id, {"COMPLETED", "FAILED"}, timeout_seconds=15.0)

        assert task_data["status"] == "COMPLETED"
        assert task_data["executive_conclusion"] is not None
        assert len(task_data["citations"]) > 0
        assert "orchestrator_node" in task_data["node_trajectory"]


@pytest.mark.asyncio
async def test_integration_api_hitl_approval_flow():
    """Tests high-risk task creation, HITL WAITING_FOR_APPROVAL interrupt, approval submission, and task completion."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        create_res = await client.post(
            "/api/v1/tasks",
            json={"query": "Midwest 100k financial refund impact carrier SLA contract penalty clause"},
        )
        assert create_res.status_code == 201
        task_id = create_res.json()["task_id"]

        # Poll status until WAITING_FOR_APPROVAL
        task_data = await _wait_for_task(client, task_id, {"WAITING_FOR_APPROVAL", "FAILED"}, timeout_seconds=15.0)
        assert task_data["status"] == "WAITING_FOR_APPROVAL"
        assert task_data["financial_impact_usd"] >= 100000.0

        # Submit APPROVAL decision
        app_res = await client.post(
            f"/api/v1/tasks/{task_id}/approval",
            json={"decision": "APPROVED", "feedback": "Approved by CFO"},
        )
        assert app_res.status_code == 200
        app_data = app_res.json()
        assert app_data["status"] == "COMPLETED"
        assert app_data["approval_status"] == "APPROVED"
        assert app_data["executive_conclusion"] is not None


@pytest.mark.asyncio
async def test_integration_api_hitl_rejection_flow():
    """Tests high-risk task creation, HITL WAITING_FOR_APPROVAL interrupt, rejection submission, and state termination."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        create_res = await client.post(
            "/api/v1/tasks",
            json={"query": "Midwest 100k financial refund impact carrier SLA contract penalty clause"},
        )
        assert create_res.status_code == 201
        task_id = create_res.json()["task_id"]

        # Poll status until WAITING_FOR_APPROVAL
        task_data = await _wait_for_task(client, task_id, {"WAITING_FOR_APPROVAL", "FAILED"}, timeout_seconds=15.0)
        assert task_data["status"] == "WAITING_FOR_APPROVAL"

        # Submit REJECTED decision
        rej_res = await client.post(
            f"/api/v1/tasks/{task_id}/approval",
            json={"decision": "REJECTED", "feedback": "Risk too high"},
        )
        assert rej_res.status_code == 200
        rej_data = rej_res.json()
        assert rej_data["status"] == "REJECTED"
        assert rej_data["approval_status"] == "REJECTED"


@pytest.mark.asyncio
async def test_integration_api_secret_leakage_prevention():
    """Verifies that API task responses do not expose internal secrets, API keys, or raw system prompts."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        create_res = await client.post(
            "/api/v1/tasks",
            json={"query": "Show supplier contract terms for Alpha Corp"},
        )
        assert create_res.status_code == 201
        task_id = create_res.json()["task_id"]

        task_data = await _wait_for_task(client, task_id, {"COMPLETED", "FAILED"}, timeout_seconds=15.0)

        raw_text = str(task_data)
        assert "sk-" not in raw_text
        assert "OPENAI_API_KEY" not in raw_text
        assert "postgres://" not in raw_text
