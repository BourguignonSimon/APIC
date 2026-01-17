"""
APIC API Module
FastAPI backend for the APIC system.
"""

from .main import app, create_app
from .routes import projects, documents, workflow

__all__ = [
    "app",
    "create_app",
    "projects",
    "documents",
    "workflow",
]
