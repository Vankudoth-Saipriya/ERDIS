"""
Integration Tests for ERDIS LangGraph Execution Layer.
Simulates complete multi-node graph executions, circuit breaker enforcement, and HITL state persistence.
"""

import pytest
from langgraph.types import Command
from app.graph import build_erdis_graph, create_initial_state
from app.graph.nodes import (
    orchestrator_node,
    router_node,
    sql_analyst_agent_node,
    doc_rag_agent_node,
    critic_agent_node,
    risk_assessment_hitl_node,
    executive_synthesizer_agent_node,
)


def test_integration_full_graph_execution_sql_path():
    """Tests end-to-end execution of a SQL-only pipeline task."""
    app = build_erdis_graph()
    initial = create_initial_state("SELECT refund_amount FROM orders WHERE region='Midwest'")
    config = {"configurable": {"thread_id": "integ-thread-sql-1"}}

    state = app.invoke(initial, config=config)

    assert state["route"] == "sql_only"
    assert len(state["sql_evidence"]) > 0
    assert state["final_answer"] is not None
    assert "EXECUTIVE CONCLUSION" in state["final_answer"]
    assert state["node_history"][-1] == "executive_synthesizer_agent_node"


def test_integration_full_graph_execution_doc_path():
    """Tests end-to-end execution of a Document-only pipeline task."""
    app = build_erdis_graph()
    initial = create_initial_state("What are the carrier SLA agreement penalty clauses?")
    config = {"configurable": {"thread_id": "integ-thread-doc-1"}}

    state = app.invoke(initial, config=config)

    assert state["route"] == "document_only"
    assert len(state["document_evidence"]) > 0
    assert state["final_answer"] is not None
    assert "carrier_logistics_x_sla_contract_2025.md#p1" in state["citations"]


def test_integration_full_graph_execution_combined_path():
    """Tests end-to-end execution of a combined SQL and Document pipeline task."""
    app = build_erdis_graph()
    initial = create_initial_state("Calculate Midwest gross margin loss and check carrier SLA contract terms")
    config = {"configurable": {"thread_id": "integ-thread-both-1"}}

    state = app.invoke(initial, config=config)

    assert state["route"] == "both"
    assert len(state["sql_evidence"]) > 0
    assert len(state["document_evidence"]) > 0
    assert state["tool_call_count"] == 2
    assert state["token_usage"]["total_tokens"] == 450


def test_integration_critic_requery_loop():
    """Tests critic node initiating a re-query loop when evidence is insufficient."""
    app = build_erdis_graph()

    # Custom initial state requesting re-query
    state = create_initial_state("Analyze Midwest margin fuel surcharge")
    state["retry_needed"] = True
    config = {"configurable": {"thread_id": "integ-thread-requery-1"}}

    result = app.invoke(state, config=config)

    assert result["iteration_count"] >= 1
    assert result["final_answer"] is not None


def test_integration_hitl_checkpoint_persistence_and_approval():
    """Tests that state checkpointing preserves execution state across HITL interrupt and approval."""
    app = build_erdis_graph()
    initial = create_initial_state("100k Midwest revenue margin refund impact carrier SLA contract penalty")
    config = {"configurable": {"thread_id": "integ-thread-checkpoint-1"}}

    # Execute graph until HITL interrupt
    app.invoke(initial, config=config)

    # Inspect snapshot state
    snapshot = app.get_state(config)
    assert len(snapshot.next) > 0
    assert snapshot.next[0] == "risk_assessment_hitl_node"
    assert snapshot.values["financial_impact_usd"] > 100000.0

    # Resume graph execution with APPROVED
    res_final = app.invoke(Command(resume="APPROVED"), config=config)

    assert res_final["approval_status"] == "APPROVED"
    assert res_final["final_answer"] is not None
    assert "EXECUTIVE CONCLUSION" in res_final["final_answer"]


def test_integration_hitl_checkpoint_persistence_and_rejection():
    """Tests that state checkpointing preserves execution state across HITL interrupt and rejection."""
    app = build_erdis_graph()
    initial = create_initial_state("100k Midwest revenue margin refund impact carrier SLA contract penalty")
    config = {"configurable": {"thread_id": "integ-thread-checkpoint-2"}}

    # Execute graph until HITL interrupt
    app.invoke(initial, config=config)

    # Resume graph execution with REJECTED
    res_final = app.invoke(Command(resume="REJECTED"), config=config)

    assert res_final["approval_status"] == "REJECTED"
    assert "EXECUTION REJECTED BY HUMAN OPERATOR" in res_final["final_answer"]


def test_integration_circuit_breaker_termination():
    """Tests circuit breaker forced termination when max iteration count is reached."""
    app = build_erdis_graph()
    state = create_initial_state("Midwest margin refund")
    state["iteration_count"] = 2
    state["retry_needed"] = True
    config = {"configurable": {"thread_id": "integ-thread-cb-1"}}

    res = app.invoke(state, config=config)
    assert any("Circuit breaker" in err for err in res["errors"])
