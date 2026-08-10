"""
Unit Tests for ERDIS Streamlit Portfolio Demo Dashboard (Phase 9).
Verifies app.dashboard module structure, API client configuration, and status handlers.
"""

import pytest
import os
from app.dashboard import API_BASE_URL, check_api_status


def test_dashboard_api_config():
    """Verifies API client base URL configuration."""
    assert API_BASE_URL is not None
    assert "localhost" in API_BASE_URL or "http" in API_BASE_URL


def test_dashboard_api_status_check():
    """Verifies API status probe returns valid status string and readiness dictionary."""
    status_str, data = check_api_status()
    assert status_str in {"ONLINE", "OFFLINE"}
    assert isinstance(data, dict)
