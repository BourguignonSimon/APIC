"""
Database Health Check Module
Provides health check functionality for PostgreSQL database.
"""

import logging
from typing import Dict, Any, List

from sqlalchemy import create_engine, text, inspect

logger = logging.getLogger(__name__)

# Required tables for APIC
REQUIRED_TABLES = ["projects", "project_states", "documents"]


def check_database_health(database_url: str = None) -> Dict[str, Any]:
    """
    Check database connectivity and health.

    Args:
        database_url: Database connection string (uses settings if not provided)

    Returns:
        Dictionary with health status
    """
    if database_url is None:
        from config.settings import settings
        database_url = settings.DATABASE_URL

    result = {
        "status": "healthy",
        "connected": False,
        "error": None,
        "latency_ms": None,
    }

    try:
        import time

        engine = create_engine(database_url)
        start = time.time()

        with engine.connect() as conn:
            # Simple query to check connectivity
            conn.execute(text("SELECT 1")).scalar()
            result["connected"] = True
            result["latency_ms"] = round((time.time() - start) * 1000, 2)

    except Exception as e:
        result["status"] = "unhealthy"
        result["connected"] = False
        result["error"] = str(e)
        logger.error(f"Database health check failed: {e}")

    return result


def check_database_tables(database_url: str = None) -> Dict[str, Any]:
    """
    Check if required database tables exist.

    Args:
        database_url: Database connection string (uses settings if not provided)

    Returns:
        Dictionary with table status
    """
    if database_url is None:
        from config.settings import settings
        database_url = settings.DATABASE_URL

    result = {
        "all_tables_exist": False,
        "existing_tables": [],
        "missing_tables": [],
        "error": None,
    }

    try:
        engine = create_engine(database_url)

        with engine.connect() as conn:
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            result["existing_tables"] = existing_tables

            missing = [t for t in REQUIRED_TABLES if t not in existing_tables]
            result["missing_tables"] = missing
            result["all_tables_exist"] = len(missing) == 0

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Database table check failed: {e}")

    return result


def get_database_info(database_url: str = None) -> Dict[str, Any]:
    """
    Get comprehensive database information.

    Args:
        database_url: Database connection string (uses settings if not provided)

    Returns:
        Dictionary with database information
    """
    if database_url is None:
        from config.settings import settings
        database_url = settings.DATABASE_URL

    result = {
        "connected": False,
        "version": None,
        "database_name": None,
        "tables": [],
        "error": None,
    }

    try:
        engine = create_engine(database_url)

        with engine.connect() as conn:
            # Get PostgreSQL version
            version = conn.execute(text("SELECT version()")).scalar()
            result["version"] = version

            # Get database name
            db_name = conn.execute(text("SELECT current_database()")).scalar()
            result["database_name"] = db_name

            # Get tables
            inspector = inspect(engine)
            result["tables"] = inspector.get_table_names()
            result["connected"] = True

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Failed to get database info: {e}")

    return result
