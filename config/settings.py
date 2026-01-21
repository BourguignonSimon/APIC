"""
APIC Configuration Settings

This module provides centralized configuration management for the APIC application.
All settings are loaded from environment variables or a .env file.

Pydantic's BaseSettings is used for:
- Automatic environment variable parsing
- Type validation and coercion
- Default value handling

Usage:
    from config.settings import settings
    api_key = settings.OPENAI_API_KEY
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All fields can be overridden by setting the corresponding
    environment variable (case-sensitive). For example:
        export OPENAI_API_KEY="your-key-here"

    Or by adding them to a .env file in the project root.
    """

    # =========================================================================
    # Application Metadata
    # =========================================================================
    # Basic application identification and runtime configuration
    APP_NAME: str = "APIC"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)  # Set to True for verbose logging
    ENVIRONMENT: str = Field(default="development")  # development, staging, production

    # =========================================================================
    # API Keys for LLM Providers
    # =========================================================================
    # At least one API key should be configured to use the application.
    # Each provider requires its own API key obtained from their platform.

    # OpenAI API key - Get from https://platform.openai.com/api-keys
    OPENAI_API_KEY: Optional[str] = Field(default=None)

    # Anthropic API key - Get from https://console.anthropic.com/
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None)

    # Google AI API key - Get from https://makersuite.google.com/app/apikey
    # Required for using Gemini models (e.g., gemini-1.5-flash, gemini-1.5-pro)
    GOOGLE_API_KEY: Optional[str] = Field(default=None)

    # =========================================================================
    # LLM (Large Language Model) Configuration
    # =========================================================================
    # Settings that control which AI model is used and how it behaves

    # Default provider: "openai", "anthropic", or "google"
    DEFAULT_LLM_PROVIDER: str = Field(default="openai")

    # Model identifiers for each provider
    OPENAI_MODEL: str = Field(default="gpt-4o")
    ANTHROPIC_MODEL: str = Field(default="claude-3-5-sonnet-20241022")
    GOOGLE_MODEL: str = Field(default="gemini-1.5-flash")  # Gemini model to use

    # Generation parameters affecting response style
    LLM_TEMPERATURE: float = Field(default=0.7)  # 0.0 = deterministic, 1.0 = creative
    LLM_MAX_TOKENS: int = Field(default=4096)  # Maximum response length

    # =========================================================================
    # Vector Database (Pinecone)
    # =========================================================================
    # Pinecone is used for semantic search over document embeddings.
    # Get your API key from https://www.pinecone.io/

    PINECONE_API_KEY: Optional[str] = Field(default=None)
    PINECONE_ENVIRONMENT: str = Field(default="us-east-1")  # Your Pinecone region
    PINECONE_INDEX_NAME: str = Field(default="apic-knowledge")  # Index for storing vectors

    # =========================================================================
    # PostgreSQL Database
    # =========================================================================
    # Primary database for storing application data (users, documents, etc.)
    # Format: postgresql://username:password@host:port/database_name

    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/apic"
    )
    DATABASE_POOL_SIZE: int = Field(default=5)  # Number of connections in the pool

    # =========================================================================
    # File Upload Configuration
    # =========================================================================
    # Controls where uploaded files are stored and size/type restrictions

    UPLOAD_DIR: str = Field(default="./uploads")  # Directory for uploaded files
    MAX_FILE_SIZE_MB: int = Field(default=50)  # Maximum file size in megabytes
    ALLOWED_EXTENSIONS: list = Field(
        default=["pdf", "docx", "doc", "txt", "pptx", "xlsx"]
    )  # Permitted file types

    # =========================================================================
    # Report Generation
    # =========================================================================
    # Output directory for generated reports and analysis documents

    REPORTS_DIR: str = Field(default="./reports")

    # =========================================================================
    # FastAPI Server Configuration
    # =========================================================================
    # Settings for the backend API server

    API_HOST: str = Field(default="0.0.0.0")  # Bind address (0.0.0.0 = all interfaces)
    API_PORT: int = Field(default=8000)  # Port for the API server
    API_WORKERS: int = Field(default=4)  # Number of uvicorn worker processes

    # =========================================================================
    # Streamlit Frontend Configuration
    # =========================================================================
    # Settings for the Streamlit-based web interface

    STREAMLIT_PORT: int = Field(default=8501)  # Port for the Streamlit frontend

    # =========================================================================
    # Pydantic Model Configuration
    # =========================================================================
    class Config:
        env_file = ".env"  # Load variables from .env file if present
        env_file_encoding = "utf-8"
        case_sensitive = True  # Environment variables are case-sensitive
        extra = "ignore"  # Ignore extra env vars not defined in the model


# =============================================================================
# Global Settings Instance
# =============================================================================
# Single instance created at module import time. All modules should import
# and use this instance rather than creating new Settings() objects.

settings = Settings()


def get_settings() -> Settings:
    """
    Get the global settings instance.

    Returns:
        Settings: The singleton settings object with all configuration values.

    Example:
        settings = get_settings()
        print(settings.API_PORT)
    """
    return settings
