"""
APIC Data Schemas
Pydantic models for the Consultant Graph workflow.
"""

from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field
import uuid


# ============================================================================
# Enums
# ============================================================================

class ProjectStatus(str, Enum):
    """Status of a consulting project."""
    CREATED = "created"
    INGESTING = "ingesting"
    ANALYZING = "analyzing"
    INTERVIEW_READY = "interview_ready"
    AWAITING_TRANSCRIPT = "awaiting_transcript"  # Human breakpoint
    PROCESSING_TRANSCRIPT = "processing_transcript"
    SOLUTIONING = "solutioning"
    REPORTING = "reporting"
    COMPLETED = "completed"
    FAILED = "failed"


class Severity(str, Enum):
    """Severity level for pain points."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class Complexity(str, Enum):
    """Implementation complexity level."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class TaskCategory(str, Enum):
    """Category of task for automation assessment."""
    AUTOMATABLE = "Automatable"
    PARTIALLY_AUTOMATABLE = "Partially Automatable"
    HUMAN_ONLY = "Human Only"


class InsightType(str, Enum):
    """Type of Google ADK insight."""
    PATTERN_DETECTION = "pattern_detection"
    EFFICIENCY_OPPORTUNITY = "efficiency_opportunity"
    RISK_IDENTIFICATION = "risk_identification"
    PROCESS_OPTIMIZATION = "process_optimization"
    GENERAL_ANALYSIS = "general_analysis"


# ============================================================================
# Project Models
# ============================================================================

class ProjectCreate(BaseModel):
    """Model for creating a new project."""
    client_name: str = Field(..., description="Name of the client organization")
    project_name: str = Field(..., description="Name of the consulting project")
    description: Optional[str] = Field(None, description="Project description")
    target_departments: List[str] = Field(
        default_factory=list,
        description="Departments to focus on during analysis"
    )


class Project(BaseModel):
    """Full project model with all metadata."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    project_name: str
    description: Optional[str] = None
    target_departments: List[str] = Field(default_factory=list)
    status: ProjectStatus = ProjectStatus.CREATED
    vector_namespace: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def model_post_init(self, __context):
        """Set vector namespace after initialization."""
        if not self.vector_namespace:
            self.vector_namespace = f"client_{self.id}"


# ============================================================================
# Document Models
# ============================================================================

class Document(BaseModel):
    """Model for uploaded documents."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    filename: str
    file_type: str  # pdf, docx, txt, etc.
    file_size: int  # bytes
    chunk_count: int = 0
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = False
    content_summary: Optional[str] = None


# ============================================================================
# Node 2: Hypothesis Generator Models
# ============================================================================

class Hypothesis(BaseModel):
    """Model for suspected inefficiency hypothesis."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    process_area: str = Field(..., description="The process or department affected")
    description: str = Field(..., description="Description of the suspected inefficiency")
    evidence: List[str] = Field(
        default_factory=list,
        description="Quotes or references from source documents"
    )
    indicators: List[str] = Field(
        default_factory=list,
        description="Keywords/patterns that triggered this hypothesis"
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1)"
    )
    category: str = Field(
        default="general",
        description="Type: manual_process, communication_gap, data_silos, etc."
    )


# ============================================================================
# Node 3: Interview Architect Models
# ============================================================================

class InterviewQuestion(BaseModel):
    """Model for a single interview question."""
    role: str = Field(..., description="Target interviewee role (e.g., CFO, Operations Manager)")
    question: str = Field(..., description="The interview question")
    intent: str = Field(..., description="Why we're asking this question")
    follow_ups: List[str] = Field(
        default_factory=list,
        description="Potential follow-up questions"
    )
    related_hypothesis_id: Optional[str] = Field(
        None,
        description="Link to the hypothesis this question validates"
    )


class InterviewScript(BaseModel):
    """Complete interview script output from Node 3."""
    project_id: str
    target_departments: List[str]
    target_roles: List[str] = Field(
        default_factory=list,
        description="Recommended roles to interview"
    )
    introduction: str = Field(
        default="",
        description="Opening statement for the interview"
    )
    questions: List[InterviewQuestion]
    closing_notes: str = Field(
        default="",
        description="Closing remarks and next steps"
    )
    estimated_duration_minutes: int = Field(
        default=60,
        description="Estimated interview duration"
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Node 4 & 5: Gap Analysis and Solution Models
# ============================================================================

class GapAnalysisItem(BaseModel):
    """Individual gap identified between SOP and reality."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    process_step: str = Field(..., description="The step in the process")
    sop_description: str = Field(..., description="How the SOP says it should work")
    observed_behavior: str = Field(..., description="How it actually works per interview")
    gap_description: str = Field(..., description="The discrepancy identified")
    root_cause: Optional[str] = Field(None, description="Suspected root cause")
    impact: str = Field(..., description="Business impact of this gap")
    task_category: TaskCategory = TaskCategory.AUTOMATABLE


class AnalysisResult(BaseModel):
    """Full analysis result combining gap and solution (Output of Node 4/5)."""
    process_step: str
    observed_behavior: str
    pain_point_severity: Severity
    proposed_solution: str
    tech_stack_recommendation: List[str]
    estimated_roi_hours: int = Field(
        ...,
        description="Estimated hours saved per month"
    )
    implementation_complexity: Complexity = Complexity.MEDIUM
    priority_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Priority score based on ROI and complexity"
    )


class SolutionRecommendation(BaseModel):
    """Detailed solution recommendation."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    gap_id: str = Field(..., description="Reference to the gap being solved")
    solution_name: str
    solution_description: str
    technology_stack: List[str]
    implementation_steps: List[str]
    estimated_effort_hours: int
    estimated_cost_range: str  # e.g., "$5,000 - $10,000"
    estimated_monthly_savings: float
    payback_period_months: float
    risks: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)


# ============================================================================
# Node 6: Report Models
# ============================================================================

class ExecutiveSummary(BaseModel):
    """Executive summary section of the report."""
    overview: str
    key_findings: List[str]
    top_recommendations: List[str]
    total_potential_savings: float
    total_implementation_cost: float
    overall_roi_percentage: float


class CurrentVsFutureState(BaseModel):
    """Comparison table entry."""
    process_area: str
    current_state: str
    future_state: str
    improvement_description: str


class Report(BaseModel):
    """Final report model (Output of Node 6)."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    title: str
    executive_summary: ExecutiveSummary
    hypotheses: List[Hypothesis]
    interview_insights: List[str]
    gap_analyses: List[GapAnalysisItem]
    solutions: List[AnalysisResult]
    current_vs_future: List[CurrentVsFutureState]
    implementation_roadmap: List[Dict[str, Any]]
    appendix: Optional[Dict[str, Any]] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Google ADK Models
# ============================================================================

class GoogleInsight(BaseModel):
    """Model for Google ADK-generated insights."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    insight_type: InsightType
    description: str = Field(..., description="Detailed description of the insight")
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1)"
    )
    source: str = Field(default="google_gemini", description="Source of the insight")
    recommended_actions: List[str] = Field(
        default_factory=list,
        description="Specific actions recommended"
    )
    related_hypotheses: List[str] = Field(
        default_factory=list,
        description="IDs of related hypotheses"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MultimodalAnalysisResult(BaseModel):
    """Result from Google Gemini multimodal analysis."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    image_count: int = Field(default=0, description="Number of images analyzed")
    analysis_summary: str = Field(..., description="Summary of multimodal analysis")
    identified_processes: List[str] = Field(
        default_factory=list,
        description="Processes identified from visual data"
    )
    identified_inefficiencies: List[str] = Field(
        default_factory=list,
        description="Inefficiencies identified from visual analysis"
    )
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# LangGraph State Models
# ============================================================================

class GraphState(BaseModel):
    """
    The state object that flows through the LangGraph workflow.
    Contains all data accumulated during the consulting process.
    """
    # Project context
    project_id: str
    project: Optional[Project] = None

    # Node 1 outputs
    documents: List[Document] = Field(default_factory=list)
    ingestion_complete: bool = False
    document_summaries: List[str] = Field(default_factory=list)

    # Node 2 outputs
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    hypothesis_generation_complete: bool = False

    # Node 3 outputs
    interview_script: Optional[InterviewScript] = None
    script_generation_complete: bool = False

    # Human breakpoint data
    is_suspended: bool = False
    suspension_reason: Optional[str] = None
    transcript: Optional[str] = None
    transcript_received: bool = False

    # Node 4 outputs
    gap_analyses: List[GapAnalysisItem] = Field(default_factory=list)
    gap_analysis_complete: bool = False

    # Node 5 outputs
    solutions: List[AnalysisResult] = Field(default_factory=list)
    solution_recommendations: List[SolutionRecommendation] = Field(default_factory=list)
    solutioning_complete: bool = False

    # Node 6 outputs
    report: Optional[Report] = None
    report_complete: bool = False
    report_pdf_path: Optional[str] = None

    # Google ADK outputs
    google_insights: List[GoogleInsight] = Field(default_factory=list)
    google_adk_complete: bool = False
    multimodal_analysis: Optional[MultimodalAnalysisResult] = None
    llm_provider: str = Field(default="openai", description="LLM provider in use")

    # Workflow metadata
    current_node: str = "start"
    errors: List[str] = Field(default_factory=list)
    messages: List[str] = Field(default_factory=list)

    class Config:
        """Pydantic config for serialization."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
