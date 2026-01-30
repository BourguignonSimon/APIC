"""
State Manager
Handles state persistence to PostgreSQL for the human breakpoint.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid


def serialize_state_data(data: Any) -> Any:
    """
    Recursively serialize data for JSON storage.

    Converts datetime objects to ISO format strings and handles
    nested dictionaries and lists.

    Args:
        data: Data to serialize

    Returns:
        JSON-serializable data
    """
    if isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, dict):
        return {key: serialize_state_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [serialize_state_data(item) for item in data]
    elif hasattr(data, 'model_dump'):
        # Handle Pydantic models
        return serialize_state_data(data.model_dump())
    elif hasattr(data, 'dict'):
        # Handle older Pydantic models (v1)
        return serialize_state_data(data.dict())
    return data

from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean, JSON, text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

from config.settings import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


class ProjectState(Base):
    """Database model for project state persistence."""

    __tablename__ = "project_states"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), unique=True, index=True, nullable=False)
    thread_id = Column(String(36), unique=True, index=True, nullable=False)
    state_data = Column(JSON, nullable=False)
    current_node = Column(String(50), nullable=False, default="start")
    is_suspended = Column(Boolean, default=False)
    suspension_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProjectRecord(Base):
    """Database model for project metadata."""

    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_name = Column(String(255), nullable=False)
    project_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_departments = Column(JSON, default=list)
    status = Column(String(50), default="created")
    vector_namespace = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DocumentRecord(Base):
    """Database model for uploaded documents and URLs."""

    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(String(50), nullable=False)
    file_path = Column(String(500), nullable=False, default="")
    source_type = Column(String(20), default="file")  # "file" or "url"
    source_url = Column(String(2000), nullable=True)  # URL if source_type is "url"
    chunk_count = Column(String(50), default="0")
    processed = Column(Boolean, default=False)
    content_summary = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    category = Column(String(50), default="general")


class StateManager:
    """
    Manages workflow state persistence to PostgreSQL.

    Enables the "human breakpoint" by:
    1. Saving state when workflow suspends
    2. Loading state when workflow resumes
    3. Tracking project progress
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the state manager.

        Args:
            database_url: Database connection URL
        """
        self.database_url = database_url or settings.DATABASE_URL

        # Create engine
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Create tables
        Base.metadata.create_all(self.engine)

        # Run migrations for existing databases
        self._run_migrations()

        logger.info("StateManager initialized")

    def _run_migrations(self) -> None:
        """Run database migrations for backward compatibility."""
        inspector = inspect(self.engine)

        # Check if documents table exists
        if "documents" in inspector.get_table_names():
            columns = [col["name"] for col in inspector.get_columns("documents")]

            # Add category column if missing
            if "category" not in columns:
                logger.info("Running migration: Adding 'category' column to documents table")
                with self.engine.connect() as conn:
                    conn.execute(
                        text("ALTER TABLE documents ADD COLUMN category VARCHAR(50) DEFAULT 'general'")
                    )
                    conn.execute(
                        text("UPDATE documents SET category = 'general' WHERE category IS NULL")
                    )
                    conn.commit()
                logger.info("Migration complete: 'category' column added")

    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()

    # =========================================================================
    # Project Management
    # =========================================================================

    def create_project(
        self,
        client_name: str,
        project_name: str,
        description: Optional[str] = None,
        target_departments: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new project.

        Args:
            client_name: Client organization name
            project_name: Project name
            description: Project description
            target_departments: List of target departments

        Returns:
            Created project data
        """
        project_id = str(uuid.uuid4())
        thread_id = str(uuid.uuid4())

        with self.get_session() as session:
            project = ProjectRecord(
                id=project_id,
                client_name=client_name,
                project_name=project_name,
                description=description,
                target_departments=target_departments or [],
                vector_namespace=f"client_{project_id}",
            )
            session.add(project)
            session.commit()

            return {
                "id": project.id,
                "client_name": project.client_name,
                "project_name": project.project_name,
                "description": project.description,
                "target_departments": project.target_departments,
                "status": project.status,
                "vector_namespace": project.vector_namespace,
                "thread_id": thread_id,
                "created_at": project.created_at.isoformat(),
            }

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get project by ID.

        Args:
            project_id: Project ID

        Returns:
            Project data or None
        """
        with self.get_session() as session:
            project = session.query(ProjectRecord).filter_by(id=project_id).first()
            if not project:
                return None

            return {
                "id": project.id,
                "client_name": project.client_name,
                "project_name": project.project_name,
                "description": project.description,
                "target_departments": project.target_departments,
                "status": project.status,
                "vector_namespace": project.vector_namespace,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat(),
            }

    def list_projects(self) -> List[Dict[str, Any]]:
        """
        List all projects.

        Returns:
            List of projects
        """
        with self.get_session() as session:
            projects = session.query(ProjectRecord).order_by(
                ProjectRecord.created_at.desc()
            ).all()

            return [
                {
                    "id": p.id,
                    "client_name": p.client_name,
                    "project_name": p.project_name,
                    "status": p.status,
                    "created_at": p.created_at.isoformat(),
                }
                for p in projects
            ]

    def update_project_status(self, project_id: str, status: str) -> None:
        """
        Update project status.

        Args:
            project_id: Project ID
            status: New status
        """
        with self.get_session() as session:
            project = session.query(ProjectRecord).filter_by(id=project_id).first()
            if project:
                project.status = status
                project.updated_at = datetime.utcnow()
                session.commit()

    # =========================================================================
    # State Management
    # =========================================================================

    def save_state(
        self,
        project_id: str,
        thread_id: str,
        state: Dict[str, Any],
    ) -> None:
        """
        Save workflow state.

        Args:
            project_id: Project ID
            thread_id: Thread ID
            state: State data
        """
        # Serialize state data to ensure datetime objects are JSON-compatible
        serialized_state = serialize_state_data(state)

        with self.get_session() as session:
            existing = session.query(ProjectState).filter_by(
                project_id=project_id
            ).first()

            if existing:
                existing.state_data = serialized_state
                existing.current_node = state.get("current_node", "unknown")
                existing.is_suspended = state.get("is_suspended", False)
                existing.suspension_reason = state.get("suspension_reason")
                existing.updated_at = datetime.utcnow()
            else:
                project_state = ProjectState(
                    project_id=project_id,
                    thread_id=thread_id,
                    state_data=serialized_state,
                    current_node=state.get("current_node", "start"),
                    is_suspended=state.get("is_suspended", False),
                    suspension_reason=state.get("suspension_reason"),
                )
                session.add(project_state)

            session.commit()
            logger.info(f"State saved for project {project_id}")

    def load_state(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Load workflow state.

        Args:
            project_id: Project ID

        Returns:
            State data or None
        """
        with self.get_session() as session:
            project_state = session.query(ProjectState).filter_by(
                project_id=project_id
            ).first()

            if not project_state:
                return None

            return project_state.state_data

    def get_thread_id(self, project_id: str) -> Optional[str]:
        """
        Get thread ID for a project.

        Args:
            project_id: Project ID

        Returns:
            Thread ID or None
        """
        with self.get_session() as session:
            project_state = session.query(ProjectState).filter_by(
                project_id=project_id
            ).first()

            return project_state.thread_id if project_state else None

    def get_suspended_projects(self) -> List[Dict[str, Any]]:
        """
        Get all suspended projects awaiting input.

        Returns:
            List of suspended projects
        """
        with self.get_session() as session:
            suspended = session.query(ProjectState).filter_by(
                is_suspended=True
            ).all()

            results = []
            for ps in suspended:
                project = session.query(ProjectRecord).filter_by(
                    id=ps.project_id
                ).first()

                results.append({
                    "project_id": ps.project_id,
                    "thread_id": ps.thread_id,
                    "project_name": project.project_name if project else "Unknown",
                    "client_name": project.client_name if project else "Unknown",
                    "current_node": ps.current_node,
                    "suspension_reason": ps.suspension_reason,
                    "suspended_at": ps.updated_at.isoformat(),
                })

            return results

    # =========================================================================
    # Document Management
    # =========================================================================

    def add_document(
        self,
        project_id: str,
        filename: str,
        file_type: str,
        file_size: int,
        file_path: str,
        category: str = "general",
        source_type: str = "file",
        source_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Add a document record.

        Args:
            project_id: Project ID
            filename: File name
            file_type: File type (pdf, docx, url, etc.)
            file_size: File size in bytes (0 for URLs)
            file_path: Path to stored file (empty for URLs)
            category: Document category (general, interview_results, etc.)
            source_type: "file" or "url"
            source_url: URL if source_type is "url"

        Returns:
            Document record
        """
        with self.get_session() as session:
            doc = DocumentRecord(
                project_id=project_id,
                filename=filename,
                file_type=file_type,
                file_size=str(file_size),
                file_path=file_path,
                category=category,
                source_type=source_type,
                source_url=source_url,
            )
            session.add(doc)
            session.commit()

            return {
                "id": doc.id,
                "project_id": doc.project_id,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "file_size": int(doc.file_size),
                "file_path": doc.file_path,
                "source_type": doc.source_type,
                "source_url": doc.source_url,
                "processed": doc.processed,
                "chunk_count": int(doc.chunk_count),
                "uploaded_at": doc.uploaded_at.isoformat(),
                "category": doc.category,
            }

    def get_project_documents(
        self, project_id: str, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all documents for a project, optionally filtered by category.

        Args:
            project_id: Project ID
            category: Optional category filter (e.g., 'general', 'interview_results')

        Returns:
            List of documents
        """
        with self.get_session() as session:
            query = session.query(DocumentRecord).filter_by(project_id=project_id)

            if category is not None:
                query = query.filter_by(category=category)

            docs = query.all()

            return [
                {
                    "id": d.id,
                    "project_id": d.project_id,
                    "filename": d.filename,
                    "file_type": d.file_type,
                    "file_size": int(d.file_size),
                    "source_type": d.source_type,
                    "source_url": d.source_url,
                    "processed": d.processed,
                    "chunk_count": int(d.chunk_count),
                    "uploaded_at": d.uploaded_at.isoformat(),
                    "category": d.category,
                }
                for d in docs
            ]

    def update_document_processed(
        self,
        document_id: str,
        processed: bool,
        chunk_count: int = 0,
        summary: Optional[str] = None,
    ) -> None:
        """
        Update document processing status.

        Args:
            document_id: Document ID
            processed: Whether document was processed
            chunk_count: Number of chunks created
            summary: Content summary
        """
        with self.get_session() as session:
            doc = session.query(DocumentRecord).filter_by(id=document_id).first()
            if doc:
                doc.processed = processed
                doc.chunk_count = str(chunk_count)
                doc.content_summary = summary
                session.commit()
