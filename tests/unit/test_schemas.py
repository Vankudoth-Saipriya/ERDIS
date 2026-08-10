"""
Unit Tests for Pydantic Base & Evidence Schemas
"""

import pytest
from pydantic import ValidationError
from app.schemas.task import TaskCreate
from app.schemas.evidence import EvidenceCreate, Claim


def test_task_create_schema_valid():
    task = TaskCreate(query="Why did Midwest margin decline in Q3?")
    assert task.query == "Why did Midwest margin decline in Q3?"
    assert task.require_hitl is True


def test_task_create_schema_invalid_short():
    with pytest.raises(ValidationError):
        TaskCreate(query="Why?")


def test_evidence_create_schema_valid():
    ev = EvidenceCreate(
        evidence_id="EVID-SQL-001",
        source_type="SQL",
        source_ref="SELECT * FROM orders",
        originating_tool="mcp-server-sql",
        originating_agent="SQL Analyst Agent",
        content={"sum": 100},
        confidence_score=0.95
    )
    assert ev.evidence_id == "EVID-SQL-001"
    assert ev.confidence_score == 0.95


def test_claim_schema_valid():
    claim = Claim(
        claim_id="CLM-001",
        text="Margin dropped due to freight surcharge.",
        evidence_ids=["EVID-SQL-001"],
        status="VERIFIED"
    )
    assert claim.claim_id == "CLM-001"
    assert claim.status == "VERIFIED"
