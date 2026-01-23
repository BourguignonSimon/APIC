"""
Document Management Routes
API endpoints for uploading and managing documents.
"""

import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, status, Form
from pydantic import BaseModel

from src.services.state_manager import StateManager
from config.settings import settings

router = APIRouter()
state_manager = StateManager()


# ============================================================================
# Response Models
# ============================================================================

class DocumentResponse(BaseModel):
    """Response model for document data."""
    id: str
    project_id: str
    filename: str
    file_type: str
    file_size: int
    processed: bool = False
    chunk_count: int = 0
    uploaded_at: str
    category: str = "source"  # 'source' for initial docs, 'interview_results' for Step 4


class DocumentListResponse(BaseModel):
    """Response model for document list."""
    documents: List[DocumentResponse]
    total_count: int


class UploadResponse(BaseModel):
    """Response model for file upload."""
    message: str
    documents: List[DocumentResponse]


# ============================================================================
# Helper Functions
# ============================================================================

def get_file_extension(filename: str) -> str:
    """Extract file extension from filename."""
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def validate_file_type(filename: str) -> bool:
    """Check if file type is allowed."""
    extension = get_file_extension(filename)
    return extension in settings.ALLOWED_EXTENSIONS


def get_project_upload_dir(project_id: str) -> str:
    """Get upload directory for a project."""
    upload_dir = os.path.join(settings.UPLOAD_DIR, project_id)
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/projects/{project_id}/documents",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload source documents",
    description="Upload one or more source documents for a project (Step 1).",
)
async def upload_documents(
    project_id: str,
    files: List[UploadFile] = File(...),
):
    """
    Upload source documents for analysis (Step 1).

    Supported formats: PDF, DOCX, DOC, TXT, PPTX, XLSX
    Maximum file size: 50MB per file
    """
    return await _upload_documents(project_id, files, category="source")


@router.post(
    "/projects/{project_id}/interview-results",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload interview result documents",
    description="Upload interview result documents for report generation (Step 4).",
)
async def upload_interview_results(
    project_id: str,
    files: List[UploadFile] = File(...),
):
    """
    Upload interview result documents (Step 4).

    These documents contain interview notes, transcripts, or recordings
    that will be analyzed to generate the final report.

    Supported formats: PDF, DOCX, DOC, TXT, PPTX, XLSX
    Maximum file size: 50MB per file
    """
    return await _upload_documents(project_id, files, category="interview_results")


async def _upload_documents(
    project_id: str,
    files: List[UploadFile],
    category: str = "source",
) -> UploadResponse:
    """
    Internal helper to upload documents with a specified category.

    Args:
        project_id: Project ID
        files: List of uploaded files
        category: Document category ('source' or 'interview_results')

    Returns:
        UploadResponse with uploaded document details
    """
    # Verify project exists
    project = state_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    upload_dir = get_project_upload_dir(project_id)
    uploaded_docs = []

    for file in files:
        # Validate file type
        if not validate_file_type(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed: {file.filename}. "
                       f"Allowed types: {settings.ALLOWED_EXTENSIONS}",
            )

        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning

        if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large: {file.filename}. "
                       f"Maximum size: {settings.MAX_FILE_SIZE_MB}MB",
            )

        # Save file
        file_path = os.path.join(upload_dir, file.filename)

        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}",
            )

        # Add to database
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
    description="Get all documents uploaded for a project, optionally filtered by category.",
)
async def list_documents(project_id: str, category: Optional[str] = None):
    """
    List all documents for a project.

    Args:
        project_id: Project ID
        category: Optional filter by category ('source' or 'interview_results')
    """
    # Verify project exists
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
    description="Get details of a specific document.",
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
    description="Delete a document from a project.",
)
async def delete_document(project_id: str, document_id: str):
    """Delete a document."""
    docs = state_manager.get_project_documents(project_id)

    for doc in docs:
        if doc["id"] == document_id:
            # Delete file
            file_path = os.path.join(
                settings.UPLOAD_DIR,
                project_id,
                doc["filename"]
            )
            if os.path.exists(file_path):
                os.remove(file_path)

            # Note: Would need to add delete method to state_manager
            return

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Document {document_id} not found",
    )
