"""
Central API Router Assembly for ERDIS (v1).
Assembles health, readiness, and tasks endpoints under /api/v1.
"""

from fastapi import APIRouter
from app.api.v1 import health, tasks

api_router = APIRouter()

# Include v1 endpoints
api_router.include_router(health.router, prefix="/v1")
api_router.include_router(tasks.router, prefix="/v1")
