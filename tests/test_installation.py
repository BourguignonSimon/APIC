"""
Test Suite for Installation Automation
Tests the automated installation process including:
- Database migrations with Alembic
- Environment validation
- Installation verification
- Database health checks
"""

import os
import sys
import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestEnvironmentValidation:
    """Tests for environment variable validation on startup."""

    def test_validate_required_env_vars_success(self):
        """Test that validation passes with all required env vars."""
        from src.utils.env_validator import validate_environment, EnvironmentValidationError

        # Mock environment with all required variables
        mock_env = {
            "DATABASE_URL": "postgresql://user:pass@localhost:5432/db",
            "DEFAULT_LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "test-key",
        }

        with patch.dict(os.environ, mock_env, clear=True):
            # Should not raise
            result = validate_environment()
            assert result["valid"] is True
            assert result["database_configured"] is True

    def test_validate_missing_database_url(self):
        """Test that validation fails without DATABASE_URL."""
        from src.utils.env_validator import validate_environment, EnvironmentValidationError

        mock_env = {
            "DEFAULT_LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "test-key",
        }

        with patch.dict(os.environ, mock_env, clear=True):
            with pytest.raises(EnvironmentValidationError) as exc_info:
                validate_environment(strict=True)
            assert "DATABASE_URL" in str(exc_info.value)

    def test_validate_llm_provider_with_key(self):
        """Test that selected LLM provider has corresponding API key."""
        from src.utils.env_validator import validate_environment, EnvironmentValidationError

        # OpenAI provider without OpenAI key
        mock_env = {
            "DATABASE_URL": "postgresql://localhost:5432/db",
            "DEFAULT_LLM_PROVIDER": "openai",
            # Missing OPENAI_API_KEY
        }

        with patch.dict(os.environ, mock_env, clear=True):
            with pytest.raises(EnvironmentValidationError) as exc_info:
                validate_environment(strict=True)
            assert "OPENAI_API_KEY" in str(exc_info.value)

    def test_validate_anthropic_provider(self):
        """Test validation for Anthropic provider."""
        from src.utils.env_validator import validate_environment

        mock_env = {
            "DATABASE_URL": "postgresql://localhost:5432/db",
            "DEFAULT_LLM_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "test-anthropic-key",
        }

        with patch.dict(os.environ, mock_env, clear=True):
            result = validate_environment()
            assert result["valid"] is True
            assert result["llm_provider"] == "anthropic"

    def test_validate_google_provider(self):
        """Test validation for Google provider."""
        from src.utils.env_validator import validate_environment

        mock_env = {
            "DATABASE_URL": "postgresql://localhost:5432/db",
            "DEFAULT_LLM_PROVIDER": "google",
            "GOOGLE_API_KEY": "test-google-key",
        }

        with patch.dict(os.environ, mock_env, clear=True):
            result = validate_environment()
            assert result["valid"] is True
            assert result["llm_provider"] == "google"

    def test_validate_with_optional_pinecone(self):
        """Test validation with optional Pinecone configuration."""
        from src.utils.env_validator import validate_environment

        mock_env = {
            "DATABASE_URL": "postgresql://localhost:5432/db",
            "DEFAULT_LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "test-key",
            "PINECONE_API_KEY": "pinecone-key",
        }

        with patch.dict(os.environ, mock_env, clear=True):
            result = validate_environment()
            assert result["valid"] is True
            assert result["vector_db_configured"] is True

    def test_get_validation_report(self):
        """Test generation of validation report."""
        from src.utils.env_validator import get_validation_report

        mock_env = {
            "DATABASE_URL": "postgresql://localhost:5432/db",
            "DEFAULT_LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "test-key",
        }

        with patch.dict(os.environ, mock_env, clear=True):
            report = get_validation_report()
            assert "status" in report
            assert "checks" in report
            assert isinstance(report["checks"], list)


class TestDatabaseMigrations:
    """Tests for Alembic database migrations."""

    def test_alembic_config_exists(self):
        """Test that alembic.ini configuration file exists."""
        alembic_ini = Path(__file__).parent.parent / "alembic.ini"
        assert alembic_ini.exists(), "alembic.ini should exist"

    def test_alembic_migrations_directory_exists(self):
        """Test that migrations directory exists."""
        migrations_dir = Path(__file__).parent.parent / "alembic"
        assert migrations_dir.exists(), "alembic/ directory should exist"
        assert (migrations_dir / "versions").exists(), "alembic/versions/ should exist"

    def test_alembic_env_file_exists(self):
        """Test that alembic env.py exists and is configured."""
        alembic_env = Path(__file__).parent.parent / "alembic" / "env.py"
        assert alembic_env.exists(), "alembic/env.py should exist"

    def test_initial_migration_exists(self):
        """Test that initial migration script exists."""
        versions_dir = Path(__file__).parent.parent / "alembic" / "versions"
        migrations = list(versions_dir.glob("*_initial_schema.py"))
        assert len(migrations) >= 1, "Initial migration should exist"

    def test_migration_creates_all_tables(self):
        """Test that migration creates all required tables."""
        from src.utils.migration_utils import get_migration_tables

        tables = get_migration_tables()
        required_tables = ["projects", "project_states", "documents"]

        for table in required_tables:
            assert table in tables, f"Migration should create {table} table"

    def test_migration_can_be_run_offline(self):
        """Test that migration can generate offline SQL."""
        from src.utils.migration_utils import generate_offline_sql

        sql = generate_offline_sql()
        assert "CREATE TABLE" in sql
        assert "projects" in sql.lower()


class TestDatabaseHealthCheck:
    """Tests for database health check functionality."""

    def test_health_check_success(self):
        """Test database health check returns success when DB is accessible."""
        from src.utils.db_health import check_database_health

        with patch("src.utils.db_health.create_engine") as mock_engine:
            mock_conn = MagicMock()
            mock_engine.return_value.connect.return_value.__enter__ = MagicMock(
                return_value=mock_conn
            )
            mock_engine.return_value.connect.return_value.__exit__ = MagicMock(
                return_value=None
            )
            mock_conn.execute.return_value.scalar.return_value = 1

            result = check_database_health()
            assert result["status"] == "healthy"
            assert result["connected"] is True

    def test_health_check_failure(self):
        """Test database health check returns failure when DB is inaccessible."""
        from src.utils.db_health import check_database_health

        with patch("src.utils.db_health.create_engine") as mock_engine:
            mock_engine.return_value.connect.side_effect = Exception("Connection refused")

            result = check_database_health()
            assert result["status"] == "unhealthy"
            assert result["connected"] is False
            assert "error" in result

    def test_health_check_tables_exist(self):
        """Test database health check verifies required tables exist."""
        from src.utils.db_health import check_database_tables

        with patch("src.utils.db_health.create_engine") as mock_engine:
            mock_conn = MagicMock()
            mock_engine.return_value.connect.return_value.__enter__ = MagicMock(
                return_value=mock_conn
            )
            mock_engine.return_value.connect.return_value.__exit__ = MagicMock(
                return_value=None
            )
            # Mock inspector
            with patch("src.utils.db_health.inspect") as mock_inspect:
                mock_inspect.return_value.get_table_names.return_value = [
                    "projects",
                    "project_states",
                    "documents",
                ]

                result = check_database_tables()
                assert result["all_tables_exist"] is True
                assert "projects" in result["existing_tables"]


class TestInstallationVerification:
    """Tests for installation verification script."""

    def test_verify_python_version(self):
        """Test Python version verification."""
        from src.utils.install_verifier import verify_python_version

        result = verify_python_version()
        assert result["valid"] is True
        assert result["version"] == f"{sys.version_info.major}.{sys.version_info.minor}"

    def test_verify_required_packages(self):
        """Test that required packages are installed."""
        from src.utils.install_verifier import verify_required_packages

        result = verify_required_packages()
        assert result["valid"] is True
        assert "fastapi" in result["installed_packages"]
        assert "sqlalchemy" in result["installed_packages"]

    def test_verify_directory_structure(self):
        """Test that required directories exist."""
        from src.utils.install_verifier import verify_directory_structure

        result = verify_directory_structure()
        assert result["valid"] is True
        assert "src" in result["directories"]
        assert "config" in result["directories"]

    def test_verify_configuration_files(self):
        """Test that configuration files exist."""
        from src.utils.install_verifier import verify_configuration_files

        result = verify_configuration_files()
        assert "requirements.txt" in result["files"]
        assert "alembic.ini" in result["files"]

    def test_full_installation_verification(self):
        """Test complete installation verification."""
        from src.utils.install_verifier import verify_installation

        result = verify_installation()
        assert "python" in result
        assert "packages" in result
        assert "directories" in result
        assert "configuration" in result
        assert "overall_status" in result


class TestMakefile:
    """Tests for Makefile automation."""

    def test_makefile_exists(self):
        """Test that Makefile exists."""
        makefile = Path(__file__).parent.parent / "Makefile"
        assert makefile.exists(), "Makefile should exist"

    def test_makefile_has_install_target(self):
        """Test that Makefile has install target."""
        makefile = Path(__file__).parent.parent / "Makefile"
        content = makefile.read_text()
        assert "install:" in content, "Makefile should have install target"

    def test_makefile_has_test_target(self):
        """Test that Makefile has test target."""
        makefile = Path(__file__).parent.parent / "Makefile"
        content = makefile.read_text()
        assert "test:" in content, "Makefile should have test target"

    def test_makefile_has_migrate_target(self):
        """Test that Makefile has migrate target."""
        makefile = Path(__file__).parent.parent / "Makefile"
        content = makefile.read_text()
        assert "migrate:" in content, "Makefile should have migrate target"

    def test_makefile_has_docker_target(self):
        """Test that Makefile has docker target."""
        makefile = Path(__file__).parent.parent / "Makefile"
        content = makefile.read_text()
        assert "docker-up:" in content or "docker:" in content, "Makefile should have docker target"

    def test_makefile_has_verify_target(self):
        """Test that Makefile has verify target."""
        makefile = Path(__file__).parent.parent / "Makefile"
        content = makefile.read_text()
        assert "verify:" in content, "Makefile should have verify target"


class TestRequirementsDev:
    """Tests for development requirements file."""

    def test_requirements_dev_exists(self):
        """Test that requirements-dev.txt exists."""
        req_dev = Path(__file__).parent.parent / "requirements-dev.txt"
        assert req_dev.exists(), "requirements-dev.txt should exist"

    def test_requirements_dev_has_testing_tools(self):
        """Test that requirements-dev.txt includes testing tools."""
        req_dev = Path(__file__).parent.parent / "requirements-dev.txt"
        content = req_dev.read_text()
        assert "pytest" in content
        assert "pytest-cov" in content

    def test_requirements_dev_has_linting_tools(self):
        """Test that requirements-dev.txt includes linting tools."""
        req_dev = Path(__file__).parent.parent / "requirements-dev.txt"
        content = req_dev.read_text()
        assert "black" in content or "ruff" in content
        assert "mypy" in content

    def test_requirements_dev_has_precommit(self):
        """Test that requirements-dev.txt includes pre-commit."""
        req_dev = Path(__file__).parent.parent / "requirements-dev.txt"
        content = req_dev.read_text()
        assert "pre-commit" in content


class TestSetupScript:
    """Tests for setup.py installation."""

    def test_setup_py_exists(self):
        """Test that setup.py exists."""
        setup_py = Path(__file__).parent.parent / "setup.py"
        pyproject = Path(__file__).parent.parent / "pyproject.toml"
        assert setup_py.exists() or pyproject.exists(), "setup.py or pyproject.toml should exist"

    def test_package_is_installable(self):
        """Test that package metadata is valid."""
        from src.utils.install_verifier import verify_package_metadata

        result = verify_package_metadata()
        assert result["valid"] is True
        assert result["name"] == "apic"


class TestIntegrationInstallation:
    """Integration tests for full installation process."""

    @pytest.mark.integration
    def test_fresh_install_creates_database(self):
        """Test that fresh installation creates database tables."""
        from src.utils.install_verifier import verify_database_setup

        # This would run with a test database
        result = verify_database_setup()
        assert result["tables_created"] is True

    @pytest.mark.integration
    def test_migration_upgrade_succeeds(self):
        """Test that database migration upgrade completes."""
        from src.utils.migration_utils import run_migration_upgrade

        result = run_migration_upgrade(target="head")
        assert result["success"] is True

    @pytest.mark.integration
    def test_migration_downgrade_succeeds(self):
        """Test that database migration downgrade completes."""
        from src.utils.migration_utils import run_migration_downgrade

        result = run_migration_downgrade(target="base")
        assert result["success"] is True


def _check_langgraph_available():
    """Check if langgraph is available for testing."""
    try:
        import langgraph
        return True
    except ImportError:
        return False


# Skip API health endpoint tests if langgraph is not installed
langgraph_available = _check_langgraph_available()


@pytest.mark.skipif(not langgraph_available, reason="Requires langgraph and full dependencies")
class TestAPIHealthEndpoint:
    """Tests for API health check endpoint.

    Note: These tests require the full API dependencies (langgraph, langchain, etc.)
    to be installed. They will be skipped if dependencies are not available.
    """

    def test_health_endpoint_returns_ok(self):
        """Test that /health endpoint returns 200 OK."""
        from fastapi.testclient import TestClient

        with patch("src.utils.db_health.check_database_health") as mock_db_check:
            mock_db_check.return_value = {"status": "healthy", "connected": True, "latency_ms": 5}

            from src.api.main import create_app
            app = create_app()
            client = TestClient(app)

            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"

    def test_health_endpoint_reports_db_status(self):
        """Test that /health endpoint reports database status."""
        from fastapi.testclient import TestClient

        with patch("src.utils.db_health.check_database_health") as mock_db_check:
            mock_db_check.return_value = {
                "status": "healthy",
                "connected": True,
                "tables_exist": True,
                "latency_ms": 5,
            }

            from src.api.main import create_app
            app = create_app()
            client = TestClient(app)

            response = client.get("/health")
            data = response.json()
            assert "database" in data
            assert data["database"]["connected"] is True

    def test_health_endpoint_reports_unhealthy(self):
        """Test that /health endpoint reports unhealthy when DB is down."""
        from fastapi.testclient import TestClient

        with patch("src.utils.db_health.check_database_health") as mock_db_check:
            mock_db_check.return_value = {
                "status": "unhealthy",
                "connected": False,
                "error": "Connection refused",
            }

            from src.api.main import create_app
            app = create_app()
            client = TestClient(app)

            response = client.get("/health")
            assert response.status_code == 503
            assert response.json()["status"] == "unhealthy"


class TestStartupValidation:
    """Tests for application startup validation."""

    def test_startup_validates_environment(self):
        """Test that application validates environment on startup."""
        import src.utils.startup as startup_module
        from src.utils.startup import run_startup_checks

        with patch.object(startup_module, "validate_environment") as mock_validate:
            with patch.object(startup_module, "check_database_health") as mock_db:
                mock_validate.return_value = {"valid": True}
                mock_db.return_value = {"status": "healthy", "connected": True}

                result = run_startup_checks()
                mock_validate.assert_called_once()
                assert result["environment_valid"] is True

    def test_startup_checks_database(self):
        """Test that application checks database on startup."""
        import src.utils.startup as startup_module
        from src.utils.startup import run_startup_checks

        with patch.object(startup_module, "validate_environment") as mock_validate:
            mock_validate.return_value = {"valid": True}
            with patch.object(startup_module, "check_database_health") as mock_db:
                mock_db.return_value = {"status": "healthy", "connected": True}

                result = run_startup_checks()
                mock_db.assert_called_once()
                assert result["database_healthy"] is True

    def test_startup_fails_gracefully_on_error(self):
        """Test that startup handles errors gracefully."""
        import src.utils.startup as startup_module
        from src.utils.startup import run_startup_checks, StartupError

        with patch.object(startup_module, "validate_environment") as mock_validate:
            mock_validate.side_effect = Exception("Config error")

            with pytest.raises(StartupError) as exc_info:
                run_startup_checks(strict=True)
            assert "Config error" in str(exc_info.value)
