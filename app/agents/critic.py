"""
Adversarial Critic Agent Implementation.
Rigorously audits collected SQL and Document evidence for grounding, contradictions, and missing items.
Does NOT execute tools directly; requests additional evidence via structured graph re-query routing.
"""

from typing import Optional, Dict, Any, List
from app.services.llm_provider import BaseLLMProvider, get_llm_provider
from app.schemas.agents import CritiqueOutput
from app.agents.prompts import ADVERSARIAL_CRITIC_SYSTEM_PROMPT


class AdversarialCriticAgent:
    """
    Adversarial Critic Agent for evidence grounding and sanity verification.
    """

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm_provider = llm_provider or get_llm_provider()

    def audit(
        self,
        question: str,
        sql_evidence: List[Dict[str, Any]],
        doc_evidence: List[Dict[str, Any]],
        iteration_count: int = 1,
    ) -> CritiqueOutput:
        """
        Audits gathered evidence and produces structured CritiqueOutput.
        """
        prompt = (
            f"Audit the gathered evidence for the question:\n"
            f"Question: {question}\n"
            f"Iteration: {iteration_count}\n"
            f"SQL Evidence Items: {sql_evidence}\n"
            f"Document Evidence Items: {doc_evidence}\n"
        )

        output = self.llm_provider.generate_structured(
            prompt=prompt,
            response_schema=CritiqueOutput,
            system_prompt=ADVERSARIAL_CRITIC_SYSTEM_PROMPT,
        )

        # Enforce max 2 iterations limit on retry_needed
        if iteration_count >= 2:
            return CritiqueOutput(
                supported_claims=output.supported_claims,
                unsupported_claims=output.unsupported_claims,
                contradictions=output.contradictions,
                missing_evidence=output.missing_evidence,
                recommended_followup=output.recommended_followup,
                retry_needed=False,  # Force False to prevent exceeding max 2 iterations
                confidence_score=output.confidence_score,
            )

        return output
