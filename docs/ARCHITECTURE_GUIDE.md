# APIC Architecture Guide

## Overview

This document provides a comprehensive technical architecture overview of APIC (Agentic Process Improvement Consultant) for solution architects, technical leads, and system designers.

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Philosophy](#core-philosophy)
3. [Architecture Patterns](#architecture-patterns)
4. [Component Architecture](#component-architecture)
5. [Data Architecture](#data-architecture)
6. [Integration Architecture](#integration-architecture)
7. [Security Architecture](#security-architecture)
8. [Scalability Considerations](#scalability-considerations)
9. [Technology Decisions](#technology-decisions)
10. [Extension Points](#extension-points)

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐ │
│  │   Streamlit     │  │   REST API      │  │   Future: React/Vue     │ │
│  │   Frontend      │  │   Clients       │  │   SPA Frontend          │ │
│  └────────┬────────┘  └────────┬────────┘  └────────────┬────────────┘ │
└───────────┼─────────────────────┼─────────────────────────┼─────────────┘
            │                     │                         │
            ▼                     ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           API LAYER                                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    FastAPI Application                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐│   │
│  │  │ Projects │  │Documents │  │ Workflow │  │  Health/Metrics  ││   │
│  │  │  Routes  │  │  Routes  │  │  Routes  │  │     Routes       ││   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────┘   │
└───────────┬─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         SERVICE LAYER                                    │
│  ┌────────────────────────────────┐  ┌──────────────────────────────┐  │
│  │      Consultant Graph          │  │       State Manager          │  │
│  │   (LangGraph Orchestration)    │  │   (PostgreSQL Persistence)   │  │
│  │                                │  │                              │  │
│  │  ┌───────────────────────────┐│  │  ┌─────────────────────────┐ │  │
│  │  │     6-Node Workflow       ││  │  │   Project CRUD          │ │  │
│  │  │  with Human Breakpoint    ││  │  │   State Persistence     │ │  │
│  │  └───────────────────────────┘│  │  │   Document Tracking     │ │  │
│  └────────────────────────────────┘  └──────────────────────────────┘  │
└───────────┬─────────────────────┬─────────────────────────────────────┘
            │                     │
            ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         AGENT LAYER                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │Ingestion │ │Hypothesis│ │Interview │ │   Gap    │ │ Solution │      │
│  │  Agent   │ │Generator │ │Architect │ │ Analyst  │ │ Architect│      │
│  │ (Node 1) │ │ (Node 2) │ │ (Node 3) │ │ (Node 4) │ │ (Node 5) │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│       │                                                    │            │
│       │            ┌──────────────────────┐               │            │
│       │            │   Reporting Engine   │               │            │
│       └────────────│      (Node 6)        │───────────────┘            │
│                    └──────────────────────┘                            │
└───────────┬─────────────────────┬─────────────────┬────────────────────┘
            │                     │                 │
            ▼                     ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                                │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────────┐   │
│  │    PostgreSQL    │  │     Pinecone     │  │    LLM Providers    │   │
│  │   (Relational)   │  │  (Vector Store)  │  │ (OpenAI/Anthropic)  │   │
│  └──────────────────┘  └──────────────────┘  └─────────────────────┘   │
│  ┌──────────────────┐  ┌──────────────────┐                            │
│  │   File System    │  │   PDF Generator  │                            │
│  │ (uploads/reports)│  │  (ReportLab)     │                            │
│  └──────────────────┘  └──────────────────┘                            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Core Philosophy

### Reality-Grounded AI

APIC implements "Reality-Grounded AI" - a principle that AI recommendations must be validated against real-world observations before being presented as solutions.

**Traditional Approach:**
```
Documents → AI Analysis → Recommendations
           ↑                    ↓
           └── Risk: Hallucinations based on theory
```

**APIC Approach:**
```
Documents → AI Hypotheses → Human Validation → AI Analysis → Recommendations
                                    ↑                              ↓
                                    └── Grounded in reality ───────┘
```

### Human-in-the-Loop Design

The human breakpoint between Phase 3 and Phase 4 is not a limitation but a feature:

1. **Hypothesis Validation:** AI identifies suspected inefficiencies
2. **Human Verification:** Real interviews confirm or refute hypotheses
3. **Grounded Solutions:** Recommendations based on verified information

---

## Architecture Patterns

### 1. State Machine Pattern (LangGraph)

The workflow is implemented as a directed graph with well-defined state transitions:

```python
# Workflow Definition
graph = StateGraph(GraphState)

# Add nodes (processing functions)
graph.add_node("ingestion", ingestion_agent.process)
graph.add_node("hypothesis", hypothesis_agent.process)
graph.add_node("interview", interview_agent.process)
graph.add_node("breakpoint", human_breakpoint)  # Special node
graph.add_node("gap_analysis", gap_agent.process)
graph.add_node("solution", solution_agent.process)
graph.add_node("reporting", reporting_agent.process)

# Define edges (transitions)
graph.add_edge(START, "ingestion")
graph.add_edge("ingestion", "hypothesis")
graph.add_edge("hypothesis", "interview")
graph.add_edge("interview", "breakpoint")  # Suspends here
graph.add_edge("breakpoint", "gap_analysis")  # Resumes here
graph.add_edge("gap_analysis", "solution")
graph.add_edge("solution", "reporting")
graph.add_edge("reporting", END)
```

### 2. Agent Pattern

Each node is implemented as an independent agent with:

```python
class Agent(ABC):
    """Abstract base for all agents."""

    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process state and return updates.

        Args:
            state: Current workflow state

        Returns:
            Updated state with agent's contributions
        """
        pass
```

**Benefits:**
- Single responsibility
- Testable in isolation
- Replaceable/upgradeable independently
- Clear input/output contracts

### 3. Repository Pattern (State Management)

State persistence uses the repository pattern for database abstraction:

```python
class StateManager:
    """Repository for workflow state."""

    def create_project(self, ...) -> Dict[str, Any]: ...
    def get_project(self, id: str) -> Optional[Dict[str, Any]]: ...
    def save_state(self, project_id: str, state: Dict) -> None: ...
    def load_state(self, project_id: str) -> Optional[Dict]: ...
```

### 4. Factory Pattern (LLM Provider)

LLM instantiation uses a factory for provider abstraction:

```python
def get_llm() -> BaseChatModel:
    """Factory for LLM instances."""
    if settings.DEFAULT_LLM_PROVIDER == "openai":
        return ChatOpenAI(...)
    elif settings.DEFAULT_LLM_PROVIDER == "anthropic":
        return ChatAnthropic(...)
    else:
        raise ValueError(f"Unknown provider: {settings.DEFAULT_LLM_PROVIDER}")
```

---

## Component Architecture

### API Layer (FastAPI)

```
src/api/
├── main.py              # App factory, lifespan, middleware
└── routes/
    ├── projects.py      # Project CRUD endpoints
    ├── documents.py     # Document upload/listing
    └── workflow.py      # Workflow control endpoints
```

**Key Design Decisions:**

1. **Async-first:** All endpoints are async for I/O efficiency
2. **Dependency Injection:** Services injected via FastAPI dependencies
3. **Pydantic Validation:** Request/response models for type safety
4. **OpenAPI Documentation:** Auto-generated from type hints

### Service Layer

```
src/services/
├── workflow.py          # ConsultantGraph orchestration
└── state_manager.py     # PostgreSQL persistence
```

**ConsultantGraph Responsibilities:**
- Build and compile LangGraph workflow
- Execute workflow to breakpoint
- Resume workflow from breakpoint
- Handle errors and state recovery

**StateManager Responsibilities:**
- Project CRUD operations
- Workflow state serialization/deserialization
- Document metadata tracking
- Query suspended projects

### Agent Layer

```
src/agents/
├── base.py              # BaseAgent + LLM factory
├── ingestion.py         # Document processing
├── hypothesis.py        # Inefficiency identification
├── interview.py         # Interview script generation
├── gap_analyst.py       # SOP vs reality comparison
├── solution.py          # Automation recommendations
└── reporting.py         # PDF report generation
```

**Agent Communication:**
- Agents communicate only through shared state
- No direct agent-to-agent calls
- State is immutable from agent perspective (returns new state)

---

## Data Architecture

### Data Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Uploads   │────▶│  Ingestion  │────▶│  Pinecone   │
│  (Documents)│     │   Agent     │     │  (Vectors)  │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ PostgreSQL  │◀───▶│   State     │◀───▶│  Workflow   │
│ (Metadata)  │     │  Manager    │     │   Engine    │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
┌─────────────┐     ┌─────────────┐
│   Reports   │◀────│  Reporting  │
│   (PDFs)    │     │    Agent    │
└─────────────┘     └─────────────┘
```

### Database Schema

```sql
-- Projects (metadata)
CREATE TABLE projects (
    id VARCHAR(36) PRIMARY KEY,
    client_name VARCHAR(255) NOT NULL,
    project_name VARCHAR(255) NOT NULL,
    description TEXT,
    target_departments JSONB DEFAULT '[]',
    status VARCHAR(50) DEFAULT 'created',
    vector_namespace VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Project States (workflow persistence)
CREATE TABLE project_states (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) UNIQUE NOT NULL,
    thread_id VARCHAR(36) UNIQUE NOT NULL,
    state_data JSONB NOT NULL,           -- Full GraphState serialized
    current_node VARCHAR(50),
    is_suspended BOOLEAN DEFAULT FALSE,
    suspension_reason VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Documents (file metadata)
CREATE TABLE documents (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size VARCHAR(50) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    chunk_count VARCHAR(50) DEFAULT '0',
    processed BOOLEAN DEFAULT FALSE,
    content_summary TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Vector Storage (Pinecone)

**Namespace Strategy:**
- Each project gets its own namespace: `client_{project_id}`
- Enables isolated vector queries per project
- Simplifies cleanup when project is deleted

**Embedding Model:**
- OpenAI `text-embedding-3-small` (default)
- 1536 dimensions
- Stored with document chunk metadata

---

## Integration Architecture

### LLM Integration

```
┌─────────────────────────────────────────────────────────┐
│                    APIC Application                      │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              LangChain Abstraction               │   │
│  │  ┌─────────────┐     ┌───────────────────────┐  │   │
│  │  │ ChatOpenAI  │     │   ChatAnthropic       │  │   │
│  │  └──────┬──────┘     └───────────┬───────────┘  │   │
│  └─────────┼────────────────────────┼───────────────┘   │
└────────────┼────────────────────────┼───────────────────┘
             │                        │
             ▼                        ▼
    ┌────────────────┐      ┌────────────────┐
    │   OpenAI API   │      │  Anthropic API │
    │   (GPT-4o)     │      │  (Claude 3.5)  │
    └────────────────┘      └────────────────┘
```

**Provider Switching:**
```env
# Switch provider via environment variable
DEFAULT_LLM_PROVIDER=openai
# or
DEFAULT_LLM_PROVIDER=anthropic
```

### Vector Database Integration

```python
# Pinecone initialization
from pinecone import Pinecone

pc = Pinecone(api_key=settings.PINECONE_API_KEY)
index = pc.Index(settings.PINECONE_INDEX_NAME)

# Per-project namespace isolation
namespace = f"client_{project_id}"
index.upsert(vectors=vectors, namespace=namespace)
index.query(vector=query_embedding, namespace=namespace)
```

---

## Security Architecture

### Authentication & Authorization

**Current Implementation (MVP):**
- No authentication (intended for internal/private deployment)
- API accessible on localhost only by default

**Recommended for Production:**
```python
# FastAPI Security
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader

# Option 1: API Key
api_key_header = APIKeyHeader(name="X-API-Key")

@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    api_key = request.headers.get("X-API-Key")
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=403)
    return await call_next(request)

# Option 2: OAuth2/JWT (for enterprise)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
```

### Data Security

| Data Type | Storage | Encryption |
|-----------|---------|------------|
| Documents | File system | At-rest (recommended) |
| Metadata | PostgreSQL | Database TLS |
| Embeddings | Pinecone | Pinecone managed |
| API Keys | Environment | Not in code/logs |
| Reports | File system | At-rest (recommended) |

### Network Security

```yaml
# Recommended Docker network isolation
services:
  postgres:
    networks:
      - backend
    # Not exposed to host

  api:
    networks:
      - backend
      - frontend
    ports:
      - "8000:8000"  # Exposed

  frontend:
    networks:
      - frontend
    ports:
      - "8501:8501"  # Exposed
```

---

## Scalability Considerations

### Horizontal Scaling

```
                    ┌─────────────────┐
                    │  Load Balancer  │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
   ┌───────────┐       ┌───────────┐       ┌───────────┐
   │  API #1   │       │  API #2   │       │  API #3   │
   └─────┬─────┘       └─────┬─────┘       └─────┬─────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
   ┌───────────┐       ┌───────────┐       ┌───────────┐
   │ PostgreSQL│       │  Pinecone │       │   Redis   │
   │  Primary  │       │  (Managed)│       │  (Cache)  │
   └───────────┘       └───────────┘       └───────────┘
```

**Stateless API Design:**
- No session state in API instances
- All state in PostgreSQL
- Enables horizontal scaling

### Bottleneck Analysis

| Component | Bottleneck | Mitigation |
|-----------|------------|------------|
| LLM Calls | Token limits, rate limits | Request queuing, caching |
| Document Processing | CPU/Memory for large files | Worker queue (Celery) |
| Vector Queries | Query latency | Pinecone pod scaling |
| Database | Connection pooling | PgBouncer, read replicas |

### Caching Strategy (Future)

```python
# Redis caching for frequent queries
from redis import Redis

redis = Redis.from_url(settings.REDIS_URL)

async def get_project_with_cache(project_id: str):
    # Check cache
    cached = redis.get(f"project:{project_id}")
    if cached:
        return json.loads(cached)

    # Query database
    project = await state_manager.get_project(project_id)

    # Cache result
    redis.setex(f"project:{project_id}", 300, json.dumps(project))
    return project
```

---

## Technology Decisions

### Decision Matrix

| Requirement | Technology | Rationale |
|-------------|------------|-----------|
| Workflow Orchestration | LangGraph | Native state machine for AI agents |
| API Framework | FastAPI | Async-first, automatic OpenAPI |
| LLM Abstraction | LangChain | Multi-provider support |
| Relational DB | PostgreSQL | JSONB support, reliability |
| Vector DB | Pinecone | Managed, serverless option |
| Frontend (MVP) | Streamlit | Rapid prototyping |
| PDF Generation | ReportLab | Python-native, no dependencies |
| Validation | Pydantic | Type safety, serialization |

### Trade-offs Made

**LangGraph vs. Custom FSM:**
- (+) Native LLM integration
- (+) Built-in checkpointing
- (-) Learning curve
- (-) Version lock-in

**Pinecone vs. Self-hosted (Weaviate, Qdrant):**
- (+) Managed infrastructure
- (+) Serverless scaling
- (-) Vendor lock-in
- (-) Cost at scale

**Streamlit vs. React SPA:**
- (+) Rapid development
- (+) Python-native
- (-) Limited customization
- (-) Not production-grade UI

---

## Extension Points

### Adding New LLM Providers

```python
# src/agents/base.py
def get_llm() -> BaseChatModel:
    provider = settings.DEFAULT_LLM_PROVIDER

    if provider == "openai":
        return ChatOpenAI(...)
    elif provider == "anthropic":
        return ChatAnthropic(...)
    elif provider == "azure":  # New provider
        from langchain_openai import AzureChatOpenAI
        return AzureChatOpenAI(
            azure_deployment=settings.AZURE_DEPLOYMENT,
            api_version=settings.AZURE_API_VERSION,
        )
```

### Adding New Agent Nodes

```python
# 1. Create agent class
class NewAgent(BaseAgent):
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation
        pass

# 2. Register in workflow
# src/services/workflow.py
workflow.add_node("new_agent", self.new_agent.process)
workflow.add_edge("previous_node", "new_agent")

# 3. Update GraphState model
# src/models/schemas.py
class GraphState(BaseModel):
    # ... existing fields ...
    new_agent_output: Optional[NewOutput] = None
    new_agent_complete: bool = False
```

### Adding New Document Types

```python
# src/agents/ingestion.py
class IngestionAgent(BaseAgent):
    SUPPORTED_TYPES = {
        "pdf": self._process_pdf,
        "docx": self._process_docx,
        "xlsx": self._process_excel,  # New type
    }

    async def _process_excel(self, file_path: str) -> List[str]:
        import openpyxl
        wb = openpyxl.load_workbook(file_path)
        chunks = []
        for sheet in wb:
            for row in sheet.iter_rows(values_only=True):
                chunks.append(" | ".join(str(cell) for cell in row))
        return chunks
```

### Custom Report Templates

```python
# src/agents/reporting.py
class ReportingEngine(BaseAgent):
    def __init__(self, template: str = "default"):
        self.template = self._load_template(template)

    def _load_template(self, name: str) -> ReportTemplate:
        templates = {
            "default": DefaultTemplate(),
            "executive": ExecutiveTemplate(),  # New template
            "technical": TechnicalTemplate(),  # New template
        }
        return templates.get(name, templates["default"])
```

---

## Appendix

### C4 Diagram (Context Level)

```
┌─────────────────────────────────────────────────────────┐
│                        Users                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │  Analysts   │  │  Managers   │  │   Consultants   │ │
│  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘ │
└─────────┼────────────────┼──────────────────┼───────────┘
          │                │                  │
          └────────────────┼──────────────────┘
                           │
                           ▼
            ┌──────────────────────────┐
            │                          │
            │          APIC            │
            │  (Process Improvement    │
            │      Consultant)         │
            │                          │
            └──────────────────────────┘
                    │         │
        ┌───────────┘         └───────────┐
        │                                 │
        ▼                                 ▼
┌───────────────────┐           ┌───────────────────┐
│   LLM Providers   │           │   Vector Database │
│ (OpenAI/Anthropic)│           │    (Pinecone)     │
└───────────────────┘           └───────────────────┘
```

### ADR (Architecture Decision Record) Template

```markdown
# ADR-001: Use LangGraph for Workflow Orchestration

## Status
Accepted

## Context
We need to orchestrate a multi-step AI workflow with human intervention points.

## Decision
Use LangGraph for workflow orchestration.

## Consequences
- (+) Native state machine with LLM support
- (+) Built-in checkpointing for resumption
- (+) Active development by LangChain team
- (-) Coupled to LangChain ecosystem
- (-) Learning curve for team
```
