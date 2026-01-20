"""Initial schema - Creates all APIC tables

Revision ID: 001_initial
Revises: None
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all APIC tables."""
    # Create projects table
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("client_name", sa.String(255), nullable=False),
        sa.Column("project_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("target_departments", sa.JSON, default=list),
        sa.Column("status", sa.String(50), default="created"),
        sa.Column("vector_namespace", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_projects_id", "projects", ["id"])
    op.create_index("ix_projects_status", "projects", ["status"])

    # Create project_states table
    op.create_table(
        "project_states",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), unique=True, nullable=False, index=True),
        sa.Column("thread_id", sa.String(36), unique=True, nullable=False, index=True),
        sa.Column("state_data", sa.JSON, nullable=False),
        sa.Column("current_node", sa.String(50), nullable=False, default="start"),
        sa.Column("is_suspended", sa.Boolean, default=False),
        sa.Column("suspension_reason", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_project_states_project_id", "project_states", ["project_id"])
    op.create_index("ix_project_states_thread_id", "project_states", ["thread_id"])
    op.create_index("ix_project_states_is_suspended", "project_states", ["is_suspended"])

    # Create documents table
    op.create_table(
        "documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), nullable=False, index=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(50), nullable=False),
        sa.Column("file_size", sa.String(50), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("chunk_count", sa.String(50), default="0"),
        sa.Column("processed", sa.Boolean, default=False),
        sa.Column("content_summary", sa.Text, nullable=True),
        sa.Column("uploaded_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_documents_project_id", "documents", ["project_id"])
    op.create_index("ix_documents_processed", "documents", ["processed"])

    # Create foreign key constraints
    op.create_foreign_key(
        "fk_project_states_project_id",
        "project_states",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_documents_project_id",
        "documents",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Drop all APIC tables."""
    # Drop foreign keys first
    op.drop_constraint("fk_documents_project_id", "documents", type_="foreignkey")
    op.drop_constraint("fk_project_states_project_id", "project_states", type_="foreignkey")

    # Drop indexes
    op.drop_index("ix_documents_processed", table_name="documents")
    op.drop_index("ix_documents_project_id", table_name="documents")
    op.drop_index("ix_project_states_is_suspended", table_name="project_states")
    op.drop_index("ix_project_states_thread_id", table_name="project_states")
    op.drop_index("ix_project_states_project_id", table_name="project_states")
    op.drop_index("ix_projects_status", table_name="projects")
    op.drop_index("ix_projects_id", table_name="projects")

    # Drop tables
    op.drop_table("documents")
    op.drop_table("project_states")
    op.drop_table("projects")
