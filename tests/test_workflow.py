"""
Tests for workflow orchestration and state management.

This module contains all workflow and integration tests including:
- ConsultantGraph workflow orchestration
- Workflow factory functions
- StateManager data persistence
- GraphState and WorkflowState models
- Document category support in StateManager
- Code structure validation tests
"""

import pytest
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import uuid

from src.services.workflow import ConsultantGraph, WorkflowState, get_workflow, create_workflow
from src.services.state_manager import StateManager
from src.models.schemas import GraphState, ProjectStatus

# Note: fixtures like 'in_memory_db', 'state_manager_with_db' are provided by conftest.py


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


# ============================================================================
# Test StateManager Document Category Support
# ============================================================================

class TestStateManagerDocumentCategory:
    """Test StateManager document methods with category support."""

    def test_add_document_with_category(self, state_manager_with_db):
        """Test adding a document with a category."""
        sm = state_manager_with_db
        project_id = str(uuid.uuid4())

        from tests.conftest import ProjectRecord
        with sm.SessionLocal() as session:
            project = ProjectRecord(
                id=project_id,
                client_name="Test Client",
                project_name="Test Project",
            )
            session.add(project)
            session.commit()

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

        from tests.conftest import ProjectRecord
        with sm.SessionLocal() as session:
            project = ProjectRecord(
                id=project_id,
                client_name="Test Client",
                project_name="Test Project",
            )
            session.add(project)
            session.commit()

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

        from tests.conftest import ProjectRecord
        with sm.SessionLocal() as session:
            project = ProjectRecord(
                id=project_id,
                client_name="Test Client",
                project_name="Test Project",
            )
            session.add(project)
            session.commit()

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

        docs = sm.get_project_documents(project_id)
        assert len(docs) == 2, f"Expected 2 documents, got {len(docs)}"

    def test_get_project_documents_with_category_filter(self, state_manager_with_db):
        """Test filtering documents by category."""
        sm = state_manager_with_db
        project_id = str(uuid.uuid4())

        from tests.conftest import ProjectRecord
        with sm.SessionLocal() as session:
            project = ProjectRecord(
                id=project_id,
                client_name="Test Client",
                project_name="Test Project",
            )
            session.add(project)
            session.commit()

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

        from tests.conftest import ProjectRecord
        with sm.SessionLocal() as session:
            project = ProjectRecord(
                id=project_id,
                client_name="Test Client",
                project_name="Test Project",
            )
            session.add(project)
            session.commit()

        sm.add_document(
            project_id=project_id,
            filename="test.pdf",
            file_type="pdf",
            file_size=1000,
            file_path="/uploads/test.pdf",
            category="financial",
        )

        docs = sm.get_project_documents(project_id)

        assert len(docs) == 1
        assert "category" in docs[0], "Document dict should include 'category' key"
        assert docs[0]["category"] == "financial"


# ============================================================================
# Test DocumentRecord Model Category Field
# ============================================================================

class TestDocumentRecordCategory:
    """Test that DocumentRecord model has category field."""

    def test_document_record_has_category_column(self, in_memory_db):
        """Test that DocumentRecord model has a category column."""
        from tests.conftest import DocumentRecord
        assert hasattr(DocumentRecord, 'category'), \
            "DocumentRecord model should have a 'category' attribute"

    def test_document_record_category_default_is_general(self, in_memory_db):
        """Test that category defaults to 'general' when not specified."""
        from tests.conftest import DocumentRecord
        engine, Session = in_memory_db
        session = Session()

        try:
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
            session.refresh(doc)
            assert doc.category == "general", \
                f"Default category should be 'general', got '{doc.category}'"
        finally:
            session.close()

    def test_document_record_can_set_category(self, in_memory_db):
        """Test that category can be set to a custom value."""
        from tests.conftest import DocumentRecord
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
# Test Code Structure Validation (StateManager)
# ============================================================================

class TestStateManagerCodeStructure:
    """Test the actual code changes to StateManager."""

    def test_state_manager_file_has_category_in_document_record(self):
        """Verify that DocumentRecord model has category column."""
        state_manager_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "src", "services", "state_manager.py"
        )

        with open(state_manager_path, 'r') as f:
            content = f.read()

        assert 'category = Column(' in content, \
            "DocumentRecord should have 'category' column defined"
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

        assert 'def add_document(' in content
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

        start = content.find('def get_project_documents(')
        end = content.find('def ', start + 1)
        get_docs_code = content[start:end]

        assert 'category' in get_docs_code, \
            "get_project_documents should have 'category' parameter"
        assert 'filter_by(category=' in get_docs_code or 'if category' in get_docs_code, \
            "get_project_documents should filter by category"
        assert '"category": d.category' in get_docs_code, \
            "get_project_documents should return category in result"


# ============================================================================
# Test Code Structure Validation (Database Schema)
# ============================================================================

class TestDatabaseSchemaStructure:
    """Test that database schema file includes category column."""

    def test_init_schema_has_category_column(self):
        """Verify that init_schema.sql has category column."""
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "scripts", "init_schema.sql"
        )

        with open(schema_path, 'r') as f:
            content = f.read()

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


# ============================================================================
# Test Code Structure Validation (Migration)
# ============================================================================

class TestMigrationStructure:
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


# ============================================================================
# Test Code Structure Validation (API Routes)
# ============================================================================

class TestAPIRoutesStructure:
    """Test that API routes file supports category."""

    def test_document_response_has_category(self):
        """Verify that DocumentResponse model has category field."""
        routes_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "src", "api", "routes", "documents.py"
        )

        with open(routes_path, 'r') as f:
            content = f.read()

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

        start = content.find('async def list_documents(')
        end = content.find('async def ', start + 1)
        list_docs_code = content[start:end]

        assert 'category' in list_docs_code, \
            "list_documents should accept category parameter"

    def test_upload_documents_accepts_category(self):
        """Verify that upload_documents can accept category."""
        routes_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "src", "api", "routes", "documents.py"
        )

        with open(routes_path, 'r') as f:
            content = f.read()

        start = content.find('async def upload_documents(')
        end = content.find('async def ', start + 1)
        upload_code = content[start:end]

        assert 'category' in upload_code, \
            "upload_documents should accept category parameter"
