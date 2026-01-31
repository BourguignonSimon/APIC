"""
Tests for workflow orchestration and state management.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import uuid

from src.services.workflow import ConsultantGraph, WorkflowState, get_workflow, create_workflow
from src.services.state_manager import StateManager
from src.models.schemas import GraphState, ProjectStatus


# ============================================================================
# Test ConsultantGraph (Workflow Orchestration)
# ============================================================================

class TestConsultantGraph:
    """Test suite for ConsultantGraph workflow orchestration."""

    @pytest.fixture
    def graph(self):
        """Create a ConsultantGraph instance for testing."""
        with patch('src.services.workflow.get_agent_config') as mock_config:
            mock_config.return_value.get_agent_config.return_value = {}
            return ConsultantGraph()

    def test_graph_initialization(self, graph):
        """Test that ConsultantGraph initializes properly."""
        assert graph is not None
        assert graph.workflow is not None
        assert graph.checkpointer is not None

    def test_get_initial_state(self, graph):
        """Test that get_initial_state returns proper WorkflowState."""
        project_id = str(uuid.uuid4())
        state = graph.get_initial_state(
            project_id=project_id,
            project={"name": "Test"},
            documents=[{"id": "doc1"}],
        )

        assert state["project_id"] == project_id
        assert state["documents"] == [{"id": "doc1"}]
        assert state["ingestion_complete"] is False
        assert state["is_suspended"] is False

    @pytest.mark.asyncio
    async def test_run_to_interview(self, graph):
        """Test that run_to_interview executes workflow."""
        project_id = str(uuid.uuid4())
        thread_id = str(uuid.uuid4())

        with patch.object(graph.workflow, 'ainvoke', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = {
                "project_id": project_id,
                "is_suspended": True,
                "interview_script": {"questions": []},
            }

            result = await graph.run_to_interview(
                project_id=project_id,
                project={"name": "Test"},
                documents=[],
                thread_id=thread_id,
            )

            assert result is not None
            assert result["project_id"] == project_id
            mock_invoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_resume_with_transcript(self, graph):
        """Test that resume_with_transcript continues workflow."""
        thread_id = str(uuid.uuid4())

        with patch.object(graph.workflow, 'get_state') as mock_get_state, \
             patch.object(graph.workflow, 'ainvoke', new_callable=AsyncMock) as mock_invoke:
            mock_get_state.return_value = MagicMock(values={
                "is_suspended": True,
                "transcript": None,
            })
            mock_invoke.return_value = {
                "is_suspended": False,
                "transcript": "Test transcript",
                "report_complete": True,
            }

            result = await graph.resume_with_transcript(
                thread_id=thread_id,
                transcript="Test transcript",
            )

            assert result is not None
            assert result["transcript"] == "Test transcript"
            mock_invoke.assert_called_once()

    def test_get_state(self, graph):
        """Test that get_state retrieves workflow state."""
        thread_id = str(uuid.uuid4())

        with patch.object(graph.workflow, 'get_state') as mock_get_state:
            mock_get_state.return_value = MagicMock(values={
                "project_id": "test",
                "current_node": "interview",
            })

            result = graph.get_state(thread_id)

            assert result is not None
            assert result["current_node"] == "interview"

    def test_get_state_returns_none_on_error(self, graph):
        """Test that get_state returns None on error."""
        thread_id = str(uuid.uuid4())

        with patch.object(graph.workflow, 'get_state', side_effect=Exception("Error")):
            result = graph.get_state(thread_id)
            assert result is None

    def test_should_wait_for_transcript(self, graph):
        """Test the conditional edge logic."""
        # Should wait when suspended and no transcript
        state_suspended = {"is_suspended": True, "transcript_received": False}
        assert graph._should_wait_for_transcript(state_suspended) == "wait"

        # Should continue when transcript received
        state_with_transcript = {"is_suspended": True, "transcript_received": True}
        assert graph._should_wait_for_transcript(state_with_transcript) == "continue"

        # Should continue when not suspended
        state_not_suspended = {"is_suspended": False, "transcript_received": False}
        assert graph._should_wait_for_transcript(state_not_suspended) == "continue"


class TestWorkflowFactoryFunctions:
    """Test workflow factory functions."""

    def test_create_workflow(self):
        """Test that create_workflow returns a new instance."""
        with patch('src.services.workflow.get_agent_config') as mock_config:
            mock_config.return_value.get_agent_config.return_value = {}

            workflow1 = create_workflow()
            workflow2 = create_workflow()

            assert workflow1 is not workflow2

    def test_get_workflow_singleton(self):
        """Test that get_workflow returns singleton instance."""
        import src.services.workflow as workflow_module
        workflow_module._workflow_instance = None

        with patch('src.services.workflow.get_agent_config') as mock_config:
            mock_config.return_value.get_agent_config.return_value = {}

            workflow1 = get_workflow()
            workflow2 = get_workflow()

            assert workflow1 is workflow2

        workflow_module._workflow_instance = None


# ============================================================================
# Test StateManager (Data Persistence)
# ============================================================================

class TestStateManager:
    """Test suite for StateManager."""

    @pytest.fixture
    def mock_engine(self):
        """Create a mock SQLAlchemy engine."""
        with patch('src.services.state_manager.create_engine') as mock_create:
            mock_engine = MagicMock()
            mock_create.return_value = mock_engine
            yield mock_engine

    @pytest.fixture
    def state_manager(self, mock_engine):
        """Create a StateManager instance for testing."""
        with patch('src.services.state_manager.inspect') as mock_inspect:
            mock_inspect.return_value.get_table_names.return_value = []
            return StateManager(database_url="sqlite:///:memory:")

    def test_initialization(self, state_manager):
        """Test that StateManager initializes properly."""
        assert state_manager is not None
        assert state_manager.engine is not None
        assert state_manager.SessionLocal is not None

    def test_create_project(self, state_manager):
        """Test that create_project creates a project with thread_id."""
        with patch.object(state_manager, 'get_session') as mock_session:
            mock_db = MagicMock()
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=False)
            mock_session.return_value = mock_db

            result = state_manager.create_project(
                client_name="Test Corp",
                project_name="Test Project",
                description="Test",
                target_departments=["Finance"],
            )

            assert result is not None
            assert "id" in result
            assert "thread_id" in result
            assert result["client_name"] == "Test Corp"

    def test_get_project(self, state_manager):
        """Test that get_project retrieves project data."""
        project_id = str(uuid.uuid4())

        with patch.object(state_manager, 'get_session') as mock_session:
            mock_db = MagicMock()
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=False)
            mock_db.query.return_value.filter_by.return_value.first.return_value = None
            mock_session.return_value = mock_db

            result = state_manager.get_project(project_id)
            assert result is None

    def test_list_projects(self, state_manager):
        """Test that list_projects returns all projects."""
        with patch.object(state_manager, 'get_session') as mock_session:
            mock_db = MagicMock()
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=False)
            mock_db.query.return_value.order_by.return_value.all.return_value = []
            mock_session.return_value = mock_db

            result = state_manager.list_projects()
            assert isinstance(result, list)

    def test_update_project_status(self, state_manager):
        """Test that update_project_status changes status."""
        project_id = str(uuid.uuid4())

        with patch.object(state_manager, 'get_session') as mock_session:
            mock_db = MagicMock()
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=False)
            mock_project = MagicMock()
            mock_db.query.return_value.filter_by.return_value.first.return_value = mock_project
            mock_session.return_value = mock_db

            state_manager.update_project_status(project_id, "completed")

            assert mock_project.status == "completed"
            mock_db.commit.assert_called_once()

    def test_get_projects_by_status(self, state_manager):
        """Test that get_projects_by_status filters correctly."""
        with patch.object(state_manager, 'get_session') as mock_session:
            mock_db = MagicMock()
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=False)
            mock_db.query.return_value.filter_by.return_value.all.return_value = []
            mock_session.return_value = mock_db

            result = state_manager.get_projects_by_status("interview_ready")
            assert isinstance(result, list)

    def test_add_document(self, state_manager):
        """Test that add_document creates document record."""
        project_id = str(uuid.uuid4())

        with patch.object(state_manager, 'get_session') as mock_session:
            mock_db = MagicMock()
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=False)
            mock_session.return_value = mock_db

            result = state_manager.add_document(
                project_id=project_id,
                filename="test.pdf",
                file_type="pdf",
                file_size=1024,
                file_path="/path/to/file",
                category="general",
            )

            assert result is not None
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    def test_get_project_documents(self, state_manager):
        """Test that get_project_documents retrieves documents."""
        project_id = str(uuid.uuid4())

        with patch.object(state_manager, 'get_session') as mock_session:
            mock_db = MagicMock()
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=False)
            mock_db.query.return_value.filter_by.return_value.all.return_value = []
            mock_session.return_value = mock_db

            result = state_manager.get_project_documents(project_id)
            assert isinstance(result, list)

    def test_get_project_documents_with_category_filter(self, state_manager):
        """Test that get_project_documents can filter by category."""
        project_id = str(uuid.uuid4())

        with patch.object(state_manager, 'get_session') as mock_session:
            mock_db = MagicMock()
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=False)
            query_mock = MagicMock()
            mock_db.query.return_value.filter_by.return_value = query_mock
            query_mock.filter_by.return_value.all.return_value = []
            mock_session.return_value = mock_db

            result = state_manager.get_project_documents(project_id, category="interview_results")
            assert isinstance(result, list)


# ============================================================================
# Test GraphState Model
# ============================================================================

class TestGraphState:
    """Test suite for GraphState model."""

    def test_graph_state_initialization(self):
        """Test that GraphState can be initialized with required fields."""
        state = GraphState(
            project_id="test-123",
            client_name="Test Corp",
            project_name="Test Project",
        )

        assert state.project_id == "test-123"
        assert state.client_name == "Test Corp"
        assert state.messages == []
        assert state.errors == []

    def test_graph_state_defaults(self):
        """Test that GraphState has proper default values."""
        state = GraphState(
            project_id="test-123",
            client_name="Test Corp",
            project_name="Test Project",
        )

        assert state.documents == []
        assert state.hypotheses == []
        assert state.ingestion_complete is False
        assert state.is_suspended is False
        assert state.final_report is None

    def test_graph_state_serialization(self):
        """Test that GraphState can be serialized to dict."""
        state = GraphState(
            project_id="test-123",
            client_name="Test Corp",
            project_name="Test Project",
        )

        state_dict = state.model_dump()
        assert isinstance(state_dict, dict)
        assert state_dict["project_id"] == "test-123"


# ============================================================================
# Test WorkflowState TypedDict
# ============================================================================

class TestWorkflowState:
    """Test suite for WorkflowState TypedDict."""

    def test_workflow_state_structure(self):
        """Test that WorkflowState has expected fields."""
        state: WorkflowState = {
            "project_id": "test-123",
            "project": None,
            "documents": [],
            "ingestion_complete": False,
            "document_summaries": [],
            "hypotheses": [],
            "hypothesis_generation_complete": False,
            "interview_script": None,
            "script_generation_complete": False,
            "is_suspended": False,
            "suspension_reason": None,
            "transcript": None,
            "transcript_received": False,
            "gap_analyses": [],
            "gap_analysis_complete": False,
            "solutions": [],
            "solution_recommendations": [],
            "solutioning_complete": False,
            "report": None,
            "report_complete": False,
            "report_pdf_path": None,
            "current_node": "start",
            "errors": [],
            "messages": [],
        }

        assert state["project_id"] == "test-123"
        assert state["is_suspended"] is False
        assert state["current_node"] == "start"
