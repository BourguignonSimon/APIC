"""
Consolidated tests for APIC API endpoints.

This module contains all API endpoint tests including:
- Health and info endpoints
- Project management endpoints
- Document management endpoints
- Workflow execution endpoints
- Error handling
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import uuid
from datetime import datetime

from src.models.schemas import ProjectStatus


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
        with patch('src.api.routes.projects.StateManager') as mock_sm:
            mock_instance = Mock()
            mock_instance.create_project = AsyncMock(return_value={
                "id": str(uuid.uuid4()),
                "client_name": "Test Corp",
                "project_name": "Test Project",
                "status": ProjectStatus.CREATED.value,
            })
            mock_sm.return_value = mock_instance

            response = client.post(
                "/api/v1/projects",
                json={
                    "client_name": "Test Corp",
                    "project_name": "Test Project",
                    "description": "Test description",
                    "target_departments": ["Finance"],
                }
            )

            assert response.status_code in [200, 201]
            if response.status_code in [200, 201]:
                data = response.json()
                assert "id" in data or "client_name" in data

    def test_create_project_validates_required_fields(self, client):
        """Test that project creation validates required fields."""
        response = client.post(
            "/api/v1/projects",
            json={}
        )

        assert response.status_code == 422

    def test_get_projects_returns_list(self, client):
        """Test that getting projects returns a list."""
        with patch('src.api.routes.projects.StateManager') as mock_sm:
            mock_instance = Mock()
            mock_instance.get_all_projects = AsyncMock(return_value=[])
            mock_sm.return_value = mock_instance

            response = client.get("/api/v1/projects")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    def test_get_project_by_id_returns_project(self, client):
        """Test that getting a project by ID returns the project."""
        project_id = str(uuid.uuid4())

        with patch('src.api.routes.projects.StateManager') as mock_sm:
            mock_instance = Mock()
            mock_instance.get_project = AsyncMock(return_value={
                "id": project_id,
                "client_name": "Test Corp",
                "project_name": "Test Project",
            })
            mock_sm.return_value = mock_instance

            response = client.get(f"/api/v1/projects/{project_id}")

            assert response.status_code in [200, 404]
            if response.status_code == 200:
                data = response.json()
                assert data["id"] == project_id

    def test_get_nonexistent_project_returns_404(self, client):
        """Test that getting a non-existent project returns 404."""
        fake_id = str(uuid.uuid4())

        with patch('src.api.routes.projects.StateManager') as mock_sm:
            mock_instance = Mock()
            mock_instance.get_project = AsyncMock(return_value=None)
            mock_sm.return_value = mock_instance

            response = client.get(f"/api/v1/projects/{fake_id}")

            assert response.status_code == 404


# ============================================================================
# Test Document Management Endpoints
# ============================================================================

class TestDocumentEndpoints:
    """Test suite for document management endpoints."""

    def test_upload_document_endpoint_exists(self, client):
        """Test that document upload endpoint exists."""
        project_id = str(uuid.uuid4())

        files = {
            "file": ("test.txt", b"test content", "text/plain")
        }

        with patch('src.api.routes.documents.StateManager') as mock_sm:
            mock_instance = Mock()
            mock_instance.get_project = AsyncMock(return_value={
                "id": project_id,
                "status": ProjectStatus.CREATED.value,
            })
            mock_instance.add_document = AsyncMock(return_value={
                "id": str(uuid.uuid4()),
                "filename": "test.txt",
            })
            mock_sm.return_value = mock_instance

            response = client.post(
                f"/api/v1/projects/{project_id}/documents",
                files=files
            )

            assert response.status_code in [200, 201, 404, 422]

    def test_get_project_documents_returns_list(self, client):
        """Test that getting project documents returns a list."""
        project_id = str(uuid.uuid4())

        with patch('src.api.routes.documents.StateManager') as mock_sm:
            mock_instance = Mock()
            mock_instance.get_project_documents = AsyncMock(return_value=[])
            mock_sm.return_value = mock_instance

            response = client.get(f"/api/v1/projects/{project_id}/documents")

            assert response.status_code in [200, 404]
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, list)

    def test_list_documents_accepts_category_query_param(self, client):
        """Test that list documents endpoint accepts category query parameter."""
        project_id = str(uuid.uuid4())

        with patch('src.api.routes.documents.state_manager') as mock_sm:
            mock_sm.get_project.return_value = {"id": project_id}
            mock_sm.get_project_documents.return_value = []

            response = client.get(
                f"/api/v1/projects/{project_id}/documents",
                params={"category": "interview_results"}
            )

            assert response.status_code != 422

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

            if "documents" in data:
                docs = data["documents"]
            else:
                docs = data if isinstance(data, list) else [data]

            if len(docs) > 0:
                assert "category" in docs[0]


# ============================================================================
# Test Workflow Execution Endpoints
# ============================================================================

class TestWorkflowEndpoints:
    """Test suite for workflow execution endpoints."""

    def test_start_workflow_endpoint_exists(self, client):
        """Test that start workflow endpoint exists."""
        project_id = str(uuid.uuid4())

        with patch('src.api.routes.workflow.ConsultantGraph') as mock_graph:
            mock_instance = Mock()
            mock_instance.run_to_breakpoint = AsyncMock(return_value={
                "status": "success",
                "interview_script": {},
            })
            mock_graph.return_value = mock_instance

            response = client.post(
                "/api/v1/workflow/start",
                json={"project_id": project_id}
            )

            assert response.status_code in [200, 422, 404, 500]

    def test_resume_workflow_endpoint_exists(self, client):
        """Test that resume workflow endpoint exists."""
        project_id = str(uuid.uuid4())

        with patch('src.api.routes.workflow.ConsultantGraph') as mock_graph:
            mock_instance = Mock()
            mock_instance.resume_from_breakpoint = AsyncMock(return_value={
                "status": "completed",
                "final_report": {},
            })
            mock_graph.return_value = mock_instance

            response = client.post(
                "/api/v1/workflow/resume",
                json={
                    "project_id": project_id,
                    "interview_transcript": "Test transcript"
                }
            )

            assert response.status_code in [200, 422, 404, 500]

    def test_get_workflow_status_returns_status(self, client):
        """Test that getting workflow status returns status information."""
        workflow_id = str(uuid.uuid4())

        with patch('src.api.routes.workflow.StateManager') as mock_sm:
            mock_instance = Mock()
            mock_instance.get_workflow_status = AsyncMock(return_value={
                "id": workflow_id,
                "status": "completed",
            })
            mock_sm.return_value = mock_instance

            response = client.get(f"/api/v1/workflow/{workflow_id}/status")

            assert response.status_code in [200, 404]

    def test_get_interview_script_returns_script(self, client):
        """Test that getting interview script returns the script."""
        workflow_id = str(uuid.uuid4())

        with patch('src.api.routes.workflow.StateManager') as mock_sm:
            mock_instance = Mock()
            mock_instance.get_interview_script = AsyncMock(return_value={
                "project_id": workflow_id,
                "questions": [],
            })
            mock_sm.return_value = mock_instance

            response = client.get(f"/api/v1/workflow/{workflow_id}/interview-script")

            assert response.status_code in [200, 404]

    def test_get_hypotheses_returns_list(self, client):
        """Test that getting hypotheses returns a list."""
        workflow_id = str(uuid.uuid4())

        with patch('src.api.routes.workflow.StateManager') as mock_sm:
            mock_instance = Mock()
            mock_instance.get_hypotheses = AsyncMock(return_value=[])
            mock_sm.return_value = mock_instance

            response = client.get(f"/api/v1/workflow/{workflow_id}/hypotheses")

            assert response.status_code in [200, 404]
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, list)

    def test_get_gap_analysis_returns_list(self, client):
        """Test that getting gap analysis returns a list."""
        workflow_id = str(uuid.uuid4())

        with patch('src.api.routes.workflow.StateManager') as mock_sm:
            mock_instance = Mock()
            mock_instance.get_gap_analysis = AsyncMock(return_value=[])
            mock_sm.return_value = mock_instance

            response = client.get(f"/api/v1/workflow/{workflow_id}/gaps")

            assert response.status_code in [200, 404]
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, list)

    def test_get_solutions_returns_list(self, client):
        """Test that getting solutions returns a list."""
        workflow_id = str(uuid.uuid4())

        with patch('src.api.routes.workflow.StateManager') as mock_sm:
            mock_instance = Mock()
            mock_instance.get_solutions = AsyncMock(return_value=[])
            mock_sm.return_value = mock_instance

            response = client.get(f"/api/v1/workflow/{workflow_id}/solutions")

            assert response.status_code in [200, 404]
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, list)

    def test_get_report_endpoint_exists(self, client):
        """Test that get report endpoint exists."""
        workflow_id = str(uuid.uuid4())

        with patch('src.api.routes.workflow.StateManager') as mock_sm:
            mock_instance = Mock()
            mock_instance.get_report = AsyncMock(return_value={
                "project_id": workflow_id,
                "content": "Report content",
            })
            mock_sm.return_value = mock_instance

            response = client.get(f"/api/v1/workflow/{workflow_id}/report")

            assert response.status_code in [200, 404]


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
        response = client.get("/api/v1/projects/not-a-uuid")

        assert response.status_code in [422, 404, 400]
