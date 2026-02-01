"""
Consolidated tests for workflow orchestration, state management, and data models.

This module contains integration tests including:
- StateManager operations (project and document management)
- GraphState model
- Workflow logic
- Data model schemas

Note: Workflow state is managed by LangGraph's built-in checkpointing.
StateManager handles project/document metadata only.
"""

import pytest
import os
import uuid
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime


# ============================================================================
# Test StateManager
# ============================================================================

class TestStateManager:
    """Test suite for StateManager."""

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
        assert result["thread_id"] is None  # No thread_id initially

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

    def test_set_and_get_thread_id(self, state_manager, sample_project_data):
        """Test that set_thread_id and get_thread_id work correctly."""
        project = state_manager.create_project(
            client_name=sample_project_data["client_name"],
            project_name=sample_project_data["project_name"],
        )

        project_id = project["id"]
        thread_id = str(uuid.uuid4())

        # Initially no thread_id
        assert state_manager.get_thread_id(project_id) is None

        # Set thread_id
        state_manager.set_thread_id(project_id, thread_id)

        # Verify it was set
        result = state_manager.get_thread_id(project_id)
        assert result == thread_id

        # Also verify it's in the project data
        project_data = state_manager.get_project(project_id)
        assert project_data["thread_id"] == thread_id

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

    def test_get_projects_by_status(self, state_manager, sample_project_data):
        """Test that get_projects_by_status returns projects with matching status."""
        project = state_manager.create_project(
            client_name=sample_project_data["client_name"],
            project_name=sample_project_data["project_name"],
        )

        project_id = project["id"]
        thread_id = str(uuid.uuid4())

        # Set thread_id and update status
        state_manager.set_thread_id(project_id, thread_id)
        state_manager.update_project_status(project_id, "interview_ready")

        # Get projects by status
        interview_ready = state_manager.get_projects_by_status("interview_ready")

        assert isinstance(interview_ready, list)
        project_ids = [p["id"] for p in interview_ready]
        assert project_id in project_ids

        # Verify thread_id is included
        for p in interview_ready:
            if p["id"] == project_id:
                assert p["thread_id"] == thread_id


# ============================================================================
# Test Document Category Feature
# ============================================================================

class TestDocumentCategory:
    """Test document category feature in StateManager."""

    def test_add_document_with_category(self, state_manager, sample_project_data, tmp_path):
        """Test adding a document with a category."""
        project = state_manager.create_project(
            client_name=sample_project_data["client_name"],
            project_name=sample_project_data["project_name"],
        )

        project_id = project["id"]
        file_path = str(tmp_path / "interview.txt")

        doc = state_manager.add_document(
            project_id=project_id,
            filename="interview_transcript.txt",
            file_type="txt",
            file_size=1500,
            file_path=file_path,
            category="interview_results",
        )

        assert doc is not None
        assert doc.get("category") == "interview_results"

    def test_add_document_without_category_defaults_to_general(self, state_manager, sample_project_data, tmp_path):
        """Test that adding a document without category defaults to 'general'."""
        project = state_manager.create_project(
            client_name=sample_project_data["client_name"],
            project_name=sample_project_data["project_name"],
        )

        project_id = project["id"]
        file_path = str(tmp_path / "report.pdf")

        doc = state_manager.add_document(
            project_id=project_id,
            filename="report.pdf",
            file_type="pdf",
            file_size=5000,
            file_path=file_path,
        )

        assert doc is not None
        assert doc.get("category") == "general"

    def test_get_documents_with_category_filter(self, state_manager, sample_project_data, tmp_path):
        """Test filtering documents by category."""
        project = state_manager.create_project(
            client_name=sample_project_data["client_name"],
            project_name=sample_project_data["project_name"],
        )

        project_id = project["id"]

        state_manager.add_document(
            project_id=project_id,
            filename="doc1.pdf",
            file_type="pdf",
            file_size=1000,
            file_path=str(tmp_path / "doc1.pdf"),
            category="general",
        )
        state_manager.add_document(
            project_id=project_id,
            filename="interview1.txt",
            file_type="txt",
            file_size=2000,
            file_path=str(tmp_path / "interview1.txt"),
            category="interview_results",
        )

        all_docs = state_manager.get_project_documents(project_id)
        assert len(all_docs) == 2

        interview_docs = state_manager.get_project_documents(project_id, category="interview_results")
        assert len(interview_docs) == 1
        assert interview_docs[0]["category"] == "interview_results"


# ============================================================================
# Test GraphState Model
# ============================================================================

class TestGraphStateModel:
    """Test GraphState model structure."""

    def test_graph_state_has_required_fields(self):
        """Test that GraphState model has all required fields."""
        from src.models.schemas import GraphState

        state = GraphState(project_id="test-123")

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
# Test Workflow Logic
# ============================================================================

class TestWorkflowLogic:
    """Test workflow logic with mocked dependencies."""

    def test_should_wait_for_transcript_logic_wait(self):
        """Test wait condition: suspended and no transcript."""
        state = {
            "is_suspended": True,
            "transcript_received": False,
        }

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

    def test_state_update_after_interview(self):
        """Test state updates after interview script generation."""
        state = {
            "project_id": "test-123",
            "is_suspended": False,
            "interview_script": None,
            "script_generation_complete": False,
            "current_node": "hypothesis",
        }

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


# ============================================================================
# Test Data Model Schemas
# ============================================================================

class TestProjectModels:
    """Test project-related models."""

    def test_project_create(self):
        """Test ProjectCreate model."""
        from src.models.schemas import ProjectCreate

        project = ProjectCreate(
            client_name="Acme Corp",
            project_name="Q1 Optimization",
            description="Process improvement initiative",
            target_departments=["Finance", "Operations"],
        )

        assert project.client_name == "Acme Corp"
        assert project.project_name == "Q1 Optimization"
        assert len(project.target_departments) == 2

    def test_project_defaults(self):
        """Test Project model defaults."""
        from src.models.schemas import Project, ProjectStatus

        project = Project(
            client_name="Test Corp",
            project_name="Test Project",
        )

        assert project.id is not None
        assert project.status == ProjectStatus.CREATED
        assert project.vector_namespace.startswith("client_")

    def test_project_status_enum(self):
        """Test project status enum values."""
        from src.models.schemas import ProjectStatus

        assert ProjectStatus.CREATED.value == "created"
        assert ProjectStatus.AWAITING_TRANSCRIPT.value == "awaiting_transcript"
        assert ProjectStatus.COMPLETED.value == "completed"


class TestHypothesisModels:
    """Test hypothesis-related models."""

    def test_hypothesis_creation(self):
        """Test Hypothesis model creation."""
        from src.models.schemas import Hypothesis

        hypothesis = Hypothesis(
            process_area="Invoice Processing",
            description="Manual data entry causing delays",
            evidence=["Takes 30 minutes per invoice", "20 invoices daily"],
            indicators=["manual", "data entry", "delay"],
            confidence=0.85,
            category="manual_process",
        )

        assert hypothesis.process_area == "Invoice Processing"
        assert hypothesis.confidence == 0.85
        assert len(hypothesis.evidence) == 2

    def test_hypothesis_defaults(self):
        """Test Hypothesis default values."""
        from src.models.schemas import Hypothesis

        hypothesis = Hypothesis(
            process_area="Test",
            description="Test hypothesis",
        )

        assert hypothesis.confidence == 0.5
        assert hypothesis.category == "general"
        assert hypothesis.evidence == []

    def test_hypothesis_confidence_bounds(self):
        """Test that confidence is bounded."""
        from src.models.schemas import Hypothesis

        hypothesis = Hypothesis(
            process_area="Test",
            description="Test",
            confidence=0.0,
        )
        assert hypothesis.confidence == 0.0

        hypothesis = Hypothesis(
            process_area="Test",
            description="Test",
            confidence=1.0,
        )
        assert hypothesis.confidence == 1.0


class TestInterviewModels:
    """Test interview-related models."""

    def test_interview_question_creation(self):
        """Test InterviewQuestion model creation."""
        from src.models.schemas import InterviewQuestion

        question = InterviewQuestion(
            role="CFO",
            question="How do you handle expenses?",
            intent="Understand expense workflow",
            follow_ups=["What tools do you use?", "How often?"],
            related_hypothesis_id="hyp-123",
        )

        assert question.role == "CFO"
        assert question.question == "How do you handle expenses?"
        assert len(question.follow_ups) == 2

    def test_interview_question_defaults(self):
        """Test InterviewQuestion defaults."""
        from src.models.schemas import InterviewQuestion

        question = InterviewQuestion(
            role="Manager",
            question="Test question",
            intent="Test intent",
        )

        assert question.follow_ups == []
        assert question.related_hypothesis_id is None

    def test_interview_script_creation(self):
        """Test InterviewScript model creation."""
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

    def test_interview_script_serialization(self):
        """Test that InterviewScript can be serialized."""
        from src.models.schemas import InterviewScript, InterviewQuestion

        script = InterviewScript(
            project_id="project-123",
            target_departments=["Finance"],
            questions=[
                InterviewQuestion(
                    role="Manager",
                    question="Test?",
                    intent="Test",
                )
            ],
        )

        script_dict = script.model_dump()

        assert isinstance(script_dict, dict)
        assert script_dict["project_id"] == "project-123"
        assert len(script_dict["questions"]) == 1


class TestGapAnalysisModels:
    """Test gap analysis models."""

    def test_gap_analysis_item(self):
        """Test GapAnalysisItem model."""
        from src.models.schemas import GapAnalysisItem, TaskCategory

        gap = GapAnalysisItem(
            process_step="Invoice Approval",
            sop_description="Manager reviews in system",
            observed_behavior="Email-based approval with printing",
            gap_description="SOP not followed, manual workaround",
            impact="2 hours wasted daily",
        )

        assert gap.task_category == TaskCategory.AUTOMATABLE
        assert gap.impact == "2 hours wasted daily"

    def test_analysis_result(self):
        """Test AnalysisResult model."""
        from src.models.schemas import AnalysisResult, Priority

        result = AnalysisResult(
            process_step="Invoice Processing",
            observed_behavior="Manual data entry",
            pain_point_priority=Priority.HIGH,
            proposed_solution="Implement OCR and RPA",
            tech_stack_recommendation=["UiPath", "Azure Form Recognizer"],
            estimated_roi_hours=40,
            implementation_priority=Priority.MEDIUM,
        )

        assert result.pain_point_priority == Priority.HIGH
        assert result.estimated_roi_hours == 40
        assert len(result.tech_stack_recommendation) == 2


class TestEnums:
    """Test enum values."""

    def test_priority_enum(self):
        """Test Priority enum."""
        from src.models.schemas import Priority

        assert Priority.LOW.value == "Low"
        assert Priority.MEDIUM.value == "Medium"
        assert Priority.HIGH.value == "High"

    def test_task_category_enum(self):
        """Test TaskCategory enum."""
        from src.models.schemas import TaskCategory

        assert TaskCategory.AUTOMATABLE.value == "Automatable"
        assert TaskCategory.HUMAN_ONLY.value == "Human Only"
