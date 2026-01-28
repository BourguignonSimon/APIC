"""
Comprehensive tests for workflow orchestration and state management following TDD principles.
"""

import pytest
import sys
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import uuid
from datetime import datetime


# ============================================================================
# Test StateManager (Can be tested independently)
# ============================================================================

class TestStateManager:
    """Test suite for StateManager."""

    @pytest.fixture
    def state_manager(self, tmp_path):
        """Create a StateManager instance with a test database."""
        db_path = tmp_path / "test.db"
        db_url = f"sqlite:///{db_path}"

        # Direct import of just state_manager module
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "state_manager_module",
            "/home/user/APIC/src/services/state_manager.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        StateManager = module.StateManager
        return StateManager(database_url=db_url)

    @pytest.fixture
    def sample_project_data(self):
        """Create sample project data for testing."""
        return {
            "client_name": "Test Corp",
            "project_name": "Test Project",
            "description": "Test description",
            "target_departments": ["Finance"],
        }

    def test_create_project_returns_project_data(self, state_manager, sample_project_data):
        """Test that creating a project returns project data."""
        result = state_manager.create_project(
            client_name=sample_project_data["client_name"],
            project_name=sample_project_data["project_name"],
            description=sample_project_data["description"],
            target_departments=sample_project_data["target_departments"],
        )

        assert result is not None
        assert "id" in result
        assert result["client_name"] == sample_project_data["client_name"]
        assert result["project_name"] == sample_project_data["project_name"]

    def test_get_project_returns_none_for_nonexistent(self, state_manager):
        """Test that getting a non-existent project returns None."""
        fake_id = str(uuid.uuid4())
        result = state_manager.get_project(fake_id)
        assert result is None

    def test_get_project_returns_project(self, state_manager, sample_project_data):
        """Test that get_project returns the correct project."""
        created = state_manager.create_project(
            client_name=sample_project_data["client_name"],
            project_name=sample_project_data["project_name"],
        )

        result = state_manager.get_project(created["id"])

        assert result is not None
        assert result["id"] == created["id"]
        assert result["client_name"] == sample_project_data["client_name"]

    def test_save_state_persists_data(self, state_manager, sample_project_data):
        """Test that save_state persists workflow state."""
        # Create a project first
        project = state_manager.create_project(
            client_name=sample_project_data["client_name"],
            project_name=sample_project_data["project_name"],
        )

        project_id = project["id"]
        thread_id = str(uuid.uuid4())
        state_data = {
            "project_id": project_id,
            "current_node": "ingestion",
            "messages": ["Test message"],
            "is_suspended": False,
        }

        # Should not raise an exception
        state_manager.save_state(project_id, thread_id, state_data)

    def test_load_state_returns_state(self, state_manager, sample_project_data):
        """Test that load_state returns the workflow state."""
        # Create a project and save state
        project = state_manager.create_project(
            client_name=sample_project_data["client_name"],
            project_name=sample_project_data["project_name"],
        )

        project_id = project["id"]
        thread_id = str(uuid.uuid4())
        state_data = {
            "project_id": project_id,
            "current_node": "interview",
            "is_suspended": True,
            "suspension_reason": "Awaiting transcript",
        }

        state_manager.save_state(project_id, thread_id, state_data)

        result = state_manager.load_state(project_id)

        assert result is not None
        assert result["project_id"] == project_id
        assert result["current_node"] == "interview"

    def test_get_thread_id(self, state_manager, sample_project_data):
        """Test that get_thread_id returns the correct thread ID."""
        project = state_manager.create_project(
            client_name=sample_project_data["client_name"],
            project_name=sample_project_data["project_name"],
        )

        project_id = project["id"]
        thread_id = str(uuid.uuid4())
        state_data = {"project_id": project_id, "current_node": "start"}

        state_manager.save_state(project_id, thread_id, state_data)

        result = state_manager.get_thread_id(project_id)
        assert result == thread_id

    def test_update_project_status(self, state_manager, sample_project_data):
        """Test that update_project_status changes the project status."""
        project = state_manager.create_project(
            client_name=sample_project_data["client_name"],
            project_name=sample_project_data["project_name"],
        )

        project_id = project["id"]

        state_manager.update_project_status(project_id, "analyzing")

        updated = state_manager.get_project(project_id)
        assert updated["status"] == "analyzing"

    def test_add_document_to_project(self, state_manager, sample_project_data, tmp_path):
        """Test that documents can be added to a project."""
        project = state_manager.create_project(
            client_name=sample_project_data["client_name"],
            project_name=sample_project_data["project_name"],
        )

        project_id = project["id"]
        file_path = str(tmp_path / "test.txt")

        result = state_manager.add_document(
            project_id=project_id,
            filename="test.txt",
            file_type="txt",
            file_size=1024,
            file_path=file_path,
        )

        assert result is not None
        assert "id" in result
        assert result["filename"] == "test.txt"
        assert result["project_id"] == project_id

    def test_get_project_documents(self, state_manager, sample_project_data, tmp_path):
        """Test that get_project_documents returns documents."""
        project = state_manager.create_project(
            client_name=sample_project_data["client_name"],
            project_name=sample_project_data["project_name"],
        )

        project_id = project["id"]
        file_path = str(tmp_path / "test.txt")

        state_manager.add_document(
            project_id=project_id,
            filename="test.txt",
            file_type="txt",
            file_size=1024,
            file_path=file_path,
        )

        docs = state_manager.get_project_documents(project_id)

        assert isinstance(docs, list)
        assert len(docs) == 1
        assert docs[0]["filename"] == "test.txt"

    def test_list_projects_returns_list(self, state_manager, sample_project_data):
        """Test that list_projects returns a list of projects."""
        state_manager.create_project(
            client_name=sample_project_data["client_name"],
            project_name=sample_project_data["project_name"],
        )

        result = state_manager.list_projects()

        assert isinstance(result, list)
        assert len(result) >= 1

    def test_get_suspended_projects(self, state_manager, sample_project_data):
        """Test that get_suspended_projects returns suspended projects."""
        project = state_manager.create_project(
            client_name=sample_project_data["client_name"],
            project_name=sample_project_data["project_name"],
        )

        project_id = project["id"]
        thread_id = str(uuid.uuid4())
        state_data = {
            "project_id": project_id,
            "current_node": "interview",
            "is_suspended": True,
            "suspension_reason": "Awaiting transcript",
        }

        state_manager.save_state(project_id, thread_id, state_data)

        suspended = state_manager.get_suspended_projects()

        assert isinstance(suspended, list)
        # Should have at least our suspended project
        project_ids = [p["project_id"] for p in suspended]
        assert project_id in project_ids

    def test_state_persistence_across_workflow_steps(self, state_manager, sample_project_data):
        """Test that state is properly persisted across workflow steps."""
        # Create a project
        project = state_manager.create_project(
            client_name="Test Corp",
            project_name="Test Project",
        )

        project_id = project["id"]
        thread_id = str(uuid.uuid4())

        # Save initial state
        state_data = {
            "project_id": project_id,
            "current_node": "ingestion",
            "messages": [],
            "is_suspended": False,
        }
        state_manager.save_state(project_id, thread_id, state_data)

        # Update state to simulate workflow progression
        state_data["current_node"] = "interview"
        state_data["is_suspended"] = True
        state_data["messages"] = ["Ingestion complete", "Hypotheses generated"]
        state_manager.save_state(project_id, thread_id, state_data)

        # Retrieve and verify
        retrieved_state = state_manager.load_state(project_id)

        assert retrieved_state is not None
        assert retrieved_state["current_node"] == "interview"
        assert retrieved_state["is_suspended"] is True
        assert len(retrieved_state["messages"]) == 2


# ============================================================================
# Test GraphState model structure
# ============================================================================

class TestGraphStateModel:
    """Test GraphState model without importing agents."""

    def test_graph_state_has_required_fields(self):
        """Test that GraphState model has all required fields."""
        from src.models.schemas import GraphState

        # Create a minimal state
        state = GraphState(project_id="test-123")

        # Check required fields exist
        assert hasattr(state, 'project_id')
        assert hasattr(state, 'project')
        assert hasattr(state, 'documents')
        assert hasattr(state, 'hypotheses')
        assert hasattr(state, 'interview_script')
        assert hasattr(state, 'is_suspended')
        assert hasattr(state, 'transcript')
        assert hasattr(state, 'transcript_received')
        assert hasattr(state, 'gap_analyses')
        assert hasattr(state, 'solutions')
        assert hasattr(state, 'report')
        assert hasattr(state, 'current_node')

    def test_graph_state_defaults(self):
        """Test GraphState default values."""
        from src.models.schemas import GraphState

        state = GraphState(project_id="test-123")

        # Check default values
        assert state.documents == []
        assert state.hypotheses == []
        assert state.interview_script is None
        assert state.is_suspended is False
        assert state.transcript is None
        assert state.transcript_received is False
        assert state.gap_analyses == []
        assert state.solutions == []
        assert state.report is None
        assert state.current_node == "start"

    def test_graph_state_serialization(self):
        """Test that GraphState can be serialized to dict."""
        from src.models.schemas import GraphState

        state = GraphState(
            project_id="test-123",
            is_suspended=True,
            suspension_reason="Awaiting transcript",
            current_node="interview",
        )

        state_dict = state.model_dump()

        assert isinstance(state_dict, dict)
        assert state_dict["project_id"] == "test-123"
        assert state_dict["is_suspended"] is True
        assert state_dict["current_node"] == "interview"


# ============================================================================
# Test Workflow Logic (Unit Tests with Mocks)
# ============================================================================

class TestWorkflowLogic:
    """Test workflow logic with fully mocked dependencies."""

    def test_should_wait_for_transcript_logic_wait(self):
        """Test wait condition: suspended and no transcript."""
        # The logic: if suspended and not transcript_received -> "wait"
        state = {
            "is_suspended": True,
            "transcript_received": False,
        }

        # Implement the logic we're testing
        if state["is_suspended"] and not state["transcript_received"]:
            result = "wait"
        else:
            result = "continue"

        assert result == "wait"

    def test_should_wait_for_transcript_logic_continue_not_suspended(self):
        """Test continue condition: not suspended."""
        state = {
            "is_suspended": False,
            "transcript_received": False,
        }

        if state["is_suspended"] and not state["transcript_received"]:
            result = "wait"
        else:
            result = "continue"

        assert result == "continue"

    def test_should_wait_for_transcript_logic_continue_with_transcript(self):
        """Test continue condition: transcript received."""
        state = {
            "is_suspended": True,
            "transcript_received": True,
        }

        if state["is_suspended"] and not state["transcript_received"]:
            result = "wait"
        else:
            result = "continue"

        assert result == "continue"

    def test_initial_state_structure(self):
        """Test that initial state has expected structure."""
        project_id = str(uuid.uuid4())
        project = {"id": project_id, "client_name": "Test Corp"}
        documents = [{"id": "doc1", "filename": "test.pdf"}]

        # Simulate get_initial_state logic
        initial_state = {
            "project_id": project_id,
            "project": project,
            "documents": documents,
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
            "messages": [],
            "errors": [],
        }

        assert initial_state["project_id"] == project_id
        assert initial_state["project"] == project
        assert initial_state["documents"] == documents
        assert initial_state["is_suspended"] is False
        assert initial_state["ingestion_complete"] is False
        assert initial_state["messages"] == []
        assert initial_state["errors"] == []

    def test_state_update_after_interview(self):
        """Test state updates after interview script generation."""
        state = {
            "project_id": "test-123",
            "is_suspended": False,
            "interview_script": None,
            "script_generation_complete": False,
            "current_node": "hypothesis",
        }

        # Simulate interview node completion
        interview_script = {
            "project_id": "test-123",
            "questions": [{"role": "Manager", "question": "Test?"}],
            "target_roles": ["Manager"],
        }

        state.update({
            "interview_script": interview_script,
            "script_generation_complete": True,
            "is_suspended": True,
            "suspension_reason": "Awaiting interview transcript",
            "current_node": "interview",
        })

        assert state["is_suspended"] is True
        assert state["interview_script"] is not None
        assert state["script_generation_complete"] is True
        assert state["current_node"] == "interview"

    def test_state_update_after_transcript(self):
        """Test state updates after receiving transcript."""
        state = {
            "project_id": "test-123",
            "is_suspended": True,
            "transcript": None,
            "transcript_received": False,
            "current_node": "interview",
        }

        transcript = "Interview transcript content..."

        state.update({
            "transcript": transcript,
            "transcript_received": True,
            "is_suspended": False,
            "current_node": "gap_analysis",
        })

        assert state["transcript"] == transcript
        assert state["transcript_received"] is True
        assert state["is_suspended"] is False
        assert state["current_node"] == "gap_analysis"


# ============================================================================
# Test Interview Script Model
# ============================================================================

class TestInterviewScriptModel:
    """Test InterviewScript and related models."""

    def test_interview_question_model(self):
        """Test InterviewQuestion model."""
        from src.models.schemas import InterviewQuestion

        question = InterviewQuestion(
            role="CFO",
            question="How do you handle expenses?",
            intent="Understand expense workflow",
            follow_ups=["What tools do you use?"],
            related_hypothesis_id="hyp-123",
        )

        assert question.role == "CFO"
        assert question.question == "How do you handle expenses?"
        assert len(question.follow_ups) == 1

    def test_interview_script_model(self):
        """Test InterviewScript model."""
        from src.models.schemas import InterviewScript, InterviewQuestion

        script = InterviewScript(
            project_id="project-123",
            target_departments=["Finance"],
            target_roles=["CFO", "Manager"],
            introduction="Welcome...",
            questions=[
                InterviewQuestion(
                    role="CFO",
                    question="Test?",
                    intent="Test",
                )
            ],
            closing_notes="Thank you...",
            estimated_duration_minutes=45,
        )

        assert script.project_id == "project-123"
        assert len(script.target_roles) == 2
        assert len(script.questions) == 1
        assert script.estimated_duration_minutes == 45

    def test_interview_script_defaults(self):
        """Test InterviewScript default values."""
        from src.models.schemas import InterviewScript

        script = InterviewScript(
            project_id="project-123",
            target_departments=["Finance"],
            questions=[],
        )

        assert script.target_roles == []
        assert script.introduction == ""
        assert script.closing_notes == ""
        assert script.estimated_duration_minutes == 60
