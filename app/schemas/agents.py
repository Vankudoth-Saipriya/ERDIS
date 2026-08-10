"""
Pydantic Schemas for Multi-Agent Structured Outputs in ERDIS.
Validates outputs from Planner, SQL Analyst, Document RAG, Adversarial Critic, and Executive Synthesizer agents.
"""

from typing import List, Dict, Any, Literal, Optional
from pydantic import Field
from app.schemas.base import BaseSchema


class PlannerOutput(BaseSchema):
    """Structured execution plan produced by Planner Agent."""
    goal: str = Field(..., description="High-level analytical goal for the query.")
    target_sources: List[Literal["SQL", "DOCUMENT"]] = Field(
        default_factory=lambda: ["SQL", "DOCUMENT"],
        description="Required data sources (SQL, DOCUMENT, or both).",
    )
    sql_queries_needed: List[str] = Field(
        default_factory=list,
        description="Descriptive SQL query objectives or requirements.",
    )
    doc_search_queries_needed: List[str] = Field(
        default_factory=list,
        description="Descriptive document search queries.",
    )
    risk_assessment: str = Field(
        default="Standard operational inquiry.",
        description="Potential financial or business risk assessment.",
    )


class SQLAnalysisOutput(BaseSchema):
    """Structured output produced by SQL Analyst Agent."""
    executed_sql: str = Field(..., description="The validated SELECT SQL query executed.")
    summary: str = Field(..., description="Quantitative findings summary.")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Extracted numerical metrics.")
    insufficient_data: bool = Field(default=False, description="True if SQL database returned 0 rows or insufficient data.")


class DocumentAnalysisOutput(BaseSchema):
    """Structured output produced by Document RAG Agent."""
    search_query: str = Field(..., description="Document search query utilized.")
    retrieved_chunks_summary: str = Field(..., description="Summary of retrieved contract/document chunk passages.")
    citations: List[str] = Field(default_factory=list, description="Document chunk references and filenames.")
    insufficient_evidence: bool = Field(default=False, description="True if no relevant document evidence was found.")


class CritiqueOutput(BaseSchema):
    """Structured output produced by Adversarial Critic Agent."""
    supported_claims: List[str] = Field(default_factory=list, description="Claims directly grounded in evidence.")
    unsupported_claims: List[str] = Field(default_factory=list, description="Claims lacking sufficient evidence backing.")
    contradictions: List[str] = Field(default_factory=list, description="Contradictions between SQL data and document contracts.")
    missing_evidence: List[str] = Field(default_factory=list, description="Key missing evidence items.")
    recommended_followup: List[str] = Field(default_factory=list, description="Suggested re-queries or follow-up tasks.")
    retry_needed: bool = Field(default=False, description="True if re-query loop is required to gather missing evidence.")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Overall critique confidence score.")


class ExecutiveSynthesisOutput(BaseSchema):
    """Structured final synthesis produced by Executive Synthesizer Agent."""
    executive_conclusion: str = Field(..., description="High-level executive summary of findings.")
    key_findings: List[str] = Field(default_factory=list, description="Bulletized key findings.")
    root_cause_analysis: str = Field(..., description="Detailed root-cause analysis explanation.")
    business_impact_usd: float = Field(default=0.0, ge=0.0, description="Calculated total financial impact in USD.")
    recommended_actions: List[str] = Field(default_factory=list, description="Actionable business recommendations.")
    model_inferences_and_assumptions: List[str] = Field(
        default_factory=list,
        description="Explicitly segregated ungrounded model inferences and operational assumptions.",
    )
    citations: List[str] = Field(default_factory=list, description="Preserved SQL and Document citations.")
