"""
Consolidated tests for APIC agents.

This module contains all agent-related tests including:
- InterviewArchitectAgent
- Interview script generation
- Hypothesis generation and analysis
"""

import pytest
import os
import tempfile
import uuid
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.models.schemas import (
    Hypothesis,
    InterviewQuestion,
    InterviewScript,
)


# ============================================================================
# Test InterviewArchitectAgent
# ============================================================================

class TestInterviewArchitectAgent:
    """Test suite for InterviewArchitectAgent."""

    @pytest.fixture
    def agent(self, mock_llm):
        """Create an InterviewArchitectAgent instance for testing."""
        with patch('src.agents.base.get_llm', return_value=mock_llm), \
             patch('src.agents.interview.get_interview_script_generator'):
            from src.agents.interview import InterviewArchitectAgent
            agent = InterviewArchitectAgent()
            agent.llm = mock_llm
            return agent

    @pytest.fixture
    def initial_state(self):
        """Create initial state with hypotheses."""
        return {
            "project_id": "test-project-123",
            "project": {
                "id": "test-project-123",
                "client_name": "Test Corp",
                "project_name": "Test Project",
                "target_departments": ["Finance", "Operations"],
            },
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

    # -------------------------------------------------------------------------
    # Process Method Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_process_returns_state_dict(self, agent, initial_state):
        """Test that process method returns a state dictionary."""
        mock_response = Mock()
        mock_response.content = '''{"key_themes": ["manual_process"], "priority_areas": [], "root_cause_patterns": [], "interconnections": [], "ddd_indicators": {"dull_tasks": [], "dirty_tasks": [], "dangerous_tasks": []}, "interview_focus_recommendations": [], "risk_areas": []}'''
        agent.llm.ainvoke = AsyncMock(return_value=mock_response)

        with patch.object(agent, '_determine_target_roles', return_value=AsyncMock(return_value=["CFO"])()):
            with patch.object(agent, '_generate_questions', return_value=AsyncMock(return_value=[])()):
                with patch.object(agent, '_generate_introduction', return_value=AsyncMock(return_value="Introduction")()):
                    with patch.object(agent, '_generate_closing_notes', return_value=AsyncMock(return_value="Closing")()):
                        with patch.object(agent, '_estimate_duration', return_value=AsyncMock(return_value=60)()):
                            mock_script_gen = Mock()
                            mock_script_gen.generate = Mock(return_value="/path/to/script.md")
                            with patch('src.agents.interview.get_interview_script_generator', return_value=mock_script_gen):
                                result = await agent.process(initial_state)

        assert isinstance(result, dict)
        assert "project_id" in result

    @pytest.mark.asyncio
    async def test_process_with_no_hypotheses(self, agent):
        """Test processing when no hypotheses are available."""
        state = {
            "project_id": "test-123",
            "project": {"target_departments": ["Finance"]},
            "hypotheses": [],
            "target_departments": ["Finance"],
            "messages": [],
            "errors": [],
        }
        result = await agent.process(state)

        assert result["interview_script"] is None
        assert result["script_generation_complete"] is True

    # -------------------------------------------------------------------------
    # Hypothesis Analysis Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_analyze_hypotheses(self, agent, sample_hypotheses):
        """Test that hypothesis analysis returns structured output."""
        mock_response = Mock()
        mock_response.content = '''{
            "key_themes": ["manual_process", "communication_gap"],
            "priority_areas": [{"area": "Invoice Processing", "reason": "High impact", "severity": "high"}],
            "root_cause_patterns": ["Lack of automation"],
            "interconnections": ["Manual processes cause communication delays"],
            "ddd_indicators": {"dull_tasks": ["data entry"], "dirty_tasks": [], "dangerous_tasks": []},
            "interview_focus_recommendations": ["Focus on daily workflows"],
            "risk_areas": ["Data entry errors"]
        }'''
        agent.llm.ainvoke = AsyncMock(return_value=mock_response)

        analysis = await agent._analyze_hypotheses(sample_hypotheses, ["Finance"])

        assert isinstance(analysis, dict)
        assert "key_themes" in analysis
        assert "priority_areas" in analysis
        assert "ddd_indicators" in analysis

    # -------------------------------------------------------------------------
    # Target Roles Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_determine_target_roles(self, agent, sample_hypotheses):
        """Test that target roles are determined based on hypotheses."""
        mock_response = Mock()
        mock_response.content = '["CFO", "Operations Manager", "Data Entry Clerk"]'
        agent.llm.ainvoke = AsyncMock(return_value=mock_response)

        analysis = {
            "key_themes": ["manual_process"],
            "priority_areas": [{"area": "Invoice Processing", "reason": "Test", "severity": "high"}],
            "interview_focus_recommendations": ["Focus on workflows"],
        }

        roles = await agent._determine_target_roles(sample_hypotheses, ["Finance"], analysis)

        assert isinstance(roles, list)
        assert len(roles) > 0
        assert all(isinstance(role, str) for role in roles)

    # -------------------------------------------------------------------------
    # Question Generation Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_generate_questions(self, agent, sample_hypotheses):
        """Test that interview questions are generated."""
        mock_response = Mock()
        mock_response.content = '''[
            {
                "role": "Finance Manager",
                "question": "How do you currently process invoices?",
                "intent": "Understand current workflow",
                "follow_ups": ["What tools do you use?"],
                "related_hypothesis_id": null
            }
        ]'''
        agent.llm.ainvoke = AsyncMock(return_value=mock_response)

        analysis = {
            "key_themes": ["manual_process"],
            "priority_areas": [{"area": "Invoice Processing", "reason": "Test", "severity": "high"}],
            "root_cause_patterns": ["Lack of automation"],
            "ddd_indicators": {"dull_tasks": [], "dirty_tasks": [], "dangerous_tasks": []},
            "risk_areas": ["Data errors"],
        }

        questions = await agent._generate_questions(sample_hypotheses, ["CFO", "Manager"], analysis)

        assert isinstance(questions, list)
        assert len(questions) > 0
        assert all(isinstance(q, InterviewQuestion) for q in questions)

    # -------------------------------------------------------------------------
    # Introduction and Closing Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_generate_introduction(self, agent, sample_hypotheses):
        """Test that introduction is generated."""
        mock_response = Mock()
        mock_response.content = """Thank you for taking the time to speak with us today.
We're conducting this interview as part of a process improvement initiative."""
        agent.llm.ainvoke = AsyncMock(return_value=mock_response)

        analysis = {
            "key_themes": ["manual_process"],
            "priority_areas": [{"area": "Invoice Processing", "reason": "Test", "severity": "high"}],
        }

        introduction = await agent._generate_introduction(sample_hypotheses, ["Finance"], analysis)

        assert isinstance(introduction, str)
        assert len(introduction) > 0

    @pytest.mark.asyncio
    async def test_generate_closing_notes(self, agent, sample_hypotheses):
        """Test that closing notes are generated."""
        mock_response = Mock()
        mock_response.content = """Thank you for your time and insights today.
We will synthesize this feedback and share our recommendations."""
        agent.llm.ainvoke = AsyncMock(return_value=mock_response)

        questions = [
            InterviewQuestion(
                role="Manager",
                question="Test question",
                intent="Test intent",
                follow_ups=[],
            )
        ]

        analysis = {
            "key_themes": ["manual_process"],
            "risk_areas": ["Data errors"],
        }

        closing = await agent._generate_closing_notes(sample_hypotheses, questions, analysis)

        assert isinstance(closing, str)
        assert len(closing) > 0

    # -------------------------------------------------------------------------
    # Duration Estimation Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_estimate_duration(self, agent):
        """Test that duration is estimated based on questions."""
        mock_response = Mock()
        mock_response.content = "60"
        agent.llm.ainvoke = AsyncMock(return_value=mock_response)

        questions = [
            InterviewQuestion(
                role="Manager",
                question="Test question",
                intent="Test intent",
                follow_ups=["Follow up 1", "Follow up 2"],
            ),
            InterviewQuestion(
                role="Manager",
                question="Another question",
                intent="Another intent",
                follow_ups=["Follow up"],
            ),
        ]

        analysis = {
            "key_themes": ["manual_process"],
            "priority_areas": [{"area": "Test", "reason": "Test", "severity": "high"}],
            "risk_areas": ["Test risk"],
        }

        duration = await agent._estimate_duration(questions, analysis)

        assert isinstance(duration, int)
        assert 30 <= duration <= 120

    # -------------------------------------------------------------------------
    # Default Questions Tests
    # -------------------------------------------------------------------------

    def test_get_default_questions(self, agent, sample_hypotheses):
        """Test that default questions are generated if LLM fails."""
        roles = ["Manager", "Clerk"]

        questions = agent._get_default_questions(roles, sample_hypotheses)

        assert isinstance(questions, list)
        assert len(questions) > 0
        assert all(isinstance(q, InterviewQuestion) for q in questions)

    def test_extract_departments(self, agent, sample_hypotheses):
        """Test that departments are extracted from hypotheses."""
        departments = agent._extract_departments(sample_hypotheses)

        assert isinstance(departments, list)
        assert len(departments) > 0


# ============================================================================
# Test Context Gathering
# ============================================================================

class TestContextGathering:
    """Test comprehensive context gathering functionality."""

    @pytest.fixture
    def agent(self):
        """Create an Interview Architect Agent instance."""
        from src.agents.interview import InterviewArchitectAgent
        return InterviewArchitectAgent()

    def test_gather_comprehensive_context(self, agent, sample_state, sample_hypotheses):
        """Test that all available context is properly gathered."""
        context = agent._gather_comprehensive_context(sample_state, sample_hypotheses)

        assert context['documents_count'] == 2
        assert context['summaries_count'] == 3
        assert len(context['document_summaries']) == 3
        assert context['combined_summaries'] != ""
        assert context['has_urls'] is True
        assert context['project']['client_name'] == "Test Corp"
        assert context['hypotheses_summary']['total_count'] == 2

    def test_gather_context_empty_state(self, agent):
        """Test context gathering with minimal/empty state."""
        empty_state = {
            "project_id": "test",
            "project": {},
            "documents": [],
            "document_summaries": [],
            "hypotheses": [],
        }

        context = agent._gather_comprehensive_context(empty_state, [])

        assert context['documents_count'] == 0
        assert context['summaries_count'] == 0
        assert context['has_urls'] is False
        assert context['hypotheses_summary']['total_count'] == 0

    def test_url_document_detection(self, agent, sample_state):
        """Test that URL documents are properly detected."""
        context = agent._gather_comprehensive_context(sample_state, [])

        assert context['has_urls'] is True
        url_docs = [d for d in context['documents'] if d['source_type'] == 'url']
        assert len(url_docs) == 1

    def test_no_url_documents(self, agent):
        """Test state with only file documents."""
        state = {
            "project_id": "test",
            "project": {},
            "documents": [{"filename": "test.pdf", "source_type": "file"}],
            "document_summaries": [],
        }

        context = agent._gather_comprehensive_context(state, [])
        assert context['has_urls'] is False


# ============================================================================
# Test AI Hypothesis Generation
# ============================================================================

class TestHypothesisGeneration:
    """Test AI-powered hypothesis generation."""

    @pytest.fixture
    def agent(self):
        """Create an Interview Architect Agent instance."""
        from src.agents.interview import InterviewArchitectAgent
        return InterviewArchitectAgent()

    def test_get_generic_hypotheses(self, agent):
        """Test generic hypotheses generation as fallback."""
        hypotheses = agent._get_generic_hypotheses()

        assert len(hypotheses) >= 3
        for h in hypotheses:
            assert isinstance(h, Hypothesis)
            assert h.process_area != ""
            assert h.description != ""

    @pytest.mark.asyncio
    async def test_generate_hypotheses_from_documents_success(self, agent, sample_state):
        """Test AI-powered hypothesis generation from documents."""
        mock_response = Mock()
        mock_response.content = '''[
            {
                "process_area": "Order Processing",
                "description": "Manual order entry causes delays",
                "evidence": ["Manual entry mentioned in docs"],
                "indicators": ["manual", "delays"],
                "confidence_score": 0.8,
                "automation_potential": "high",
                "task_category": "automatable"
            }
        ]'''

        agent.llm = AsyncMock()
        agent.llm.ainvoke = AsyncMock(return_value=mock_response)

        hypotheses = await agent._generate_hypotheses_from_documents(sample_state)

        assert len(hypotheses) == 1
        assert hypotheses[0].process_area == "Order Processing"

    @pytest.mark.asyncio
    async def test_generate_hypotheses_no_summaries(self, agent):
        """Test hypothesis generation with no document summaries."""
        state = {
            "document_summaries": [],
            "project": {},
        }

        hypotheses = await agent._generate_hypotheses_from_documents(state)
        assert hypotheses == []

    @pytest.mark.asyncio
    async def test_generate_hypotheses_parse_error(self, agent, sample_state):
        """Test hypothesis generation when AI returns invalid JSON."""
        mock_response = Mock()
        mock_response.content = "This is not valid JSON"

        agent.llm = AsyncMock()
        agent.llm.ainvoke = AsyncMock(return_value=mock_response)

        hypotheses = await agent._generate_hypotheses_from_documents(sample_state)
        assert hypotheses == []


# ============================================================================
# Test Interview Script Generation
# ============================================================================

class TestInterviewScriptGeneration:
    """Test suite for interview script generation."""

    def test_interview_script_generator_initialization(self, tmp_path):
        """Test that InterviewScriptGenerator initializes properly."""
        with patch('src.services.interview_script_generator.settings') as mock_settings:
            mock_settings.SCRIPTS_DIR = str(tmp_path / "scripts")

            from src.services.interview_script_generator import InterviewScriptGenerator
            generator = InterviewScriptGenerator()

            assert generator.scripts_dir.exists()

    def test_get_project_scripts_dir(self, tmp_path):
        """Test that project scripts directory is created."""
        with patch('src.services.interview_script_generator.settings') as mock_settings:
            mock_settings.SCRIPTS_DIR = str(tmp_path / "scripts")

            from src.services.interview_script_generator import InterviewScriptGenerator
            generator = InterviewScriptGenerator()

            project_dir = generator.get_project_scripts_dir("test-123")

            assert project_dir.exists()
            assert "test-123" in str(project_dir)

    def test_generate_markdown(self, tmp_path, script_data, project_data):
        """Test that markdown script is generated."""
        with patch('src.services.interview_script_generator.settings') as mock_settings:
            mock_settings.SCRIPTS_DIR = str(tmp_path / "scripts")

            from src.services.interview_script_generator import InterviewScriptGenerator
            generator = InterviewScriptGenerator()

            md_path = generator.generate_markdown(script_data, project_data)

            assert os.path.exists(md_path)
            assert md_path.endswith(".md")

            with open(md_path, "r") as f:
                content = f.read()
                assert "Interview Script" in content
                assert "Test Corp" in content

    def test_generate(self, tmp_path, script_data, project_data):
        """Test that markdown file is generated via generate method."""
        with patch('src.services.interview_script_generator.settings') as mock_settings:
            mock_settings.SCRIPTS_DIR = str(tmp_path / "scripts")

            from src.services.interview_script_generator import InterviewScriptGenerator
            generator = InterviewScriptGenerator()

            path = generator.generate(script_data, project_data)

            assert path is not None
            assert path.endswith(".md")
            assert os.path.exists(path)

    def test_list_all_scripts(self, tmp_path, script_data, project_data):
        """Test that all scripts can be listed."""
        with patch('src.services.interview_script_generator.settings') as mock_settings:
            mock_settings.SCRIPTS_DIR = str(tmp_path / "scripts")

            from src.services.interview_script_generator import InterviewScriptGenerator
            generator = InterviewScriptGenerator()

            generator.generate_markdown(script_data, project_data)
            scripts = generator.list_all_scripts(script_data["project_id"])

            assert isinstance(scripts, list)
            assert len(scripts) >= 1
            assert "filename" in scripts[0]
            assert scripts[0]["filename"].endswith(".md")


# ============================================================================
# Integration Tests
# ============================================================================

class TestInterviewArchitectIntegration:
    """Integration tests for Interview Architect Agent."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_end_to_end_no_hypotheses_scenario(self):
        """Test complete flow when no hypotheses exist."""
        # Placeholder for future implementation with actual LLM
        pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_end_to_end_with_urls(self):
        """Test complete flow with URL documents."""
        # Placeholder for future implementation
        pass


# ============================================================================
# Performance Tests
# ============================================================================

class TestInterviewArchitectPerformance:
    """Performance tests for Interview Architect Agent."""

    def test_context_gathering_performance(self, benchmark):
        """Benchmark context gathering performance."""
        from src.agents.interview import InterviewArchitectAgent
        agent = InterviewArchitectAgent()

        state = {
            "project_id": "test",
            "project": {"client_name": "Test"},
            "documents": [{"filename": f"doc{i}.pdf", "source_type": "file"} for i in range(100)],
            "document_summaries": [f"Summary {i}" for i in range(100)],
            "hypotheses": [],
        }

        result = benchmark(agent._gather_comprehensive_context, state, [])
        assert result is not None
