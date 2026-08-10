"""
Task ORM Model for ERDIS State & Decision Intelligence Persistence.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Boolean, Float, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.evidence import EvidenceModel
    from app.models.log import ToolExecutionLogModel


class TaskModel(Base):
    """
    SQLAlchemy ORM Model representing an enterprise task record in PostgreSQL.
    """
    __tablename__ = "tasks"

    task_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    route: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    executive_conclusion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    key_findings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    root_cause_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    business_impact_usd: Mapped[float] = mapped_column(Float, default=0.0)
    recommended_actions: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    model_inferences_and_assumptions: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    citations: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    financial_impact_usd: Mapped[float] = mapped_column(Float, default=0.0)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    approval_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    execution_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    node_trajectory: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    tool_call_count: Mapped[int] = mapped_column(Float, default=0)
    token_usage: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    errors: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
