"""
Task Management REST API Endpoints (v1).
Provides endpoints for task creation, status polling, structured result retrieval, and HITL decision submissions.
"""

import re
from fastapi import APIRouter, HTTPException, status, Path
from app.schemas.task import (
    TaskCreateRequest,
    TaskApprovalRequest,
    TaskResponse,
)
from app.services.task_service import task_service

router = APIRouter(prefix="/tasks", tags=["Decision Intelligence Tasks"])

# Regex pattern for validating task IDs
TASK_ID_PATTERN = re.compile(r"^TASK-[A-F0-9]{8}$", re.IGNORECASE)


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Root-Cause Analysis Task",
    description="Submits a business query to create an asynchronous decision intelligence task executing through ERDIS multi-agent LangGraph.",
)
async def create_task(request: TaskCreateRequest) -> TaskResponse:
    """Creates a new decision intelligence task and initiates background execution."""
    return await task_service.create_task(request)


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Task Status & Executive Decision Report",
    description="Retrieves current execution status, node trajectory, metrics, and final executive report for a given task_id.",
)
async def get_task(
    task_id: str = Path(..., description="Unique task identifier (e.g. TASK-A1B2C3D4)")
) -> TaskResponse:
    """Retrieves status and executive response details for a task_id."""
    if not TASK_ID_PATTERN.match(task_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Malformed task_id format '{task_id}'. Task ID must match pattern 'TASK-XXXXXXXX'.",
        )

    task_resp = await task_service.get_task(task_id)
    if not task_resp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID '{task_id}' was not found.",
        )

    return task_resp


@router.post(
    "/{task_id}/approval",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit HITL Approval Decision",
    description="Submits human operator approval ('APPROVED') or rejection ('REJECTED') to resume an interrupted high-risk task.",
)
async def submit_approval(
    request: TaskApprovalRequest,
    task_id: str = Path(..., description="Unique task identifier (e.g. TASK-A1B2C3D4)"),
) -> TaskResponse:
    """Submits human approval decision to resume graph execution."""
    if not TASK_ID_PATTERN.match(task_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Malformed task_id format '{task_id}'. Task ID must match pattern 'TASK-XXXXXXXX'.",
        )

    # Verify task exists
    existing = await task_service.get_task(task_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID '{task_id}' was not found.",
        )

    if existing.status != "WAITING_FOR_APPROVAL":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task '{task_id}' is in status '{existing.status}', not 'WAITING_FOR_APPROVAL'.",
        )

    try:
        updated_resp = await task_service.submit_approval(task_id, request)
        if not updated_resp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID '{task_id}' was not found.",
            )
        return updated_resp
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
