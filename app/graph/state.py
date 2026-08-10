"""
LangGraph State Schema Definition for ERDIS Workflow.
Defines strongly typed GraphState containing task tracking, evidence, claims, critique, and circuit breaker metrics.
"""

from typing import List, Dict, Any, Optional, Literal, TypedDict


class TokenUsage(TypedDict):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ToolExecutionRecord(TypedDict):
    tool_name: str
    input_args: Dict[str, Any]
    output_summary: str
    status: Literal["SUCCESS", "ERROR"]
    execution_time_ms: float


class GraphState(TypedDict, total=False):
    task_id: str
    original_question: str
    normalized_question: str
    plan: Dict[str, Any]
    sql_evidence: List[Dict[str, Any]]
    document_evidence: List[Dict[str, Any]]
    claims: List[Dict[str, Any]]
    critique_findings: List[Dict[str, Any]]
    final_answer: Optional[str]
    assumptions: List[str]
    citations: List[str]
    tool_execution_history: List[ToolExecutionRecord]
    node_history: List[str]
    iteration_count: int
    tool_call_count: int
    token_usage: TokenUsage
    start_time_timestamp: float
    execution_time_ms: float
    financial_impact_usd: float
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    approval_status: Literal["PENDING", "APPROVED", "REJECTED", "NOT_REQUIRED"]
    errors: List[str]
    route: Literal["sql_only", "document_only", "both", "clarification"]
    retry_needed: bool


def create_initial_state(
    original_question: str,
    task_id: Optional[str] = None,
) -> GraphState:
    """
    Initializes a clean, strongly-typed GraphState object.
    """
    import uuid
    import time

    tid = task_id or f"TASK-{uuid.uuid4().hex[:8].upper()}"
    return {
        "task_id": tid,
        "original_question": original_question,
        "normalized_question": original_question.strip(),
        "plan": {},
        "sql_evidence": [],
        "document_evidence": [],
        "claims": [],
        "critique_findings": [],
        "final_answer": None,
        "assumptions": [],
        "citations": [],
        "tool_execution_history": [],
        "node_history": [],
        "iteration_count": 0,
        "tool_call_count": 0,
        "token_usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
        "start_time_timestamp": time.time(),
        "execution_time_ms": 0.0,
        "financial_impact_usd": 0.0,
        "risk_level": "LOW",
        "approval_status": "NOT_REQUIRED",
        "errors": [],
        "route": "both",
        "retry_needed": False,
    }
