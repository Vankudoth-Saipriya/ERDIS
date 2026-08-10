"""
Evidence and Claim Pydantic Schemas
"""

from typing import Dict, Any, List, Literal, Optional
from pydantic import Field
from app.schemas.base import BaseSchema, TimestampedSchema


class EvidenceCreate(BaseSchema):
    evidence_id: str = Field(..., json_schema_extra={"example": "EVID-SQL-004"})
    source_type: Literal["SQL", "DOCUMENT"] = Field(...)
    source_ref: str = Field(..., json_schema_extra={"example": "SELECT SUM(amount)... or DOC-CONTRACT-01.pdf#p4"})
    originating_tool: str = Field(..., json_schema_extra={"example": "mcp-server-sql"})
    originating_agent: str = Field(..., json_schema_extra={"example": "SQL Analyst Agent"})
    content: Dict[str, Any] = Field(default_factory=dict)
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)


class EvidenceResponse(TimestampedSchema, EvidenceCreate):
    task_id: str


class Claim(BaseSchema):
    claim_id: str = Field(..., json_schema_extra={"example": "CLM-012"})
    text: str = Field(..., json_schema_extra={"example": "Carrier X delivery delays cost $42,500 in refunds."})
    evidence_ids: List[str] = Field(default_factory=list)
    status: Literal["VERIFIED", "UNVERIFIED_INFERENCE", "REJECTED"] = Field(default="VERIFIED")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
