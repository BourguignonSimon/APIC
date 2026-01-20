"""
Migration Utilities Module
Provides utilities for Alembic database migrations.
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from io import StringIO

logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent


def get_migration_tables() -> List[str]:
    """
    Get list of tables that would be created by migrations.

    Returns:
        List of table names defined in migrations
    """
    tables = []

    versions_dir = PROJECT_ROOT / "alembic" / "versions"
    if not versions_dir.exists():
        return tables

    # Parse migration files to find table creations
    for migration_file in versions_dir.glob("*.py"):
        content = migration_file.read_text()
        # Look for op.create_table calls
        import re

        matches = re.findall(r'op\.create_table\(\s*["\'](\w+)["\']', content)
        tables.extend(matches)

    return list(set(tables))


def generate_offline_sql() -> str:
    """
    Generate offline SQL for migrations without database connection.

    Returns:
        SQL string for creating tables
    """
    # This generates SQL that would be executed
    sql_statements = []

    # Read migration files and extract SQL
    versions_dir = PROJECT_ROOT / "alembic" / "versions"
    if not versions_dir.exists():
        return ""

    # Generate CREATE TABLE statements from our known schema
    sql_statements.append("""
-- APIC Database Schema
-- Generated from Alembic migrations

CREATE TABLE IF NOT EXISTS projects (
    id VARCHAR(36) PRIMARY KEY,
    client_name VARCHAR(255) NOT NULL,
    project_name VARCHAR(255) NOT NULL,
    description TEXT,
    target_departments JSON DEFAULT '[]',
    status VARCHAR(50) DEFAULT 'created',
    vector_namespace VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_projects_id ON projects(id);
CREATE INDEX IF NOT EXISTS ix_projects_status ON projects(status);

CREATE TABLE IF NOT EXISTS project_states (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) UNIQUE NOT NULL,
    thread_id VARCHAR(36) UNIQUE NOT NULL,
    state_data JSON NOT NULL,
    current_node VARCHAR(50) NOT NULL DEFAULT 'start',
    is_suspended BOOLEAN DEFAULT FALSE,
    suspension_reason VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_project_states_project_id ON project_states(project_id);
CREATE INDEX IF NOT EXISTS ix_project_states_thread_id ON project_states(thread_id);
CREATE INDEX IF NOT EXISTS ix_project_states_is_suspended ON project_states(is_suspended);

CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size VARCHAR(50) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    chunk_count VARCHAR(50) DEFAULT '0',
    processed BOOLEAN DEFAULT FALSE,
    content_summary TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_documents_project_id ON documents(project_id);
CREATE INDEX IF NOT EXISTS ix_documents_processed ON documents(processed);

-- Foreign Key Constraints
ALTER TABLE project_states ADD CONSTRAINT fk_project_states_project_id
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;

ALTER TABLE documents ADD CONSTRAINT fk_documents_project_id
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
""")

    return "\n".join(sql_statements)


def run_migration_upgrade(target: str = "head") -> Dict[str, Any]:
    """
    Run database migration upgrade.

    Args:
        target: Migration target (default: "head" for latest)

    Returns:
        Dictionary with migration result
    """
    result = {
        "success": False,
        "target": target,
        "error": None,
    }

    try:
        from alembic import command
        from alembic.config import Config

        # Get alembic config
        alembic_ini = PROJECT_ROOT / "alembic.ini"
        if not alembic_ini.exists():
            result["error"] = "alembic.ini not found"
            return result

        alembic_cfg = Config(str(alembic_ini))

        # Run upgrade
        command.upgrade(alembic_cfg, target)
        result["success"] = True
        logger.info(f"Migration upgraded to {target}")

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Migration upgrade failed: {e}")

    return result


def run_migration_downgrade(target: str = "base") -> Dict[str, Any]:
    """
    Run database migration downgrade.

    Args:
        target: Migration target (default: "base" for initial state)

    Returns:
        Dictionary with migration result
    """
    result = {
        "success": False,
        "target": target,
        "error": None,
    }

    try:
        from alembic import command
        from alembic.config import Config

        # Get alembic config
        alembic_ini = PROJECT_ROOT / "alembic.ini"
        if not alembic_ini.exists():
            result["error"] = "alembic.ini not found"
            return result

        alembic_cfg = Config(str(alembic_ini))

        # Run downgrade
        command.downgrade(alembic_cfg, target)
        result["success"] = True
        logger.info(f"Migration downgraded to {target}")

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Migration downgrade failed: {e}")

    return result


def get_current_revision() -> Optional[str]:
    """
    Get current database revision.

    Returns:
        Current revision ID or None
    """
    try:
        from alembic import command
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        from alembic.runtime.migration import MigrationContext
        from sqlalchemy import create_engine

        from config.settings import settings

        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            return context.get_current_revision()

    except Exception as e:
        logger.error(f"Failed to get current revision: {e}")
        return None


def get_pending_migrations() -> List[str]:
    """
    Get list of pending migrations.

    Returns:
        List of pending revision IDs
    """
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        from alembic.runtime.migration import MigrationContext
        from sqlalchemy import create_engine

        from config.settings import settings

        alembic_ini = PROJECT_ROOT / "alembic.ini"
        alembic_cfg = Config(str(alembic_ini))

        script = ScriptDirectory.from_config(alembic_cfg)
        engine = create_engine(settings.DATABASE_URL)

        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            current = context.get_current_revision()

        pending = []
        for revision in script.walk_revisions():
            if current is None or revision.revision != current:
                pending.append(revision.revision)
            if revision.revision == current:
                break

        return pending

    except Exception as e:
        logger.error(f"Failed to get pending migrations: {e}")
        return []
