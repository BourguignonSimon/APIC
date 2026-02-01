"""
Shared fixtures for APIC tests.

This module provides common fixtures used across all test files.
"""

import pytest
import os
import uuid
import tempfile
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from fastapi.testclient import TestClient


# ============================================================================
# LLM and Agent Fixtures
# ============================================================================

@pytest.fixture
def mock_llm():
    """Create a mock LLM for testing."""
    mock = Mock()
    mock.ainvoke = AsyncMock()
    return mock


@pytest.fixture
def mock_embeddings():
    """Create mock embeddings for testing."""
    return Mock()


# ============================================================================
# API Client Fixture
# ============================================================================

@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    from src.api.main import create_app
    app = create_app()
    return TestClient(app)


# ============================================================================
# Database and State Manager Fixtures
# ============================================================================

@pytest.fixture
def tmp_db_path(tmp_path):
    """Create a temporary database path."""
    return tmp_path / "test.db"


@pytest.fixture
def state_manager(tmp_path):
    """Create a StateManager instance with a test database."""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite:///{db_path}"

    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "state_manager_module",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "src", "services", "state_manager.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    StateManager = module.StateManager
    return StateManager(database_url=db_url)


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_project_data():
    """Create sample project data for testing."""
    return {
        "client_name": "Test Corp",
        "project_name": "Test Project",
        "description": "Test description",
        "target_departments": ["Finance", "Operations"],
    }


@pytest.fixture
def sample_hypotheses():
    """Create sample hypotheses for testing."""
    from src.models.schemas import Hypothesis

    return [
        Hypothesis(
            id=str(uuid.uuid4()),
            process_area="Invoice Processing",
            description="Manual data entry causing delays",
            evidence=["Manual entry required", "Multiple data systems"],
            indicators=["manual", "delay"],
            confidence=0.8,
            category="manual_process",
        ),
        Hypothesis(
            id=str(uuid.uuid4()),
            process_area="Approval Workflow",
            description="Email-based approvals causing bottlenecks",
            evidence=["Email chains", "Delayed responses"],
            indicators=["approval", "email", "bottleneck"],
            confidence=0.7,
            category="communication_gap",
        ),
    ]


@pytest.fixture
def sample_interview_questions():
    """Create sample interview questions for testing."""
    from src.models.schemas import InterviewQuestion

    return [
        InterviewQuestion(
            role="CFO",
            question="How do you track expenses?",
            intent="Understand expense workflow",
            follow_ups=["What tools do you use?"],
        ),
        InterviewQuestion(
            role="Operations Manager",
            question="What are your biggest bottlenecks?",
            intent="Identify pain points",
            follow_ups=["How often does this occur?"],
        ),
    ]


@pytest.fixture
def sample_state(sample_project_data):
    """Create a sample workflow state for testing."""
    return {
        "project_id": "test-project-123",
        "project": {
            "id": "test-project-123",
            "client_name": sample_project_data["client_name"],
            "project_name": sample_project_data["project_name"],
            "industry": "Manufacturing",
            "target_departments": sample_project_data["target_departments"],
            "description": sample_project_data["description"],
        },
        "documents": [
            {
                "id": "doc1",
                "filename": "sales_sop.pdf",
                "file_type": "pdf",
                "source_type": "file",
                "processed": True,
                "chunk_count": 42,
            },
            {
                "id": "doc2",
                "filename": "www.company.com",
                "file_type": "url",
                "source_type": "url",
                "source_url": "https://www.company.com/docs",
                "processed": True,
                "chunk_count": 18,
            },
        ],
        "document_summaries": [
            "Sales SOP describes a 7-step manual approval process.",
            "Company website shows automated order submission API.",
            "Customer complaints mention frequent delays.",
        ],
        "hypotheses": [],
        "target_departments": sample_project_data["target_departments"],
        "messages": [],
        "errors": [],
    }


@pytest.fixture
def script_data():
    """Create sample interview script data."""
    return {
        "project_id": "test-project-123",
        "target_departments": ["Finance", "Operations"],
        "target_roles": ["CFO", "Operations Manager"],
        "introduction": "Thank you for taking the time to speak with us.",
        "questions": [
            {
                "role": "CFO",
                "question": "How do you track expenses?",
                "intent": "Understand expense workflow",
                "follow_ups": ["What tools do you use?"],
                "related_hypothesis_id": None,
            },
        ],
        "closing_notes": "Thank you for your insights.",
        "estimated_duration_minutes": 45,
        "generated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def project_data():
    """Create sample project metadata."""
    return {
        "id": "test-project-123",
        "client_name": "Test Corp",
        "project_name": "Process Improvement",
    }


# ============================================================================
# Helper Functions
# ============================================================================

def create_mock_state(
    num_documents=5,
    num_summaries=5,
    num_hypotheses=3,
    include_urls=True
):
    """Utility function to create mock state for testing."""
    documents = []
    for i in range(num_documents):
        if include_urls and i == 0:
            documents.append({
                "id": f"doc{i}",
                "filename": f"example{i}.com",
                "file_type": "url",
                "source_type": "url",
                "source_url": f"https://example{i}.com",
                "processed": True,
            })
        else:
            documents.append({
                "id": f"doc{i}",
                "filename": f"document{i}.pdf",
                "file_type": "pdf",
                "source_type": "file",
                "processed": True,
            })

    return {
        "project_id": "test-project",
        "project": {
            "client_name": "Test Corporation",
            "industry": "Technology",
            "target_departments": ["Engineering", "Sales"],
        },
        "documents": documents,
        "document_summaries": [f"Summary of document {i}" for i in range(num_summaries)],
        "hypotheses": [],
        "messages": [],
    }
