# APIC Developer Guide

## Overview

This guide is intended for developers who want to contribute to APIC, extend its functionality, or understand its internal architecture for debugging purposes.

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Project Structure](#project-structure)
3. [Architecture Deep Dive](#architecture-deep-dive)
4. [Development Workflow](#development-workflow)
5. [Testing](#testing)
6. [Code Style and Standards](#code-style-and-standards)
7. [Adding New Features](#adding-new-features)
8. [Debugging](#debugging)

---

## Development Environment Setup

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 15+ (or Docker)
- Git

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/your-org/APIC.git
cd APIC

# Option 1: Using Makefile (Recommended)
make install

# Option 2: Using setup script
./scripts/setup.sh --full

# Option 3: Manual setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
```

### Environment Configuration

Edit `.env` with your credentials:

```env
# Required for LLM functionality
OPENAI_API_KEY=your-openai-key
# OR
ANTHROPIC_API_KEY=your-anthropic-key

# Required for vector storage
PINECONE_API_KEY=your-pinecone-key
PINECONE_ENVIRONMENT=us-east-1

# Database (use Docker or local PostgreSQL)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/apic
```

### Database Setup

```bash
# Option 1: Using Docker (Recommended for development)
docker-compose up -d postgres

# Option 2: Local PostgreSQL
make db-init
```

---

## Project Structure

```
APIC/
├── config/
│   └── settings.py          # Pydantic settings configuration
├── src/
│   ├── agents/              # 6 workflow agent implementations
│   │   ├── base.py          # Base agent class with LLM factory
│   │   ├── ingestion.py     # Node 1: Document processing
│   │   ├── hypothesis.py    # Node 2: Hypothesis generation
│   │   ├── interview.py     # Node 3: Interview script creation
│   │   ├── gap_analyst.py   # Node 4: Gap analysis
│   │   ├── solution.py      # Node 5: Solution architecture
│   │   └── reporting.py     # Node 6: Report generation
│   ├── api/
│   │   ├── main.py          # FastAPI app factory
│   │   └── routes/          # API endpoint definitions
│   │       ├── projects.py
│   │       ├── documents.py
│   │       └── workflow.py
│   ├── models/
│   │   └── schemas.py       # Pydantic models (321+ lines)
│   ├── services/
│   │   ├── workflow.py      # ConsultantGraph orchestration
│   │   └── state_manager.py # PostgreSQL state persistence
│   └── utils/
│       ├── helpers.py       # Utility functions
│       └── logging_config.py
├── frontend/
│   └── app.py               # Streamlit MVP interface
├── tests/
│   ├── test_agents.py       # Agent unit tests
│   ├── test_api.py          # API endpoint tests
│   ├── test_workflow.py     # Workflow integration tests
│   └── test_models.py       # Pydantic model tests
├── scripts/
│   ├── setup.sh             # Bash installation script
│   ├── install_utils.py     # Python installation utilities
│   ├── init_db.py           # Database initialization
│   └── init_schema.sql      # Database schema
├── docs/                    # Documentation
├── uploads/                 # Document uploads (gitignored)
├── reports/                 # Generated reports (gitignored)
├── logs/                    # Application logs (gitignored)
├── main.py                  # Application entry point
├── Makefile                 # Development commands
├── Dockerfile               # Multi-stage Docker build
├── docker-compose.yml       # Service orchestration
├── requirements.txt         # All dependencies
├── requirements-core.txt    # Production dependencies
├── requirements-dev.txt     # Development dependencies
└── requirements-optional.txt # Optional features
```

---

## Architecture Deep Dive

### The Consultant Graph (6-Node Workflow)

APIC implements a LangGraph-based state machine with a **human breakpoint**:

```
┌─────────────────┐
│  Node 1         │
│  Ingestion      │──────► Parse documents, create embeddings
│  Agent          │        Store in Pinecone vector DB
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Node 2         │
│  Hypothesis     │──────► Analyze documents for inefficiencies
│  Generator      │        Generate confidence-scored hypotheses
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Node 3         │
│  Interview      │──────► Create role-specific interview scripts
│  Architect      │        Target "Dull, Dirty, Dangerous" tasks
└────────┬────────┘
         │
    ⏸️ HUMAN BREAKPOINT ⏸️
    (State persisted to PostgreSQL)
         │
         ▼
┌─────────────────┐
│  Node 4         │
│  Gap Analyst    │──────► Compare SOPs vs interview transcript
│                 │        Classify as Automatable/Partial/Human
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Node 5         │
│  Solution       │──────► Map gaps to automation tools
│  Architect      │        Generate ROI estimates
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Node 6         │
│  Reporting      │──────► Compile executive summary
│  Engine         │        Generate PDF roadmap
└─────────────────┘
```

### State Management

The `GraphState` model (in `src/models/schemas.py`) flows through all nodes:

```python
class GraphState(BaseModel):
    # Project context
    project_id: str
    client_name: str
    project_name: str
    target_departments: List[str] = []

    # Node 1 outputs
    documents: List[Document] = []
    ingestion_complete: bool = False

    # Node 2 outputs
    hypotheses: List[Hypothesis] = []
    hypothesis_generation_complete: bool = False

    # Node 3 outputs
    interview_script: Optional[InterviewScript] = None
    script_generation_complete: bool = False

    # Human breakpoint
    is_suspended: bool = False
    suspension_reason: Optional[str] = None
    transcript: Optional[str] = None

    # Node 4-6 outputs
    gap_analyses: List[GapAnalysisItem] = []
    solutions: List[SolutionRecommendation] = []
    final_report: Optional[Report] = None

    # Metadata
    current_node: str = "start"
    messages: List[str] = []
    errors: List[str] = []
```

### LLM Provider Abstraction

The `BaseAgent` class provides multi-provider LLM support:

```python
# src/agents/base.py
def get_llm():
    provider = settings.DEFAULT_LLM_PROVIDER

    if provider == "openai":
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=settings.LLM_TEMPERATURE,
        )
    elif provider == "anthropic":
        return ChatAnthropic(
            model=settings.ANTHROPIC_MODEL,
            temperature=settings.LLM_TEMPERATURE,
        )
```

---

## Development Workflow

### Running the Application

```bash
# Start API server (development mode with hot reload)
make api
# Or: python main.py api

# Start frontend (in separate terminal)
make frontend
# Or: python main.py frontend

# Or use Docker
make docker-up
```

### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Write tests first (TDD)**
   ```bash
   # Create failing tests
   pytest tests/test_your_feature.py -v
   ```

3. **Implement the feature**

4. **Run tests**
   ```bash
   make test
   # Or: pytest tests/ -v
   ```

5. **Run linting and type checks**
   ```bash
   make check
   # Or: make lint && make type-check
   ```

6. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: Add your feature description"
   ```

---

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest tests/test_agents.py -v

# Run specific test class
pytest tests/test_agents.py::TestIngestionAgent -v

# Run specific test
pytest tests/test_agents.py::TestIngestionAgent::test_document_processing -v
```

### Test Structure

```python
# Example test structure
class TestYourAgent:
    @pytest.fixture
    def agent(self):
        """Create agent instance for testing."""
        with patch('src.agents.your_agent.get_llm'):
            return YourAgent()

    @pytest.mark.asyncio
    async def test_process_returns_updated_state(self, agent):
        """Test that process updates state correctly."""
        initial_state = GraphState(
            project_id="test-123",
            client_name="Test Corp",
            project_name="Test Project",
        )

        result = await agent.process(initial_state.model_dump())

        assert result is not None
        assert result["your_field_complete"] is True
```

### Mocking External Services

```python
from unittest.mock import patch, AsyncMock

# Mock LLM responses
with patch('langchain_openai.ChatOpenAI') as mock_llm:
    mock_llm.return_value.ainvoke = AsyncMock(
        return_value=AIMessage(content="Mocked response")
    )
    # Your test code

# Mock database
with patch('src.services.state_manager.asyncpg.connect') as mock_db:
    mock_db.return_value.fetch = AsyncMock(return_value=[])
    # Your test code
```

---

## Code Style and Standards

### Formatting

- **Black** for code formatting (line length: 88)
- **isort** for import sorting
- **Ruff** for linting

```bash
# Format code
make format

# Or manually
black src/ tests/
isort src/ tests/
```

### Type Hints

All functions should have type hints:

```python
from typing import Dict, List, Optional, Any

async def process_document(
    document_path: str,
    options: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Process a document and return chunks."""
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def calculate_roi(
    current_hours: float,
    automation_percentage: float,
    hourly_rate: float = 50.0,
) -> Dict[str, float]:
    """
    Calculate ROI for automation implementation.

    Args:
        current_hours: Current hours spent on task per week.
        automation_percentage: Percentage of task that can be automated (0-100).
        hourly_rate: Hourly cost of labor.

    Returns:
        Dictionary containing:
            - weekly_savings: Hours saved per week
            - annual_savings: Dollar savings per year
            - roi_percentage: Return on investment percentage

    Raises:
        ValueError: If automation_percentage is not between 0 and 100.
    """
    ...
```

---

## Adding New Features

### Adding a New Agent Node

1. Create the agent class in `src/agents/`:

```python
# src/agents/new_agent.py
from src.agents.base import BaseAgent, get_llm

class NewAgent(BaseAgent):
    """Description of what this agent does."""

    def __init__(self):
        super().__init__("NewAgent")
        self.llm = get_llm()

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the state and return updates."""
        self.log_info(f"Processing project {state.get('project_id')}")

        # Your processing logic here

        return {
            **state,
            "new_field": result,
            "new_agent_complete": True,
        }
```

2. Register in the workflow (`src/services/workflow.py`):

```python
from src.agents.new_agent import NewAgent

class ConsultantGraph:
    def __init__(self):
        # ... existing agents ...
        self.new_agent = NewAgent()

    def _build_graph(self):
        # Add node
        workflow.add_node("new_agent", self.new_agent.process)

        # Add edge from previous node
        workflow.add_edge("previous_node", "new_agent")
```

3. Write tests in `tests/test_agents.py`

### Adding a New API Endpoint

1. Create route in `src/api/routes/`:

```python
# src/api/routes/new_feature.py
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/new-feature", tags=["new-feature"])

@router.get("/{item_id}")
async def get_item(item_id: str):
    """Get a specific item."""
    return {"item_id": item_id}
```

2. Register in `src/api/main.py`:

```python
from src.api.routes import new_feature

app.include_router(new_feature.router, prefix="/api/v1")
```

3. Add tests in `tests/test_api.py`

---

## Debugging

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Log levels
logger.debug("Detailed information for debugging")
logger.info("General information about program execution")
logger.warning("Something unexpected but not critical")
logger.error("Error occurred but program continues")
logger.critical("Serious error, program may not continue")
```

### Common Issues

**Database connection errors:**
```bash
# Check PostgreSQL is running
docker-compose ps

# Check connection
psql postgresql://postgres:postgres@localhost:5432/apic
```

**LLM API errors:**
```python
# Verify API keys are set
from config.settings import settings
print(f"OpenAI key set: {bool(settings.OPENAI_API_KEY)}")
print(f"Anthropic key set: {bool(settings.ANTHROPIC_API_KEY)}")
```

**Import errors:**
```bash
# Ensure PYTHONPATH includes project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or use the installed package
pip install -e .
```

### Using IPython for Debugging

```python
# Add this anywhere in your code
import IPython; IPython.embed()

# Or use breakpoint()
breakpoint()
```

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [pytest Documentation](https://docs.pytest.org/)
