"""
Unit Tests for ERDIS Streamlit Portfolio Demo Dashboard (Phase 9 & 10).
Verifies app.dashboard module structure, API client configuration, dynamic response mapping, and mode handling.
"""

import pytest
import os
from app.dashboard import (
    API_BASE_URL,
    check_api_status,
    check_backend_status,
    generate_dynamic_demo_task,
)


def test_dashboard_api_config():
    """Verifies API client base URL configuration."""
    assert API_BASE_URL is not None
    assert "localhost" in API_BASE_URL or "http" in API_BASE_URL


def test_dashboard_api_status_check():
    """Verifies API status probe returns valid status string and readiness dictionary."""
    status_str, data = check_api_status()
    assert status_str in {"ONLINE", "OFFLINE"}
    assert isinstance(data, dict)


def test_dynamic_demo_task_refund_query():
    """Verifies refund query generates Midwest refund specific demo data."""
    task = generate_dynamic_demo_task("What is the total Midwest customer refund payout amount?")
    assert task["route"] == "sql_only"
    assert "42,500" in task["executive_conclusion"]
    assert task["financial_impact_usd"] == 42500.0
    assert len(task["sql_evidence"]) == 1
    assert len(task["document_evidence"]) == 0


def test_dynamic_demo_task_sla_query():
    """Verifies SLA query generates carrier SLA breach specific demo data."""
    task = generate_dynamic_demo_task("Did the carrier breach its delivery SLA?")
    assert task["route"] == "document_only"
    assert "Section 4.1 delivery SLA" in task["executive_conclusion"]
    assert task["financial_impact_usd"] == 50000.0
    assert len(task["sql_evidence"]) == 0
    assert len(task["document_evidence"]) == 1


def test_dynamic_demo_task_sorter_query():
    """Verifies sorter outage query generates high financial impact HITL demo data."""
    task = generate_dynamic_demo_task("What caused the automated sorter outage?")
    assert task["route"] == "both"
    assert task["status"] == "WAITING_FOR_APPROVAL"
    assert task["financial_impact_usd"] == 142500.0
    assert len(task["sql_evidence"]) == 1
    assert len(task["document_evidence"]) == 1


def test_dynamic_demo_task_uniqueness():
    """Verifies different questions generate distinct task IDs, routes, conclusions, and evidence."""
    t1 = generate_dynamic_demo_task("What is the total Midwest customer refund payout amount?")
    t2 = generate_dynamic_demo_task("Did the carrier breach its delivery SLA?")

    assert t1["task_id"] != t2["task_id"]
    assert t1["route"] != t2["route"]
    assert t1["executive_conclusion"] != t2["executive_conclusion"]
    assert t1["key_findings"] != t2["key_findings"]
    assert t1["recommended_actions"] != t2["recommended_actions"]
    assert t1["financial_impact_usd"] != t2["financial_impact_usd"]
    assert t1["sql_evidence"] != t2["sql_evidence"]
    assert t1["document_evidence"] != t2["document_evidence"]
