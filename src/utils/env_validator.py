"""
Environment Validation Module
Validates required environment variables on startup.
"""

import os
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class EnvironmentValidationError(Exception):
    """Raised when environment validation fails."""

    def __init__(self, message: str, missing_vars: Optional[List[str]] = None):
        self.message = message
        self.missing_vars = missing_vars or []
        super().__init__(self.message)


# LLM provider to API key mapping
LLM_PROVIDER_KEYS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
}


def validate_environment(strict: bool = False) -> Dict[str, Any]:
    """
    Validate required environment variables.

    Args:
        strict: If True, raise exception on validation failure

    Returns:
        Dictionary with validation results

    Raises:
        EnvironmentValidationError: If strict=True and validation fails
    """
    result = {
        "valid": True,
        "database_configured": False,
        "llm_provider": None,
        "vector_db_configured": False,
        "warnings": [],
        "errors": [],
    }

    # Check DATABASE_URL
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        result["database_configured"] = True
    else:
        result["errors"].append("DATABASE_URL is not set")
        result["valid"] = False
        if strict:
            raise EnvironmentValidationError(
                "DATABASE_URL environment variable is required",
                missing_vars=["DATABASE_URL"],
            )

    # Check LLM provider and corresponding API key
    llm_provider = os.environ.get("DEFAULT_LLM_PROVIDER", "openai")
    result["llm_provider"] = llm_provider

    required_key = LLM_PROVIDER_KEYS.get(llm_provider)
    if required_key:
        api_key = os.environ.get(required_key)
        if not api_key:
            result["errors"].append(f"{required_key} is required for provider '{llm_provider}'")
            result["valid"] = False
            if strict:
                raise EnvironmentValidationError(
                    f"{required_key} is required when using {llm_provider} as LLM provider",
                    missing_vars=[required_key],
                )

    # Check optional Pinecone configuration
    pinecone_key = os.environ.get("PINECONE_API_KEY")
    if pinecone_key:
        result["vector_db_configured"] = True
    else:
        result["warnings"].append("PINECONE_API_KEY not set - vector database features will be limited")

    return result


def get_validation_report() -> Dict[str, Any]:
    """
    Generate a comprehensive validation report.

    Returns:
        Dictionary containing status and list of checks
    """
    checks = []

    # Python version check
    import sys

    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    checks.append({
        "name": "Python Version",
        "status": "pass" if sys.version_info >= (3, 11) else "warn",
        "value": python_version,
        "message": "Python 3.11+ recommended" if sys.version_info < (3, 11) else "OK",
    })

    # Database URL check
    database_url = os.environ.get("DATABASE_URL")
    checks.append({
        "name": "DATABASE_URL",
        "status": "pass" if database_url else "fail",
        "value": "***" if database_url else "Not set",
        "message": "OK" if database_url else "Required",
    })

    # LLM Provider check
    llm_provider = os.environ.get("DEFAULT_LLM_PROVIDER", "openai")
    required_key = LLM_PROVIDER_KEYS.get(llm_provider)
    api_key = os.environ.get(required_key) if required_key else None
    checks.append({
        "name": f"LLM Provider ({llm_provider})",
        "status": "pass" if api_key else "fail",
        "value": "***" if api_key else "Not set",
        "message": "OK" if api_key else f"{required_key} required",
    })

    # Pinecone check
    pinecone_key = os.environ.get("PINECONE_API_KEY")
    checks.append({
        "name": "PINECONE_API_KEY",
        "status": "pass" if pinecone_key else "warn",
        "value": "***" if pinecone_key else "Not set",
        "message": "OK" if pinecone_key else "Optional - vector DB disabled",
    })

    # Determine overall status
    has_failures = any(c["status"] == "fail" for c in checks)
    has_warnings = any(c["status"] == "warn" for c in checks)

    if has_failures:
        status = "fail"
    elif has_warnings:
        status = "warn"
    else:
        status = "pass"

    return {
        "status": status,
        "checks": checks,
    }
