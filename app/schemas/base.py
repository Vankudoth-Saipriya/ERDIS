"""
Pydantic Base Model Schemas
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base Pydantic schema with standard configuration."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
    )


class TimestampedSchema(BaseSchema):
    """Base schema for resources containing timestamp metadata."""
    created_at: datetime
