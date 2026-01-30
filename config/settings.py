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
    api_key = settings.GOOGLE_API_KEY  # Gemini is the default provider
"""

from typing import Optional, Dict
from pydantic_settings import BaseSettings
from pydantic import BaseModel, Field


# =============================================================================
# Agent Configuration Schema
# =============================================================================


class ModelConfig(BaseModel):
    """Configuration for LLM model settings (uses global provider)"""

    temperature: Optional[float] = Field(
        None, ge=0.0, le=2.0, description="Temperature for sampling"
    )
    max_tokens: Optional[int] = Field(
        None, gt=0, description="Maximum tokens to generate"
    )


class PromptConfig(BaseModel):
    """Configuration for agent prompts"""

    system: Optional[str] = Field(None, description="System prompt/role definition")
    templates: Optional[Dict[str, str]] = Field(
        default_factory=dict, description="Named prompt templates"
    )


class AgentConfig(BaseModel):
    """Configuration for a single agent"""

    name: str = Field(..., description="Agent name")
    enabled: bool = Field(True, description="Whether the agent is enabled")
    model: Optional[ModelConfig] = Field(
        None, description="Model configuration for this agent"
    )
    prompts: Optional[PromptConfig] = Field(
        None, description="Prompt configuration for this agent"
    )

    class Config:
        extra = "allow"  # Allow additional configuration fields


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
    # GOOGLE_API_KEY is required for the default Gemini provider.
    # Set DEFAULT_LLM_PROVIDER env var to switch to a different provider.

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
    # Gemini is the default provider. Switch globally via DEFAULT_LLM_PROVIDER env var.

    # Default LLM provider - Set via LLM_PROVIDER env var to switch globally
    # Supported: "google" (default), "openai", "anthropic"
    DEFAULT_LLM_PROVIDER: str = Field(default="google")

    # Model identifiers for each provider
    OPENAI_MODEL: str = Field(default="gpt-4o")
    ANTHROPIC_MODEL: str = Field(default="claude-3-5-sonnet-20241022")
    GOOGLE_MODEL: str = Field(default="gemini-1.5-flash")  # Gemini model to use

    # Generation parameters affecting response style
    LLM_TEMPERATURE: float = Field(default=0.7)  # 0.0 = deterministic, 1.0 = creative
    LLM_MAX_TOKENS: int = Field(default=4096)  # Maximum response length

    # =========================================================================
    # Vector Database (ChromaDB)
    # =========================================================================
    # ChromaDB is used for semantic search over document embeddings.
    # Completely free and open-source, no API keys required.

    CHROMA_PERSIST_DIR: str = Field(default="./chroma_db")  # Directory for ChromaDB storage
    CHROMA_COLLECTION_NAME: str = Field(default="apic-knowledge")  # Collection for storing vectors

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
    # Interview Scripts Storage
    # =========================================================================
    # Directory for storing generated interview scripts per project
    # Scripts are stored in: SCRIPTS_DIR/{project_id}/interview_script.{format}

    SCRIPTS_DIR: str = Field(default="./scripts")

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


# =============================================================================
# Default Agent Configurations
# =============================================================================
# These defaults were previously stored in config/agents.yaml
# Override per-agent settings by modifying these values

DEFAULT_AGENT_CONFIGS: Dict[str, dict] = {
    "ingestion": {
        "name": "IngestionAgent",
        "enabled": True,
        "model": {"temperature": 0.3, "max_tokens": 2000},
        "prompts": {
            "system": "You are a document processing expert. Your role is to analyze documents and extract key information.\nFocus on identifying main themes, processes, and potential inefficiencies.\n",
            "templates": {
                "summary": "Analyze the following document and provide a concise summary.\nFocus on:\n- Main topics and themes\n- Key processes described\n- Any mentioned inefficiencies or pain points\n- Important stakeholders or departments\n\nDocument: {content}\n\nProvide a clear, structured summary.\n"
            },
        },
    },
    "hypothesis": {
        "name": "HypothesisGeneratorAgent",
        "enabled": True,
        "model": {"temperature": 0.7, "max_tokens": 3000},
        "prompts": {
            "system": "You are an expert management consultant specializing in process optimization and operational efficiency.\nYour expertise includes identifying inefficiencies in business operations, technology gaps, and workflow bottlenecks.\n",
            "templates": {
                "generate_hypotheses": "Based on the following documents, identify potential inefficiencies and areas for improvement.\n\nDocuments:\n{documents}\n\nGenerate hypotheses about:\n1. Manual processes that could be automated\n2. Communication gaps between teams\n3. Data entry inefficiencies\n4. Approval bottlenecks\n5. Technology gaps or underutilization\n\nReturn a JSON array of hypotheses with fields: category, description, severity, and evidence.\n"
            },
        },
    },
    "interview": {
        "name": "InterviewArchitectAgent",
        "enabled": True,
        "model": {"temperature": 0.7, "max_tokens": 3000},
        "prompts": {
            "system": "You are an expert management consultant who designs effective interview scripts.\nYour interviews uncover process inefficiencies and gather insights from stakeholders.\n",
            "templates": {
                "determine_roles": "Based on these hypotheses, determine which roles should be interviewed:\n\nHypotheses:\n{hypotheses}\n\nReturn a JSON array of roles with their departments and why they should be interviewed.\n",
                "generate_questions": "Create interview questions for the {role} role to investigate:\n\nHypotheses:\n{hypotheses}\n\nGenerate 8-10 open-ended questions that will help validate or refute these hypotheses.\nReturn a JSON array of question objects.\n",
            },
        },
    },
    "gap_analyst": {
        "name": "GapAnalystAgent",
        "enabled": True,
        "model": {"temperature": 0.5, "max_tokens": 4000},
        "prompts": {
            "system": "You are a process analysis expert specializing in identifying gaps between documented procedures and actual practices.\nYou excel at analyzing SOPs, interview transcripts, and identifying discrepancies.\n",
            "templates": {
                "analyze_gaps": "Compare the standard operating procedures with the interview transcript to identify gaps:\n\nSOPs:\n{sops}\n\nInterview Transcript:\n{transcript}\n\nIdentify:\n1. Processes described in SOPs but not followed in practice\n2. Undocumented processes revealed in interviews\n3. Workarounds and shadow processes\n4. Technology gaps\n5. Training or knowledge gaps\n\nReturn a detailed JSON analysis of gaps found.\n"
            },
        },
    },
    "solution": {
        "name": "SolutionArchitectAgent",
        "enabled": True,
        "model": {"temperature": 0.6, "max_tokens": 4000},
        "prompts": {
            "system": "You are a solutions architect specializing in business process automation and optimization.\nYou recommend practical, implementable solutions with clear ROI and implementation paths.\n",
            "templates": {
                "recommend_solutions": "Based on the identified gaps and inefficiencies, recommend solutions:\n\nGaps:\n{gaps}\n\nHypotheses:\n{hypotheses}\n\nFor each major issue, provide:\n1. Recommended solution (technology, process change, training)\n2. Expected benefits and ROI\n3. Implementation complexity (Low/Medium/High)\n4. Timeline estimate\n5. Dependencies and prerequisites\n\nReturn structured JSON recommendations.\n"
            },
        },
    },
    "reporting": {
        "name": "ReportingAgent",
        "enabled": True,
        "model": {"temperature": 0.5, "max_tokens": 8000},
        "prompts": {
            "system": "You are an expert consultant report writer. You create clear, executive-level reports\nthat communicate findings and recommendations effectively to C-suite audiences.\n",
            "templates": {
                "executive_summary": "Create an executive summary of the analysis:\n\nHypotheses: {hypotheses}\nGaps: {gaps}\nSolutions: {solutions}\n\nWrite a compelling 2-3 paragraph executive summary highlighting:\n- Key findings\n- Critical inefficiencies discovered\n- Top recommendations\n- Expected business impact\n",
                "roadmap": "Create an implementation roadmap based on:\n\nSolutions: {solutions}\n\nOrganize recommendations into:\n- Quick wins (0-3 months)\n- Medium-term initiatives (3-6 months)\n- Long-term strategic changes (6-12 months)\n\nFor each phase, list initiatives with brief descriptions and expected impact.\n",
            },
        },
    },
}


class AgentConfigRegistry(BaseModel):
    """Registry of all agent configurations"""

    version: str = Field("1.0", description="Configuration schema version")
    agents: Dict[str, AgentConfig] = Field(
        default_factory=dict, description="Agent configurations by name"
    )

    def get_agent_config(self, agent_name: str) -> Optional[AgentConfig]:
        """Get configuration for a specific agent"""
        return self.agents.get(agent_name)


def get_agent_config() -> AgentConfigRegistry:
    """
    Get the agent configuration registry.

    Returns the default agent configurations defined in this module.

    Returns:
        AgentConfigRegistry: Registry containing all agent configurations
    """
    agents = {}
    for agent_name, config_dict in DEFAULT_AGENT_CONFIGS.items():
        agents[agent_name] = AgentConfig(**config_dict)
    return AgentConfigRegistry(agents=agents)
