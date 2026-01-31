"""
Workflow Management Routes
API endpoints for running and managing the Consultant Graph workflow.

Workflow state is managed by LangGraph's built-in checkpointing.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from src.services.workflow import get_workflow
from src.services.state_manager import StateManager

router = APIRouter()
logger = logging.getLogger(__name__)

# Global instances
state_manager = StateManager()


# ============================================================================
# Request/Response Models
# ============================================================================

class StartAnalysisRequest(BaseModel):
    """Request model for starting analysis."""
    project_id: str = Field(..., description="Project ID to analyze")


class StartAnalysisResponse(BaseModel):
    """Response model for analysis start."""
    message: str
    project_id: str
    thread_id: str
    status: str
    interview_script: Optional[Dict[str, Any]] = None


class SubmitTranscriptRequest(BaseModel):
    """Request model for submitting interview transcript."""
    project_id: str = Field(..., description="Project ID")
    transcript: str = Field(..., description="Interview transcript text")


class SubmitTranscriptResponse(BaseModel):
    """Response model for transcript submission."""
    message: str
    project_id: str
    status: str


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status."""
    project_id: str
    thread_id: Optional[str]
    current_node: str
    is_suspended: bool
    suspension_reason: Optional[str]
    messages: List[str]
    errors: List[str]


class ReportResponse(BaseModel):
    """Response model for completed report."""
    project_id: str
    report_pdf_path: Optional[str]
    report: Optional[Dict[str, Any]]
    status: str


class InterviewScriptResponse(BaseModel):
    """Response model for interview script."""
    project_id: str
    interview_script: Optional[Dict[str, Any]]
    target_roles: List[str]
    estimated_duration_minutes: int


class HypothesesResponse(BaseModel):
    """Response model for hypotheses."""
    project_id: str
    hypotheses: List[Dict[str, Any]]
    count: int


class GapsResponse(BaseModel):
    """Response model for gap analysis."""
    project_id: str
    gap_analyses: List[Dict[str, Any]]
    count: int


class SolutionsResponse(BaseModel):
    """Response model for solutions."""
    project_id: str
    solutions: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    count: int


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/workflow/start",
    response_model=StartAnalysisResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start analysis workflow",
    description="Start the Consultant Graph analysis for a project.",
)
async def start_analysis(
    request: StartAnalysisRequest,
    background_tasks: BackgroundTasks,
):
    """
    Start the analysis workflow.

    This will:
    1. Ingest uploaded documents
    2. Generate hypotheses about inefficiencies
    3. Create interview script
    4. Suspend execution awaiting interview transcript
    """
    project_id = request.project_id

    # Verify project exists
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Get documents
    docs = state_manager.get_project_documents(project_id)
    if not docs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No documents uploaded for this project",
        )

    # Use thread_id from project record
    thread_id = project.get("thread_id")
    if not thread_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Project missing thread_id",
        )

    try:
        workflow = get_workflow()
        # Run workflow to interview breakpoint (state saved by LangGraph checkpointer)
        final_state = await workflow.run_to_interview(
            project_id=project_id,
            project=project,
            documents=docs,
            thread_id=thread_id,
        )

        state_manager.update_project_status(project_id, "interview_ready")

        return StartAnalysisResponse(
            message="Analysis complete. Interview script generated. Awaiting transcript.",
            project_id=project_id,
            thread_id=thread_id,
            status="suspended",
            interview_script=final_state.get("interview_script"),
        )

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        state_manager.update_project_status(project_id, "failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )


@router.post(
    "/workflow/resume",
    response_model=SubmitTranscriptResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Resume workflow with transcript",
    description="Submit interview transcript and resume the analysis.",
)
async def submit_transcript(
    request: SubmitTranscriptRequest,
    background_tasks: BackgroundTasks,
):
    """
    Submit interview transcript and resume analysis.

    This will:
    1. Resume from the human breakpoint
    2. Perform gap analysis
    3. Generate solution recommendations
    4. Create final report
    """
    project_id = request.project_id
    transcript = request.transcript

    # Verify project exists
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Get thread ID from project
    thread_id = project.get("thread_id")
    if not thread_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active workflow found. Start analysis first.",
        )

    # Get current state from LangGraph checkpointer
    workflow = get_workflow()
    current_state = workflow.get_state(thread_id)
    if not current_state or not current_state.get("is_suspended"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow is not suspended. Cannot submit transcript.",
        )

    try:
        # Resume workflow with transcript (state saved by LangGraph checkpointer)
        await workflow.resume_with_transcript(
            thread_id=thread_id,
            transcript=transcript,
        )

        state_manager.update_project_status(project_id, "completed")

        return SubmitTranscriptResponse(
            message="Analysis resumed and completed. Report generated.",
            project_id=project_id,
            status="completed",
        )

    except Exception as e:
        logger.error(f"Resume failed: {e}")
        state_manager.update_project_status(project_id, "failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume analysis: {str(e)}",
        )


@router.get(
    "/workflow/{project_id}/status",
    response_model=WorkflowStatusResponse,
    summary="Get workflow status",
    description="Get the current status of a project's workflow.",
)
async def get_workflow_status(project_id: str):
    """Get current workflow status."""
    # Verify project exists
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    thread_id = project.get("thread_id")
    if not thread_id:
        return WorkflowStatusResponse(
            project_id=project_id,
            thread_id=None,
            current_node="not_started",
            is_suspended=False,
            suspension_reason=None,
            messages=[],
            errors=[],
        )

    # Get state from LangGraph checkpointer
    workflow = get_workflow()
    state = workflow.get_state(thread_id)

    if not state:
        return WorkflowStatusResponse(
            project_id=project_id,
            thread_id=thread_id,
            current_node="not_started",
            is_suspended=False,
            suspension_reason=None,
            messages=[],
            errors=[],
        )

    return WorkflowStatusResponse(
        project_id=project_id,
        thread_id=thread_id,
        current_node=state.get("current_node", "unknown"),
        is_suspended=state.get("is_suspended", False),
        suspension_reason=state.get("suspension_reason"),
        messages=state.get("messages", []),
        errors=state.get("errors", []),
    )


@router.get(
    "/workflow/{project_id}/interview-script",
    response_model=InterviewScriptResponse,
    summary="Get interview script",
    description="Get the generated interview script for a project.",
)
async def get_interview_script(project_id: str):
    """Get the interview script."""
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    thread_id = project.get("thread_id")
    if not thread_id:
        return InterviewScriptResponse(
            project_id=project_id,
            interview_script=None,
            target_roles=[],
            estimated_duration_minutes=0,
        )

    workflow = get_workflow()
    state = workflow.get_state(thread_id)

    if not state:
        return InterviewScriptResponse(
            project_id=project_id,
            interview_script=None,
            target_roles=[],
            estimated_duration_minutes=0,
        )

    script = state.get("interview_script")
    return InterviewScriptResponse(
        project_id=project_id,
        interview_script=script,
        target_roles=script.get("target_roles", []) if script else [],
        estimated_duration_minutes=script.get("estimated_duration_minutes", 60) if script else 0,
    )


@router.get(
    "/workflow/{project_id}/interview-script/markdown",
    response_class=PlainTextResponse,
    summary="Export interview script as Markdown",
    description="Export the interview script in Markdown format. Users can convert to PDF/DOCX using external tools if needed.",
)
async def get_interview_script_markdown(project_id: str):
    """
    Export the interview script as Markdown.

    This is the only supported export format. Users can convert to
    PDF or DOCX using external tools like pandoc if needed.
    """
    from src.models.schemas import InterviewScript, InterviewQuestion

    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    thread_id = project.get("thread_id")
    if not thread_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview script not yet generated",
        )

    workflow = get_workflow()
    state = workflow.get_state(thread_id)

    if not state or not state.get("interview_script"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview script not yet generated",
        )

    script_data = state.get("interview_script")

    # Convert questions to InterviewQuestion objects
    questions = [
        InterviewQuestion(**q) if isinstance(q, dict) else q
        for q in script_data.get("questions", [])
    ]

    # Create InterviewScript object
    script = InterviewScript(
        project_id=script_data.get("project_id", project_id),
        target_departments=script_data.get("target_departments", []),
        target_roles=script_data.get("target_roles", []),
        introduction=script_data.get("introduction", ""),
        questions=questions,
        closing_notes=script_data.get("closing_notes", ""),
        estimated_duration_minutes=script_data.get("estimated_duration_minutes", 60),
    )

    return script.to_markdown()


@router.get(
    "/workflow/{project_id}/report",
    response_model=ReportResponse,
    summary="Get final report",
    description="Get the final analysis report for a project.",
)
async def get_report(project_id: str):
    """Get the final report."""
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    thread_id = project.get("thread_id")
    if not thread_id:
        return ReportResponse(
            project_id=project_id,
            report_pdf_path=None,
            report=None,
            status="not_started",
        )

    workflow = get_workflow()
    state = workflow.get_state(thread_id)

    if not state:
        return ReportResponse(
            project_id=project_id,
            report_pdf_path=None,
            report=None,
            status="not_started",
        )

    if not state.get("report_complete"):
        return ReportResponse(
            project_id=project_id,
            report_pdf_path=None,
            report=None,
            status="in_progress",
        )

    return ReportResponse(
        project_id=project_id,
        report_pdf_path=state.get("report_pdf_path"),
        report=state.get("report"),
        status="completed",
    )


@router.get(
    "/workflow/{project_id}/hypotheses",
    response_model=HypothesesResponse,
    summary="Get hypotheses",
    description="Get generated hypotheses for a project.",
)
async def get_hypotheses(project_id: str):
    """Get the hypotheses."""
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    thread_id = project.get("thread_id")
    if not thread_id:
        return HypothesesResponse(
            project_id=project_id,
            hypotheses=[],
            count=0,
        )

    workflow = get_workflow()
    state = workflow.get_state(thread_id)

    if not state:
        return HypothesesResponse(
            project_id=project_id,
            hypotheses=[],
            count=0,
        )

    return HypothesesResponse(
        project_id=project_id,
        hypotheses=state.get("hypotheses", []),
        count=len(state.get("hypotheses", [])),
    )


@router.get(
    "/workflow/{project_id}/gaps",
    response_model=GapsResponse,
    summary="Get gap analysis",
    description="Get gap analysis results for a project.",
)
async def get_gaps(project_id: str):
    """Get the gap analysis results."""
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    thread_id = project.get("thread_id")
    if not thread_id:
        return GapsResponse(
            project_id=project_id,
            gap_analyses=[],
            count=0,
        )

    workflow = get_workflow()
    state = workflow.get_state(thread_id)

    if not state:
        return GapsResponse(
            project_id=project_id,
            gap_analyses=[],
            count=0,
        )

    return GapsResponse(
        project_id=project_id,
        gap_analyses=state.get("gap_analyses", []),
        count=len(state.get("gap_analyses", [])),
    )


@router.get(
    "/workflow/{project_id}/solutions",
    response_model=SolutionsResponse,
    summary="Get solutions",
    description="Get solution recommendations for a project.",
)
async def get_solutions(project_id: str):
    """Get the solution recommendations."""
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    thread_id = project.get("thread_id")
    if not thread_id:
        return SolutionsResponse(
            project_id=project_id,
            solutions=[],
            recommendations=[],
            count=0,
        )

    workflow = get_workflow()
    state = workflow.get_state(thread_id)

    if not state:
        return SolutionsResponse(
            project_id=project_id,
            solutions=[],
            recommendations=[],
            count=0,
        )

    return SolutionsResponse(
        project_id=project_id,
        solutions=state.get("solutions", []),
        recommendations=state.get("solution_recommendations", []),
        count=len(state.get("solutions", [])),
    )
