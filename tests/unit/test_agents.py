"""
Unit Tests for ERDIS Multi-Agent System (Phase 5).
Tests PlannerAgent, SQLAnalystAgent, DocumentRAGAgent, AdversarialCriticAgent, and ExecutiveSynthesizerAgent.
"""

import pytest
from app.agents import (
    PlannerAgent,
    SQLAnalystAgent,
    DocumentRAGAgent,
    AdversarialCriticAgent,
    ExecutiveSynthesizerAgent,
)
from app.schemas.agents import (
    PlannerOutput,
    SQLAnalysisOutput,
    DocumentAnalysisOutput,
    CritiqueOutput,
    ExecutiveSynthesisOutput,
)


def test_planner_agent():
    """Verifies PlannerAgent generates valid PlannerOutput schema."""
    planner = PlannerAgent()
    out = planner.plan("Why did Midwest revenue drop in Q3?")

    assert isinstance(out, PlannerOutput)
    assert out.goal is not None
    assert len(out.target_sources) > 0


@pytest.mark.asyncio
async def test_sql_analyst_agent():
    """Verifies SQLAnalystAgent executes SELECT query via SQL MCP Server."""
    agent = SQLAnalystAgent()
    out = await agent.analyze("What is total Midwest refund amount?")

    assert isinstance(out, SQLAnalysisOutput)
    assert out.executed_sql.startswith("SELECT")
    assert out.summary is not None
    assert out.insufficient_data is False


@pytest.mark.asyncio
async def test_doc_rag_agent():
    """Verifies DocumentRAGAgent retrieves chunks via Document MCP Server with untrusted framing."""
    agent = DocumentRAGAgent()
    out = await agent.search("carrier SLA contract penalty")

    assert isinstance(out, DocumentAnalysisOutput)
    assert out.search_query == "carrier SLA contract penalty"
    assert len(out.citations) > 0
    assert out.insufficient_evidence is False


def test_adversarial_critic_agent():
    """Verifies AdversarialCriticAgent audits evidence and enforces max iteration limit."""
    critic = AdversarialCriticAgent()
    sql_ev = [{"evidence_id": "EVID-SQL-1", "source_ref": "SELECT..."}]
    doc_ev = [{"evidence_id": "EVID-DOC-1", "source_ref": "contract.md#p1"}]

    out = critic.audit(
        question="Midwest margin loss",
        sql_evidence=sql_ev,
        doc_evidence=doc_ev,
        iteration_count=1,
    )
    assert isinstance(out, CritiqueOutput)
    assert out.confidence_score > 0.0

    # Iteration 2 forces retry_needed = False
    out_iter2 = critic.audit(
        question="Midwest margin loss",
        sql_evidence=sql_ev,
        doc_evidence=doc_ev,
        iteration_count=2,
    )
    assert out_iter2.retry_needed is False


def test_executive_synthesizer_agent():
    """Verifies ExecutiveSynthesizerAgent produces evidence-grounded final report."""
    synthesizer = ExecutiveSynthesizerAgent()
    sql_ev = [{"evidence_id": "EVID-SQL-1", "source_ref": "SELECT SUM(refund) FROM orders"}]
    doc_ev = [{"evidence_id": "EVID-DOC-1", "source_ref": "contract.md#p1"}]
    critique = {"supported_claims": ["Refunds increased"]}

    out = synthesizer.synthesize(
        question="Why did Midwest margin erosion occur?",
        sql_evidence=sql_ev,
        doc_evidence=doc_ev,
        critique=critique,
        approval_status="APPROVED",
        financial_impact_usd=142500.0,
    )

    assert isinstance(out, ExecutiveSynthesisOutput)
    assert "Root-cause" in out.executive_conclusion or "margin" in out.executive_conclusion.lower()
    assert len(out.key_findings) > 0
    assert out.business_impact_usd == 142500.0
    assert len(out.citations) > 0
