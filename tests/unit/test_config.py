"""
Unit Tests for Configuration Settings
"""

from app.core.config import settings


def test_settings_load_defaults():
    assert settings.APP_NAME == "ERDIS"
    assert settings.POSTGRES_PORT == 5432
    assert settings.MAX_CRITIC_LOOPS == 2
    assert settings.MAX_TOOL_CALLS_PER_RUN == 10
    assert settings.MAX_TOKEN_BUDGET_PER_RUN == 60000


def test_database_url_property():
    assert "postgresql+asyncpg://" in settings.database_url_async
    assert "postgresql+psycopg2://" in settings.database_url_sync
