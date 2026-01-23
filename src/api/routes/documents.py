"""
Document Management Routes
API endpoints for uploading and managing documents.
"""

import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, status, Form, Query
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
    summary="Upload documents",
    description="Upload one or more documents for a project.",
)
async def upload_documents(
    project_id: str,
    files: List[UploadFile] = File(...),
    category: str = Form(default="general", description="Document category"),
):
    """
    Upload documents for analysis.

    Supported formats: PDF, DOCX, DOC, TXT, PPTX, XLSX
    Maximum file size: 50MB per file
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
async def list_documents(
    project_id: str,
    category: Optional[str] = Query(
        None,
        description="Filter documents by category (e.g., 'general', 'interview_results')",
    ),
):
    """List all documents for a project, optionally filtered by category."""
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


# ============================================================================
# Enhanced Features - Bulk Operations
# ============================================================================

async def bulk_upload_documents(project_id: str, files: list) -> dict:
    """
    Bulk upload multiple documents with partial failure handling.

    Args:
        project_id: ID of the project
        files: List of file dictionaries with filename, content, size

    Returns:
        Dictionary with upload results
    """
    from src.models.schemas import BulkUploadResult, Document

    uploaded_docs = []
    errors = []

    for file_data in files:
        try:
            # Validate file
            from src.utils.validators import DocumentValidator
            validator = DocumentValidator()

            validation_error = validator.validate_file(
                filename=file_data["filename"],
                file_size=file_data["size"],
                file_type=""
            )

            if validation_error:
                errors.append({
                    "filename": file_data["filename"],
                    "error": validation_error.message
                })
                continue

            # Create document record
            doc = Document(
                project_id=project_id,
                filename=file_data["filename"],
                file_type=get_file_extension(file_data["filename"]),
                file_size=file_data["size"]
            )

            uploaded_docs.append(doc)

        except Exception as e:
            errors.append({
                "filename": file_data["filename"],
                "error": str(e)
            })

    return {
        "total": len(files),
        "successful": len(uploaded_docs),
        "failed": len(errors),
        "documents": uploaded_docs,
        "errors": errors
    }
