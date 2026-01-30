"""
Workflow Management Routes
API endpoints for running and managing the Consultant Graph workflow.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Literal
import uuid
import zipfile
import tempfile
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.services.workflow import ConsultantGraph
from src.services.state_manager import StateManager
from src.services.interview_script_generator import get_interview_script_generator

router = APIRouter()
logger = logging.getLogger(__name__)

# Global instances
state_manager = StateManager()
consultant_graph = ConsultantGraph()


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
    script_files: Optional[Dict[str, Optional[str]]] = None


class InterviewScriptFileInfo(BaseModel):
    """Information about a single interview script file."""
    filename: str
    path: str
    format: str
    size_bytes: int
    created_at: str
    modified_at: str


class InterviewScriptFilesResponse(BaseModel):
    """Response model for listing interview script files."""
    project_id: str
    files: List[InterviewScriptFileInfo]
    available_formats: List[str]


class InterviewScriptRegenerateResponse(BaseModel):
    """Response model for regenerating interview script files."""
    project_id: str
    message: str
    files: Dict[str, Optional[str]]


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

    # Generate thread ID
    thread_id = str(uuid.uuid4())

    try:
        # Run workflow to interview breakpoint
        final_state = await consultant_graph.run_to_interview(
            project_id=project_id,
            project=project,
            documents=docs,
            thread_id=thread_id,
        )

        # Save state
        state_manager.save_state(project_id, thread_id, final_state)
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

    # Get thread ID
    thread_id = state_manager.get_thread_id(project_id)
    if not thread_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active workflow found. Start analysis first.",
        )

    # Verify workflow is suspended
    current_state = state_manager.load_state(project_id)
    if not current_state or not current_state.get("is_suspended"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow is not suspended. Cannot submit transcript.",
        )

    try:
        # Resume workflow with transcript
        final_state = await consultant_graph.resume_with_transcript(
            thread_id=thread_id,
            transcript=transcript,
        )

        # Save final state
        state_manager.save_state(project_id, thread_id, final_state)
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

    # Get state
    state = state_manager.load_state(project_id)
    thread_id = state_manager.get_thread_id(project_id)

    if not state:
        return WorkflowStatusResponse(
            project_id=project_id,
            thread_id=None,
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
    # Verify project exists
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    state = state_manager.load_state(project_id)

    # Return empty response if workflow not started yet
    if not state:
        return InterviewScriptResponse(
            project_id=project_id,
            interview_script=None,
            target_roles=[],
            estimated_duration_minutes=0,
            script_files=None,
        )

    script = state.get("interview_script")
    script_files = state.get("interview_script_files")

    # If no script files in state, check the file system
    if not script_files and script:
        generator = get_interview_script_generator()
        script_files = generator.get_script_files(project_id)

    return InterviewScriptResponse(
        project_id=project_id,
        interview_script=script,
        target_roles=script.get("target_roles", []) if script else [],
        estimated_duration_minutes=script.get("estimated_duration_minutes", 60) if script else 0,
        script_files=script_files,
    )


@router.get(
    "/workflow/{project_id}/interview-script/files",
    response_model=InterviewScriptFilesResponse,
    summary="List interview script files",
    description="List all generated interview script files for a project.",
)
async def list_interview_script_files(project_id: str):
    """List all interview script files for a project."""
    # Verify project exists
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    generator = get_interview_script_generator()
    files = generator.list_all_scripts(project_id)

    return InterviewScriptFilesResponse(
        project_id=project_id,
        files=[InterviewScriptFileInfo(**f) for f in files],
        available_formats=["pdf", "docx", "markdown"],
    )


@router.get(
    "/workflow/{project_id}/interview-script/export/{format}",
    summary="Export interview script",
    description="Download the interview script in the specified format (pdf, docx, or markdown).",
)
async def export_interview_script(
    project_id: str,
    format: Literal["pdf", "docx", "markdown"],
):
    """
    Download the interview script in the specified format.

    Args:
        project_id: The project ID
        format: The format to download (pdf, docx, or markdown)

    Returns:
        File response with the interview script
    """
    # Verify project exists
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    generator = get_interview_script_generator()
    script_files = generator.get_script_files(project_id)

    file_path = script_files.get(format)

    if not file_path or not os.path.exists(file_path):
        # Try to generate the file if interview script exists in state
        state = state_manager.load_state(project_id)
        if state and state.get("interview_script"):
            try:
                script_data = state["interview_script"]
                project_data = state.get("project", project)

                if format == "pdf":
                    file_path = generator.generate_pdf(script_data, project_data)
                elif format == "docx":
                    file_path = generator.generate_docx(script_data, project_data)
                elif format == "markdown":
                    file_path = generator.generate_markdown(script_data, project_data)
            except Exception as e:
                logger.error(f"Failed to generate {format} file: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to generate {format} file: {str(e)}",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Interview script not found. Start analysis first.",
            )

    # Determine media type
    media_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "markdown": "text/markdown",
    }

    # Get filename for download
    filename = os.path.basename(file_path)

    return FileResponse(
        path=file_path,
        media_type=media_types.get(format, "application/octet-stream"),
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get(
    "/workflow/{project_id}/interview-script/export/all",
    summary="Export all interview script formats as ZIP",
    description="Download all interview script formats (PDF, DOCX, Markdown) in a single ZIP file.",
)
async def export_all_interview_scripts(project_id: str):
    """
    Download all interview script formats in a single ZIP file.

    Args:
        project_id: The project ID

    Returns:
        ZIP file containing PDF, DOCX, and Markdown versions
    """
    # Verify project exists
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    generator = get_interview_script_generator()
    state = state_manager.load_state(project_id)

    if not state or not state.get("interview_script"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview script not found. Start analysis first.",
        )

    # Generate all formats if they don't exist
    script_data = state["interview_script"]
    project_data = state.get("project", project)

    file_paths = {}
    formats = ["pdf", "docx", "markdown"]

    for fmt in formats:
        try:
            script_files = generator.get_script_files(project_id)
            file_path = script_files.get(fmt)

            # Generate if doesn't exist
            if not file_path or not os.path.exists(file_path):
                if fmt == "pdf":
                    file_path = generator.generate_pdf(script_data, project_data)
                elif fmt == "docx":
                    file_path = generator.generate_docx(script_data, project_data)
                elif fmt == "markdown":
                    file_path = generator.generate_markdown(script_data, project_data)

            if file_path and os.path.exists(file_path):
                file_paths[fmt] = file_path
        except Exception as e:
            logger.error(f"Failed to generate {fmt} file: {e}")

    if not file_paths:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate interview script files.",
        )

    # Create a temporary ZIP file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    client_name = project_data.get("client_name", project_id)
    zip_filename = f"interview_script_{client_name}_{timestamp}.zip"

    # Create temp file
    temp_fd, temp_path = tempfile.mkstemp(suffix=".zip")
    os.close(temp_fd)

    try:
        # Create ZIP file
        with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for fmt, file_path in file_paths.items():
                # Add file to ZIP with just the basename
                arcname = os.path.basename(file_path)
                zipf.write(file_path, arcname=arcname)

        # Return the ZIP file
        return FileResponse(
            path=temp_path,
            media_type="application/zip",
            filename=zip_filename,
            headers={
                "Content-Disposition": f"attachment; filename={zip_filename}",
            },
            background=BackgroundTasks().add_task(lambda: os.unlink(temp_path) if os.path.exists(temp_path) else None)
        )
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        logger.error(f"Failed to create ZIP file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create ZIP file: {str(e)}",
        )


@router.post(
    "/workflow/{project_id}/interview-script/regenerate",
    response_model=InterviewScriptRegenerateResponse,
    summary="Regenerate interview script files",
    description="Regenerate interview script files from existing script data.",
)
async def regenerate_interview_script_files(project_id: str):
    """
    Regenerate interview script files from existing script data.

    This is useful if the original files were deleted or if you want
    to regenerate with updated formatting.
    """
    # Verify project exists
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Get the interview script from state
    state = state_manager.load_state(project_id)
    if not state or not state.get("interview_script"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No interview script found. Start analysis first.",
        )

    try:
        generator = get_interview_script_generator()
        script_data = state["interview_script"]
        project_data = state.get("project", project)

        # Generate all formats
        file_paths = generator.generate_all_formats(script_data, project_data)

        # Update state with new file paths
        state["interview_script_files"] = file_paths
        thread_id = state_manager.get_thread_id(project_id)
        if thread_id:
            state_manager.save_state(project_id, thread_id, state)

        return InterviewScriptRegenerateResponse(
            project_id=project_id,
            message="Interview script files regenerated successfully.",
            files=file_paths,
        )

    except Exception as e:
        logger.error(f"Failed to regenerate interview script files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate files: {str(e)}",
        )


@router.get(
    "/workflow/{project_id}/report",
    response_model=ReportResponse,
    summary="Get final report",
    description="Get the final analysis report for a project.",
)
async def get_report(project_id: str):
    """Get the final report."""
    # Verify project exists
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    state = state_manager.load_state(project_id)

    # Return empty response if workflow not started yet
    if not state:
        return ReportResponse(
            project_id=project_id,
            report_pdf_path=None,
            report=None,
            status="not_started",
        )

    # Return status based on workflow progress
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
    # Verify project exists
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    state = state_manager.load_state(project_id)

    # Return empty response if workflow not started yet
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
    # Verify project exists
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    state = state_manager.load_state(project_id)

    # Return empty response if workflow not started yet
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
    # Verify project exists
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    state = state_manager.load_state(project_id)

    # Return empty response if workflow not started yet
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
