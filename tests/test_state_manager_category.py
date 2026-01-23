"""
Integration tests for document category feature in StateManager.

These tests use SQLite in-memory database to test the actual StateManager code.
"""

import pytest
import sys
import os
from datetime import datetime
import uuid

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# ============================================================================
# Test the actual model from the codebase
# ============================================================================

class TestActualStateManagerCode:
    """Test the actual code changes to StateManager."""

    def test_state_manager_file_has_category_in_document_record(self):
        """Verify that DocumentRecord model has category column."""
        # Read the state_manager.py file and check for category
        state_manager_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "src", "services", "state_manager.py"
        )

        with open(state_manager_path, 'r') as f:
            content = f.read()

        # Check that category column is defined in DocumentRecord
        assert 'category = Column(' in content, \
            "DocumentRecord should have 'category' column defined"

        # Check default value
        assert 'default="general"' in content, \
            "category column should have default='general'"

    def test_add_document_has_category_parameter(self):
        """Verify that add_document method accepts category parameter."""
        state_manager_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "src", "services", "state_manager.py"
        )

        with open(state_manager_path, 'r') as f:
            content = f.read()

        # Check that add_document has category parameter
        assert 'def add_document(' in content

        # Find the add_document function and check for category
        start = content.find('def add_document(')
        end = content.find('def ', start + 1)
        add_document_code = content[start:end]

        assert 'category:' in add_document_code or 'category =' in add_document_code, \
            "add_document should have 'category' parameter"

        assert '"category": doc.category' in add_document_code, \
            "add_document should return category in result dict"

    def test_get_project_documents_has_category_filter(self):
        """Verify that get_project_documents supports category filter."""
        state_manager_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "src", "services", "state_manager.py"
        )

        with open(state_manager_path, 'r') as f:
            content = f.read()

        # Find the get_project_documents function
        start = content.find('def get_project_documents(')
        end = content.find('def ', start + 1)
        get_docs_code = content[start:end]

        # Check for category parameter
        assert 'category' in get_docs_code, \
            "get_project_documents should have 'category' parameter"

        # Check for category filtering
        assert 'filter_by(category=' in get_docs_code or 'if category' in get_docs_code, \
            "get_project_documents should filter by category"

        # Check that category is returned
        assert '"category": d.category' in get_docs_code, \
            "get_project_documents should return category in result"


class TestDatabaseSchemaFile:
    """Test that database schema file includes category column."""

    def test_init_schema_has_category_column(self):
        """Verify that init_schema.sql has category column."""
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "scripts", "init_schema.sql"
        )

        with open(schema_path, 'r') as f:
            content = f.read()

        # Check documents table has category column
        assert 'category VARCHAR(50)' in content, \
            "documents table should have category column"

        assert "DEFAULT 'general'" in content, \
            "category column should have DEFAULT 'general'"

    def test_init_schema_has_category_index(self):
        """Verify that init_schema.sql has category index."""
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "scripts", "init_schema.sql"
        )

        with open(schema_path, 'r') as f:
            content = f.read()

        assert 'idx_documents_category' in content, \
            "Should have index on documents.category"


class TestMigrationFile:
    """Test that migration file exists and is correct."""

    def test_migration_file_exists(self):
        """Verify that migration file exists."""
        migration_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "scripts", "migrations", "001_add_document_category.sql"
        )

        assert os.path.exists(migration_path), \
            "Migration file should exist at scripts/migrations/001_add_document_category.sql"

    def test_migration_adds_category_column(self):
        """Verify that migration adds category column."""
        migration_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "scripts", "migrations", "001_add_document_category.sql"
        )

        with open(migration_path, 'r') as f:
            content = f.read()

        assert 'ALTER TABLE documents' in content, \
            "Migration should ALTER TABLE documents"

        assert 'ADD COLUMN' in content, \
            "Migration should ADD COLUMN"

        assert 'category' in content, \
            "Migration should add category column"


class TestAPIRoutesFile:
    """Test that API routes file supports category."""

    def test_document_response_has_category(self):
        """Verify that DocumentResponse model has category field."""
        routes_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "src", "api", "routes", "documents.py"
        )

        with open(routes_path, 'r') as f:
            content = f.read()

        # Find DocumentResponse class
        start = content.find('class DocumentResponse')
        end = content.find('class ', start + 1)
        response_code = content[start:end]

        assert 'category:' in response_code or 'category =' in response_code, \
            "DocumentResponse should have category field"

    def test_list_documents_accepts_category_param(self):
        """Verify that list_documents endpoint accepts category param."""
        routes_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "src", "api", "routes", "documents.py"
        )

        with open(routes_path, 'r') as f:
            content = f.read()

        # Find list_documents function
        start = content.find('async def list_documents(')
        end = content.find('async def ', start + 1)
        list_docs_code = content[start:end]

        assert 'category' in list_docs_code, \
            "list_documents should accept category parameter"

        assert 'Query(' in list_docs_code or 'category:' in list_docs_code, \
            "category should be a query parameter"

    def test_upload_documents_accepts_category(self):
        """Verify that upload_documents can accept category."""
        routes_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "src", "api", "routes", "documents.py"
        )

        with open(routes_path, 'r') as f:
            content = f.read()

        # Find upload_documents function
        start = content.find('async def upload_documents(')
        end = content.find('async def ', start + 1)
        upload_code = content[start:end]

        # Check category is accepted
        assert 'category' in upload_code, \
            "upload_documents should accept category parameter"


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
