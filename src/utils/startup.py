"""
Startup Utilities Module
Handles application startup checks and validation.
"""

import logging
from typing import Dict, Any

from src.utils.env_validator import validate_environment
from src.utils.db_health import check_database_health

logger = logging.getLogger(__name__)


class StartupError(Exception):
    """Raised when startup checks fail."""

    def __init__(self, message: str, check_name: str = None):
        self.message = message
        self.check_name = check_name
        super().__init__(self.message)


def run_startup_checks(strict: bool = False) -> Dict[str, Any]:
    """
    Run all startup checks.

    Args:
        strict: If True, raise exception on failure

    Returns:
        Dictionary with check results

    Raises:
        StartupError: If strict=True and checks fail
    """
    result = {
        "environment_valid": False,
        "database_healthy": False,
        "all_checks_passed": False,
        "errors": [],
    }

    # Environment validation
    try:
        env_result = validate_environment()
        result["environment_valid"] = env_result.get("valid", False)
        if not result["environment_valid"]:
            result["errors"].extend(env_result.get("errors", []))
    except Exception as e:
        result["errors"].append(f"Environment validation error: {str(e)}")
        if strict:
            raise StartupError(str(e), "environment_validation")

    # Database health check
    try:
        db_result = check_database_health()
        result["database_healthy"] = db_result.get("status") == "healthy"
        if not result["database_healthy"]:
            error = db_result.get("error", "Database unhealthy")
            result["errors"].append(f"Database check: {error}")
    except Exception as e:
        result["errors"].append(f"Database check error: {str(e)}")
        # Database might not be required for all operations
        logger.warning(f"Database health check skipped: {e}")

    # Determine overall status
    result["all_checks_passed"] = (
        result["environment_valid"] and
        result["database_healthy"]
    )

    if strict and not result["all_checks_passed"]:
        raise StartupError(
            f"Startup checks failed: {'; '.join(result['errors'])}",
            "startup_checks",
        )

    return result


def log_startup_info() -> None:
    """Log startup information."""
    from config.settings import settings

    logger.info("=" * 60)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"LLM Provider: {settings.DEFAULT_LLM_PROVIDER}")
    logger.info("=" * 60)


def run_safe_startup() -> Dict[str, Any]:
    """
    Run startup with graceful error handling.

    Returns:
        Dictionary with startup status
    """
    result = {
        "started": False,
        "warnings": [],
        "errors": [],
    }

    try:
        log_startup_info()
        checks = run_startup_checks(strict=False)

        if checks["all_checks_passed"]:
            result["started"] = True
            logger.info("All startup checks passed")
        else:
            # Start with warnings
            result["started"] = True
            result["warnings"] = checks["errors"]
            logger.warning(f"Started with warnings: {checks['errors']}")

    except StartupError as e:
        result["errors"].append(str(e))
        logger.error(f"Startup failed: {e}")

    except Exception as e:
        result["errors"].append(str(e))
        logger.error(f"Unexpected startup error: {e}")

    return result
