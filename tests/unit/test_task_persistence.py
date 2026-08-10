"""
Unit Tests for ERDIS Task Persistence & Restart Survival (Phase 6.1).
Tests task record persistence, TaskService re-instantiation, simulated service restart recovery, and HITL resumption.
"""

import pytest
import asyncio
import datetime
from app.schemas.task import TaskCreateRequest, TaskApprovalRequest
from app.services.task_service import TaskService, _PERSISTENT_TASK_STORE, _PROCESS_START_ISO


async def _wait_task_status(service: TaskService, task_id: str, target_statuses: set, max_seconds: float = 20.0):
    start = asyncio.get_event_loop().time()
    last = None
    while (asyncio.get_event_loop().time() - start) < max_seconds:
        last = await service.get_task(task_id)
        if last and last.status in target_statuses:
            return last
        await asyncio.sleep(0.2)
    return last


@pytest.mark.asyncio
async def test_task_creation_persists():
    """Verifies task creation persists record in TaskService store."""
    service = TaskService()
    req = TaskCreateRequest(query="Why did Midwest margin decline in Q3?")
    resp = await service.create_task(req)

    assert resp.task_id.startswith("TASK-")
    assert resp.status in {"PENDING", "RUNNING"}

    # Retrieve created task
    get_resp = await service.get_task(resp.task_id)
    assert get_resp is not None
    assert get_resp.task_id == resp.task_id


@pytest.mark.asyncio
async def test_task_survives_task_service_reinstantiation():
    """
    Verifies that a task created by TaskService instance A is retrievable by TaskService instance B.
    Simulates service reinstantiation and process survival.
    """
    service_a = TaskService()
    req = TaskCreateRequest(query="What is the total Midwest refund payout amount?")
    resp_a = await service_a.create_task(req)
    task_id = resp_a.task_id

    # Wait for execution completion
    resp_done = await _wait_task_status(service_a, task_id, {"COMPLETED", "FAILED"}, max_seconds=20.0)
    assert resp_done.status == "COMPLETED"

    # Instantiate new TaskService instance B
    service_b = TaskService()
    resp_b = await service_b.get_task(task_id)

    assert resp_b is not None
    assert resp_b.task_id == task_id
    assert resp_b.status == "COMPLETED"
    assert resp_b.executive_conclusion is not None


@pytest.mark.asyncio
async def test_hitl_waiting_for_approval_persistence_and_reinstantiation_resume():
    """
    Verifies high-risk task pauses at WAITING_FOR_APPROVAL, survives TaskService reinstantiation, and resumes.
    """
    service_a = TaskService()
    req = TaskCreateRequest(query="Midwest 100k financial refund impact carrier SLA contract penalty clause")
    resp_a = await service_a.create_task(req)
    task_id = resp_a.task_id

    # Poll status until WAITING_FOR_APPROVAL
    check_waiting = await _wait_task_status(service_a, task_id, {"WAITING_FOR_APPROVAL", "FAILED"}, max_seconds=20.0)
    assert check_waiting.status == "WAITING_FOR_APPROVAL"

    # Re-instantiate TaskService instance B (Simulate service restart/new worker)
    service_b = TaskService()
    check_b = await service_b.get_task(task_id)
    assert check_b is not None
    assert check_b.status == "WAITING_FOR_APPROVAL"

    # Submit APPROVAL via instance B
    app_resp = await service_b.submit_approval(task_id, TaskApprovalRequest(decision="APPROVED", feedback="Approved CFO"))
    assert app_resp is not None
    assert app_resp.status == "COMPLETED"
    assert app_resp.approval_status == "APPROVED"


@pytest.mark.asyncio
async def test_simulated_process_crash_recovery():
    """
    Verifies that a task left in RUNNING status prior to a process crash is marked FAILED upon process restart recovery.
    """
    old_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=5)).isoformat()
    mock_crash_id = "TASK-CRASHED01"
    _PERSISTENT_TASK_STORE[mock_crash_id] = {
        "task_id": mock_crash_id,
        "status": "RUNNING",
        "original_question": "Crashed query",
        "created_at": old_time,
        "updated_at": old_time,
        "errors": [],
    }

    # Re-instantiate TaskService (triggers _recover_interrupted_tasks)
    service_recovery = TaskService()
    crashed_task = await service_recovery.get_task(mock_crash_id)

    assert crashed_task is not None
    assert crashed_task.status == "FAILED"
    assert any("interrupted by process restart" in err for err in crashed_task.errors)


@pytest.mark.asyncio
async def test_no_secrets_persisted():
    """Verifies that secrets, API keys, or raw passwords are not persisted in task records."""
    service = TaskService()
    req = TaskCreateRequest(query="Show supplier contract terms for Alpha Corp")
    resp = await service.create_task(req)

    check = await _wait_task_status(service, resp.task_id, {"COMPLETED", "FAILED"}, max_seconds=20.0)

    raw_str = str(check.model_dump())
    assert "sk-" not in raw_str
    assert "OPENAI_API_KEY" not in raw_str
    assert "postgres://" not in raw_str
