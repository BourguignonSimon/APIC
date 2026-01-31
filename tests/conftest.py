"""
Shared test fixtures and utilities for APIC test suite.

This module provides common fixtures used across multiple test files:
- Database fixtures (in-memory SQLite for testing)
- API client fixtures (FastAPI TestClient)
- Mock objects for agents and services
- Sample data fixtures
"""

import pytest
import os
import uuid
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# ============================================================================
# Database Fixtures
# ============================================================================

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
    category = Column(String(50), default="general")


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
# API Client Fixtures
# ============================================================================

@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    from fastapi.testclient import TestClient
    from src.api.main import create_app
    app = create_app()
    return TestClient(app)


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_project_id():
    """Generate a sample project ID."""
    return str(uuid.uuid4())


@pytest.fixture
def sample_thread_id():
    """Generate a sample thread ID."""
    return str(uuid.uuid4())


@pytest.fixture
def sample_document():
    """Create a sample document for testing."""
    from src.models.schemas import Document
    return Document(
        id=str(uuid.uuid4()),
        project_id="test-project-123",
        filename="test_document.txt",
        file_type="txt",
        file_size=1024,
    )


@pytest.fixture
def sample_project_data():
    """Create sample project data."""
    return {
        "id": str(uuid.uuid4()),
        "thread_id": str(uuid.uuid4()),
        "client_name": "Test Corp",
        "project_name": "Test Project",
        "description": "Test description",
        "target_departments": ["Finance", "Operations"],
        "status": "created",
        "vector_namespace": "test-namespace",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_document_data():
    """Create sample document data."""
    return {
        "id": str(uuid.uuid4()),
        "project_id": str(uuid.uuid4()),
        "filename": "test.pdf",
        "file_type": "pdf",
        "file_size": 1024,
        "file_path": "/uploads/test.pdf",
        "processed": False,
        "chunk_count": 0,
        "uploaded_at": datetime.utcnow().isoformat(),
        "category": "general",
    }


# ============================================================================
# Workflow State Fixtures
# ============================================================================

@pytest.fixture
def initial_workflow_state(sample_document):
    """Create initial state for workflow testing."""
    return {
        "project_id": "test-project-123",
        "documents": [sample_document],
        "messages": [],
        "errors": [],
        "document_summaries": [],
        "ingestion_complete": False,
        "is_suspended": False,
    }


@pytest.fixture
def workflow_state_with_hypotheses():
    """Create workflow state with hypotheses."""
    return {
        "project_id": "test-project-123",
        "hypotheses": [
            {
                "id": str(uuid.uuid4()),
                "process_area": "Invoice Processing",
                "description": "Manual data entry causing delays",
                "evidence": ["Manual entry required"],
                "indicators": ["manual", "delay"],
                "confidence": 0.8,
                "category": "manual_process",
            }
        ],
        "target_departments": ["Finance", "Operations"],
        "messages": [],
        "errors": [],
    }


# ============================================================================
# Mock Agent Fixtures
# ============================================================================

@pytest.fixture
def mock_llm():
    """Create a mock LLM for testing."""
    mock = Mock()
    mock.ainvoke = AsyncMock(return_value=Mock(content="Mock response"))
    return mock


@pytest.fixture
def mock_llm_response():
    """Create a mock LLM response."""
    response = Mock()
    response.content = "This is a mock LLM response."
    return response


# ============================================================================
# Database Test Helpers
# ============================================================================

def create_test_project(session, project_id=None, **kwargs):
    """Helper to create a test project in the database."""
    project = ProjectRecord(
        id=project_id or str(uuid.uuid4()),
        client_name=kwargs.get("client_name", "Test Client"),
        project_name=kwargs.get("project_name", "Test Project"),
        description=kwargs.get("description", "Test description"),
        status=kwargs.get("status", "created"),
    )
    session.add(project)
    session.commit()
    return project


def create_test_document(session, project_id, **kwargs):
    """Helper to create a test document in the database."""
    doc = DocumentRecord(
        id=kwargs.get("id", str(uuid.uuid4())),
        project_id=project_id,
        filename=kwargs.get("filename", "test.pdf"),
        file_type=kwargs.get("file_type", "pdf"),
        file_size=kwargs.get("file_size", "1024"),
        file_path=kwargs.get("file_path", "/uploads/test.pdf"),
        category=kwargs.get("category", "general"),
    )
    session.add(doc)
    session.commit()
    return doc


# ============================================================================
# Valid Category Constants
# ============================================================================

VALID_CATEGORIES = [
    "general",
    "interview_results",
    "operational",
    "financial",
    "strategic",
    "technical",
]
