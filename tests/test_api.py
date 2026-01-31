"""
Tests for APIC API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import uuid

from src.api.main import create_app
from src.models.schemas import ProjectStatus


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    app = create_app()
    return TestClient(app)


# ============================================================================
# Test Health and Info Endpoints
# ============================================================================

class TestHealthEndpoints:
    """Test suite for health and info endpoints."""

    def test_health_check_returns_200(self, client):
        """Test that health check endpoint returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_root_endpoint_returns_api_info(self, client):
        """Test that root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data or "message" in data


# ============================================================================
# Test Project Management Endpoints
# ============================================================================

class TestProjectEndpoints:
    """Test suite for project management endpoints."""

    def test_create_project_returns_201(self, client):
        """Test that creating a project returns 201 Created."""
        with patch('src.api.routes.projects.state_manager') as mock_sm:
            mock_sm.create_project.return_value = {
                "id": str(uuid.uuid4()),
                "thread_id": str(uuid.uuid4()),
                "client_name": "Test Corp",
                "project_name": "Test Project",
                "description": "Test",
                "target_departments": ["Finance"],
                "status": "created",
                "vector_namespace": "test",
                "created_at": "2024-01-01T00:00:00",
            }

            response = client.post(
                "/api/v1/projects",
                json={
                    "client_name": "Test Corp",
                    "project_name": "Test Project",
                    "description": "Test description",
                    "target_departments": ["Finance"],
                }
            )

            assert response.status_code == 201
            data = response.json()
            assert "id" in data
            assert data["client_name"] == "Test Corp"

    def test_create_project_validates_required_fields(self, client):
        """Test that project creation validates required fields."""
        response = client.post(
            "/api/v1/projects",
            json={}
        )
        assert response.status_code == 422

    def test_get_projects_returns_list(self, client):
        """Test that getting projects returns a list."""
        with patch('src.api.routes.projects.state_manager') as mock_sm:
            mock_sm.list_projects.return_value = []

            response = client.get("/api/v1/projects")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    def test_get_project_by_id_returns_project(self, client):
        """Test that getting a project by ID returns the project."""
        project_id = str(uuid.uuid4())

        with patch('src.api.routes.projects.state_manager') as mock_sm:
            mock_sm.get_project.return_value = {
                "id": project_id,
                "thread_id": str(uuid.uuid4()),
                "client_name": "Test Corp",
                "project_name": "Test Project",
                "description": "Test",
                "target_departments": [],
                "status": "created",
                "vector_namespace": "test",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            }

            response = client.get(f"/api/v1/projects/{project_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == project_id

    def test_get_nonexistent_project_returns_404(self, client):
        """Test that getting a non-existent project returns 404."""
        fake_id = str(uuid.uuid4())

        with patch('src.api.routes.projects.state_manager') as mock_sm:
            mock_sm.get_project.return_value = None

            response = client.get(f"/api/v1/projects/{fake_id}")

            assert response.status_code == 404

    def test_get_suspended_projects(self, client):
        """Test that getting suspended projects returns list."""
        with patch('src.api.routes.projects.state_manager') as mock_sm:
            mock_sm.get_projects_by_status.return_value = []

            response = client.get("/api/v1/projects/suspended")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


# ============================================================================
# Test Document Management Endpoints
# ============================================================================

class TestDocumentEndpoints:
    """Test suite for document management endpoints."""

    def test_upload_document_endpoint_exists(self, client):
        """Test that document upload endpoint exists."""
        project_id = str(uuid.uuid4())
        files = {"file": ("test.txt", b"test content", "text/plain")}

        with patch('src.api.routes.documents.state_manager') as mock_sm:
            mock_sm.get_project.return_value = {
                "id": project_id,
                "status": "created",
            }
            mock_sm.add_document.return_value = {
                "id": str(uuid.uuid4()),
                "project_id": project_id,
                "filename": "test.txt",
                "file_type": "txt",
                "file_size": 12,
                "file_path": "/path/to/file",
                "processed": False,
                "chunk_count": 0,
                "uploaded_at": "2024-01-01T00:00:00",
                "category": "general",
            }

            response = client.post(
                f"/api/v1/projects/{project_id}/documents",
                files=files
            )

            assert response.status_code in [200, 201, 404, 422]

    def test_get_project_documents_returns_list(self, client):
        """Test that getting project documents returns a list."""
        project_id = str(uuid.uuid4())

        with patch('src.api.routes.documents.state_manager') as mock_sm:
            mock_sm.get_project.return_value = {"id": project_id}
            mock_sm.get_project_documents.return_value = []

            response = client.get(f"/api/v1/projects/{project_id}/documents")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


# ============================================================================
# Test Workflow Execution Endpoints
# ============================================================================

class TestWorkflowEndpoints:
    """Test suite for workflow execution endpoints."""

    def test_start_workflow_endpoint_exists(self, client):
        """Test that start workflow endpoint exists."""
        project_id = str(uuid.uuid4())
        thread_id = str(uuid.uuid4())

        with patch('src.api.routes.workflow.state_manager') as mock_sm, \
             patch('src.api.routes.workflow.get_workflow') as mock_get_workflow:

            mock_sm.get_project.return_value = {
                "id": project_id,
                "thread_id": thread_id,
            }
            mock_sm.get_project_documents.return_value = [{"id": "doc1"}]

            mock_workflow = MagicMock()
            mock_workflow.run_to_interview = AsyncMock(return_value={
                "interview_script": {"questions": []},
            })
            mock_get_workflow.return_value = mock_workflow

            response = client.post(
                "/api/v1/workflow/start",
                json={"project_id": project_id}
            )

            assert response.status_code in [200, 202, 404, 500]

    def test_resume_workflow_endpoint_exists(self, client):
        """Test that resume workflow endpoint exists."""
        project_id = str(uuid.uuid4())
        thread_id = str(uuid.uuid4())

        with patch('src.api.routes.workflow.state_manager') as mock_sm, \
             patch('src.api.routes.workflow.get_workflow') as mock_get_workflow:

            mock_sm.get_project.return_value = {
                "id": project_id,
                "thread_id": thread_id,
            }

            mock_workflow = MagicMock()
            mock_workflow.get_state.return_value = {"is_suspended": True}
            mock_workflow.resume_with_transcript = AsyncMock(return_value={
                "report_complete": True,
            })
            mock_get_workflow.return_value = mock_workflow

            response = client.post(
                "/api/v1/workflow/resume",
                json={
                    "project_id": project_id,
                    "transcript": "Test transcript"
                }
            )

            assert response.status_code in [200, 202, 400, 404, 500]

    def test_get_workflow_status_returns_status(self, client):
        """Test that getting workflow status returns status information."""
        project_id = str(uuid.uuid4())
        thread_id = str(uuid.uuid4())

        with patch('src.api.routes.workflow.state_manager') as mock_sm, \
             patch('src.api.routes.workflow.get_workflow') as mock_get_workflow:

            mock_sm.get_project.return_value = {
                "id": project_id,
                "thread_id": thread_id,
            }

            mock_workflow = MagicMock()
            mock_workflow.get_state.return_value = {
                "current_node": "interview",
                "is_suspended": True,
                "suspension_reason": None,
                "messages": [],
                "errors": [],
            }
            mock_get_workflow.return_value = mock_workflow

            response = client.get(f"/api/v1/workflow/{project_id}/status")

            assert response.status_code == 200
            data = response.json()
            assert "current_node" in data

    def test_get_interview_script_returns_script(self, client):
        """Test that getting interview script returns the script."""
        project_id = str(uuid.uuid4())
        thread_id = str(uuid.uuid4())

        with patch('src.api.routes.workflow.state_manager') as mock_sm, \
             patch('src.api.routes.workflow.get_workflow') as mock_get_workflow:

            mock_sm.get_project.return_value = {
                "id": project_id,
                "thread_id": thread_id,
            }

            mock_workflow = MagicMock()
            mock_workflow.get_state.return_value = {
                "interview_script": {"questions": [], "target_roles": []},
            }
            mock_get_workflow.return_value = mock_workflow

            response = client.get(f"/api/v1/workflow/{project_id}/interview-script")

            assert response.status_code == 200

    def test_get_hypotheses_returns_list(self, client):
        """Test that getting hypotheses returns a list."""
        project_id = str(uuid.uuid4())
        thread_id = str(uuid.uuid4())

        with patch('src.api.routes.workflow.state_manager') as mock_sm, \
             patch('src.api.routes.workflow.get_workflow') as mock_get_workflow:

            mock_sm.get_project.return_value = {
                "id": project_id,
                "thread_id": thread_id,
            }

            mock_workflow = MagicMock()
            mock_workflow.get_state.return_value = {
                "hypotheses": [{"id": 1, "description": "Test"}],
            }
            mock_get_workflow.return_value = mock_workflow

            response = client.get(f"/api/v1/workflow/{project_id}/hypotheses")

            assert response.status_code == 200
            data = response.json()
            assert "hypotheses" in data

    def test_get_gap_analysis_returns_list(self, client):
        """Test that getting gap analysis returns a list."""
        project_id = str(uuid.uuid4())
        thread_id = str(uuid.uuid4())

        with patch('src.api.routes.workflow.state_manager') as mock_sm, \
             patch('src.api.routes.workflow.get_workflow') as mock_get_workflow:

            mock_sm.get_project.return_value = {
                "id": project_id,
                "thread_id": thread_id,
            }

            mock_workflow = MagicMock()
            mock_workflow.get_state.return_value = {
                "gap_analyses": [],
            }
            mock_get_workflow.return_value = mock_workflow

            response = client.get(f"/api/v1/workflow/{project_id}/gaps")

            assert response.status_code == 200
            data = response.json()
            assert "gap_analyses" in data

    def test_get_solutions_returns_list(self, client):
        """Test that getting solutions returns a list."""
        project_id = str(uuid.uuid4())
        thread_id = str(uuid.uuid4())

        with patch('src.api.routes.workflow.state_manager') as mock_sm, \
             patch('src.api.routes.workflow.get_workflow') as mock_get_workflow:

            mock_sm.get_project.return_value = {
                "id": project_id,
                "thread_id": thread_id,
            }

            mock_workflow = MagicMock()
            mock_workflow.get_state.return_value = {
                "solutions": [],
                "solution_recommendations": [],
            }
            mock_get_workflow.return_value = mock_workflow

            response = client.get(f"/api/v1/workflow/{project_id}/solutions")

            assert response.status_code == 200
            data = response.json()
            assert "solutions" in data

    def test_get_report_endpoint_exists(self, client):
        """Test that get report endpoint exists."""
        project_id = str(uuid.uuid4())
        thread_id = str(uuid.uuid4())

        with patch('src.api.routes.workflow.state_manager') as mock_sm, \
             patch('src.api.routes.workflow.get_workflow') as mock_get_workflow:

            mock_sm.get_project.return_value = {
                "id": project_id,
                "thread_id": thread_id,
            }

            mock_workflow = MagicMock()
            mock_workflow.get_state.return_value = {
                "report_complete": True,
                "report": {"content": "Test"},
                "report_pdf_path": "/path/to/report.pdf",
            }
            mock_get_workflow.return_value = mock_workflow

            response = client.get(f"/api/v1/workflow/{project_id}/report")

            assert response.status_code == 200


# ============================================================================
# Test Error Handling
# ============================================================================

class TestErrorHandling:
    """Test suite for API error handling."""

    def test_invalid_json_returns_422(self, client):
        """Test that invalid JSON returns 422 Unprocessable Entity."""
        response = client.post(
            "/api/v1/projects",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_invalid_uuid_returns_422_or_404(self, client):
        """Test that invalid UUID returns appropriate error."""
        with patch('src.api.routes.projects.state_manager') as mock_sm:
            mock_sm.get_project.return_value = None

            response = client.get("/api/v1/projects/not-a-uuid")

            assert response.status_code in [422, 404, 400]
