"""
Health Check API Routes
Provides comprehensive health check endpoints for APIC.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Response, status

from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()


def check_database_health() -> Dict[str, Any]:
    """
    Check database health status.

    Returns:
        Dictionary with database health information
    """
    try:
        from src.utils.db_health import check_database_health as db_check
        return db_check()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e),
        }


@router.get("/health")
async def health_check(response: Response) -> Dict[str, Any]:
    """
    Comprehensive health check endpoint.

    Returns:
        Health status including database connectivity
    """
    # Check database
    db_health = check_database_health()

    # Determine overall status
    if db_health.get("connected", False):
        overall_status = "healthy"
        response.status_code = status.HTTP_200_OK
    else:
        overall_status = "unhealthy"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": overall_status,
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": {
            "connected": db_health.get("connected", False),
            "status": db_health.get("status", "unknown"),
            "latency_ms": db_health.get("latency_ms"),
            "error": db_health.get("error"),
        },
    }


@router.get("/health/live")
async def liveness_check() -> Dict[str, str]:
    """
    Kubernetes liveness probe endpoint.

    Returns:
        Simple alive status
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_check(response: Response) -> Dict[str, Any]:
    """
    Kubernetes readiness probe endpoint.

    Returns:
        Readiness status with dependency checks
    """
    db_health = check_database_health()

    is_ready = db_health.get("connected", False)

    if is_ready:
        response.status_code = status.HTTP_200_OK
        return {"status": "ready", "database": "connected"}
    else:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "database": "disconnected",
            "error": db_health.get("error"),
        }


@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check with all system information.

    Returns:
        Comprehensive system health information
    """
    import sys
    from pathlib import Path

    # Database check
    db_health = check_database_health()

    # Environment check
    try:
        from src.utils.env_validator import get_validation_report
        env_report = get_validation_report()
    except Exception as e:
        env_report = {"status": "error", "error": str(e)}

    # Installation check
    try:
        from src.utils.install_verifier import verify_installation
        install_status = verify_installation()
    except Exception as e:
        install_status = {"overall_status": "error", "error": str(e)}

    return {
        "service": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
        },
        "runtime": {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": sys.platform,
        },
        "database": db_health,
        "environment": env_report,
        "installation": install_status,
        "llm_provider": settings.DEFAULT_LLM_PROVIDER,
    }
