"""
Evaluation Run ORM Model
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class EvalRunModel(Base):
    __tablename__ = "eval_runs"

    eval_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    scenario_id: Mapped[str] = mapped_column(String(100), nullable=False)
    groundedness_score: Mapped[float] = mapped_column(Numeric(4, 3), nullable=True)
    sql_accuracy_score: Mapped[float] = mapped_column(Numeric(4, 3), nullable=True)
    citation_recall: Mapped[float] = mapped_column(Numeric(4, 3), nullable=True)
    latency_seconds: Mapped[float] = mapped_column(Numeric(6, 2), nullable=True)
    cost_usd: Mapped[float] = mapped_column(Numeric(6, 4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
