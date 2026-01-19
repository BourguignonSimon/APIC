# APIC - Developer Guide

**Document Version:** 1.0
**Last Updated:** January 2026
**Audience:** Software Engineers, DevOps Engineers, Contributors

---

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Project Structure](#project-structure)
3. [Core Concepts](#core-concepts)
4. [Agent Development](#agent-development)
5. [API Development](#api-development)
6. [Frontend Development](#frontend-development)
7. [Database Management](#database-management)
8. [Testing](#testing)
9. [Debugging](#debugging)
10. [Contributing](#contributing)
11. [Deployment](#deployment)
12. [Performance Optimization](#performance-optimization)
13. [Code Style & Standards](#code-style--standards)

---

## Development Environment Setup

### Prerequisites

Ensure you have the following installed:

| Tool | Version | Purpose | Installation |
|------|---------|---------|--------------|
| **Python** | 3.11+ | Runtime environment | `brew install python@3.11` |
| **PostgreSQL** | 15+ | Relational database | `brew install postgresql@15` |
| **Git** | 2.40+ | Version control | `brew install git` |
| **Docker** | 24+ | Containerization (optional) | [Docker Desktop](https://www.docker.com/products/docker-desktop) |
| **VS Code** | Latest | IDE (recommended) | [Download](https://code.visualstudio.com/) |

### Initial Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/your-org/apic.git
cd apic
```

#### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Verify activation
which python  # Should show path to venv/bin/python
```

#### 3. Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt  # If exists, else install manually:
pip install pytest black mypy ruff pre-commit

# Verify installation
pip list | grep -E "fastapi|langchain|pydantic"
```

#### 4. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

**Required Environment Variables:**

```bash
# .env file
APP_NAME=APIC
DEBUG=True
ENVIRONMENT=development

# LLM Provider (choose at least one)
OPENAI_API_KEY=sk-your-openai-key-here
# ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
# GOOGLE_API_KEY=your-google-api-key-here

# Default LLM Provider
DEFAULT_LLM_PROVIDER=openai  # "openai", "anthropic", or "google"

# Vector Database (Pinecone)
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=apic-knowledge

# PostgreSQL Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/apic

# File Storage
UPLOAD_DIR=./uploads
REPORTS_DIR=./reports
```

#### 5. Initialize Database

```bash
# Start PostgreSQL
brew services start postgresql@15  # macOS
# or: sudo systemctl start postgresql  # Linux

# Create database
createdb apic

# Run migrations (if using Alembic)
# alembic upgrade head

# Or, tables will be created automatically on first run
python main.py api  # Start once to initialize tables
```

#### 6. Setup Pinecone

```bash
# Install Pinecone CLI (optional)
pip install pinecone-client

# Create index (one-time setup)
python -c "
from pinecone import Pinecone
pc = Pinecone(api_key='your-api-key')
pc.create_index(
    name='apic-knowledge',
    dimension=1536,  # OpenAI embedding dimension
    metric='cosine',
    spec={'serverless': {'cloud': 'aws', 'region': 'us-east-1'}}
)
"
```

#### 7. Verify Installation

```bash
# Run tests
pytest tests/ -v

# Start API server
python main.py api

# In another terminal, start frontend
python main.py frontend

# Check API health
curl http://localhost:8000/health
# Expected: {"status": "healthy", "version": "1.0.0"}

# Access frontend
open http://localhost:8501
```

### IDE Setup (VS Code)

#### Recommended Extensions

Install these VS Code extensions:

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "charliermarsh.ruff",
    "ms-toolsai.jupyter",
    "redhat.vscode-yaml",
    "eamodio.gitlens"
  ]
}
```

#### VS Code Settings

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "100"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.tabSize": 4
  }
}
```

### Troubleshooting Setup

#### Issue: `ModuleNotFoundError: No module named 'X'`

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt

# Verify specific package
pip show <package-name>
```

#### Issue: `psycopg2` installation fails

**Solution:**
```bash
# Install PostgreSQL development headers
brew install postgresql  # macOS
# or: sudo apt-get install libpq-dev  # Ubuntu/Debian

# Then reinstall
pip install psycopg2-binary
```

#### Issue: "Cannot connect to PostgreSQL"

**Solution:**
```bash
# Check if PostgreSQL is running
pg_isready

# Start PostgreSQL
brew services start postgresql@15  # macOS
# or: sudo systemctl start postgresql  # Linux

# Verify connection
psql -U postgres -c "SELECT version();"
```

---

## Project Structure

### Directory Layout

```
apic/
├── config/                     # Configuration management
│   ├── __init__.py
│   └── settings.py             # Pydantic settings (env vars)
│
├── src/                        # Source code
│   ├── __init__.py
│   │
│   ├── agents/                 # Consultant Graph nodes
│   │   ├── __init__.py
│   │   ├── base.py             # BaseAgent abstract class
│   │   ├── ingestion.py        # Node 1: Document ingestion
│   │   ├── hypothesis.py       # Node 2: Hypothesis generation
│   │   ├── interview.py        # Node 3: Interview script creation
│   │   ├── gap_analyst.py      # Node 4: Gap analysis
│   │   ├── solution.py         # Node 5: Solution recommendations
│   │   ├── reporting.py        # Node 6: Report generation
│   │   └── google_adk.py       # Google ADK integration
│   │
│   ├── api/                    # FastAPI backend
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI app initialization
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── projects.py     # Project CRUD endpoints
│   │       ├── documents.py    # Document upload endpoints
│   │       └── workflow.py     # Workflow control endpoints
│   │
│   ├── models/                 # Data models
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic models for all entities
│   │
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── workflow.py         # LangGraph workflow orchestration
│   │   └── state_manager.py   # State persistence & retrieval
│   │
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       ├── helpers.py          # Helper functions
│       └── logging_config.py   # Logging setup
│
├── frontend/                   # Streamlit UI
│   └── app.py                  # Main Streamlit application
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── test_agents.py          # Agent unit tests
│   ├── test_api.py             # API integration tests
│   ├── test_models.py          # Model validation tests
│   ├── test_workflow.py        # Workflow tests
│   └── test_google_adk.py      # Google ADK tests
│
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md         # Architecture documentation
│   ├── USER_GUIDE.md           # User guide
│   └── DEVELOPER_GUIDE.md      # This file
│
├── uploads/                    # Uploaded documents (gitignored)
├── reports/                    # Generated reports (gitignored)
│
├── .env                        # Environment variables (gitignored)
├── .env.example                # Example environment variables
├── .gitignore                  # Git ignore rules
├── docker-compose.yml          # Docker Compose configuration
├── Dockerfile                  # Docker image definition
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
└── README.md                   # Project overview
```

### Key Files Explained

#### `main.py` - Application Entry Point

```python
"""
Main entry point for APIC application.
Provides CLI for running API server or frontend.
"""

import sys
from src.api.main import start_api
from frontend.app import start_frontend

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py [api|frontend]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "api":
        start_api()
    elif command == "frontend":
        start_frontend()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

#### `config/settings.py` - Configuration Management

Uses Pydantic Settings for type-safe environment variable loading.

```python
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # All settings loaded from .env file
    OPENAI_API_KEY: str
    DATABASE_URL: str
    # ... etc

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

#### `src/models/schemas.py` - Data Models

All data structures defined using Pydantic for validation and serialization.

Key models:
- `Project`: Project metadata
- `Document`: Uploaded document metadata
- `Hypothesis`: Generated hypothesis
- `InterviewScript`: Interview questions
- `GapAnalysisItem`: Identified gap
- `AnalysisResult`: Solution recommendation
- `Report`: Final report
- `GraphState`: LangGraph workflow state

---

## Core Concepts

### The Consultant Graph (LangGraph)

APIC uses LangGraph to orchestrate a stateful workflow with a human breakpoint.

#### Graph Definition

```python
# src/services/workflow.py
from langgraph.graph import StateGraph
from src.models.schemas import GraphState
from src.agents import (
    ingestion_node,
    hypothesis_node,
    interview_node,
    gap_analyst_node,
    solution_node,
    reporting_node
)

# Define the state graph
graph = StateGraph(GraphState)

# Add nodes
graph.add_node("ingestion", ingestion_node)
graph.add_node("hypothesis", hypothesis_node)
graph.add_node("interview", interview_node)
graph.add_node("gap_analyst", gap_analyst_node)
graph.add_node("solution", solution_node)
graph.add_node("reporting", reporting_node)

# Define edges
graph.add_edge("ingestion", "hypothesis")
graph.add_edge("hypothesis", "interview")
# interview node leads to conditional edge (breakpoint)
graph.add_conditional_edges(
    "interview",
    should_continue,  # Function that checks if transcript is available
    {
        "continue": "gap_analyst",  # Transcript available
        "wait": "end"  # Pause for transcript
    }
)
graph.add_edge("gap_analyst", "solution")
graph.add_edge("solution", "reporting")
graph.add_edge("reporting", "end")

# Set entry point
graph.set_entry_point("ingestion")

# Compile graph
app = graph.compile()
```

#### State Management

State flows through the graph and is updated by each node.

```python
def ingestion_node(state: GraphState) -> GraphState:
    """
    Node 1: Ingest documents and create vector embeddings.
    """
    # Process documents
    for doc in state.documents:
        chunks = parse_document(doc)
        embeddings = create_embeddings(chunks)
        store_in_pinecone(embeddings, state.project.vector_namespace)

    # Update state
    state.ingestion_complete = True
    state.current_node = "ingestion"

    return state
```

### RAG (Retrieval-Augmented Generation)

APIC uses RAG to provide LLMs with relevant context from uploaded documents.

#### RAG Flow

```python
from pinecone import Pinecone
from openai import OpenAI

def rag_query(question: str, namespace: str) -> str:
    """
    Perform RAG query: retrieve relevant chunks, then generate answer.
    """
    # Step 1: Create query embedding
    openai_client = OpenAI()
    query_embedding = openai_client.embeddings.create(
        input=question,
        model="text-embedding-3-small"
    ).data[0].embedding

    # Step 2: Search vector database
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    index = pc.Index(settings.PINECONE_INDEX_NAME)

    results = index.query(
        vector=query_embedding,
        top_k=5,
        namespace=namespace,
        include_metadata=True
    )

    # Step 3: Assemble context
    context = "\n\n".join([
        match.metadata['text'] for match in results.matches
    ])

    # Step 4: Generate answer with LLM
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a process analyst."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
        ]
    )

    return response.choices[0].message.content
```

### Multi-Provider LLM Support

APIC abstracts LLM calls to support multiple providers.

#### LLM Router

```python
# src/utils/llm_router.py
from abc import ABC, abstractmethod
from typing import List, Dict
from openai import OpenAI
from anthropic import Anthropic

class BaseLLM(ABC):
    """Base class for LLM providers."""

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]]) -> str:
        pass

class OpenAILLM(BaseLLM):
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def chat(self, messages: List[Dict[str, str]]) -> str:
        response = self.client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            temperature=settings.LLM_TEMPERATURE
        )
        return response.choices[0].message.content

class AnthropicLLM(BaseLLM):
    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def chat(self, messages: List[Dict[str, str]]) -> str:
        response = self.client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            messages=messages
        )
        return response.content[0].text

def get_llm(provider: str = None) -> BaseLLM:
    """Factory function to get LLM instance."""
    provider = provider or settings.DEFAULT_LLM_PROVIDER

    if provider == "openai":
        return OpenAILLM()
    elif provider == "anthropic":
        return AnthropicLLM()
    else:
        raise ValueError(f"Unknown provider: {provider}")
```

---

## Agent Development

### Creating a New Agent

Follow this template to create a new agent node.

#### Step 1: Define Agent Class

Create `src/agents/your_agent.py`:

```python
"""
Node X: Your Agent Name
Brief description of what this agent does.
"""

from typing import List
from src.agents.base import BaseAgent
from src.models.schemas import GraphState, YourOutputModel
from src.utils.llm_router import get_llm
import structlog

logger = structlog.get_logger()

class YourAgent(BaseAgent[GraphState, List[YourOutputModel]]):
    """
    Your agent description.

    Strategy:
    1. Validate inputs
    2. Perform core logic
    3. Update state
    4. Return outputs
    """

    def __init__(self, llm_provider: str = "openai"):
        super().__init__(llm_provider)
        self.llm = get_llm(llm_provider)

    def execute(self, state: GraphState) -> List[YourOutputModel]:
        """Main execution logic."""

        # Validate inputs
        if not self.validate_inputs(state):
            raise ValueError("Required inputs not available")

        logger.info("your_agent_started", project_id=state.project_id)

        # Core logic here
        results = self._perform_analysis(state)

        # Update state
        state.your_field = results
        state.your_completion_flag = True
        state.current_node = "your_agent"

        logger.info(
            "your_agent_completed",
            project_id=state.project_id,
            results_count=len(results)
        )

        return results

    def validate_inputs(self, state: GraphState) -> bool:
        """Validate that required inputs are present."""
        # Check prerequisites
        return state.previous_node_complete and len(state.required_data) > 0

    def _perform_analysis(self, state: GraphState) -> List[YourOutputModel]:
        """Private method for core analysis logic."""
        # Implementation details
        pass
```

#### Step 2: Create Node Function

```python
def your_agent_node(state: GraphState) -> GraphState:
    """
    LangGraph node function wrapper.
    """
    agent = YourAgent(llm_provider=state.llm_provider)
    results = agent.execute(state)
    return state
```

#### Step 3: Register in Graph

Update `src/services/workflow.py`:

```python
from src.agents.your_agent import your_agent_node

# In graph definition
graph.add_node("your_agent", your_agent_node)
graph.add_edge("previous_node", "your_agent")
graph.add_edge("your_agent", "next_node")
```

#### Step 4: Add Tests

Create `tests/test_your_agent.py`:

```python
import pytest
from src.agents.your_agent import YourAgent
from src.models.schemas import GraphState, Project

def test_your_agent_execution():
    """Test that agent executes successfully."""
    # Arrange
    state = GraphState(
        project_id="test-123",
        project=Project(client_name="Test", project_name="Test"),
        previous_node_complete=True,
        required_data=["some", "data"]
    )
    agent = YourAgent(llm_provider="openai")

    # Act
    results = agent.execute(state)

    # Assert
    assert len(results) > 0
    assert state.your_completion_flag is True

def test_your_agent_validation_failure():
    """Test that agent raises error when inputs are invalid."""
    # Arrange
    state = GraphState(project_id="test-123", required_data=[])
    agent = YourAgent()

    # Act & Assert
    with pytest.raises(ValueError):
        agent.execute(state)
```

### Agent Best Practices

#### 1. Use Structured Outputs

Always use Pydantic models for outputs to ensure type safety.

```python
# Good
class HypothesisOutput(BaseModel):
    process_area: str
    description: str
    confidence: float

# Bad
def generate_hypothesis() -> dict:
    return {"area": "something", "desc": "..."}  # Untyped
```

#### 2. Log Extensively

Use structured logging for debugging and monitoring.

```python
logger.info(
    "hypothesis_generated",
    project_id=state.project_id,
    hypothesis_count=len(hypotheses),
    avg_confidence=sum(h.confidence for h in hypotheses) / len(hypotheses)
)
```

#### 3. Handle Errors Gracefully

```python
def execute(self, state: GraphState):
    try:
        results = self._perform_analysis(state)
    except Exception as e:
        logger.error("agent_error", error=str(e), project_id=state.project_id)
        state.errors.append(f"YourAgent failed: {str(e)}")
        # Optionally return partial results or raise
        raise

    return results
```

#### 4. Make Agents Idempotent

Agents should be safe to re-run without side effects.

```python
def execute(self, state: GraphState):
    # Check if already completed
    if state.your_completion_flag:
        logger.info("agent_already_completed", project_id=state.project_id)
        return state.your_field  # Return cached results

    # Proceed with execution
    # ...
```

---

## API Development

### FastAPI Application Structure

APIC uses FastAPI for the REST API.

#### Main Application (`src/api/main.py`)

```python
"""
FastAPI application initialization.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import projects, documents, workflow
from config.settings import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Agentic Process Improvement Consultant API"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(workflow.router, prefix="/api/v1/workflow", tags=["workflow"])

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.APP_VERSION}

def start_api():
    """Start the API server."""
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
```

### Creating API Endpoints

#### Example: Project Endpoints (`src/api/routes/projects.py`)

```python
"""
Project management endpoints.
"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends
from src.models.schemas import Project, ProjectCreate
from src.services.project_service import ProjectService

router = APIRouter()

@router.post("/", response_model=Project, status_code=201)
def create_project(project: ProjectCreate):
    """
    Create a new consulting project.

    Args:
        project: Project creation data

    Returns:
        Created project with generated ID

    Raises:
        HTTPException: If creation fails
    """
    try:
        service = ProjectService()
        created_project = service.create(project)
        return created_project
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[Project])
def list_projects(skip: int = 0, limit: int = 100):
    """
    List all projects with pagination.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of projects
    """
    service = ProjectService()
    return service.list_all(skip=skip, limit=limit)

@router.get("/{project_id}", response_model=Project)
def get_project(project_id: str):
    """
    Get a specific project by ID.

    Args:
        project_id: Project UUID

    Returns:
        Project details

    Raises:
        HTTPException: If project not found
    """
    service = ProjectService()
    project = service.get_by_id(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project

@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str):
    """
    Delete a project.

    Args:
        project_id: Project UUID

    Raises:
        HTTPException: If project not found
    """
    service = ProjectService()
    deleted = service.delete(project_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
```

### File Upload Handling

```python
# src/api/routes/documents.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import shutil
from pathlib import Path
from config.settings import settings

router = APIRouter()

@router.post("/projects/{project_id}/documents")
async def upload_documents(
    project_id: str,
    files: List[UploadFile] = File(...)
):
    """
    Upload multiple documents for a project.

    Args:
        project_id: Project UUID
        files: List of files to upload

    Returns:
        List of uploaded document metadata
    """
    uploaded_docs = []

    for file in files:
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower().lstrip('.')
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type .{file_ext} not allowed"
            )

        # Validate file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning

        if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} exceeds size limit"
            )

        # Save file
        upload_dir = Path(settings.UPLOAD_DIR) / project_id
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / file.filename

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Create document record
        doc = Document(
            project_id=project_id,
            filename=file.filename,
            file_type=file_ext,
            file_size=file_size
        )

        # Save to database
        # db.save_document(doc)

        uploaded_docs.append(doc)

    return uploaded_docs
```

### API Testing

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_create_project():
    """Test project creation."""
    project_data = {
        "client_name": "Test Corp",
        "project_name": "Test Project",
        "target_departments": ["Finance", "HR"]
    }

    response = client.post("/api/v1/projects", json=project_data)

    assert response.status_code == 201
    data = response.json()
    assert data["client_name"] == "Test Corp"
    assert "id" in data

def test_upload_document():
    """Test document upload."""
    # Create test file
    files = {
        "files": ("test.pdf", b"PDF content", "application/pdf")
    }

    response = client.post(
        "/api/v1/documents/projects/test-123/documents",
        files=files
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
```

---

## Frontend Development

### Streamlit Application

The frontend is built with Streamlit for rapid development.

#### Main Application (`frontend/app.py`)

```python
"""
Streamlit frontend for APIC.
"""

import streamlit as st
import requests
from pathlib import Path

API_BASE_URL = "http://localhost:8000/api/v1"

def main():
    st.set_page_config(
        page_title="APIC - Process Improvement Consultant",
        page_icon="🔍",
        layout="wide"
    )

    st.title("🔍 APIC - Agentic Process Improvement Consultant")

    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["Home", "New Project", "Upload Documents", "Start Analysis", "Results"]
    )

    if page == "Home":
        show_home()
    elif page == "New Project":
        show_new_project()
    elif page == "Upload Documents":
        show_upload_documents()
    elif page == "Start Analysis":
        show_start_analysis()
    elif page == "Results":
        show_results()

def show_new_project():
    """Show project creation form."""
    st.header("Create New Project")

    with st.form("new_project_form"):
        client_name = st.text_input("Client Name", placeholder="Acme Corporation")
        project_name = st.text_input("Project Name", placeholder="Q1 2026 Audit")
        description = st.text_area("Description", placeholder="Project goals...")
        departments = st.text_area(
            "Target Departments (one per line)",
            placeholder="Finance\nOperations\nHR"
        )

        submitted = st.form_submit_button("Create Project")

        if submitted:
            # Parse departments
            dept_list = [d.strip() for d in departments.split("\n") if d.strip()]

            # API call
            project_data = {
                "client_name": client_name,
                "project_name": project_name,
                "description": description,
                "target_departments": dept_list
            }

            response = requests.post(f"{API_BASE_URL}/projects", json=project_data)

            if response.status_code == 201:
                st.success("✅ Project created successfully!")
                st.json(response.json())
            else:
                st.error(f"❌ Error: {response.text}")

def show_upload_documents():
    """Show document upload interface."""
    st.header("Upload Documents")

    # Project selection
    projects = requests.get(f"{API_BASE_URL}/projects").json()
    project_options = {p["id"]: f"{p['client_name']} - {p['project_name']}" for p in projects}

    selected_project_id = st.selectbox("Select Project", options=project_options.keys(),
                                       format_func=lambda x: project_options[x])

    # File upload
    uploaded_files = st.file_uploader(
        "Choose files",
        accept_multiple_files=True,
        type=["pdf", "docx", "doc", "txt", "pptx", "xlsx"]
    )

    if st.button("Upload"):
        if not uploaded_files:
            st.warning("Please select files to upload")
        else:
            files = [("files", (f.name, f, f.type)) for f in uploaded_files]

            response = requests.post(
                f"{API_BASE_URL}/documents/projects/{selected_project_id}/documents",
                files=files
            )

            if response.status_code == 200:
                st.success(f"✅ {len(uploaded_files)} files uploaded successfully!")
            else:
                st.error(f"❌ Upload failed: {response.text}")

def start_frontend():
    """Start the Streamlit frontend."""
    import sys
    sys.argv = ["streamlit", "run", "frontend/app.py"]
    from streamlit.web import cli
    cli.main()

if __name__ == "__main__":
    main()
```

### Streamlit Best Practices

#### 1. Use Session State

```python
# Initialize session state
if "project_id" not in st.session_state:
    st.session_state.project_id = None

# Use in callbacks
def create_project_callback():
    st.session_state.project_id = created_project["id"]

st.button("Create", on_click=create_project_callback)
```

#### 2. Cache API Calls

```python
@st.cache_data(ttl=60)  # Cache for 60 seconds
def get_projects():
    """Fetch projects from API (cached)."""
    response = requests.get(f"{API_BASE_URL}/projects")
    return response.json()
```

#### 3. Show Progress

```python
with st.spinner("Uploading documents..."):
    response = requests.post(url, files=files)

if response.status_code == 200:
    st.success("Upload complete!")
```

---

## Database Management

### PostgreSQL Schema

Tables are created via SQLAlchemy or manual SQL.

#### Schema Definition

```sql
-- Create tables
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_name VARCHAR(255) NOT NULL,
    project_name VARCHAR(255) NOT NULL,
    description TEXT,
    target_departments TEXT[],
    status VARCHAR(50) NOT NULL,
    vector_namespace VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT NOT NULL,
    chunk_count INTEGER DEFAULT 0,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    content_summary TEXT
);

CREATE TABLE workflow_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    state_data JSONB NOT NULL,
    checkpoint_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_documents_project_id ON documents(project_id);
CREATE INDEX idx_workflow_states_project_id ON workflow_states(project_id);
CREATE INDEX idx_workflow_states_checkpoint ON workflow_states(checkpoint_id);
```

### Database Connection

```python
# src/utils/database.py
import psycopg2
from psycopg2.extras import RealDictCursor
from config.settings import settings
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = psycopg2.connect(
        settings.DATABASE_URL,
        cursor_factory=RealDictCursor
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# Usage
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
    project = cursor.fetchone()
```

---

## Testing

### Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures
├── test_agents.py           # Agent tests
├── test_api.py              # API tests
├── test_models.py           # Model validation tests
└── test_workflow.py         # Workflow integration tests
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_agents.py

# Run specific test
pytest tests/test_agents.py::test_hypothesis_agent

# Run with verbose output
pytest -v

# Run with print statements
pytest -s
```

### Example Tests

```python
# tests/test_agents.py
import pytest
from src.agents.hypothesis import HypothesisAgent
from src.models.schemas import GraphState, Project

@pytest.fixture
def mock_state():
    """Fixture for test state."""
    return GraphState(
        project_id="test-123",
        project=Project(client_name="Test", project_name="Test"),
        ingestion_complete=True,
        documents=[],
        document_summaries=["Test summary"]
    )

def test_hypothesis_agent(mock_state):
    """Test hypothesis generation."""
    agent = HypothesisAgent(llm_provider="openai")
    hypotheses = agent.execute(mock_state)

    assert len(hypotheses) > 0
    assert all(h.confidence >= 0 and h.confidence <= 1 for h in hypotheses)
```

### Mocking LLM Calls

```python
from unittest.mock import patch, MagicMock

def test_hypothesis_with_mock_llm(mock_state):
    """Test hypothesis generation with mocked LLM."""

    mock_response = MagicMock()
    mock_response.choices[0].message.content = """
    [
        {
            "process_area": "Finance",
            "description": "Manual invoice entry",
            "confidence": 0.85
        }
    ]
    """

    with patch("openai.OpenAI") as mock_openai:
        mock_openai.return_value.chat.completions.create.return_value = mock_response

        agent = HypothesisAgent()
        hypotheses = agent.execute(mock_state)

        assert len(hypotheses) == 1
        assert hypotheses[0].process_area == "Finance"
```

---

## Debugging

### Logging

APIC uses `structlog` for structured logging.

#### Configuration

```python
# src/utils/logging_config.py
import structlog
import logging

def configure_logging():
    """Configure structured logging."""
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO
    )
```

#### Usage

```python
import structlog

logger = structlog.get_logger()

logger.info("event_name", key1="value1", key2="value2")
logger.error("error_occurred", error=str(e), project_id=project_id)
```

### Debugging Tips

#### 1. Enable Debug Mode

```python
# .env
DEBUG=True

# Enables:
# - Auto-reload on code changes
# - Verbose error messages
# - Request/response logging
```

#### 2. Use iPDB for Breakpoints

```bash
pip install ipdb
```

```python
import ipdb

def some_function():
    x = 10
    ipdb.set_trace()  # Debugger stops here
    y = x * 2
```

#### 3. Print State for LangGraph

```python
def debug_node(state: GraphState) -> GraphState:
    """Debug node to inspect state."""
    print("=== STATE DEBUG ===")
    print(f"Project ID: {state.project_id}")
    print(f"Current Node: {state.current_node}")
    print(f"Hypotheses: {len(state.hypotheses)}")
    print(f"Errors: {state.errors}")
    return state

# Add to graph
graph.add_node("debug", debug_node)
```

---

## Contributing

### Contribution Workflow

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make changes** with clear, atomic commits
4. **Write tests** for new functionality
5. **Run tests** and ensure they pass: `pytest`
6. **Run linters**: `black src/ tests/` and `mypy src/`
7. **Commit changes**: `git commit -m "Add feature X"`
8. **Push to branch**: `git push origin feature/your-feature-name`
9. **Create Pull Request** with description of changes

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(agents): add Google ADK integration

- Implement GoogleADKAgent class
- Add multimodal analysis support
- Update workflow to include ADK step

Closes #42
```

```
fix(api): handle file upload errors gracefully

- Add file size validation
- Improve error messages
- Add retry logic for network failures
```

### Code Review Checklist

Before submitting PR, ensure:

- [ ] Code follows project style guide (Black formatting)
- [ ] All tests pass (`pytest`)
- [ ] New features have tests (coverage > 80%)
- [ ] Documentation updated (if API changes)
- [ ] No secrets committed (check with `git diff`)
- [ ] Type hints added for new functions
- [ ] Docstrings added for public methods

---

## Deployment

### Docker Deployment

#### Build Image

```bash
docker build -t apic:latest .
```

#### Run with Docker Compose

```bash
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Production Deployment (AWS Example)

#### Prerequisites

- AWS account with ECS/Fargate access
- Docker registry (ECR)
- RDS PostgreSQL instance
- Environment variables configured in AWS Secrets Manager

#### Steps

1. **Push image to ECR**:
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker tag apic:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/apic:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/apic:latest
```

2. **Deploy to ECS**: Use Terraform or AWS Console to create ECS service

3. **Configure environment variables** via AWS Secrets Manager

4. **Setup load balancer** for API and frontend

---

## Performance Optimization

### Database Optimization

```python
# Use connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10
)
```

### Async Processing

```python
import asyncio

async def process_documents_parallel(documents):
    """Process multiple documents concurrently."""
    tasks = [process_document(doc) for doc in documents]
    results = await asyncio.gather(*tasks)
    return results
```

### Caching

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_embedding(text: str):
    """Cache embeddings for frequently used text."""
    return openai.embeddings.create(input=text)
```

---

## Code Style & Standards

### Formatting

Use Black with 100-character line length:

```bash
black src/ tests/ --line-length 100
```

### Type Hints

All functions must have type hints:

```python
def process_document(doc: Document) -> List[str]:
    """Process a document and return chunks."""
    chunks: List[str] = []
    # ...
    return chunks
```

### Docstrings

Use Google-style docstrings:

```python
def create_hypothesis(data: dict, confidence: float) -> Hypothesis:
    """
    Create a hypothesis from analysis data.

    Args:
        data: Dictionary containing hypothesis details
        confidence: Confidence score (0-1)

    Returns:
        Hypothesis object

    Raises:
        ValueError: If confidence is out of range
    """
    if not 0 <= confidence <= 1:
        raise ValueError("Confidence must be between 0 and 1")

    return Hypothesis(**data, confidence=confidence)
```

---

## Appendix

### Useful Commands

```bash
# Start development environment
python main.py api & python main.py frontend

# Run tests with coverage
pytest --cov=src --cov-report=term-missing

# Format code
black src/ tests/

# Type check
mypy src/

# Lint
ruff check src/

# Generate requirements.txt
pip freeze > requirements.txt

# Database migrations (if using Alembic)
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Pinecone Documentation](https://docs.pinecone.io/)

---

**Happy Coding!**

For questions or issues, open a GitHub issue or contact the maintainers.
