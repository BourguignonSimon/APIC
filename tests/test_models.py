"""
Tests for APIC data models.
"""

import pytest
from datetime import datetime

from src.models.schemas import (
    Project,
    ProjectCreate,
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


class TestProjectModels:
    """Test project-related models."""

    def test_project_create(self):
        """Test ProjectCreate model."""
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
        project = Project(
            client_name="Test Corp",
            project_name="Test Project",
        )

        assert project.id is not None
        assert project.status == ProjectStatus.CREATED
        assert project.vector_namespace.startswith("client_")

    def test_project_status_enum(self):
        """Test project status enum values."""
        assert ProjectStatus.CREATED.value == "created"
        assert ProjectStatus.AWAITING_TRANSCRIPT.value == "awaiting_transcript"
        assert ProjectStatus.COMPLETED.value == "completed"


class TestHypothesisModels:
    """Test hypothesis-related models."""

    def test_hypothesis_creation(self):
        """Test Hypothesis model creation."""
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
        hypothesis = Hypothesis(
            process_area="Test",
            description="Test hypothesis",
        )

        assert hypothesis.confidence == 0.5
        assert hypothesis.category == "general"
        assert hypothesis.evidence == []


class TestInterviewModels:
    """Test interview-related models."""

    def test_interview_question(self):
        """Test InterviewQuestion model."""
        question = InterviewQuestion(
            role="CFO",
            question="How do you approve invoices?",
            intent="Identify approval bottlenecks",
            follow_ups=["How long does it take?", "What tools do you use?"],
        )

        assert question.role == "CFO"
        assert len(question.follow_ups) == 2

    def test_interview_script(self):
        """Test InterviewScript model."""
        questions = [
            InterviewQuestion(
                role="Manager",
                question="Describe your daily workflow",
                intent="Understand process",
            )
        ]

        script = InterviewScript(
            project_id="test-123",
            target_departments=["Finance"],
            target_roles=["Manager", "Analyst"],
            questions=questions,
        )

        assert script.project_id == "test-123"
        assert len(script.questions) == 1
        assert script.estimated_duration_minutes == 60


class TestGapAnalysisModels:
    """Test gap analysis models."""

    def test_gap_analysis_item(self):
        """Test GapAnalysisItem model."""
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
        result = AnalysisResult(
            process_step="Invoice Processing",
            observed_behavior="Manual data entry",
            pain_point_severity=Severity.HIGH,
            proposed_solution="Implement OCR and RPA",
            tech_stack_recommendation=["UiPath", "Azure Form Recognizer"],
            estimated_roi_hours=40,
            implementation_complexity=Complexity.MEDIUM,
        )

        assert result.pain_point_severity == Severity.HIGH
        assert result.estimated_roi_hours == 40
        assert len(result.tech_stack_recommendation) == 2


class TestEnums:
    """Test enum values."""

    def test_severity_enum(self):
        """Test Severity enum."""
        assert Severity.LOW.value == "Low"
        assert Severity.CRITICAL.value == "Critical"

    def test_complexity_enum(self):
        """Test Complexity enum."""
        assert Complexity.LOW.value == "Low"
        assert Complexity.HIGH.value == "High"

    def test_task_category_enum(self):
        """Test TaskCategory enum."""
        assert TaskCategory.AUTOMATABLE.value == "Automatable"
        assert TaskCategory.HUMAN_ONLY.value == "Human Only"
