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


def test_strict_evidence_and_citation_grounding():
    """
    Verifies that citations strictly match retrieved evidence.
    Ensures unretrieved citations (e.g. SQL query on doc-only route) are stripped out.
    """
    from app.graph.nodes import filter_grounded_citations

    sql_ev = [{"evidence_id": "EVID-SQL-1", "source_ref": "SELECT region, SUM(refund_amount) FROM orders WHERE region='Midwest';"}]
    doc_ev = [{"evidence_id": "EVID-DOC-1", "source_ref": "customer_refund_policy_2025.md#p1"}]

    raw_citations = [
        "customer_refund_policy_2025.md#p1",
        "carrier_logistics_x_sla_contract_2025.md#p1",  # NOT in evidence -> MUST BE FILTERED
        "SELECT carrier_id, on_time_pct FROM carrier_metrics;",  # NOT in evidence -> MUST BE FILTERED
        "SELECT region, SUM(refund_amount) FROM orders WHERE region='Midwest';",  # Valid
    ]

    filtered = filter_grounded_citations(raw_citations, sql_ev, doc_ev)
    assert "customer_refund_policy_2025.md#p1" in filtered
    assert "SELECT region, SUM(refund_amount) FROM orders WHERE region='Midwest';" in filtered
    assert "carrier_logistics_x_sla_contract_2025.md#p1" not in filtered
    assert "SELECT carrier_id, on_time_pct FROM carrier_metrics;" not in filtered


def test_all_output_fields_grounded():
    """
    Explicitly tests evidence grounding across all output fields for individual queries:
    - Q1: If policy document is not retrieved, key_findings must not claim Policy Section 2.
    - Q2: If carrier_metrics SQL is not retrieved, output must not claim 88.2% performance.
    - Q4: If carrier SLA evidence is not retrieved, recommended_actions must not recommend carrier penalty recovery.
    - Q5: If carrier SLA contract is not retrieved, recommended_actions must not recommend Section 4.2 penalties.
    """
    synthesizer = ExecutiveSynthesizerAgent()

    # Q1 test without refund policy doc
    out_q1 = synthesizer.synthesize(
        question="What is the total Midwest customer refund payout amount?",
        sql_evidence=[{"evidence_id": "EVID-SQL-1", "source_ref": "SELECT region, SUM(refund_amount) FROM orders WHERE region='Midwest';"}]
    )
    for kf in out_q1.key_findings:
        assert "Section 2" not in kf

    # Q2 test without SQL carrier metrics
    out_q2 = synthesizer.synthesize(
        question="Did the carrier breach its delivery SLA?",
        doc_evidence=[{"evidence_id": "EVID-DOC-1", "source_ref": "carrier_logistics_x_sla_contract_2025.md#p1"}]
    )
    assert "88.2%" not in out_q2.executive_conclusion
    for kf in out_q2.key_findings:
        assert "88.2%" not in kf

    # Q4 test without carrier SLA evidence
    out_q4 = synthesizer.synthesize(
        question="Why did logistics margins decline?",
        sql_evidence=[{"evidence_id": "EVID-SQL-1", "source_ref": "SELECT region, SUM(refund_amount) FROM orders WHERE region='Midwest';"}],
        doc_evidence=[{"evidence_id": "EVID-DOC-1", "source_ref": "customer_refund_policy_2025.md#p1"}]
    )
    for act in out_q4.recommended_actions:
        assert "carrier penalty" not in act.lower()
        assert "sla rate credits" not in act.lower()

    # Q5 test without carrier SLA contract
    out_q5 = synthesizer.synthesize(
        question="Does the force-majeure clause apply to this disruption?",
        doc_evidence=[{"evidence_id": "EVID-DOC-1", "source_ref": "force_majeure_clause_policy.md#p1"}]
    )
    for act in out_q5.recommended_actions:
        assert "section 4.2" not in act.lower()
