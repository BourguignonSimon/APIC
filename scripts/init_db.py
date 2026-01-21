#!/usr/bin/env python3
"""
APIC Database Initialization Script.
Initializes the PostgreSQL database with required schema.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.install_utils import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_env_file():
    """Load environment variables from .env file."""
    env_path = project_root / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())


def init_database(reset: bool = False) -> bool:
    """
    Initialize the database with required schema.

    Args:
        reset: If True, drop and recreate tables.

    Returns:
        bool: True if successful.
    """
    load_env_file()

    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/apic"
    )

    logger.info(f"Initializing database...")

    db_manager = DatabaseManager(database_url=database_url)

    # Validate connection URL
    if not db_manager.validate_connection_url():
        logger.error("Invalid database URL")
        return False

    parsed = db_manager.parse_connection_url()
    logger.info(f"Connecting to {parsed['host']}:{parsed['port']}/{parsed['database']}")

    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

        # Connect to database
        conn = psycopg2.connect(
            host=parsed["host"],
            port=parsed["port"],
            user=parsed["user"],
            password=parsed["password"],
            database=parsed["database"],
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        if reset:
            logger.warning("Resetting database - dropping existing tables...")
            cursor.execute("DROP TABLE IF EXISTS documents CASCADE;")
            cursor.execute("DROP TABLE IF EXISTS project_states CASCADE;")
            cursor.execute("DROP TABLE IF EXISTS projects CASCADE;")
            logger.info("Tables dropped")

        # Read and execute init SQL
        sql_path = Path(__file__).parent / "init_schema.sql"
        if sql_path.exists():
            with open(sql_path) as f:
                sql_content = f.read()
            cursor.execute(sql_content)
            logger.info("Schema initialized from init_schema.sql")
        else:
            # Use generated SQL
            init_sql = db_manager.generate_init_sql()
            cursor.execute(init_sql)
            logger.info("Schema initialized from generated SQL")

        cursor.close()
        conn.close()

        logger.info("Database initialization complete!")
        return True

    except ImportError:
        logger.error("psycopg2 not installed. Run: pip install psycopg2-binary")
        return False
    except psycopg2.OperationalError as e:
        logger.error(f"Could not connect to database: {e}")
        logger.info("Make sure PostgreSQL is running and credentials are correct")
        return False
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


def check_tables_exist() -> bool:
    """Check if required tables exist."""
    load_env_file()

    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/apic"
    )

    db_manager = DatabaseManager(database_url=database_url)
    parsed = db_manager.parse_connection_url()

    try:
        import psycopg2

        conn = psycopg2.connect(
            host=parsed["host"],
            port=parsed["port"],
            user=parsed["user"],
            password=parsed["password"],
            database=parsed["database"],
        )
        cursor = conn.cursor()

        # Check for required tables
        required_tables = ["projects", "project_states", "documents"]

        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        existing_tables = {row[0] for row in cursor.fetchall()}

        cursor.close()
        conn.close()

        missing = set(required_tables) - existing_tables
        if missing:
            logger.warning(f"Missing tables: {missing}")
            return False

        logger.info("All required tables exist")
        return True

    except Exception as e:
        logger.error(f"Could not check tables: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="APIC Database Initialization"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset database (drop and recreate tables)"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if tables exist"
    )

    args = parser.parse_args()

    if args.check:
        success = check_tables_exist()
        sys.exit(0 if success else 1)
    else:
        success = init_database(reset=args.reset)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
