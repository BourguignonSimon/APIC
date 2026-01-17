"""
Project Management Routes
API endpoints for managing consulting projects.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.services.state_manager import StateManager

router = APIRouter()
state_manager = StateManager()


# ============================================================================
# Request/Response Models
# ============================================================================

class ProjectCreateRequest(BaseModel):
    """Request model for creating a project."""
    client_name: str = Field(..., description="Name of the client organization")
    project_name: str = Field(..., description="Name of the consulting project")
    description: Optional[str] = Field(None, description="Project description")
    target_departments: List[str] = Field(
        default_factory=list,
        description="Departments to focus on"
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
# Endpoints
# ============================================================================

@router.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    description="Create a new consulting project for a client.",
)
async def create_project(request: ProjectCreateRequest):
    """
    Create a new consulting project.

    This will:
    - Generate a unique project ID
    - Create a vector namespace for document storage
    - Initialize project state
    """
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
    description="Get a list of all consulting projects.",
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
    "/projects/{project_id}",
    response_model=ProjectResponse,
    summary="Get project details",
    description="Get detailed information about a specific project.",
)
async def get_project(project_id: str):
    """Get project by ID."""
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Get thread ID if available
    thread_id = state_manager.get_thread_id(project_id)
    project["thread_id"] = thread_id

    return ProjectResponse(**project)


@router.get(
    "/projects/suspended",
    response_model=List[SuspendedProjectResponse],
    summary="Get suspended projects",
    description="Get all projects that are suspended awaiting input.",
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


@router.patch(
    "/projects/{project_id}/status",
    summary="Update project status",
    description="Update the status of a project.",
)
async def update_project_status(project_id: str, status: str):
    """Update project status."""
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    try:
        state_manager.update_project_status(project_id, status)
        return {"message": f"Project status updated to {status}"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update status: {str(e)}",
        )
