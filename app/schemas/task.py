"""
Pydantic Schemas for Task Lifecycle and API Requests/Responses in ERDIS.
Validates input requests, approval decisions, and structured executive outputs.
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import Field, field_validator
from app.schemas.base import BaseSchema, TimestampedSchema


class TaskCreateRequest(BaseSchema):
    """Payload for POST /api/v1/tasks task creation."""
    query: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        description="The business query or root-cause analytical question.",
        json_schema_extra={"example": "Why did Midwest Q3 margin erosion occur, and what carrier SLA penalties apply?"},
    )
    require_hitl: bool = Field(
        default=True,
        description="Whether high-risk tasks (> $100k or HIGH risk) require HITL approval.",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional metadata or operational context.",
    )

    @field_validator("query")
    @classmethod
    def validate_query_content(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Query cannot be empty or whitespace only.")
        return s


class TaskApprovalRequest(BaseSchema):
    """Payload for POST /api/v1/tasks/{task_id}/approval HITL decision."""
    decision: Literal["APPROVED", "REJECTED"] = Field(
        ...,
        description="Human operator decision ('APPROVED' or 'REJECTED').",
        json_schema_extra={"example": "APPROVED"},
    )
    feedback: Optional[str] = Field(
        default=None,
        description="Optional operator feedback or justification notes.",
        json_schema_extra={"example": "Approved. Enforce contract section 4.2 rate penalty."},
    )


class TaskResponse(BaseSchema):
    """Structured executive task response schema returned by GET /api/v1/tasks/{task_id}."""
    task_id: str = Field(..., description="Unique task identifier.")
    status: Literal["PENDING", "RUNNING", "WAITING_FOR_APPROVAL", "COMPLETED", "FAILED", "REJECTED"] = Field(
        ..., description="Current lifecycle execution status."
    )
    original_question: str = Field(..., description="The original submitted question.")
    route: Optional[str] = Field(None, description="Query execution route (sql_only, document_only, both).")

    executive_conclusion: Optional[str] = Field(None, description="High-level executive summary.")
    key_findings: List[str] = Field(default_factory=list, description="Bulletized key findings.")
    root_cause_analysis: Optional[str] = Field(None, description="Detailed root-cause analysis.")
    business_impact_usd: float = Field(default=0.0, description="Calculated financial impact in USD.")
    recommended_actions: List[str] = Field(default_factory=list, description="Actionable business recommendations.")
    model_inferences_and_assumptions: List[str] = Field(
        default_factory=list, description="Explicitly segregated ungrounded model inferences and assumptions."
    )
    citations: List[str] = Field(default_factory=list, description="Preserved SQL and Document references.")

    financial_impact_usd: float = Field(default=0.0, description="Evaluated financial impact.")
    approval_status: Optional[str] = Field(None, description="HITL approval status (APPROVED, REJECTED, NOT_REQUIRED).")
    execution_time_ms: Optional[float] = Field(None, description="Total execution time in milliseconds.")
    node_trajectory: List[str] = Field(default_factory=list, description="LangGraph node execution trajectory.")
    tool_call_count: int = Field(default=0, description="Number of MCP tool calls executed.")
    token_usage: Dict[str, int] = Field(default_factory=dict, description="Token consumption metrics.")
    errors: List[str] = Field(default_factory=list, description="Execution errors or circuit breaker warnings.")

    sql_evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Structured SQL execution evidence.")
    document_evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Retrieved document RAG excerpts.")
    claims: List[Dict[str, Any]] = Field(default_factory=list, description="Claims and verification statuses.")
    critique_findings: List[Dict[str, Any]] = Field(default_factory=list, description="Adversarial critic findings.")

    created_at: str = Field(..., description="Task creation ISO timestamp.")
    updated_at: str = Field(..., description="Task last update ISO timestamp.")



class HealthResponse(BaseSchema):
    """Liveness probe response schema."""
    status: str = Field(default="healthy")
    app_name: str
    environment: str


class ReadinessResponse(BaseSchema):
    """Readiness probe response schema."""
    status: str = Field(default="ready")
    database: str = Field(default="connected")
    vector_store: str = Field(default="ready")
    mcp_sql_server: str = Field(default="ready")
    mcp_document_server: str = Field(default="ready")


# Backward-compatibility aliases
TaskCreate = TaskCreateRequest
TaskApprovalDecision = TaskApprovalRequest
