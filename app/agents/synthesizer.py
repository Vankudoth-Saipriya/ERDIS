"""
Executive Synthesizer Agent Implementation.
Synthesizes final evidence-grounded decision intelligence reports.
Strictly segregates ungrounded model inferences and operational assumptions.
"""

from typing import Optional, Dict, Any, List
from app.services.llm_provider import BaseLLMProvider, get_llm_provider
from app.schemas.agents import ExecutiveSynthesisOutput
from app.agents.prompts import EXECUTIVE_SYNTHESIZER_SYSTEM_PROMPT


class ExecutiveSynthesizerAgent:
    """
    Executive Synthesizer Agent producing grounded decision intelligence reports.
    """

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm_provider = llm_provider or get_llm_provider()

    def synthesize(
        self,
        question: str,
        sql_evidence: List[Dict[str, Any]],
        doc_evidence: List[Dict[str, Any]],
        critique: Dict[str, Any],
        approval_status: str = "NOT_REQUIRED",
        financial_impact_usd: float = 0.0,
    ) -> ExecutiveSynthesisOutput:
        """
        Synthesizes structured final report from evidence and critique.
        """
        if approval_status == "REJECTED":
            return ExecutiveSynthesisOutput(
                executive_conclusion="EXECUTION REJECTED BY HUMAN OPERATOR.",
                key_findings=["Recommendation involved high financial impact exceeding safety threshold."],
                root_cause_analysis="Human operator rejected execution during HITL review.",
                business_impact_usd=financial_impact_usd,
                recommended_actions=["Submit modified request with lower financial risk scope."],
                model_inferences_and_assumptions=["Operator intervention halted downstream execution."],
                citations=[],
            )

        prompt = (
            f"Synthesize an executive decision intelligence report:\n"
            f"User Question: {question}\n"
            f"SQL Evidence: {sql_evidence}\n"
            f"Document Evidence: {doc_evidence}\n"
            f"Critique Audit: {critique}\n"
            f"Financial Impact USD: {financial_impact_usd}\n"
            f"Approval Status: {approval_status}\n"
        )

        return self.llm_provider.generate_structured(
            prompt=prompt,
            response_schema=ExecutiveSynthesisOutput,
            system_prompt=EXECUTIVE_SYNTHESIZER_SYSTEM_PROMPT,
        )
