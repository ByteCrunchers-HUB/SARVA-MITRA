"""
Health check and system status router.
"""

from datetime import datetime, timezone
from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Check backend health status")
async def health_check():
    """
    Returns the operating status of the centralized FastAPI backend.
    """
    return {
        "status": "healthy",
        "service": "Smart Agriculture Monitoring System Backend",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
