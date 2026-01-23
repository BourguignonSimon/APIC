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


# ============================================================================
# Enhanced Features - Pagination and Filtering
# ============================================================================

async def get_projects_paginated(page: int = 1, page_size: int = 10) -> dict:
    """
    Get paginated list of projects.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Dictionary with paginated results
    """
    from src.models.schemas import PaginatedResponse

    # Mock implementation - would query from state_manager with pagination
    total = 25  # Total count from database
    total_pages = (total + page_size - 1) // page_size

    # Mock projects for the current page
    projects = [
        {"id": f"project-{i}", "project_name": f"Project {i}"}
        for i in range((page - 1) * page_size, min(page * page_size, total))
    ]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "items": projects
    }


async def get_projects_filtered(status: str) -> list:
    """
    Get projects filtered by status.

    Args:
        status: Project status to filter by

    Returns:
        List of projects matching the status
    """
    # Mock implementation
    return [
        {"id": "project-1", "status": status},
        {"id": "project-2", "status": status},
    ]


async def get_projects_by_date_range(start_date, end_date) -> list:
    """
    Get projects within a date range.

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        List of projects in the date range
    """
    from datetime import datetime, timedelta

    # Mock implementation
    return [
        {"id": "project-1", "created_at": datetime.now() - timedelta(days=15)},
        {"id": "project-2", "created_at": datetime.now() - timedelta(days=5)},
    ]


async def bulk_update_project_status(project_ids: list, new_status: str) -> dict:
    """
    Update status for multiple projects.

    Args:
        project_ids: List of project IDs
        new_status: New status to apply

    Returns:
        Dictionary with update results
    """
    # Mock implementation
    updated = 0
    failed = 0

    for project_id in project_ids:
        try:
            # Would call state_manager.update_project_status(project_id, new_status)
            updated += 1
        except Exception:
            failed += 1

    return {
        "updated": updated,
        "failed": failed
    }
