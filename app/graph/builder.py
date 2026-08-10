"""
LangGraph Workflow Builder for ERDIS Decision Intelligence System.
Assembles and compiles StateGraph with deterministic control nodes, conditional edges, circuit breakers, and MemorySaver checkpointing.
"""

from typing import Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import GraphState
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


def route_after_planner(state: GraphState) -> str:
    """Routes execution after planner based on query classification."""
    route = state.get("route", "both")
    if route == "sql_only":
        return "sql_analyst_agent_node"
    elif route == "document_only":
        return "doc_rag_agent_node"
    elif route == "clarification":
        return "executive_synthesizer_agent_node"
    else:
        # For 'both', run SQL first then Document RAG
        return "sql_analyst_agent_node"


def route_after_sql(state: GraphState) -> str:
    """Routes execution after SQL analyst agent node."""
    route = state.get("route", "sql_only")
    if route == "both":
        return "doc_rag_agent_node"
    return "evidence_aggregation_node"


def route_after_critic(state: GraphState) -> str:
    """Routes execution after critic evaluation (re-query loop vs risk assessment)."""
    if state.get("retry_needed") is True:
        return "router_node"
    return "risk_assessment_hitl_node"


def build_erdis_graph(checkpointer: Optional[MemorySaver] = None):
    """
    Constructs and compiles the ERDIS LangGraph StateGraph workflow.
    """
    builder = StateGraph(GraphState)

    # Add Nodes
    builder.add_node("orchestrator_node", orchestrator_node)
    builder.add_node("planner_agent_node", planner_agent_node)
    builder.add_node("router_node", router_node)
    builder.add_node("sql_analyst_agent_node", sql_analyst_agent_node)
    builder.add_node("doc_rag_agent_node", doc_rag_agent_node)
    builder.add_node("evidence_aggregation_node", evidence_aggregation_node)
    builder.add_node("critic_agent_node", critic_agent_node)
    builder.add_node("risk_assessment_hitl_node", risk_assessment_hitl_node)
    builder.add_node("executive_synthesizer_agent_node", executive_synthesizer_agent_node)

    # Add Edges
    builder.add_edge(START, "orchestrator_node")
    builder.add_edge("orchestrator_node", "planner_agent_node")
    builder.add_edge("planner_agent_node", "router_node")

    # Conditional Routing from Router Node
    builder.add_conditional_edges(
        "router_node",
        route_after_planner,
        {
            "sql_analyst_agent_node": "sql_analyst_agent_node",
            "doc_rag_agent_node": "doc_rag_agent_node",
            "executive_synthesizer_agent_node": "executive_synthesizer_agent_node",
        },
    )

    # Edge after SQL Analyst
    builder.add_conditional_edges(
        "sql_analyst_agent_node",
        route_after_sql,
        {
            "doc_rag_agent_node": "doc_rag_agent_node",
            "evidence_aggregation_node": "evidence_aggregation_node",
        },
    )

    # Edge after Document RAG
    builder.add_edge("doc_rag_agent_node", "evidence_aggregation_node")

    # Aggregation to Critic
    builder.add_edge("evidence_aggregation_node", "critic_agent_node")

    # Conditional Loop / Next Step after Critic
    builder.add_conditional_edges(
        "critic_agent_node",
        route_after_critic,
        {
            "router_node": "router_node",
            "risk_assessment_hitl_node": "risk_assessment_hitl_node",
        },
    )

    # Risk Assessment HITL to Synthesizer
    builder.add_edge("risk_assessment_hitl_node", "executive_synthesizer_agent_node")

    # Synthesizer to END
    builder.add_edge("executive_synthesizer_agent_node", END)

    saver = checkpointer if checkpointer is not None else MemorySaver()
    return builder.compile(checkpointer=saver)
