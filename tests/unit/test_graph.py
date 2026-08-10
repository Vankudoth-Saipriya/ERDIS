"""
Unit Tests for ERDIS LangGraph Orchestration & Control Layer.
Tests graph construction, state initialization, deterministic routing, circuit breakers, and HITL interrupts.
"""

import pytest
from langgraph.types import Command
from app.graph import (
    build_erdis_graph,
    create_initial_state,
    determine_route,
    MAX_ITERATIONS,
    MAX_TOOL_CALLS,
    MAX_TOKEN_BUDGET,
    MAX_EXECUTION_TIME_MS,
)
from app.graph.nodes import (
    orchestrator_node,
    planner_agent_node,
    router_node,
    sql_analyst_agent_node,
    doc_rag_agent_node,
    evidence_aggregation_node,
    critic_agent_node,
    risk_assessment_hitl_node,
    executive_synthesizer_agent_node,
)


def test_graph_construction():
    """Verifies that build_erdis_graph compiles a valid StateGraph instance."""
    app = build_erdis_graph()
    assert app is not None
    assert hasattr(app, "invoke")
    assert hasattr(app, "stream")


def test_initial_state():
    """Verifies initial state creation with default values."""
    state = create_initial_state("What is the Midwest margin loss?")
    assert state["task_id"].startswith("TASK-")
    assert state["original_question"] == "What is the Midwest margin loss?"
    assert state["normalized_question"] == "What is the Midwest margin loss?"
    assert state["iteration_count"] == 0
    assert state["tool_call_count"] == 0
    assert state["token_usage"]["total_tokens"] == 0
    assert state["financial_impact_usd"] == 0.0
    assert state["approval_status"] == "NOT_REQUIRED"
    assert state["errors"] == []


def test_deterministic_routing():
    """Verifies query route classification logic."""
    assert determine_route("What is Midwest revenue and order refund amount?") == "sql_only"
    assert determine_route("What are the carrier contract SLA terms and policy rules?") == "document_only"
    assert determine_route("Why did Midwest revenue drop and what SLA penalty applies in contract?") == "both"
    assert determine_route("") == "clarification"
    assert determine_route("hi") == "clarification"


def test_sql_only_route_execution():
    """Verifies execution flow for a SQL-only question."""
    app = build_erdis_graph()
    initial = create_initial_state("What is total Midwest refund amount in revenue?")
    config = {"configurable": {"thread_id": "test-thread-sql"}}

    result = app.invoke(initial, config=config)

    assert result["route"] == "sql_only"
    assert len(result["sql_evidence"]) > 0
    assert len(result["document_evidence"]) == 0
    assert "orchestrator_node" in result["node_history"]
    assert "sql_analyst_agent_node" in result["node_history"]
    assert "doc_rag_agent_node" not in result["node_history"]
    assert result["final_answer"] is not None


def test_document_only_route_execution():
    """Verifies execution flow for a Document-only question."""
    app = build_erdis_graph()
    initial = create_initial_state("What are the carrier contract SLA terms and policy rules?")
    config = {"configurable": {"thread_id": "test-thread-doc"}}

    result = app.invoke(initial, config=config)

    assert result["route"] == "document_only"
    assert len(result["document_evidence"]) > 0
    assert len(result["sql_evidence"]) == 0
    assert "orchestrator_node" in result["node_history"]
    assert "doc_rag_agent_node" in result["node_history"]
    assert "sql_analyst_agent_node" not in result["node_history"]
    assert result["final_answer"] is not None


def test_combined_route_execution():
    """Verifies execution flow for a combined (both) question."""
    app = build_erdis_graph()
    initial = create_initial_state("What is Midwest refund cost and carrier SLA contract penalty?")
    config = {"configurable": {"thread_id": "test-thread-both"}}

    result = app.invoke(initial, config=config)

    assert result["route"] == "both"
    assert len(result["sql_evidence"]) > 0
    assert len(result["document_evidence"]) > 0
    assert "sql_analyst_agent_node" in result["node_history"]
    assert "doc_rag_agent_node" in result["node_history"]
    assert result["final_answer"] is not None


def test_clarification_route_execution():
    """Verifies execution flow for invalid / short queries."""
    app = build_erdis_graph()
    initial = create_initial_state("hi")
    config = {"configurable": {"thread_id": "test-thread-clarify"}}

    result = app.invoke(initial, config=config)

    assert result["route"] == "clarification"
    assert "executive_synthesizer_agent_node" in result["node_history"]


def test_max_2_iterations_limit():
    """Verifies circuit breaker stops execution when max 2 iterations are reached."""
    state = create_initial_state("test query")
    state["iteration_count"] = 2  # Already ran 2 iterations
    state["retry_needed"] = True

    res = critic_agent_node(state)
    assert res["iteration_count"] == 3
    assert res["retry_needed"] is False
    assert any("Max iteration count exceeded" in err for err in res["errors"])


def test_max_10_tool_calls_limit():
    """Verifies circuit breaker stops execution when max 10 tool calls are reached."""
    state = create_initial_state("test query")
    state["tool_call_count"] = 10
    state["retry_needed"] = True

    res = critic_agent_node(state)
    assert res["retry_needed"] is False
    assert any("Max tool call limit reached" in err for err in res["errors"])


def test_token_budget_termination():
    """Verifies circuit breaker stops execution when 60k token budget is exceeded."""
    state = create_initial_state("test query")
    state["token_usage"] = {"prompt_tokens": 50000, "completion_tokens": 10001, "total_tokens": 60001}
    state["retry_needed"] = True

    res = critic_agent_node(state)
    assert res["retry_needed"] is False
    assert any("Token budget exhausted" in err for err in res["errors"])


def test_timeout_termination():
    """Verifies circuit breaker stops execution when 45s execution limit is exceeded."""
    state = create_initial_state("test query")
    state["start_time_timestamp"] = 1000.0  # Far in past
    state["retry_needed"] = True

    res = critic_agent_node(state)
    assert res["retry_needed"] is False
    assert any("Execution time limit exceeded" in err for err in res["errors"])


def test_hitl_required_and_approval():
    """Verifies HITL interrupt trigger and successful operator approval resumption."""
    app = build_erdis_graph()
    initial = create_initial_state("Midwest revenue margin loss 100k financial impact carrier SLA penalty")
    config = {"configurable": {"thread_id": "test-thread-hitl-approve"}}

    # First invocation hits interrupt at risk_assessment_hitl_node
    res_interrupt = app.invoke(initial, config=config)

    # Verify state paused at interrupt
    snapshot = app.get_state(config)
    assert len(snapshot.next) > 0
    assert snapshot.next[0] == "risk_assessment_hitl_node"

    # Resume with approval
    res_approved = app.invoke(Command(resume="APPROVED"), config=config)

    assert res_approved["approval_status"] == "APPROVED"
    assert res_approved["final_answer"] is not None
    assert "EXECUTION REJECTED" not in res_approved["final_answer"]


def test_hitl_required_and_rejection():
    """Verifies HITL interrupt trigger and operator rejection resumption."""
    app = build_erdis_graph()
    initial = create_initial_state("Midwest revenue margin loss 100k financial impact carrier SLA penalty")
    config = {"configurable": {"thread_id": "test-thread-hitl-reject"}}

    # First invocation hits interrupt
    app.invoke(initial, config=config)

    # Resume with rejection
    res_rejected = app.invoke(Command(resume="REJECTED"), config=config)

    assert res_rejected["approval_status"] == "REJECTED"
    assert "EXECUTION REJECTED BY HUMAN OPERATOR" in res_rejected["final_answer"]
    assert any("rejected" in err.lower() for err in res_rejected["errors"])


def test_empty_evidence_handling():
    """Verifies graceful answer formatting when 0 evidence items match."""
    app = build_erdis_graph()
    initial = create_initial_state("nonexistentquery999999")
    config = {"configurable": {"thread_id": "test-thread-empty"}}

    res = app.invoke(initial, config=config)
    assert res["final_answer"] is not None
