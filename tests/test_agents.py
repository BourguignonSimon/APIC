"""
Comprehensive tests for APIC agents following TDD principles.
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import uuid

from src.models.schemas import (
    Document,
    Hypothesis,
    InterviewQuestion,
    InterviewScript,
    GapAnalysisItem,
    AnalysisResult,
    TaskCategory,
    ProjectStatus,
)


# ============================================================================
# Fixtures for mocking LangChain dependencies
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
# Test InterviewArchitectAgent
# ============================================================================

class TestInterviewArchitectAgent:
    """Test suite for InterviewArchitectAgent following TDD principles."""

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

    @pytest.fixture
    def sample_hypotheses(self):
        """Create sample hypotheses for testing."""
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

    @pytest.mark.asyncio
    async def test_process_returns_state_dict(self, agent, initial_state):
        """Test that process method returns a state dictionary."""
        # Mock LLM responses
        mock_response = Mock()
        mock_response.content = '''{"key_themes": ["manual_process"], "priority_areas": [], "root_cause_patterns": [], "interconnections": [], "ddd_indicators": {"dull_tasks": [], "dirty_tasks": [], "dangerous_tasks": []}, "interview_focus_recommendations": [], "risk_areas": []}'''
        agent.llm.ainvoke = AsyncMock(return_value=mock_response)

        with patch.object(agent, '_determine_target_roles', return_value=AsyncMock(return_value=["CFO"])()):
            with patch.object(agent, '_generate_questions', return_value=AsyncMock(return_value=[])()):
                with patch.object(agent, '_generate_introduction', return_value=AsyncMock(return_value="Introduction")()):
                    with patch.object(agent, '_generate_closing_notes', return_value=AsyncMock(return_value="Closing")()):
                        with patch.object(agent, '_estimate_duration', return_value=AsyncMock(return_value=60)()):
                            # Simplify by mocking entire flow
                            mock_script_gen = Mock()
                            mock_script_gen.generate_all_formats = Mock(return_value={})
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
        assert 30 <= duration <= 120  # Reasonable bounds

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
# Test Interview Script Generation
# ============================================================================

class TestInterviewScriptGeneration:
    """Test suite for interview script generation."""

    @pytest.fixture
    def script_data(self):
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
                {
                    "role": "Operations Manager",
                    "question": "What are your biggest bottlenecks?",
                    "intent": "Identify pain points",
                    "follow_ups": ["How often does this occur?"],
                    "related_hypothesis_id": None,
                },
            ],
            "closing_notes": "Thank you for your insights.",
            "estimated_duration_minutes": 45,
            "generated_at": datetime.utcnow().isoformat(),
        }

    @pytest.fixture
    def project_data(self):
        """Create sample project data."""
        return {
            "id": "test-project-123",
            "client_name": "Test Corp",
            "project_name": "Process Improvement",
        }

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

            # Check content
            with open(md_path, "r") as f:
                content = f.read()
                assert "Interview Script" in content
                assert "Test Corp" in content
                assert "How do you track expenses?" in content

    def test_generate_all_formats(self, tmp_path, script_data, project_data):
        """Test that all formats are generated."""
        with patch('src.services.interview_script_generator.settings') as mock_settings:
            mock_settings.SCRIPTS_DIR = str(tmp_path / "scripts")

            from src.services.interview_script_generator import InterviewScriptGenerator
            generator = InterviewScriptGenerator()

            paths = generator.generate_all_formats(script_data, project_data)

            # Should have entries for all formats
            assert "markdown" in paths
            assert paths["markdown"] is not None

            # PDF and DOCX may fail due to missing dependencies, but markdown should work
            if paths.get("pdf"):
                assert os.path.exists(paths["pdf"])
            if paths.get("docx"):
                assert os.path.exists(paths["docx"])

    def test_list_all_scripts(self, tmp_path, script_data, project_data):
        """Test that all scripts can be listed."""
        with patch('src.services.interview_script_generator.settings') as mock_settings:
            mock_settings.SCRIPTS_DIR = str(tmp_path / "scripts")

            from src.services.interview_script_generator import InterviewScriptGenerator
            generator = InterviewScriptGenerator()

            # Generate a script first
            generator.generate_markdown(script_data, project_data)

            # List scripts
            scripts = generator.list_all_scripts(script_data["project_id"])

            assert isinstance(scripts, list)
            assert len(scripts) >= 1
            assert "filename" in scripts[0]
            assert "path" in scripts[0]
            assert "format" in scripts[0]


# ============================================================================
# Test Model Schemas for Interview
# ============================================================================

class TestInterviewModels:
    """Test suite for interview-related Pydantic models."""

    def test_interview_question_creation(self):
        """Test creating an InterviewQuestion."""
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
        question = InterviewQuestion(
            role="Manager",
            question="Test question",
            intent="Test intent",
        )

        assert question.follow_ups == []
        assert question.related_hypothesis_id is None

    def test_interview_script_creation(self):
        """Test creating an InterviewScript."""
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
        """Test InterviewScript defaults."""
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


# ============================================================================
# Test Hypothesis Model
# ============================================================================

class TestHypothesisModel:
    """Test suite for Hypothesis model."""

    def test_hypothesis_creation(self):
        """Test creating a Hypothesis."""
        hypothesis = Hypothesis(
            process_area="Invoice Processing",
            description="Manual data entry causing delays",
            evidence=["Quote from SOP"],
            indicators=["manual", "delay"],
            confidence=0.85,
            category="manual_process",
        )

        assert hypothesis.process_area == "Invoice Processing"
        assert hypothesis.confidence == 0.85
        assert len(hypothesis.evidence) == 1

    def test_hypothesis_defaults(self):
        """Test Hypothesis defaults."""
        hypothesis = Hypothesis(
            process_area="Test Area",
            description="Test description",
        )

        assert hypothesis.evidence == []
        assert hypothesis.indicators == []
        assert hypothesis.confidence == 0.5
        assert hypothesis.category == "general"

    def test_hypothesis_confidence_bounds(self):
        """Test that confidence is bounded."""
        # Valid confidence
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
