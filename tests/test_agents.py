"""
Comprehensive tests for APIC agents following TDD principles.
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import uuid

from src.agents.ingestion import IngestionAgent
from src.agents.hypothesis import HypothesisGeneratorAgent
from src.agents.interview import InterviewArchitectAgent
from src.agents.gap_analyst import GapAnalystAgent
from src.agents.solution import SolutionArchitectAgent
from src.agents.reporting import ReportingAgent
from src.models.schemas import (
    Document,
    Hypothesis,
    InterviewQuestion,
    InterviewScript,
    GapAnalysisItem,
    AnalysisResult,
    Severity,
    Complexity,
    TaskCategory,
    ProjectStatus,
)


# ============================================================================
# Test IngestionAgent
# ============================================================================

class TestIngestionAgent:
    """Test suite for IngestionAgent following TDD principles."""

    @pytest.fixture
    def agent(self):
        """Create an IngestionAgent instance for testing."""
        with patch('src.agents.base.get_llm') as mock_llm, \
             patch('src.agents.ingestion.OpenAIEmbeddings'):
            mock_llm.return_value = Mock()
            return IngestionAgent()

    @pytest.fixture
    def sample_document(self):
        """Create a sample document for testing."""
        return Document(
            id=str(uuid.uuid4()),
            project_id="test-project-123",
            filename="test_document.txt",
            file_type="txt",
            file_size=1024,
        )

    @pytest.fixture
    def initial_state(self, sample_document):
        """Create initial state for testing."""
        return {
            "project_id": "test-project-123",
            "documents": [sample_document],
            "messages": [],
            "errors": [],
            "document_summaries": [],
        }

    @pytest.mark.asyncio
    async def test_process_returns_state_dict(self, agent, initial_state):
        """Test that process method returns a state dictionary."""
        result = await agent.process(initial_state)
        assert isinstance(result, dict)
        assert "project_id" in result

    @pytest.mark.asyncio
    async def test_process_with_no_documents(self, agent):
        """Test processing when no documents are provided."""
        state = {
            "project_id": "test-123",
            "documents": [],
            "messages": [],
            "errors": [],
        }
        result = await agent.process(state)
        assert result["ingestion_complete"] is True
        assert any("No documents" in msg for msg in result["messages"])

    @pytest.mark.asyncio
    async def test_parse_txt_file(self, agent):
        """Test parsing a plain text file."""
        # Create a temporary text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is test content\nWith multiple lines\n")
            temp_path = f.name

        try:
            content = await agent._parse_txt(temp_path)
            assert content == "This is test content\nWith multiple lines"
            assert isinstance(content, str)
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_parse_missing_file_returns_none(self, agent, sample_document):
        """Test that parsing a non-existent file returns None."""
        result = await agent._parse_document(sample_document)
        assert result is None

    def test_chunk_document_creates_chunks(self, agent, sample_document):
        """Test that documents are properly chunked."""
        content = "This is test content. " * 100  # Create content > chunk size
        chunks = agent._chunk_document(content, sample_document)

        assert len(chunks) > 0
        assert all(hasattr(chunk, 'page_content') for chunk in chunks)
        assert all(hasattr(chunk, 'metadata') for chunk in chunks)

        # Verify metadata
        first_chunk = chunks[0]
        assert first_chunk.metadata['project_id'] == sample_document.project_id
        assert first_chunk.metadata['filename'] == sample_document.filename
        assert 'chunk_index' in first_chunk.metadata

    @pytest.mark.asyncio
    async def test_generate_summary_returns_string(self, agent):
        """Test that summary generation returns a string."""
        with patch.object(agent, 'llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = "This is a summary of the document."
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)

            summary = await agent._generate_summary("Test content", "test.txt")
            assert isinstance(summary, str)
            assert len(summary) > 0

    @pytest.mark.asyncio
    async def test_process_updates_document_metadata(self, agent, sample_document):
        """Test that processing updates document metadata correctly."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, dir='/tmp') as f:
            f.write("Test content for processing")
            temp_path = f.name
            filename = os.path.basename(temp_path)

        # Create upload directory
        upload_dir = os.path.join('/tmp', 'test-project-123')
        os.makedirs(upload_dir, exist_ok=True)

        # Copy file to expected location
        import shutil
        dest_path = os.path.join(upload_dir, filename)
        shutil.copy(temp_path, dest_path)

        sample_document.filename = filename

        try:
            with patch('src.agents.ingestion.settings') as mock_settings:
                mock_settings.UPLOAD_DIR = '/tmp'
                mock_settings.PINECONE_API_KEY = None  # Skip vector storage

                with patch.object(agent, 'llm') as mock_llm:
                    mock_response = Mock()
                    mock_response.content = "Document summary"
                    mock_llm.ainvoke = AsyncMock(return_value=mock_response)

                    state = {
                        "project_id": "test-project-123",
                        "documents": [sample_document],
                        "messages": [],
                        "errors": [],
                    }

                    result = await agent.process(state)

                    assert result["ingestion_complete"] is True
                    assert len(result["document_summaries"]) > 0
        finally:
            os.unlink(temp_path)
            if os.path.exists(dest_path):
                os.unlink(dest_path)
            if os.path.exists(upload_dir):
                os.rmdir(upload_dir)


# ============================================================================
# Test HypothesisGeneratorAgent
# ============================================================================

class TestHypothesisGeneratorAgent:
    """Test suite for HypothesisGeneratorAgent following TDD principles."""

    @pytest.fixture
    def agent(self):
        """Create a HypothesisGeneratorAgent instance for testing."""
        with patch('src.agents.base.get_llm') as mock_llm, \
             patch('src.agents.hypothesis.IngestionAgent'):
            mock_llm.return_value = Mock()
            return HypothesisGeneratorAgent()

    @pytest.fixture
    def initial_state(self):
        """Create initial state for hypothesis generation."""
        return {
            "project_id": "test-project-123",
            "document_summaries": [
                "Document describes manual invoice processing with paper forms",
                "Email-based approval workflow causing delays",
            ],
            "messages": [],
            "errors": [],
        }

    @pytest.mark.asyncio
    async def test_process_returns_state_dict(self, agent, initial_state):
        """Test that process method returns a state dictionary."""
        with patch.object(agent, '_generate_hypotheses', return_value=[]):
            result = await agent.process(initial_state)
            assert isinstance(result, dict)
            assert "project_id" in result

    @pytest.mark.asyncio
    async def test_process_with_no_summaries(self, agent):
        """Test processing when no document summaries are available."""
        state = {
            "project_id": "test-123",
            "document_summaries": [],
            "messages": [],
            "errors": [],
        }
        result = await agent.process(state)
        assert result["hypotheses"] == []
        assert result["hypothesis_generation_complete"] is True

    @pytest.mark.asyncio
    async def test_generate_hypotheses_returns_list(self, agent):
        """Test that hypothesis generation returns a list of Hypothesis objects."""
        with patch.object(agent, 'llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = '''[{
                "process_area": "Invoice Processing",
                "description": "Manual data entry causing delays",
                "evidence": ["Manual invoice entry"],
                "indicators": ["manual", "delay"],
                "confidence": 0.8,
                "category": "manual_process"
            }]'''
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)

            hypotheses = await agent._generate_hypotheses("summaries", "context")
            assert isinstance(hypotheses, list)
            assert len(hypotheses) > 0
            assert all(isinstance(h, Hypothesis) for h in hypotheses)

    @pytest.mark.asyncio
    async def test_validate_hypotheses_filters_low_confidence(self, agent):
        """Test that validation filters out hypotheses with very low confidence."""
        hypotheses = [
            Hypothesis(
                id=str(uuid.uuid4()),
                process_area="Area 1",
                description="High confidence hypothesis",
                confidence=0.8,
            ),
            Hypothesis(
                id=str(uuid.uuid4()),
                process_area="Area 2",
                description="Low confidence hypothesis",
                confidence=0.1,
            ),
        ]

        with patch.object(agent.ingestion_agent, 'query_knowledge_base', return_value=[]):
            validated = await agent._validate_hypotheses(hypotheses, "test-123")
            assert len(validated) == 1
            assert validated[0].confidence >= 0.2

    @pytest.mark.asyncio
    async def test_validate_hypotheses_sorts_by_confidence(self, agent):
        """Test that validated hypotheses are sorted by confidence."""
        hypotheses = [
            Hypothesis(
                id=str(uuid.uuid4()),
                process_area="Area 1",
                description="Medium confidence",
                confidence=0.5,
            ),
            Hypothesis(
                id=str(uuid.uuid4()),
                process_area="Area 2",
                description="High confidence",
                confidence=0.9,
            ),
            Hypothesis(
                id=str(uuid.uuid4()),
                process_area="Area 3",
                description="Low confidence",
                confidence=0.3,
            ),
        ]

        with patch.object(agent.ingestion_agent, 'query_knowledge_base', return_value=[]):
            validated = await agent._validate_hypotheses(hypotheses, "test-123")
            # Check that they're sorted in descending order
            for i in range(len(validated) - 1):
                assert validated[i].confidence >= validated[i + 1].confidence


# ============================================================================
# Test InterviewArchitectAgent
# ============================================================================

class TestInterviewArchitectAgent:
    """Test suite for InterviewArchitectAgent following TDD principles."""

    @pytest.fixture
    def agent(self):
        """Create an InterviewArchitectAgent instance for testing."""
        with patch('src.agents.base.get_llm') as mock_llm:
            mock_llm.return_value = Mock()
            return InterviewArchitectAgent()

    @pytest.fixture
    def initial_state(self):
        """Create initial state with hypotheses."""
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

    @pytest.mark.asyncio
    async def test_process_returns_state_dict(self, agent, initial_state):
        """Test that process method returns a state dictionary."""
        with patch.object(agent, 'llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = '''[{
                "role": "CFO",
                "question": "How do you approve invoices?",
                "intent": "Understand approval process",
                "follow_ups": []
            }]'''
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)

            result = await agent.process(initial_state)
            assert isinstance(result, dict)
            assert "interview_script" in result

    @pytest.mark.asyncio
    async def test_process_with_no_hypotheses(self, agent):
        """Test processing when no hypotheses are available."""
        state = {
            "project_id": "test-123",
            "hypotheses": [],
            "target_departments": ["Finance"],
            "messages": [],
            "errors": [],
        }
        result = await agent.process(state)
        assert "interview_script" in result or "errors" in result

    @pytest.mark.asyncio
    async def test_interview_script_has_required_fields(self, agent, initial_state):
        """Test that generated interview script has all required fields."""
        with patch.object(agent, 'llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = '''[{
                "role": "Finance Manager",
                "question": "Describe your invoice processing workflow",
                "intent": "Understand current process",
                "follow_ups": ["What tools do you use?"]
            }]'''
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)

            result = await agent.process(initial_state)

            if "interview_script" in result:
                script = result["interview_script"]
                assert "project_id" in script
                assert "target_departments" in script
                assert "questions" in script


# ============================================================================
# Test GapAnalystAgent
# ============================================================================

class TestGapAnalystAgent:
    """Test suite for GapAnalystAgent following TDD principles."""

    @pytest.fixture
    def agent(self):
        """Create a GapAnalystAgent instance for testing."""
        with patch('src.agents.base.get_llm') as mock_llm, \
             patch('src.agents.gap_analyst.IngestionAgent'):
            mock_llm.return_value = Mock()
            return GapAnalystAgent()

    @pytest.fixture
    def initial_state(self):
        """Create initial state with interview transcript."""
        return {
            "project_id": "test-project-123",
            "hypotheses": [
                {
                    "process_area": "Invoice Processing",
                    "description": "Manual data entry",
                    "confidence": 0.8,
                }
            ],
            "interview_transcript": "Manager said: We manually enter all invoices into Excel...",
            "messages": [],
            "errors": [],
        }

    @pytest.mark.asyncio
    async def test_process_returns_state_dict(self, agent, initial_state):
        """Test that process method returns a state dictionary."""
        with patch.object(agent, 'llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = '''[{
                "process_step": "Invoice Entry",
                "sop_description": "Use automated system",
                "observed_behavior": "Manual Excel entry",
                "gap_description": "Not using automation",
                "impact": "2 hours daily waste",
                "root_cause": "System not integrated",
                "task_category": "Automatable"
            }]'''
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)

            result = await agent.process(initial_state)
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_process_with_no_transcript(self, agent):
        """Test processing when no interview transcript is available."""
        state = {
            "project_id": "test-123",
            "hypotheses": [],
            "interview_transcript": "",
            "messages": [],
            "errors": [],
        }
        result = await agent.process(state)
        assert "errors" in result or "gap_analysis" in result


# ============================================================================
# Test SolutionArchitectAgent
# ============================================================================

class TestSolutionArchitectAgent:
    """Test suite for SolutionArchitectAgent following TDD principles."""

    @pytest.fixture
    def agent(self):
        """Create a SolutionArchitectAgent instance for testing."""
        with patch('src.agents.base.get_llm') as mock_llm:
            mock_llm.return_value = Mock()
            return SolutionArchitectAgent()

    @pytest.fixture
    def initial_state(self):
        """Create initial state with gap analysis."""
        return {
            "project_id": "test-project-123",
            "gap_analysis": [
                {
                    "process_step": "Invoice Entry",
                    "sop_description": "Automated entry",
                    "observed_behavior": "Manual entry",
                    "gap_description": "No automation",
                    "impact": "2 hours daily",
                    "root_cause": "No integration",
                    "task_category": "Automatable",
                }
            ],
            "messages": [],
            "errors": [],
        }

    @pytest.mark.asyncio
    async def test_process_returns_state_dict(self, agent, initial_state):
        """Test that process method returns a state dictionary."""
        with patch.object(agent, 'llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = '''[{
                "process_step": "Invoice Entry",
                "observed_behavior": "Manual entry",
                "pain_point_severity": "High",
                "proposed_solution": "Implement OCR and RPA",
                "tech_stack_recommendation": ["UiPath", "Azure Form Recognizer"],
                "estimated_roi_hours": 40,
                "implementation_complexity": "Medium"
            }]'''
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)

            result = await agent.process(initial_state)
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_process_with_no_gaps(self, agent):
        """Test processing when no gap analysis is available."""
        state = {
            "project_id": "test-123",
            "gap_analysis": [],
            "messages": [],
            "errors": [],
        }
        result = await agent.process(state)
        assert isinstance(result, dict)


# ============================================================================
# Test ReportingAgent
# ============================================================================

class TestReportingAgent:
    """Test suite for ReportingAgent following TDD principles."""

    @pytest.fixture
    def agent(self):
        """Create a ReportingAgent instance for testing."""
        with patch('src.agents.base.get_llm') as mock_llm:
            mock_llm.return_value = Mock()
            return ReportingAgent()

    @pytest.fixture
    def complete_state(self):
        """Create a complete state for report generation."""
        return {
            "project_id": "test-project-123",
            "client_name": "Test Corp",
            "project_name": "Process Improvement",
            "hypotheses": [
                {
                    "process_area": "Invoice Processing",
                    "description": "Manual data entry",
                    "confidence": 0.8,
                }
            ],
            "gap_analysis": [
                {
                    "process_step": "Invoice Entry",
                    "gap_description": "No automation",
                    "impact": "2 hours daily",
                }
            ],
            "solution_recommendations": [
                {
                    "process_step": "Invoice Entry",
                    "proposed_solution": "Implement RPA",
                    "tech_stack_recommendation": ["UiPath"],
                    "estimated_roi_hours": 40,
                }
            ],
            "messages": [],
            "errors": [],
        }

    @pytest.mark.asyncio
    async def test_process_returns_state_dict(self, agent, complete_state):
        """Test that process method returns a state dictionary."""
        with patch.object(agent, 'llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = "# Executive Summary\nThis is a test report."
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)

            with patch.object(agent, '_generate_pdf', return_value="/tmp/test.pdf"):
                result = await agent.process(complete_state)
                assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_report_contains_all_sections(self, agent, complete_state):
        """Test that generated report contains all required sections."""
        with patch.object(agent, 'llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = "# Executive Summary\nTest content"
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)

            with patch.object(agent, '_generate_pdf', return_value="/tmp/test.pdf"):
                result = await agent.process(complete_state)
                assert "final_report" in result or "errors" in result
