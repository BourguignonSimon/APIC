"""
API Routes
Consolidated endpoints for projects, documents, and workflow management.
"""

import logging
import os
import shutil
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from config.settings import settings
from src.services.interview_script_generator import get_interview_script_generator
from src.services.state_manager import StateManager
from src.services.workflow import ConsultantGraph

router = APIRouter()
logger = logging.getLogger(__name__)

# Global instances
state_manager = StateManager()
consultant_graph = ConsultantGraph()


# ============================================================================
# Project Models
# ============================================================================


class ProjectCreateRequest(BaseModel):
    """Request model for creating a project."""

    client_name: str = Field(..., description="Name of the client organization")
    project_name: str = Field(..., description="Name of the consulting project")
    description: Optional[str] = Field(None, description="Project description")
    target_departments: List[str] = Field(
        default_factory=list, description="Departments to focus on"
    )


class ProjectResponse(BaseModel):
    """Response model for project data."""

    id: str
    client_name: str
    project_name: str
    description: Optional[str]
    target_departments: List[str]
    status: str
    vector_namespace: Optional[str]
    thread_id: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None


class ProjectListResponse(BaseModel):
    """Response model for project list."""

    id: str
    client_name: str
    project_name: str
    status: str
    created_at: str


class SuspendedProjectResponse(BaseModel):
    """Response model for suspended projects."""

    project_id: str
    thread_id: str
    project_name: str
    client_name: str
    current_node: str
    suspension_reason: Optional[str]
    suspended_at: str


# ============================================================================
# Document Models
# ============================================================================


class DocumentResponse(BaseModel):
    """Response model for document data."""

    id: str
    project_id: str
    filename: str
    file_type: str
    file_size: int
    source_type: str = "file"
    source_url: Optional[str] = None
    processed: bool = False
    chunk_count: int = 0
    uploaded_at: str
    category: str = "general"


class DocumentListResponse(BaseModel):
    """Response model for document list."""

    documents: List[DocumentResponse]
    total_count: int


class UploadResponse(BaseModel):
    """Response model for file upload."""

    message: str
    documents: List[DocumentResponse]


# ============================================================================
# Workflow Models
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
    script_file: Optional[str] = None


class InterviewScriptFileInfo(BaseModel):
    """Information about a single interview script file."""

    filename: str
    path: str
    size_bytes: int
    created_at: str
    modified_at: str


class InterviewScriptFilesResponse(BaseModel):
    """Response model for listing interview script files."""

    project_id: str
    files: List[InterviewScriptFileInfo]


class InterviewScriptRegenerateResponse(BaseModel):
    """Response model for regenerating interview script files."""

    project_id: str
    message: str
    file: Optional[str]


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
# Helper Functions
# ============================================================================


def get_file_extension(filename: str) -> str:
    """Extract file extension from filename."""
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def validate_file_type(filename: str) -> bool:
    """Check if file type is allowed."""
    return get_file_extension(filename) in settings.ALLOWED_EXTENSIONS


def get_project_upload_dir(project_id: str) -> str:
    """Get upload directory for a project."""
    upload_dir = os.path.join(settings.UPLOAD_DIR, project_id)
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


# ============================================================================
# Project Endpoints
# ============================================================================


@router.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    tags=["Projects"],
)
async def create_project(request: ProjectCreateRequest):
    """Create a new consulting project."""
    try:
        project = state_manager.create_project(
            client_name=request.client_name,
            project_name=request.project_name,
            description=request.description,
            target_departments=request.target_departments,
        )
        return ProjectResponse(**project)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}",
        )


@router.get(
    "/projects",
    response_model=List[ProjectListResponse],
    summary="List all projects",
    tags=["Projects"],
)
async def list_projects():
    """List all projects ordered by creation date."""
    try:
        projects = state_manager.list_projects()
        return [ProjectListResponse(**p) for p in projects]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list projects: {str(e)}",
        )


@router.get(
    "/projects/suspended",
    response_model=List[SuspendedProjectResponse],
    summary="Get suspended projects",
    tags=["Projects"],
)
async def get_suspended_projects():
    """Get all projects waiting at the human breakpoint."""
    try:
        suspended = state_manager.get_suspended_projects()
        return [SuspendedProjectResponse(**p) for p in suspended]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get suspended projects: {str(e)}",
        )


@router.get(
    "/projects/{project_id}",
    response_model=ProjectResponse,
    summary="Get project details",
    tags=["Projects"],
)
async def get_project(project_id: str):
    """Get project by ID."""
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    project["thread_id"] = state_manager.get_thread_id(project_id)
    return ProjectResponse(**project)


@router.patch(
    "/projects/{project_id}/status",
    summary="Update project status",
    tags=["Projects"],
)
async def update_project_status(project_id: str, new_status: str):
    """Update project status."""
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    try:
        state_manager.update_project_status(project_id, new_status)
        return {"message": f"Project status updated to {new_status}"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update status: {str(e)}",
        )


# ============================================================================
# Document Endpoints
# ============================================================================


@router.post(
    "/projects/{project_id}/documents",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload documents",
    tags=["Documents"],
)
async def upload_documents(
    project_id: str,
    files: List[UploadFile] = File(...),
    category: str = Form(default="general"),
):
    """Upload documents for analysis."""
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    upload_dir = get_project_upload_dir(project_id)
    uploaded_docs = []

    for file in files:
        if not validate_file_type(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed: {file.filename}",
            )

        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large: {file.filename}",
            )

        file_path = os.path.join(upload_dir, file.filename)
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}",
            )

        doc = state_manager.add_document(
            project_id=project_id,
            filename=file.filename,
            file_type=get_file_extension(file.filename),
            file_size=file_size,
            file_path=file_path,
            category=category,
        )
        uploaded_docs.append(DocumentResponse(**doc))

    return UploadResponse(
        message=f"Successfully uploaded {len(uploaded_docs)} document(s)",
        documents=uploaded_docs,
    )


@router.get(
    "/projects/{project_id}/documents",
    response_model=DocumentListResponse,
    summary="List project documents",
    tags=["Documents"],
)
async def list_documents(
    project_id: str,
    category: Optional[str] = Query(None),
):
    """List all documents for a project."""
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    docs = state_manager.get_project_documents(project_id, category=category)
    return DocumentListResponse(
        documents=[DocumentResponse(**d) for d in docs],
        total_count=len(docs),
    )


@router.get(
    "/projects/{project_id}/documents/{document_id}",
    response_model=DocumentResponse,
    summary="Get document details",
    tags=["Documents"],
)
async def get_document(project_id: str, document_id: str):
    """Get document by ID."""
    docs = state_manager.get_project_documents(project_id)
    for doc in docs:
        if doc["id"] == document_id:
            return DocumentResponse(**doc)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Document {document_id} not found",
    )


@router.delete(
    "/projects/{project_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document",
    tags=["Documents"],
)
async def delete_document(project_id: str, document_id: str):
    """Delete a document."""
    docs = state_manager.get_project_documents(project_id)
    for doc in docs:
        if doc["id"] == document_id:
            file_path = os.path.join(settings.UPLOAD_DIR, project_id, doc["filename"])
            if os.path.exists(file_path):
                os.remove(file_path)
            return
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Document {document_id} not found",
    )


# ============================================================================
# Workflow Endpoints
# ============================================================================


@router.post(
    "/workflow/start",
    response_model=StartAnalysisResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start analysis workflow",
    tags=["Workflow"],
)
async def start_analysis(request: StartAnalysisRequest, background_tasks: BackgroundTasks):
    """Start the analysis workflow."""
    project_id = request.project_id

    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    docs = state_manager.get_project_documents(project_id)
    if not docs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No documents uploaded for this project",
        )

    thread_id = str(uuid.uuid4())

    try:
        final_state = await consultant_graph.run_to_interview(
            project_id=project_id,
            project=project,
            documents=docs,
            thread_id=thread_id,
        )

        state_manager.save_state(project_id, thread_id, final_state)
        state_manager.update_project_status(project_id, "interview_ready")

        return StartAnalysisResponse(
            message="Analysis complete. Interview script generated.",
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
    tags=["Workflow"],
)
async def submit_transcript(request: SubmitTranscriptRequest, background_tasks: BackgroundTasks):
    """Submit interview transcript and resume analysis."""
    project_id = request.project_id

    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    thread_id = state_manager.get_thread_id(project_id)
    if not thread_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active workflow found. Start analysis first.",
        )

    current_state = state_manager.load_state(project_id)
    if not current_state or not current_state.get("is_suspended"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow is not suspended. Cannot submit transcript.",
        )

    try:
        final_state = await consultant_graph.resume_with_transcript(
            thread_id=thread_id,
            transcript=request.transcript,
        )

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
    tags=["Workflow"],
)
async def get_workflow_status(project_id: str):
    """Get current workflow status."""
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

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
    tags=["Workflow"],
)
async def get_interview_script(project_id: str):
    """Get the interview script."""
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    state = state_manager.load_state(project_id)
    if not state:
        return InterviewScriptResponse(
            project_id=project_id,
            interview_script=None,
            target_roles=[],
            estimated_duration_minutes=0,
            script_file=None,
        )

    script = state.get("interview_script")
    script_file = state.get("interview_script_file")

    if not script_file and script:
        generator = get_interview_script_generator()
        script_file = generator.get_script_file(project_id)

    return InterviewScriptResponse(
        project_id=project_id,
        interview_script=script,
        target_roles=script.get("target_roles", []) if script else [],
        estimated_duration_minutes=script.get("estimated_duration_minutes", 60) if script else 0,
        script_file=script_file,
    )


@router.get(
    "/workflow/{project_id}/interview-script/files",
    response_model=InterviewScriptFilesResponse,
    summary="List interview script files",
    tags=["Workflow"],
)
async def list_interview_script_files(project_id: str):
    """List all interview script files for a project."""
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
    )


@router.get(
    "/workflow/{project_id}/interview-script/export",
    summary="Export interview script",
    tags=["Workflow"],
)
async def export_interview_script(project_id: str):
    """Download the interview script as Markdown."""
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    generator = get_interview_script_generator()
    file_path = generator.get_script_file(project_id)

    if not file_path or not os.path.exists(file_path):
        state = state_manager.load_state(project_id)
        if state and state.get("interview_script"):
            try:
                script_data = state["interview_script"]
                project_data = state.get("project", project)
                file_path = generator.generate_markdown(script_data, project_data)
            except Exception as e:
                logger.error(f"Failed to generate markdown file: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to generate markdown file: {str(e)}",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview script not found. Start analysis first.",
            )

    filename = os.path.basename(file_path)
    return FileResponse(
        path=file_path,
        media_type="text/markdown",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post(
    "/workflow/{project_id}/interview-script/regenerate",
    response_model=InterviewScriptRegenerateResponse,
    summary="Regenerate interview script file",
    tags=["Workflow"],
)
async def regenerate_interview_script_file(project_id: str):
    """Regenerate interview script file from existing script data."""
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

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

        file_path = generator.generate(script_data, project_data)

        state["interview_script_file"] = file_path
        thread_id = state_manager.get_thread_id(project_id)
        if thread_id:
            state_manager.save_state(project_id, thread_id, state)

        return InterviewScriptRegenerateResponse(
            project_id=project_id,
            message="Interview script file regenerated successfully.",
            file=file_path,
        )
    except Exception as e:
        logger.error(f"Failed to regenerate interview script file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate file: {str(e)}",
        )


@router.get(
    "/workflow/{project_id}/report",
    response_model=ReportResponse,
    summary="Get final report",
    tags=["Workflow"],
)
async def get_report(project_id: str):
    """Get the final report."""
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    state = state_manager.load_state(project_id)

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
    tags=["Workflow"],
)
async def get_hypotheses(project_id: str):
    """Get the hypotheses."""
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    state = state_manager.load_state(project_id)

    if not state:
        return HypothesesResponse(project_id=project_id, hypotheses=[], count=0)

    return HypothesesResponse(
        project_id=project_id,
        hypotheses=state.get("hypotheses", []),
        count=len(state.get("hypotheses", [])),
    )


@router.get(
    "/workflow/{project_id}/gaps",
    response_model=GapsResponse,
    summary="Get gap analysis",
    tags=["Workflow"],
)
async def get_gaps(project_id: str):
    """Get the gap analysis results."""
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    state = state_manager.load_state(project_id)

    if not state:
        return GapsResponse(project_id=project_id, gap_analyses=[], count=0)

    return GapsResponse(
        project_id=project_id,
        gap_analyses=state.get("gap_analyses", []),
        count=len(state.get("gap_analyses", [])),
    )


@router.get(
    "/workflow/{project_id}/solutions",
    response_model=SolutionsResponse,
    summary="Get solutions",
    tags=["Workflow"],
)
async def get_solutions(project_id: str):
    """Get the solution recommendations."""
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    state = state_manager.load_state(project_id)

    if not state:
        return SolutionsResponse(
            project_id=project_id, solutions=[], recommendations=[], count=0
        )

    return SolutionsResponse(
        project_id=project_id,
        solutions=state.get("solutions", []),
        recommendations=state.get("solution_recommendations", []),
        count=len(state.get("solutions", [])),
    )
