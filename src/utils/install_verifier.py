"""
Installation Verification Module
Verifies that APIC is properly installed and configured.
"""

import os
import sys
import logging
import importlib.metadata
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Required directories
REQUIRED_DIRECTORIES = [
    "src",
    "src/agents",
    "src/api",
    "src/api/routes",
    "src/models",
    "src/services",
    "src/utils",
    "config",
    "tests",
    "alembic",
    "alembic/versions",
]

# Required configuration files
REQUIRED_CONFIG_FILES = [
    "requirements.txt",
    "alembic.ini",
    ".env.example",
]

# Required packages (core dependencies)
REQUIRED_PACKAGES = [
    "fastapi",
    "sqlalchemy",
    "alembic",
    "pydantic",
    "pydantic-settings",
    "uvicorn",
]


def verify_python_version() -> Dict[str, Any]:
    """
    Verify Python version meets requirements.

    Returns:
        Dictionary with version info and validity
    """
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    full_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    # Python 3.11+ required
    valid = sys.version_info >= (3, 11)

    return {
        "valid": valid,
        "version": version,
        "full_version": full_version,
        "minimum_required": "3.11",
        "message": "OK" if valid else "Python 3.11 or higher required",
    }


def verify_required_packages() -> Dict[str, Any]:
    """
    Verify required packages are installed.

    Returns:
        Dictionary with package status
    """
    installed_packages = []
    missing_packages = []

    for package in REQUIRED_PACKAGES:
        try:
            version = importlib.metadata.version(package)
            installed_packages.append(package)
        except importlib.metadata.PackageNotFoundError:
            missing_packages.append(package)

    return {
        "valid": len(missing_packages) == 0,
        "installed_packages": installed_packages,
        "missing_packages": missing_packages,
        "message": "OK" if not missing_packages else f"Missing: {', '.join(missing_packages)}",
    }


def verify_directory_structure() -> Dict[str, Any]:
    """
    Verify required directories exist.

    Returns:
        Dictionary with directory status
    """
    existing = []
    missing = []

    for dir_path in REQUIRED_DIRECTORIES:
        full_path = PROJECT_ROOT / dir_path
        if full_path.exists() and full_path.is_dir():
            existing.append(dir_path)
        else:
            missing.append(dir_path)

    return {
        "valid": len(missing) == 0,
        "directories": existing,
        "missing_directories": missing,
        "message": "OK" if not missing else f"Missing: {', '.join(missing)}",
    }


def verify_configuration_files() -> Dict[str, Any]:
    """
    Verify required configuration files exist.

    Returns:
        Dictionary with file status
    """
    existing = []
    missing = []

    for file_name in REQUIRED_CONFIG_FILES:
        full_path = PROJECT_ROOT / file_name
        if full_path.exists() and full_path.is_file():
            existing.append(file_name)
        else:
            missing.append(file_name)

    return {
        "valid": len(missing) == 0,
        "files": existing,
        "missing_files": missing,
        "message": "OK" if not missing else f"Missing: {', '.join(missing)}",
    }


def verify_package_metadata() -> Dict[str, Any]:
    """
    Verify package metadata is valid.

    Returns:
        Dictionary with package metadata
    """
    result = {
        "valid": False,
        "name": None,
        "version": None,
        "error": None,
    }

    # Check for pyproject.toml or setup.py
    pyproject = PROJECT_ROOT / "pyproject.toml"
    setup_py = PROJECT_ROOT / "setup.py"

    if pyproject.exists():
        try:
            import tomllib

            with open(pyproject, "rb") as f:
                data = tomllib.load(f)
            project = data.get("project", {})
            result["name"] = project.get("name", "apic")
            result["version"] = project.get("version", "1.0.0")
            result["valid"] = True
        except Exception as e:
            result["error"] = str(e)
    elif setup_py.exists():
        # Basic setup.py exists check
        result["name"] = "apic"
        result["valid"] = True
    else:
        result["error"] = "No pyproject.toml or setup.py found"

    return result


def verify_database_setup() -> Dict[str, Any]:
    """
    Verify database is set up correctly.

    Returns:
        Dictionary with database setup status
    """
    result = {
        "tables_created": False,
        "error": None,
    }

    try:
        from src.utils.db_health import check_database_tables

        table_check = check_database_tables()
        result["tables_created"] = table_check["all_tables_exist"]
        if not result["tables_created"]:
            result["error"] = f"Missing tables: {table_check['missing_tables']}"
    except Exception as e:
        result["error"] = str(e)

    return result


def verify_installation() -> Dict[str, Any]:
    """
    Perform complete installation verification.

    Returns:
        Dictionary with all verification results
    """
    python = verify_python_version()
    packages = verify_required_packages()
    directories = verify_directory_structure()
    configuration = verify_configuration_files()

    # Determine overall status
    all_valid = all([
        python["valid"],
        packages["valid"],
        directories["valid"],
        # configuration is optional for basic installation
    ])

    return {
        "python": python,
        "packages": packages,
        "directories": directories,
        "configuration": configuration,
        "overall_status": "pass" if all_valid else "fail",
    }


def print_verification_report() -> None:
    """Print a formatted verification report to console."""
    result = verify_installation()

    print("\n" + "=" * 60)
    print("APIC Installation Verification Report")
    print("=" * 60)

    # Python
    py = result["python"]
    status = "PASS" if py["valid"] else "FAIL"
    print(f"\n[{status}] Python Version: {py['full_version']} (required: {py['minimum_required']}+)")

    # Packages
    pkg = result["packages"]
    status = "PASS" if pkg["valid"] else "FAIL"
    print(f"[{status}] Required Packages: {len(pkg['installed_packages'])}/{len(REQUIRED_PACKAGES)}")
    if pkg["missing_packages"]:
        print(f"       Missing: {', '.join(pkg['missing_packages'])}")

    # Directories
    dirs = result["directories"]
    status = "PASS" if dirs["valid"] else "FAIL"
    print(f"[{status}] Directory Structure: {len(dirs['directories'])}/{len(REQUIRED_DIRECTORIES)}")
    if dirs["missing_directories"]:
        print(f"       Missing: {', '.join(dirs['missing_directories'])}")

    # Configuration
    cfg = result["configuration"]
    status = "PASS" if cfg["valid"] else "WARN"
    print(f"[{status}] Configuration Files: {len(cfg['files'])}/{len(REQUIRED_CONFIG_FILES)}")
    if cfg["missing_files"]:
        print(f"       Missing: {', '.join(cfg['missing_files'])}")

    # Overall
    print("\n" + "-" * 60)
    overall = result["overall_status"].upper()
    print(f"Overall Status: {overall}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    print_verification_report()
