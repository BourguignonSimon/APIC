"""
APIC Configuration Settings
Environment-based configuration management.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "APIC"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")

    # API Keys
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None)
    GOOGLE_API_KEY: Optional[str] = Field(default=None)

    # LLM Configuration
    DEFAULT_LLM_PROVIDER: str = Field(default="openai")  # "openai", "anthropic", or "google"
    OPENAI_MODEL: str = Field(default="gpt-4o")
    ANTHROPIC_MODEL: str = Field(default="claude-3-5-sonnet-20241022")
    GOOGLE_MODEL: str = Field(default="gemini-1.5-pro")
    LLM_TEMPERATURE: float = Field(default=0.7)
    LLM_MAX_TOKENS: int = Field(default=4096)

    # Google Vertex AI Configuration (optional)
    VERTEX_AI_PROJECT_ID: Optional[str] = Field(default=None)
    VERTEX_AI_LOCATION: str = Field(default="us-central1")

    # Vector Database (Pinecone)
    PINECONE_API_KEY: Optional[str] = Field(default=None)
    PINECONE_ENVIRONMENT: str = Field(default="us-east-1")
    PINECONE_INDEX_NAME: str = Field(default="apic-knowledge")

    # PostgreSQL Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/apic"
    )
    DATABASE_POOL_SIZE: int = Field(default=5)

    # File Upload
    UPLOAD_DIR: str = Field(default="./uploads")
    MAX_FILE_SIZE_MB: int = Field(default=50)
    ALLOWED_EXTENSIONS: list = Field(
        default=["pdf", "docx", "doc", "txt", "pptx", "xlsx"]
    )

    # Report Generation
    REPORTS_DIR: str = Field(default="./reports")

    # API Configuration
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)
    API_WORKERS: int = Field(default=4)

    # Streamlit Configuration
    STREAMLIT_PORT: int = Field(default=8501)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings
