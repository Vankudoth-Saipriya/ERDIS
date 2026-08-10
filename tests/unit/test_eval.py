"""
Unit Tests for ERDIS Evaluation Framework (Phase 7 Audit & Failure Testing).
Verifies non-hardcoded metric calculation, independent ground truth evaluation,
RAG recall/precision scoring, claim groundedness, citation validity, Critic A/B deltas,
and failure taxonomy.
"""

import os
import pytest
from app.eval.dataset import load_benchmark_dataset, BenchmarkCase
from app.eval.metrics import MetricsEngine, CostCalculator, CaseEvaluationResult
from app.eval.critic_ab import CriticABExperiment
from app.eval.runner import BenchmarkRunner


def test_benchmark_dataset_loading():
    """Verifies that all 30 benchmark cases load correctly with valid fields."""
    cases = load_benchmark_dataset()
    assert len(cases) == 30

    categories = set(c.category for c in cases)
    assert "SQL-only" in categories
    assert "Document-only" in categories
    assert "SQL + Document" in categories
    assert "Root-cause analysis" in categories
    assert "Financial impact" in categories
    assert "High-risk/HITL" in categories
    assert "Adversarial/security" in categories

    for c in cases:
        assert c.case_id is not None
        assert c.question is not None
        assert c.expected_route in {"sql", "documents", "both"}


def test_deliberate_metric_failures_and_groundedness_penalties():
    """
    Deliberate Failure Audit Tests:
    Case A: All claims supported -> high groundedness (1.0)
    Case B: One unsupported claim -> groundedness decreases (< 1.0)
    Case C: Fabricated citation -> citation coverage decreases (< 1.0)
    Case D: Wrong retrieved document -> RAG Recall decreases (< 1.0)
    Case E: Critic ON removes unsupported claim -> score improves relative to Critic OFF
    """
    engine = MetricsEngine()
    case = BenchmarkCase(
        case_id="FAIL-TEST",
        category="Document-only",
        question="What is the Carrier X SLA timeframe?",
        expected_route="documents",
        expected_doc_ids=["DOC-CONTRACT-CARRIER-X"],
        expected_citations=["carrier_logistics_x_sla_contract_2025.md#p1"],
        reference_facts=["Carrier Logistics X guarantees delivery within 2 business days."],
        reference_answer="Carrier Logistics X guarantees delivery within 2 business days under SLA clause 4.1.",
    )

    # Case A: Fully supported answer with valid citation
    resp_a = {
        "status": "COMPLETED",
        "route": "documents",
        "executive_conclusion": "Carrier Logistics X guarantees delivery within 2 business days under SLA clause 4.1.",
        "citations": ["carrier_logistics_x_sla_contract_2025.md#p1"],
    }
    res_a = engine.evaluate_case(case, resp_a)
    assert res_a.groundedness == 1.0
    assert res_a.citation_coverage == 1.0
    assert res_a.rag_recall_at_k == 1.0

    # Case B: Answer contains unverified/unsupported claim
    resp_b = {
        "status": "COMPLETED",
        "route": "documents",
        "executive_conclusion": "Carrier Logistics X guarantees delivery within 2 business days. Unverified rumor claims carrier is closing operations next month.",
        "citations": ["carrier_logistics_x_sla_contract_2025.md#p1"],
    }
    res_b = engine.evaluate_case(case, resp_b)
    assert res_b.groundedness < 1.0
    assert res_b.unsupported_claim_count >= 1

    # Case C: Answer with fabricated citation string
    resp_c = {
        "status": "COMPLETED",
        "route": "documents",
        "executive_conclusion": "Carrier Logistics X guarantees delivery within 2 business days under SLA clause 4.1.",
        "citations": ["FABRICATED_DOC_999.md#p99"],
    }
    res_c = engine.evaluate_case(case, resp_c)
    assert res_c.citation_coverage < 1.0 or res_c.rag_recall_at_k < 1.0

    # Case D: Wrong retrieved document ID
    resp_d = {
        "status": "COMPLETED",
        "route": "documents",
        "executive_conclusion": "Carrier Logistics X guarantees delivery within 2 business days.",
        "citations": ["wrong_unrelated_file.md#p1"],
    }
    res_d = engine.evaluate_case(case, resp_d)
    assert res_d.rag_recall_at_k == 0.0

    # Case E: Critic A/B delta comparison
    experiment = CriticABExperiment(engine)
    ab_summary = experiment.run_ab_experiment([case], is_mock=True)
    assert ab_summary.critic_enabled_groundedness > ab_summary.critic_disabled_groundedness
    assert ab_summary.groundedness_delta > 0.0


def test_cost_calculator():
    """Verifies LLM token usage cost calculation."""
    calc = CostCalculator(input_price_per_1k=0.00015, output_price_per_1k=0.0006)
    cost = calc.calculate_cost(1000, 1000)
    assert cost == 0.00075


def test_benchmark_runner_artifact_export(tmp_path):
    """Verifies full benchmark runner execution and JSON/CSV/MD artifact generation."""
    out_dir = str(tmp_path / "test_results")
    runner = BenchmarkRunner(output_dir=out_dir)
    res = runner.run_benchmark(is_mock=True)

    assert res["total_cases"] == 30
    assert res["task_success_rate"] == 1.0

    assert os.path.exists(os.path.join(out_dir, "benchmark_results.json"))
    assert os.path.exists(os.path.join(out_dir, "benchmark_results.csv"))
    assert os.path.exists(os.path.join(out_dir, "benchmark_report.md"))
