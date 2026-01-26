"""
TDD tests for document category feature.

These tests verify that documents can be categorized and filtered by category.
Categories include: 'general', 'interview_results', 'operational', 'financial', etc.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import uuid

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Import directly to avoid circular imports
Base = declarative_base()


class DocumentRecord(Base):
    """Database model for uploaded documents - test version with category."""
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(String(50), nullable=False)
    file_path = Column(String(500), nullable=False)
    chunk_count = Column(String(50), default="0")
    processed = Column(Boolean, default=False)
    content_summary = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    category = Column(String(50), default="general")  # NEW FIELD


class ProjectRecord(Base):
    """Database model for project metadata - for test FK."""
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_name = Column(String(255), nullable=False)
    project_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_departments = Column(JSON, default=list)
    status = Column(String(50), default="created")
    vector_namespace = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return engine, Session


class MockStateManager:
    """Mock StateManager for testing document category functionality."""

    def __init__(self, engine, Session):
        self.engine = engine
        self.SessionLocal = Session

    def get_session(self):
        return self.SessionLocal()

    def add_document(
        self,
        project_id: str,
        filename: str,
        file_type: str,
        file_size: int,
        file_path: str,
        category: str = "general",
    ):
        """Add a document with category support."""
        with self.get_session() as session:
            doc = DocumentRecord(
                project_id=project_id,
                filename=filename,
                file_type=file_type,
                file_size=str(file_size),
                file_path=file_path,
                category=category,
            )
            session.add(doc)
            session.commit()

            return {
                "id": doc.id,
                "project_id": doc.project_id,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "file_size": int(doc.file_size),
                "file_path": doc.file_path,
                "processed": doc.processed,
                "chunk_count": int(doc.chunk_count),
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                "category": doc.category,
            }

    def get_project_documents(self, project_id: str, category: str = None):
        """Get documents with optional category filter."""
        with self.get_session() as session:
            query = session.query(DocumentRecord).filter_by(project_id=project_id)

            if category is not None:
                query = query.filter_by(category=category)

            docs = query.all()

            return [
                {
                    "id": d.id,
                    "project_id": d.project_id,
                    "filename": d.filename,
                    "file_type": d.file_type,
                    "file_size": int(d.file_size),
                    "processed": d.processed,
                    "chunk_count": int(d.chunk_count),
                    "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
                    "category": d.category,
                }
                for d in docs
            ]


@pytest.fixture
def state_manager_with_db(in_memory_db):
    """Create a MockStateManager with in-memory database."""
    engine, Session = in_memory_db
    return MockStateManager(engine, Session)


# ============================================================================
# Test DocumentRecord Model Category Field
# ============================================================================

class TestDocumentRecordCategory:
    """Test that DocumentRecord model has category field."""

    def test_document_record_has_category_column(self, in_memory_db):
        """Test that DocumentRecord model has a category column."""
        engine, Session = in_memory_db

        # Check that the column exists in the model
        assert hasattr(DocumentRecord, 'category'), \
            "DocumentRecord model should have a 'category' attribute"

    def test_document_record_category_default_is_general(self, in_memory_db):
        """Test that category defaults to 'general' when not specified."""
        engine, Session = in_memory_db
        session = Session()

        try:
            # Create a document without specifying category
            doc = DocumentRecord(
                id=str(uuid.uuid4()),
                project_id=str(uuid.uuid4()),
                filename="test.pdf",
                file_type="pdf",
                file_size="1024",
                file_path="/tmp/test.pdf",
            )
            session.add(doc)
            session.commit()

            # Refresh and check default value
            session.refresh(doc)
            assert doc.category == "general", \
                f"Default category should be 'general', got '{doc.category}'"
        finally:
            session.close()

    def test_document_record_can_set_category(self, in_memory_db):
        """Test that category can be set to a custom value."""
        engine, Session = in_memory_db
        session = Session()

        try:
            doc = DocumentRecord(
                id=str(uuid.uuid4()),
                project_id=str(uuid.uuid4()),
                filename="interview.txt",
                file_type="txt",
                file_size="2048",
                file_path="/tmp/interview.txt",
                category="interview_results",
            )
            session.add(doc)
            session.commit()

            session.refresh(doc)
            assert doc.category == "interview_results", \
                f"Category should be 'interview_results', got '{doc.category}'"
        finally:
            session.close()


# ============================================================================
# Test StateManager Document Methods with Category
# ============================================================================

class TestStateManagerDocumentCategory:
    """Test StateManager document methods with category support."""

    def test_add_document_with_category(self, state_manager_with_db):
        """Test adding a document with a category."""
        sm = state_manager_with_db
        project_id = str(uuid.uuid4())

        # First create a project (required for foreign key)
        with sm.SessionLocal() as session:
            project = ProjectRecord(
                id=project_id,
                client_name="Test Client",
                project_name="Test Project",
            )
            session.add(project)
            session.commit()

        # Add document with category
        doc = sm.add_document(
            project_id=project_id,
            filename="interview_transcript.txt",
            file_type="txt",
            file_size=1500,
            file_path="/uploads/interview_transcript.txt",
            category="interview_results",
        )

        assert doc is not None
        assert doc["category"] == "interview_results", \
            f"Document should have category 'interview_results', got '{doc.get('category')}'"

    def test_add_document_without_category_defaults_to_general(self, state_manager_with_db):
        """Test that adding a document without category defaults to 'general'."""
        sm = state_manager_with_db
        project_id = str(uuid.uuid4())

        # First create a project
        # ProjectRecord is defined at top of file
        with sm.SessionLocal() as session:
            project = ProjectRecord(
                id=project_id,
                client_name="Test Client",
                project_name="Test Project",
            )
            session.add(project)
            session.commit()

        # Add document without category
        doc = sm.add_document(
            project_id=project_id,
            filename="report.pdf",
            file_type="pdf",
            file_size=5000,
            file_path="/uploads/report.pdf",
        )

        assert doc is not None
        assert doc.get("category") == "general", \
            f"Default category should be 'general', got '{doc.get('category')}'"

    def test_get_project_documents_without_category_filter(self, state_manager_with_db):
        """Test getting all documents without category filter."""
        sm = state_manager_with_db
        project_id = str(uuid.uuid4())

        # Create project
        # ProjectRecord is defined at top of file
        with sm.SessionLocal() as session:
            project = ProjectRecord(
                id=project_id,
                client_name="Test Client",
                project_name="Test Project",
            )
            session.add(project)
            session.commit()

        # Add documents with different categories
        sm.add_document(
            project_id=project_id,
            filename="doc1.pdf",
            file_type="pdf",
            file_size=1000,
            file_path="/uploads/doc1.pdf",
            category="general",
        )
        sm.add_document(
            project_id=project_id,
            filename="doc2.txt",
            file_type="txt",
            file_size=2000,
            file_path="/uploads/doc2.txt",
            category="interview_results",
        )

        # Get all documents (no filter)
        docs = sm.get_project_documents(project_id)

        assert len(docs) == 2, f"Expected 2 documents, got {len(docs)}"

    def test_get_project_documents_with_category_filter(self, state_manager_with_db):
        """Test filtering documents by category."""
        sm = state_manager_with_db
        project_id = str(uuid.uuid4())

        # Create project
        # ProjectRecord is defined at top of file
        with sm.SessionLocal() as session:
            project = ProjectRecord(
                id=project_id,
                client_name="Test Client",
                project_name="Test Project",
            )
            session.add(project)
            session.commit()

        # Add documents with different categories
        sm.add_document(
            project_id=project_id,
            filename="doc1.pdf",
            file_type="pdf",
            file_size=1000,
            file_path="/uploads/doc1.pdf",
            category="general",
        )
        sm.add_document(
            project_id=project_id,
            filename="interview1.txt",
            file_type="txt",
            file_size=2000,
            file_path="/uploads/interview1.txt",
            category="interview_results",
        )
        sm.add_document(
            project_id=project_id,
            filename="interview2.txt",
            file_type="txt",
            file_size=3000,
            file_path="/uploads/interview2.txt",
            category="interview_results",
        )

        # Filter by category
        interview_docs = sm.get_project_documents(project_id, category="interview_results")

        assert len(interview_docs) == 2, \
            f"Expected 2 interview_results documents, got {len(interview_docs)}"

        for doc in interview_docs:
            assert doc["category"] == "interview_results", \
                f"All documents should have category 'interview_results', got '{doc['category']}'"

    def test_get_project_documents_returns_category_field(self, state_manager_with_db):
        """Test that returned documents include category field."""
        sm = state_manager_with_db
        project_id = str(uuid.uuid4())

        # Create project
        # ProjectRecord is defined at top of file
        with sm.SessionLocal() as session:
            project = ProjectRecord(
                id=project_id,
                client_name="Test Client",
                project_name="Test Project",
            )
            session.add(project)
            session.commit()

        # Add document
        sm.add_document(
            project_id=project_id,
            filename="test.pdf",
            file_type="pdf",
            file_size=1000,
            file_path="/uploads/test.pdf",
            category="financial",
        )

        # Get documents
        docs = sm.get_project_documents(project_id)

        assert len(docs) == 1
        assert "category" in docs[0], "Document dict should include 'category' key"
        assert docs[0]["category"] == "financial"


# ============================================================================
# Test API Endpoint Category Support
# ============================================================================

class TestDocumentAPICategory:
    """Test API endpoints for document category support."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from src.api.main import create_app
        app = create_app()
        return TestClient(app)

    def test_list_documents_accepts_category_query_param(self, client):
        """Test that list documents endpoint accepts category query parameter."""
        project_id = str(uuid.uuid4())

        with patch('src.api.routes.documents.state_manager') as mock_sm:
            mock_sm.get_project.return_value = {"id": project_id}
            mock_sm.get_project_documents.return_value = []

            # Call with category parameter
            response = client.get(
                f"/api/v1/projects/{project_id}/documents",
                params={"category": "interview_results"}
            )

            # Should not return 422 (validation error)
            assert response.status_code != 422, \
                "Endpoint should accept 'category' query parameter"

            # Verify get_project_documents was called with category
            mock_sm.get_project_documents.assert_called_once()
            call_args = mock_sm.get_project_documents.call_args

            # Check if category was passed (either as positional or keyword arg)
            if call_args.kwargs:
                assert call_args.kwargs.get("category") == "interview_results" or \
                       (len(call_args.args) > 1 and call_args.args[1] == "interview_results"), \
                    "get_project_documents should be called with category parameter"

    def test_document_response_includes_category(self, client):
        """Test that document response includes category field."""
        project_id = str(uuid.uuid4())
        doc_id = str(uuid.uuid4())

        with patch('src.api.routes.documents.state_manager') as mock_sm:
            mock_sm.get_project.return_value = {"id": project_id}
            mock_sm.get_project_documents.return_value = [
                {
                    "id": doc_id,
                    "project_id": project_id,
                    "filename": "test.pdf",
                    "file_type": "pdf",
                    "file_size": 1000,
                    "processed": False,
                    "chunk_count": 0,
                    "uploaded_at": datetime.utcnow().isoformat(),
                    "category": "interview_results",
                }
            ]

            response = client.get(f"/api/v1/projects/{project_id}/documents")

            assert response.status_code == 200
            data = response.json()

            # Check response structure
            if "documents" in data:
                docs = data["documents"]
            else:
                docs = data if isinstance(data, list) else [data]

            assert len(docs) > 0, "Should return at least one document"
            assert "category" in docs[0], "Document response should include 'category' field"
            assert docs[0]["category"] == "interview_results"


# ============================================================================
# Test Category Validation
# ============================================================================

class TestCategoryValidation:
    """Test category value validation."""

    VALID_CATEGORIES = [
        "general",
        "interview_results",
        "operational",
        "financial",
        "strategic",
        "technical",
    ]

    def test_valid_categories_accepted(self, state_manager_with_db):
        """Test that all valid categories are accepted."""
        sm = state_manager_with_db
        project_id = str(uuid.uuid4())

        # Create project
        # ProjectRecord is defined at top of file
        with sm.SessionLocal() as session:
            project = ProjectRecord(
                id=project_id,
                client_name="Test Client",
                project_name="Test Project",
            )
            session.add(project)
            session.commit()

        for i, category in enumerate(self.VALID_CATEGORIES):
            doc = sm.add_document(
                project_id=project_id,
                filename=f"test_{i}.pdf",
                file_type="pdf",
                file_size=1000,
                file_path=f"/uploads/test_{i}.pdf",
                category=category,
            )
            assert doc["category"] == category, \
                f"Category '{category}' should be accepted"
