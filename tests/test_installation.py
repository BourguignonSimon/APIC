"""
TDD Tests for Automated Installation System.
These tests validate the installation process, database setup,
environment configuration, and system health checks.
"""

import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================================
# Test Installation Utilities Module
# ============================================================================

class TestInstallationConfig:
    """Test installation configuration management."""

    def test_install_config_module_exists(self):
        """Test that the installation config module can be imported."""
        try:
            from scripts.install_utils import InstallConfig
            assert InstallConfig is not None
        except ImportError:
            pytest.fail("InstallConfig module should exist in scripts/install_utils.py")

    def test_install_config_default_values(self):
        """Test InstallConfig has proper default values."""
        from scripts.install_utils import InstallConfig

        config = InstallConfig()
        assert config.project_root is not None
        assert config.venv_dir is not None
        assert config.uploads_dir is not None
        assert config.reports_dir is not None

    def test_install_config_validates_python_version(self):
        """Test that InstallConfig validates Python version."""
        from scripts.install_utils import InstallConfig

        config = InstallConfig()
        # Should validate Python 3.11+
        is_valid = config.validate_python_version()
        assert isinstance(is_valid, bool)

    def test_install_config_paths_are_absolute(self):
        """Test that all config paths are absolute."""
        from scripts.install_utils import InstallConfig

        config = InstallConfig()
        assert Path(config.project_root).is_absolute()
        assert Path(config.uploads_dir).is_absolute()
        assert Path(config.reports_dir).is_absolute()


class TestEnvironmentSetup:
    """Test environment file creation and validation."""

    def test_env_manager_module_exists(self):
        """Test that environment manager module exists."""
        try:
            from scripts.install_utils import EnvManager
            assert EnvManager is not None
        except ImportError:
            pytest.fail("EnvManager should exist in scripts/install_utils.py")

    def test_env_manager_creates_env_from_template(self):
        """Test that EnvManager can create .env from .env.example."""
        from scripts.install_utils import EnvManager

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock .env.example
            example_path = Path(tmpdir) / ".env.example"
            example_path.write_text("TEST_VAR=default_value\n")

            manager = EnvManager(project_root=tmpdir)
            result = manager.create_env_file()

            assert result is True
            assert (Path(tmpdir) / ".env").exists()

    def test_env_manager_preserves_existing_env(self):
        """Test that EnvManager doesn't overwrite existing .env."""
        from scripts.install_utils import EnvManager

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create existing .env
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("EXISTING_VAR=value\n")

            # Create .env.example
            example_path = Path(tmpdir) / ".env.example"
            example_path.write_text("NEW_VAR=new_value\n")

            manager = EnvManager(project_root=tmpdir)
            result = manager.create_env_file(overwrite=False)

            assert result is False  # Should not overwrite
            assert "EXISTING_VAR" in env_path.read_text()

    def test_env_manager_validates_required_vars(self):
        """Test that EnvManager validates required environment variables."""
        from scripts.install_utils import EnvManager

        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("")  # Empty env file

            manager = EnvManager(project_root=tmpdir)
            validation_result = manager.validate_env()

            assert isinstance(validation_result, dict)
            assert "missing" in validation_result
            assert "optional_missing" in validation_result


class TestDirectorySetup:
    """Test directory creation and permissions."""

    def test_directory_manager_exists(self):
        """Test that DirectoryManager module exists."""
        try:
            from scripts.install_utils import DirectoryManager
            assert DirectoryManager is not None
        except ImportError:
            pytest.fail("DirectoryManager should exist in scripts/install_utils.py")

    def test_directory_manager_creates_required_dirs(self):
        """Test that DirectoryManager creates all required directories."""
        from scripts.install_utils import DirectoryManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = DirectoryManager(project_root=tmpdir)
            manager.create_all_directories()

            # Check required directories
            assert (Path(tmpdir) / "uploads").exists()
            assert (Path(tmpdir) / "reports").exists()
            assert (Path(tmpdir) / "logs").exists()

    def test_directory_manager_sets_correct_permissions(self):
        """Test that directories have correct permissions."""
        from scripts.install_utils import DirectoryManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = DirectoryManager(project_root=tmpdir)
            manager.create_all_directories()

            uploads_path = Path(tmpdir) / "uploads"
            # Should be readable and writable
            assert os.access(uploads_path, os.R_OK)
            assert os.access(uploads_path, os.W_OK)


class TestDatabaseSetup:
    """Test database initialization and migration."""

    def test_database_manager_exists(self):
        """Test that DatabaseManager module exists."""
        try:
            from scripts.install_utils import DatabaseManager
            assert DatabaseManager is not None
        except ImportError:
            pytest.fail("DatabaseManager should exist in scripts/install_utils.py")

    def test_database_manager_parses_connection_url(self):
        """Test that DatabaseManager parses connection URLs correctly."""
        from scripts.install_utils import DatabaseManager

        test_url = "postgresql://user:pass@localhost:5432/testdb"
        manager = DatabaseManager(database_url=test_url)

        parsed = manager.parse_connection_url()
        assert parsed["user"] == "user"
        assert parsed["password"] == "pass"
        assert parsed["host"] == "localhost"
        assert parsed["port"] == "5432"
        assert parsed["database"] == "testdb"

    def test_database_manager_validates_connection_string(self):
        """Test that DatabaseManager validates connection strings."""
        from scripts.install_utils import DatabaseManager

        # Valid URL
        valid_manager = DatabaseManager(
            database_url="postgresql://user:pass@localhost:5432/db"
        )
        assert valid_manager.validate_connection_url() is True

        # Invalid URL
        invalid_manager = DatabaseManager(database_url="invalid")
        assert invalid_manager.validate_connection_url() is False

    @pytest.mark.asyncio
    async def test_database_manager_checks_connection(self):
        """Test that DatabaseManager can check database connectivity."""
        from scripts.install_utils import DatabaseManager

        # With mock - should handle connection gracefully
        manager = DatabaseManager(
            database_url="postgresql://postgres:postgres@localhost:5432/apic"
        )

        # Test without asyncpg installed - should return error gracefully
        result = await manager.check_connection()
        assert result["connected"] is False or result["connected"] is True
        # Should always have these keys
        assert "connected" in result
        assert "error" in result or result["connected"] is True

    def test_database_manager_generates_init_sql(self):
        """Test that DatabaseManager generates initialization SQL."""
        from scripts.install_utils import DatabaseManager

        manager = DatabaseManager(
            database_url="postgresql://postgres:postgres@localhost:5432/apic"
        )

        init_sql = manager.generate_init_sql()
        assert "CREATE TABLE" in init_sql or "CREATE DATABASE" in init_sql


class TestDependencyChecker:
    """Test dependency validation and installation."""

    def test_dependency_checker_exists(self):
        """Test that DependencyChecker module exists."""
        try:
            from scripts.install_utils import DependencyChecker
            assert DependencyChecker is not None
        except ImportError:
            pytest.fail("DependencyChecker should exist in scripts/install_utils.py")

    def test_dependency_checker_validates_python_packages(self):
        """Test that DependencyChecker can validate Python packages."""
        from scripts.install_utils import DependencyChecker

        checker = DependencyChecker()

        # pathlib is a standard library module that should always be available
        result = checker.check_package("pathlib")
        assert result["installed"] is True

        # Non-existent package
        result = checker.check_package("nonexistent-fake-package-12345")
        assert result["installed"] is False

    def test_dependency_checker_validates_system_deps(self):
        """Test that DependencyChecker validates system dependencies."""
        from scripts.install_utils import DependencyChecker

        checker = DependencyChecker()

        # Check for common system tool
        result = checker.check_system_dependency("python3")
        assert result["available"] is True

    def test_dependency_checker_parses_requirements(self):
        """Test that DependencyChecker parses requirements.txt."""
        from scripts.install_utils import DependencyChecker

        with tempfile.TemporaryDirectory() as tmpdir:
            req_path = Path(tmpdir) / "requirements.txt"
            req_path.write_text("pytest>=8.0.0\nfastapi>=0.115.0\n")

            checker = DependencyChecker()
            packages = checker.parse_requirements(str(req_path))

            assert "pytest" in packages
            assert "fastapi" in packages


class TestHealthChecker:
    """Test system health check functionality."""

    def test_health_checker_exists(self):
        """Test that HealthChecker module exists."""
        try:
            from scripts.install_utils import HealthChecker
            assert HealthChecker is not None
        except ImportError:
            pytest.fail("HealthChecker should exist in scripts/install_utils.py")

    def test_health_checker_runs_all_checks(self):
        """Test that HealthChecker runs all health checks."""
        from scripts.install_utils import HealthChecker

        checker = HealthChecker()
        results = checker.run_all_checks()

        assert isinstance(results, dict)
        assert "python_version" in results
        assert "directories" in results
        assert "environment" in results

    def test_health_checker_returns_overall_status(self):
        """Test that HealthChecker returns overall status."""
        from scripts.install_utils import HealthChecker

        checker = HealthChecker()
        results = checker.run_all_checks()

        assert "overall_status" in results
        assert results["overall_status"] in ["healthy", "degraded", "unhealthy"]


class TestInstaller:
    """Test main installer orchestration."""

    def test_installer_exists(self):
        """Test that Installer module exists."""
        try:
            from scripts.install_utils import Installer
            assert Installer is not None
        except ImportError:
            pytest.fail("Installer should exist in scripts/install_utils.py")

    def test_installer_has_required_methods(self):
        """Test that Installer has required methods."""
        from scripts.install_utils import Installer

        installer = Installer()

        assert hasattr(installer, "run_full_install")
        assert hasattr(installer, "run_quick_setup")
        assert hasattr(installer, "verify_installation")

    def test_installer_validates_prerequisites(self):
        """Test that Installer validates prerequisites."""
        from scripts.install_utils import Installer

        installer = Installer()
        prereq_result = installer.check_prerequisites()

        assert isinstance(prereq_result, dict)
        assert "python" in prereq_result
        assert "all_met" in prereq_result


# ============================================================================
# Test CLI Scripts
# ============================================================================

class TestSetupScript:
    """Test the main setup.sh script functionality."""

    def test_setup_script_exists(self):
        """Test that setup.sh script exists."""
        setup_script = Path(__file__).parent.parent / "scripts" / "setup.sh"
        assert setup_script.exists(), "scripts/setup.sh should exist"

    def test_setup_script_is_executable(self):
        """Test that setup.sh is executable."""
        setup_script = Path(__file__).parent.parent / "scripts" / "setup.sh"
        assert os.access(setup_script, os.X_OK), "scripts/setup.sh should be executable"


class TestMakefile:
    """Test Makefile targets."""

    def test_makefile_exists(self):
        """Test that Makefile exists."""
        makefile = Path(__file__).parent.parent / "Makefile"
        assert makefile.exists(), "Makefile should exist"

    def test_makefile_has_required_targets(self):
        """Test that Makefile has required targets."""
        makefile = Path(__file__).parent.parent / "Makefile"
        content = makefile.read_text()

        required_targets = [
            "install",
            "setup",
            "test",
            "lint",
            "clean",
            "db-init",
            "docker-up",
            "docker-down",
        ]

        for target in required_targets:
            assert f"{target}:" in content, f"Makefile should have '{target}' target"


class TestDatabaseInitScript:
    """Test database initialization scripts."""

    def test_db_init_script_exists(self):
        """Test that database init script exists."""
        db_script = Path(__file__).parent.parent / "scripts" / "init_db.py"
        assert db_script.exists(), "scripts/init_db.py should exist"

    def test_db_init_sql_exists(self):
        """Test that database init SQL exists."""
        sql_file = Path(__file__).parent.parent / "scripts" / "init_schema.sql"
        assert sql_file.exists(), "scripts/init_schema.sql should exist"


# ============================================================================
# Integration Tests
# ============================================================================

class TestInstallationIntegration:
    """Integration tests for the complete installation process."""

    def test_full_installation_workflow(self):
        """Test the complete installation workflow in a temp directory."""
        from scripts.install_utils import (
            InstallConfig,
            EnvManager,
            DirectoryManager,
            HealthChecker,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. Initialize config
            config = InstallConfig(project_root=tmpdir)
            assert config.project_root == tmpdir

            # 2. Create directories
            dir_manager = DirectoryManager(project_root=tmpdir)
            dir_manager.create_all_directories()

            assert (Path(tmpdir) / "uploads").exists()
            assert (Path(tmpdir) / "reports").exists()

            # 3. Create env file
            example_path = Path(tmpdir) / ".env.example"
            example_path.write_text("TEST_VAR=value\n")

            env_manager = EnvManager(project_root=tmpdir)
            env_manager.create_env_file()

            assert (Path(tmpdir) / ".env").exists()

    def test_installation_is_idempotent(self):
        """Test that installation can be run multiple times safely."""
        from scripts.install_utils import DirectoryManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = DirectoryManager(project_root=tmpdir)

            # Run twice - should not fail
            manager.create_all_directories()
            manager.create_all_directories()

            assert (Path(tmpdir) / "uploads").exists()

    def test_installation_handles_missing_example(self):
        """Test that installation handles missing .env.example gracefully."""
        from scripts.install_utils import EnvManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = EnvManager(project_root=tmpdir)

            # Should not crash, should create default env
            result = manager.create_env_file()
            assert isinstance(result, bool)


# ============================================================================
# Requirements Optimization Tests
# ============================================================================

class TestRequirementsOptimization:
    """Test requirements file optimization."""

    def test_requirements_analyzer_exists(self):
        """Test that RequirementsAnalyzer exists."""
        try:
            from scripts.install_utils import RequirementsAnalyzer
            assert RequirementsAnalyzer is not None
        except ImportError:
            pytest.fail("RequirementsAnalyzer should exist")

    def test_requirements_analyzer_finds_unused(self):
        """Test that analyzer can identify potentially unused packages."""
        from scripts.install_utils import RequirementsAnalyzer

        analyzer = RequirementsAnalyzer()
        # Should analyze project and return findings
        result = analyzer.analyze()

        assert isinstance(result, dict)
        assert "required" in result
        assert "development" in result

    def test_requirements_categorizes_packages(self):
        """Test that requirements are properly categorized."""
        from scripts.install_utils import RequirementsAnalyzer

        analyzer = RequirementsAnalyzer()
        categories = analyzer.categorize_packages()

        assert "core" in categories
        assert "development" in categories
        assert "optional" in categories
