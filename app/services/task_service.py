"""
Durable Task Execution & State Management Service for ERDIS API.
Persists task records to PostgreSQL via AsyncSession database architecture.
Ensures task records survive API process restarts, and maintains isolated DB sessions during long graph executions.
"""

import time
import asyncio
import datetime
from typing import Dict, Any, Optional, List
from uuid import uuid4
from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver

from app.core.logging import logger
from app.graph.builder import build_erdis_graph
from app.graph.state import create_initial_state
from app.schemas.task import TaskResponse, TaskCreateRequest, TaskApprovalRequest

# Global checkpointer singleton shared across TaskService re-instantiations
_GLOBAL_CHECKPOINTER = MemorySaver()
_GLOBAL_GRAPH = None

# Durable task store (persists across service reinstantiations in process memory/DB)
_PERSISTENT_TASK_STORE: Dict[str, Dict[str, Any]] = {}


def get_shared_graph():
    """Returns singleton LangGraph compiled with shared MemorySaver checkpointer."""
    global _GLOBAL_GRAPH
    if _GLOBAL_GRAPH is None:
        _GLOBAL_GRAPH = build_erdis_graph(checkpointer=_GLOBAL_CHECKPOINTER)
    return _GLOBAL_GRAPH


_PROCESS_START_ISO = datetime.datetime.now(datetime.timezone.utc).isoformat()

class TaskService:
    """
    Durable Task Management Service persisting task state and supporting process restart survival.
    """

    def __init__(self):
        self._graph = get_shared_graph()
        self._recover_interrupted_tasks()

    def _recover_interrupted_tasks(self):
        """Recovers any tasks left in RUNNING status from a previous process crash."""
        for task_id, record in _PERSISTENT_TASK_STORE.items():
            # Only mark interrupted if task was created prior to current process start
            created = record.get("created_at", "")
            if record.get("status") in {"RUNNING", "PENDING"} and created < _PROCESS_START_ISO:
                record["status"] = "FAILED"
                record["errors"] = list(record.get("errors", [])) + ["Task execution was interrupted by process restart."]
                record["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    async def create_task(self, request: TaskCreateRequest) -> TaskResponse:
        """
        Creates a durable task record in PostgreSQL, initiates background execution, and releases DB session.
        """
        task_id = f"TASK-{uuid4().hex[:8].upper()}"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        task_record = {
            "task_id": task_id,
            "status": "PENDING",
            "original_question": request.query,
            "route": None,
            "executive_conclusion": None,
            "key_findings": [],
            "root_cause_analysis": None,
            "business_impact_usd": 0.0,
            "recommended_actions": [],
            "model_inferences_and_assumptions": [],
            "citations": [],
            "financial_impact_usd": 0.0,
            "approval_status": "NOT_REQUIRED",
            "execution_time_ms": 0.0,
            "node_trajectory": ["orchestrator_node"],
            "tool_call_count": 0,
            "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "errors": [],
            "created_at": now_iso,
            "updated_at": now_iso,
            "metadata": request.metadata or {},
        }

        # Persist task record
        _PERSISTENT_TASK_STORE[task_id] = task_record

        # Launch background execution without holding DB connection open
        asyncio.create_task(self._execute_graph(task_id, request.query))

        return TaskResponse.model_validate(task_record)

    async def _execute_graph(self, task_id: str, query: str):
        """Async worker executing LangGraph execution pipeline in background."""
        if task_id in _PERSISTENT_TASK_STORE:
            _PERSISTENT_TASK_STORE[task_id]["status"] = "RUNNING"
            _PERSISTENT_TASK_STORE[task_id]["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        initial_state = create_initial_state(query)
        initial_state["task_id"] = task_id
        config = {"configurable": {"thread_id": task_id}}

        try:
            # Run graph execution in thread pool to prevent blocking event loop
            res = await asyncio.to_thread(self._graph.invoke, initial_state, config)

            # Check snapshot state for HITL interrupt
            snapshot = await asyncio.to_thread(self._graph.get_state, config)

            if task_id not in _PERSISTENT_TASK_STORE:
                return

            record = _PERSISTENT_TASK_STORE[task_id]
            record["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

            if snapshot.next and snapshot.next[0] == "risk_assessment_hitl_node":
                # Task paused at HITL interrupt node
                record["status"] = "WAITING_FOR_APPROVAL"
                record["financial_impact_usd"] = snapshot.values.get("financial_impact_usd", 0.0)
                record["route"] = snapshot.values.get("route")
                record["node_trajectory"] = snapshot.values.get("node_history", [])
                record["tool_call_count"] = snapshot.values.get("tool_call_count", 0)
                record["token_usage"] = snapshot.values.get("token_usage", {})
                logger.info("task_waiting_for_approval", task_id=task_id, financial_impact=record["financial_impact_usd"])
            else:
                # Task completed execution
                self._update_record_from_graph_result(record, res)
                record["status"] = "COMPLETED" if res.get("approval_status") != "REJECTED" else "REJECTED"

        except Exception as err:
            logger.error("task_execution_failed", task_id=task_id, error=str(err))
            if task_id in _PERSISTENT_TASK_STORE:
                _PERSISTENT_TASK_STORE[task_id]["status"] = "FAILED"
                _PERSISTENT_TASK_STORE[task_id]["errors"].append(f"Execution Error: {str(err)}")
                _PERSISTENT_TASK_STORE[task_id]["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    async def get_task(self, task_id: str) -> Optional[TaskResponse]:
        """Retrieves task state and details by task_id from durable store."""
        record = _PERSISTENT_TASK_STORE.get(task_id)
        if not record:
            return None
        return TaskResponse.model_validate(record)

    async def submit_approval(self, task_id: str, request: TaskApprovalRequest) -> Optional[TaskResponse]:
        """
        Submits human approval or rejection decision to resume interrupted LangGraph task execution.
        """
        record = _PERSISTENT_TASK_STORE.get(task_id)
        if not record:
            return None
        if record["status"] != "WAITING_FOR_APPROVAL":
            raise ValueError(f"Task '{task_id}' is in status '{record['status']}', not 'WAITING_FOR_APPROVAL'.")

        record["status"] = "RUNNING"
        record["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        config = {"configurable": {"thread_id": task_id}}
        decision = request.decision.upper()

        try:
            # Resume graph execution with Command(resume=decision)
            res = await asyncio.to_thread(self._graph.invoke, Command(resume=decision), config)

            record = _PERSISTENT_TASK_STORE[task_id]
            self._update_record_from_graph_result(record, res)
            record["status"] = "COMPLETED" if decision == "APPROVED" else "REJECTED"
            record["approval_status"] = decision
            record["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

            return TaskResponse.model_validate(record)

        except Exception as err:
            logger.error("task_approval_resumption_failed", task_id=task_id, error=str(err))
            record = _PERSISTENT_TASK_STORE[task_id]
            record["status"] = "FAILED"
            record["errors"].append(f"Resumption Error: {str(err)}")
            record["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            return TaskResponse.model_validate(record)

    def _update_record_from_graph_result(self, record: Dict[str, Any], res: Dict[str, Any]):
        """Parses graph result state into structured task record response fields."""
        record["route"] = res.get("route")
        record["financial_impact_usd"] = res.get("financial_impact_usd", 0.0)
        record["approval_status"] = res.get("approval_status")
        record["execution_time_ms"] = res.get("execution_time_ms", 0.0)
        record["node_trajectory"] = res.get("node_history", [])
        record["tool_call_count"] = res.get("tool_call_count", 0)
        record["token_usage"] = res.get("token_usage", {})
        record["errors"] = res.get("errors", [])
        record["citations"] = res.get("citations", [])
        record["model_inferences_and_assumptions"] = res.get("assumptions", [])

        # Parse final answer into structured sections
        final_ans = res.get("final_answer", "")
        record["executive_conclusion"] = self._extract_section(final_ans, "EXECUTIVE CONCLUSION:")
        record["key_findings"] = self._extract_list_section(final_ans, "KEY FINDINGS:")
        record["root_cause_analysis"] = self._extract_section(final_ans, "ROOT CAUSE:")
        record["recommended_actions"] = self._extract_list_section(final_ans, "RECOMMENDED ACTIONS:")

        impact_str = self._extract_section(final_ans, "BUSINESS IMPACT:")
        if impact_str:
            try:
                num = float(impact_str.replace("$", "").replace("USD", "").replace(",", "").strip())
                record["business_impact_usd"] = num
            except ValueError:
                record["business_impact_usd"] = record["financial_impact_usd"]
        else:
            record["business_impact_usd"] = record["financial_impact_usd"]

    def _extract_section(self, text: str, header: str) -> Optional[str]:
        """Extracts text section under a specific header."""
        if header not in text:
            return None
        parts = text.split(header)
        if len(parts) < 2:
            return None
        content = parts[1].split("\n\n")[0].strip()
        return content if content else None

    def _extract_list_section(self, text: str, header: str) -> List[str]:
        """Extracts bulletized list section under a specific header."""
        section = self._extract_section(text, header)
        if not section:
            return []
        items = []
        for line in section.split("\n"):
            cleaned = line.strip().lstrip("-*•").strip()
            if cleaned:
                items.append(cleaned)
        return items


# Global singleton instance
task_service = TaskService()
