"""
Planner Agent Implementation.
Analyzes strategic user questions and formulates a structured execution plan without direct tool permissions.
"""

from typing import Optional
from app.services.llm_provider import BaseLLMProvider, get_llm_provider
from app.schemas.agents import PlannerOutput
from app.agents.prompts import PLANNER_SYSTEM_PROMPT


class PlannerAgent:
    """
    Planner Agent for strategic question breakdown and evidence planning.
    """

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm_provider = llm_provider or get_llm_provider()

    def plan(self, question: str) -> PlannerOutput:
        """Generates a validated PlannerOutput schema."""
        prompt = f"Analyze the following enterprise query and generate an execution plan:\n\nUser Question: {question}"
        return self.llm_provider.generate_structured(
            prompt=prompt,
            response_schema=PlannerOutput,
            system_prompt=PLANNER_SYSTEM_PROMPT,
        )
