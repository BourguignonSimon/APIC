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
    ARCHIVED = "archived"


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
    """Model for uploaded documents and URLs."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    filename: str
    file_type: str  # pdf, docx, txt, url, etc.
    file_size: int = 0  # bytes (0 for URLs)
    source_type: str = "file"  # "file" or "url"
    source_url: Optional[str] = None  # URL if source_type is "url"
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

class CustomerContext(BaseModel):
    """Customer context derived from ingested data analysis."""
    business_overview: str = Field(
        default="",
        description="Overview of the customer's business and industry"
    )
    organization_structure: str = Field(
        default="",
        description="Summary of relevant organizational structure"
    )
    current_challenges: List[str] = Field(
        default_factory=list,
        description="Key challenges identified from data analysis"
    )
    key_processes: List[str] = Field(
        default_factory=list,
        description="Main processes identified for review"
    )
    stakeholders: List[str] = Field(
        default_factory=list,
        description="Key stakeholders identified from documents"
    )
    industry_context: str = Field(
        default="",
        description="Industry-specific context and considerations"
    )
    data_sources_summary: str = Field(
        default="",
        description="Summary of analyzed data sources"
    )


class DiagnosticLead(BaseModel):
    """A lead/hypothesis to be validated during the interview."""
    hypothesis_id: str = Field(..., description="Reference to the hypothesis being validated")
    lead_summary: str = Field(..., description="Brief summary of the suspected inefficiency")
    category: str = Field(..., description="Category: manual_process, communication_gap, etc.")
    confidence: float = Field(default=0.5, description="AI confidence score (0-1)")
    validation_questions: List[str] = Field(
        default_factory=list,
        description="Questions to validate or invalidate this lead"
    )
    expected_evidence: List[str] = Field(
        default_factory=list,
        description="What evidence would confirm this lead"
    )


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
    question_type: str = Field(
        default="validation",
        description="Type: validation (review leads) or discovery (find new opportunities)"
    )


class InterviewScript(BaseModel):
    """Complete interview script output from Node 3."""
    project_id: str
    target_departments: List[str]
    target_roles: List[str] = Field(
        default_factory=list,
        description="Recommended roles to interview"
    )
    # Customer Context Section
    customer_context: Optional[CustomerContext] = Field(
        default=None,
        description="Customer context derived from data analysis"
    )
    # Diagnostic Form - Leads to validate
    diagnostic_leads: List[DiagnosticLead] = Field(
        default_factory=list,
        description="AI-generated leads/hypotheses to validate during interview"
    )
    introduction: str = Field(
        default="",
        description="Opening statement for the interview"
    )
    questions: List[InterviewQuestion]
    # Discovery questions for new opportunities
    discovery_questions: List[InterviewQuestion] = Field(
        default_factory=list,
        description="Open-ended questions to identify new customer-specific opportunities"
    )
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
    interview_script_files: Optional[Dict[str, Optional[str]]] = Field(
        default=None,
        description="Paths to generated interview script files (pdf, docx, markdown)"
    )

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

    # Workflow metadata
    current_node: str = "start"
    errors: List[str] = Field(default_factory=list)
    messages: List[str] = Field(default_factory=list)

    class Config:
        """Pydantic config for serialization."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# Enhanced Features Models
# ============================================================================

class ValidationError(BaseModel):
    """Validation error details."""
    field: str
    message: str
    suggested_action: Optional[str] = None
    error_code: Optional[str] = None


class BulkUploadResult(BaseModel):
    """Result of a bulk document upload operation."""
    total: int
    successful: int
    failed: int
    documents: List[Document]
    errors: List[Dict[str, str]] = Field(default_factory=list)


class PaginatedResponse(BaseModel):
    """Generic paginated response."""
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[Any]
