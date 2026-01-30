"""
FastAPI Main Application
Entry point for the APIC API backend.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager."""
    # Startup
    logger.info("Starting APIC API server...")

    # Create required directories
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.REPORTS_DIR, exist_ok=True)
    os.makedirs(settings.SCRIPTS_DIR, exist_ok=True)

    logger.info(f"Upload directory: {settings.UPLOAD_DIR}")
    logger.info(f"Reports directory: {settings.REPORTS_DIR}")
    logger.info(f"Scripts directory: {settings.SCRIPTS_DIR}")

    yield

    # Shutdown
    logger.info("Shutting down APIC API server...")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="APIC - Agentic Process Improvement Consultant",
        description="""
        A multi-agent system designed to act as a digital management consultant.

        ## Features
        - Document ingestion and analysis
        - Hypothesis generation for inefficiencies
        - Dynamic interview script generation
        - Gap analysis (SOP vs Reality)
        - Solution recommendations with ROI
        - Professional PDF report generation

        ## Workflow
        1. Create a project
        2. Upload documents (SOPs, process docs)
        3. Start analysis (generates interview script)
        4. Conduct interview and submit transcript
        5. Resume analysis for gap analysis and solutions
        6. Download final report
        """,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files for reports
    if os.path.exists(settings.REPORTS_DIR):
        app.mount(
            "/reports",
            StaticFiles(directory=settings.REPORTS_DIR),
            name="reports",
        )

    # Mount static files for interview scripts
    if os.path.exists(settings.SCRIPTS_DIR):
        app.mount(
            "/scripts",
            StaticFiles(directory=settings.SCRIPTS_DIR),
            name="scripts",
        )

    # Include router
    from src.api.routes.routes import router

    app.include_router(router, prefix="/api/v1")

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Check API health status."""
        return {
            "status": "healthy",
            "service": "APIC API",
            "version": settings.APP_VERSION,
        }

    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """API root endpoint."""
        return {
            "message": "Welcome to APIC - Agentic Process Improvement Consultant",
            "docs": "/docs",
            "version": settings.APP_VERSION,
        }

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
