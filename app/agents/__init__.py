"""
Multi-Agent Systems Package for ERDIS.
Exposes PlannerAgent, SQLAnalystAgent, DocumentRAGAgent, AdversarialCriticAgent, and ExecutiveSynthesizerAgent.
"""

from app.agents.planner import PlannerAgent
from app.agents.sql_analyst import SQLAnalystAgent
from app.agents.doc_rag import DocumentRAGAgent
from app.agents.critic import AdversarialCriticAgent
from app.agents.synthesizer import ExecutiveSynthesizerAgent
from app.agents.prompts import (
    PLANNER_SYSTEM_PROMPT,
    SQL_ANALYST_SYSTEM_PROMPT,
    DOCUMENT_RAG_SYSTEM_PROMPT,
    ADVERSARIAL_CRITIC_SYSTEM_PROMPT,
    EXECUTIVE_SYNTHESIZER_SYSTEM_PROMPT,
)

__all__ = [
    "PlannerAgent",
    "SQLAnalystAgent",
    "DocumentRAGAgent",
    "AdversarialCriticAgent",
    "ExecutiveSynthesizerAgent",
    "PLANNER_SYSTEM_PROMPT",
    "SQL_ANALYST_SYSTEM_PROMPT",
    "DOCUMENT_RAG_SYSTEM_PROMPT",
    "ADVERSARIAL_CRITIC_SYSTEM_PROMPT",
    "EXECUTIVE_SYNTHESIZER_SYSTEM_PROMPT",
]
