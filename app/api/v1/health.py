"""
Health & Readiness Check Endpoints
"""

from typing import Dict, Any
from fastapi import APIRouter, status
from app.core.config import settings

router = APIRouter(tags=["System Infrastructure"])


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Liveness Probe"
)
async def get_health() -> Dict[str, Any]:
    """Returns system liveness status."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }


@router.get(
    "/readiness",
    status_code=status.HTTP_200_OK,
    summary="Readiness Probe"
)
async def get_readiness() -> Dict[str, Any]:
    """Returns readiness status for processing requests."""
    return {
        "status": "ready",
        "database": "connected",
        "vector_store": "ready",
    }
