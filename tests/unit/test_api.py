"""
Unit Tests for ERDIS REST API Layer (Phase 6).
Tests health probes, input validation schemas, task creation, malformed ID handling, and error responses.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.task import TaskCreateRequest, TaskApprovalRequest

client = TestClient(app)


def test_api_health_liveness():
    """Verifies GET /api/v1/health returns healthy liveness status."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "app_name" in data


def test_api_health_readiness():
    """Verifies GET /api/v1/readiness returns ready status."""
    res = client.get("/api/v1/readiness")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"


def test_task_create_validation():
    """Verifies TaskCreateRequest input validation."""
    # Too short query (< 5 chars)
    res = client.post("/api/v1/tasks", json={"query": "hi"})
    assert res.status_code == 422

    # Empty query
    res = client.post("/api/v1/tasks", json={"query": "   "})
    assert res.status_code == 422


def test_malformed_task_id_rejection():
    """Verifies GET /api/v1/tasks/{task_id} rejects malformed IDs."""
    res = client.get("/api/v1/tasks/INVALID-ID-FORMAT")
    assert res.status_code == 400
    assert "Malformed task_id format" in res.json()["detail"]


def test_task_not_found():
    """Verifies GET /api/v1/tasks/{task_id} returns 404 for nonexistent tasks."""
    res = client.get("/api/v1/tasks/TASK-00000000")
    assert res.status_code == 404
    assert "was not found" in res.json()["detail"]


def test_approval_invalid_status_rejection():
    """Verifies approval endpoint rejects tasks not in WAITING_FOR_APPROVAL status."""
    # Create task first
    create_res = client.post("/api/v1/tasks", json={"query": "What is Midwest refund amount?"})
    assert create_res.status_code == 201
    task_id = create_res.json()["task_id"]

    # Attempt immediate approval before entering WAITING_FOR_APPROVAL
    app_res = client.post(f"/api/v1/tasks/{task_id}/approval", json={"decision": "APPROVED"})
    assert app_res.status_code in {400, 404}
