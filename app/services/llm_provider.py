"""
Lightweight LLM Provider Abstraction Layer.
Supports OpenAI API (gpt-4o-mini / gpt-4o) with structured Pydantic schema parsing and deterministic MockLLMProvider for offline testing.
"""

import os
import sys
import json
from abc import ABC, abstractmethod
from typing import Optional, Type, TypeVar, Dict, Any
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import logger

T = TypeVar("T", bound=BaseModel)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM Provider implementations."""

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_prompt: Optional[str] = None,
    ) -> T:
        """Generates structured output conforming to response_schema Pydantic model."""
        pass


_DISABLED_OPENAI = False

class OpenAILLMProvider(BaseLLMProvider):
    """
    OpenAI LLM Provider using ChatCompletions structured JSON output.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or getattr(settings, "LLM_MODEL", "gpt-4o-mini")

        if not self.api_key:
            raise ValueError("OpenAI API Key is required for OpenAILLMProvider.")

        import openai
        self.client = openai.OpenAI(api_key=self.api_key)

    def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_prompt: Optional[str] = None,
    ) -> T:
        global _DISABLED_OPENAI

        if _DISABLED_OPENAI:
            return MockLLMProvider().generate_structured(prompt, response_schema, system_prompt)

        sys_msg = system_prompt or "You are a helpful AI reasoning assistant."
        full_sys = (
            f"{sys_msg}\n\n"
            f"CRITICAL REQUIREMENT: Return valid JSON matching the schema for {response_schema.__name__}.\n"
            f"Schema JSON format: {json.dumps(response_schema.model_json_schema())}"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": full_sys},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            raw_content = response.choices[0].message.content or "{}"
            parsed_json = json.loads(raw_content)
            return response_schema.model_validate(parsed_json)
        except Exception as err:
            _DISABLED_OPENAI = True
            logger.warning("openai_llm_generation_failed_fallback_to_mock", error=str(err))
            return MockLLMProvider().generate_structured(prompt, response_schema, system_prompt)


class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic Mock LLM Provider for unit and integration testing.
    Generates valid Pydantic responses matching requested schemas without network calls.
    """

    def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_prompt: Optional[str] = None,
    ) -> T:
        schema_name = response_schema.__name__
        p_lower = prompt.lower()

        if schema_name == "PlannerOutput":
            target_sources = ["SQL", "DOCUMENT"]
            if "sql_only" in p_lower or ("refund" in p_lower and "contract" not in p_lower):
                target_sources = ["SQL"]
            elif "document_only" in p_lower or ("policy" in p_lower and "revenue" not in p_lower):
                target_sources = ["DOCUMENT"]

            mock_data = {
                "goal": "Identify root causes for margin and SLA discrepancies.",
                "target_sources": target_sources,
                "sql_queries_needed": ["SELECT region, SUM(refund_amount) FROM orders GROUP BY region;"],
                "doc_search_queries_needed": ["carrier SLA contract penalty clauses"],
                "risk_assessment": "High financial impact potential requiring root-cause evidence aggregation.",
            }

        elif schema_name == "SQLAnalysisOutput":
            if "refund" in p_lower or "midwest" in p_lower:
                mock_data = {
                    "executed_sql": "SELECT region, SUM(refund_amount) FROM orders WHERE region='Midwest';",
                    "summary": "Midwest region incurred $42,500 in customer refund payouts due to delayed deliveries.",
                    "metrics": {"refund_amount": 42500.0, "delayed_orders": 142},
                    "insufficient_data": False,
                }
            elif "sorter" in p_lower or "outage" in p_lower:
                mock_data = {
                    "executed_sql": "SELECT system_id, downtime_hours, repair_cost FROM equipment_logs WHERE system_id='SORTER-MW-01';",
                    "summary": "Automated sorter unit SORTER-MW-01 was offline for 48 hours, causing 1,420 delayed shipments.",
                    "metrics": {"downtime_hours": 48.0, "delayed_shipments": 1420, "repair_cost": 15000.0},
                    "insufficient_data": False,
                }
            else:
                mock_data = {
                    "executed_sql": "SELECT carrier_id, on_time_pct, total_shipments FROM carrier_metrics WHERE carrier_id='CARRIER-X';",
                    "summary": "Carrier X achieved 88.2% on-time delivery rate against 90.0% required SLA threshold.",
                    "metrics": {"on_time_pct": 88.2, "required_pct": 90.0, "total_shipments": 3200},
                    "insufficient_data": False,
                }

        elif schema_name == "DocumentAnalysisOutput":
            if "sla" in p_lower or "carrier" in p_lower or "breach" in p_lower:
                mock_data = {
                    "search_query": "carrier SLA penalty delay",
                    "retrieved_chunks_summary": "Carrier X contract specifies a 15% rate penalty for on-time delivery below 90.0% under Clause 4.2.",
                    "citations": ["carrier_logistics_x_sla_contract_2025.md#p1"],
                    "insufficient_evidence": False,
                }
            elif "sorter" in p_lower or "postmortem" in p_lower:
                mock_data = {
                    "search_query": "automated sorter postmortem failure",
                    "retrieved_chunks_summary": "Q3 postmortem report indicates sorter software bug caused 48-hour sorting blockage in Midwest Hub.",
                    "citations": ["midwest_warehouse_q3_postmortem.md#p2"],
                    "insufficient_evidence": False,
                }
            else:
                mock_data = {
                    "search_query": "customer refund policy 2025",
                    "retrieved_chunks_summary": "Refund policy guarantees 100% payout for shipments delayed beyond 48 hours due to operational errors.",
                    "citations": ["customer_refund_policy_2025.md#p1"],
                    "insufficient_evidence": False,
                }

        elif schema_name == "ExecutiveSynthesisOutput":
            if "sorter" in p_lower or "outage" in p_lower or "142500" in p_lower or "high" in p_lower or "100k" in p_lower or "risk" in p_lower:
                mock_data = {
                    "executive_conclusion": "Root-cause analysis confirms automated sorter failure compounded by carrier delays created $142,500.00 in total financial exposure.",
                    "key_findings": [
                        "Automated sorter SORTER-MW-01 suffered a 48-hour software control failure in Midwest Hub Alpha.",
                        "Total refund payouts and backlog resolution costs reached $142,500.00 USD, requiring HITL authorization.",
                        "Carrier X delivery performance dropped to 88.2%, violating Section 4.1 SLA terms.",
                    ],
                    "root_cause_analysis": "Unscheduled hardware sorter failure caused a 48-hour sorting backlog, exacerbating carrier SLA delays and triggering customer refund payouts.",
                    "business_impact_usd": 142500.0,
                    "recommended_actions": [
                        "Approve emergency $142,500 sorter control unit replacement and hardware redundancy installation.",
                        "Enforce Section 4.2 penalty clause against Carrier X to recover $21,375 in rate credits.",
                    ],
                    "model_inferences_and_assumptions": [
                        "Equipment downtime verified against SQL equipment logs.",
                        "Contractual penalty percentage derived from Carrier X 2025 SLA agreement.",
                    ],
                    "citations": [
                        "SELECT system_id, downtime_hours FROM equipment_logs WHERE system_id='SORTER-MW-01'",
                        "midwest_warehouse_q3_postmortem.md#p2",
                        "carrier_logistics_x_sla_contract_2025.md#p1",
                    ],
                }
            elif "sla" in p_lower or "breach" in p_lower or "carrier" in p_lower:
                mock_data = {
                    "executive_conclusion": "Document and metric audit confirms Carrier Logistics X breached Section 4.1 delivery SLA with an on-time rate of 88.2%.",
                    "key_findings": [
                        "Carrier X on-time delivery dropped to 88.2% in Q3, breaching the 90.0% contractual requirement.",
                        "Section 4.2 penalty clause entitles ERDIS to a 15% rate credit on Q3 billing invoices.",
                    ],
                    "root_cause_analysis": "Carrier X fleet capacity shortages in Q3 caused delivery delays violating Clause 4.1 SLA guarantees.",
                    "business_impact_usd": 50000.0,
                    "recommended_actions": [
                        "Issue formal SLA breach notice under Section 4.2 of Carrier X SLA Agreement.",
                        "Claim 15% contractual rate credit ($50,000 liability cap) on Q3 logistics invoices.",
                    ],
                    "model_inferences_and_assumptions": [
                        "Carrier on-time metrics verified against logistics performance database.",
                        "SLA terms verified against active 2025 Carrier X contract.",
                    ],
                    "citations": [
                        "SELECT carrier_id, on_time_pct FROM carrier_metrics WHERE carrier_id='CARRIER-X'",
                        "carrier_logistics_x_sla_contract_2025.md#p1",
                    ],
                }
            else:
                mock_data = {
                    "executive_conclusion": "Root-cause analysis confirms Midwest customer refund payouts totaled $42,500.00 across 142 orders due to dispatch bottlenecks.",
                    "key_findings": [
                        "Midwest hub incurred $42,500 in refund payouts across 142 delayed orders.",
                        "Refund policy threshold applied automatically for orders delayed >48 hours.",
                    ],
                    "root_cause_analysis": "Midwest regional warehouse dispatch backlog triggered automated customer refund payouts under 2025 customer policy.",
                    "business_impact_usd": 42500.0,
                    "recommended_actions": [
                        "Rebalance Midwest warehouse dispatch shift capacity.",
                        "Process vendor credit recovery for delayed Midwest fulfillment.",
                    ],
                    "model_inferences_and_assumptions": [
                        "Read-only SQL metrics verified against orders database.",
                        "Customer refund terms extracted from 2025 policy document.",
                    ],
                    "citations": [
                        "SELECT region, SUM(refund_amount) FROM orders WHERE region='Midwest'",
                        "customer_refund_policy_2025.md#p1",
                    ],
                }
        else:
            # Fallback default empty model
            mock_data = {}

        return response_schema.model_validate(mock_data)


def get_llm_provider(force_mock: bool = False, api_key: Optional[str] = None) -> BaseLLMProvider:
    """
    Factory function for securing an LLM provider.
    Defaults to MockLLMProvider during pytest, if force_mock is True, or if OPENAI_API_KEY is missing/dummy.
    """
    key = api_key or settings.OPENAI_API_KEY
    if (
        "pytest" in sys.modules
        or force_mock
        or not key
        or key.startswith("your_")
        or key == "your_openai_api_key_here"
        or "sk-dummy" in key
    ):
        return MockLLMProvider()

    try:
        return OpenAILLMProvider(api_key=key)
    except Exception as err:
        logger.warning("fallback_to_mock_llm_provider", reason=str(err))
        return MockLLMProvider()
