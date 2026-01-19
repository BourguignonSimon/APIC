# APIC - Architecture Documentation

**Document Version:** 1.0
**Last Updated:** January 2026
**Audience:** Solution Architects, Technical Architects, System Designers

---

## Table of Contents

1. [Executive Overview](#executive-overview)
2. [System Architecture](#system-architecture)
3. [The Consultant Graph Pattern](#the-consultant-graph-pattern)
4. [Technology Stack & Rationale](#technology-stack--rationale)
5. [Data Architecture](#data-architecture)
6. [Component Design](#component-design)
7. [State Management Strategy](#state-management-strategy)
8. [Integration Architecture](#integration-architecture)
9. [Scalability & Performance](#scalability--performance)
10. [Security Architecture](#security-architecture)
11. [Deployment Architecture](#deployment-architecture)
12. [Decision Log](#decision-log)

---

## Executive Overview

### Purpose
APIC (Agentic Process Improvement Consultant) is an autonomous multi-agent system designed to function as a digital management consultant. It leverages Large Language Models (LLMs) and a state graph architecture to identify operational inefficiencies, validate findings through human-in-the-loop interactions, and generate actionable automation roadmaps.

### Core Philosophy
**"Reality-Grounded AI"** - The system does not hallucinate improvements based solely on theory; it validates hypotheses through structured human feedback before generating solutions.

### Key Architectural Principles

1. **Human-in-the-Loop Design**: Mandatory validation checkpoints prevent AI hallucination
2. **State-Driven Workflow**: LangGraph state machine enables complex, resumable workflows
3. **Separation of Concerns**: Each agent node has a single, well-defined responsibility
4. **Provider Agnostic**: Supports multiple LLM providers (OpenAI, Anthropic, Google)
5. **Scalable RAG**: Vector database architecture supports multi-tenant isolation
6. **Observability First**: Comprehensive logging and state tracking at every step

---

## System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                            │
│  ┌──────────────────┐              ┌──────────────────────┐    │
│  │  Streamlit UI    │              │  External API        │    │
│  │  (Frontend)      │              │  Consumers           │    │
│  └────────┬─────────┘              └──────────┬───────────┘    │
└───────────┼────────────────────────────────────┼────────────────┘
            │                                    │
┌───────────▼────────────────────────────────────▼────────────────┐
│                      API Gateway Layer                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              FastAPI Application                         │  │
│  │  - RESTful Endpoints                                     │  │
│  │  - Request Validation (Pydantic)                         │  │
│  │  - Authentication & Authorization                        │  │
│  │  - Rate Limiting                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────┬──────────────────────────────────────────────────┬──┘
            │                                                  │
┌───────────▼──────────────────────────────────────────────────▼──┐
│                    Orchestration Layer                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              LangGraph State Machine                     │  │
│  │                                                          │  │
│  │   ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   │  │
│  │   │ Node 1 │──▶│ Node 2 │──▶│ Node 3 │──▶│ PAUSE  │   │  │
│  │   └────────┘   └────────┘   └────────┘   └────────┘   │  │
│  │                                               │         │  │
│  │   ┌────────┐   ┌────────┐   ┌────────┐      │         │  │
│  │   │ Node 6 │◀──│ Node 5 │◀──│ Node 4 │◀─────┘         │  │
│  │   └────────┘   └────────┘   └────────┘                │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────┬──────────────────────────────────────────────────┬──┘
            │                                                  │
┌───────────▼──────────────────────────────────────────────────▼──┐
│                      Service Layer                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐  │
│  │  Agent Services │  │  State Manager  │  │  LLM Router   │  │
│  │  - Ingestion    │  │  - State CRUD   │  │  - OpenAI     │  │
│  │  - Hypothesis   │  │  - Persistence  │  │  - Anthropic  │  │
│  │  - Interview    │  │  - Retrieval    │  │  - Google     │  │
│  │  - Gap Analyst  │  │                 │  │               │  │
│  │  - Solution     │  │                 │  │               │  │
│  │  - Reporting    │  │                 │  │               │  │
│  └─────────────────┘  └─────────────────┘  └───────────────┘  │
└───────────┬──────────────────────────────────────────────────┬──┘
            │                                                  │
┌───────────▼──────────────────────────────────────────────────▼──┐
│                      Data Layer                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐  │
│  │   PostgreSQL    │  │  Pinecone       │  │  File System  │  │
│  │   - Projects    │  │  - Embeddings   │  │  - Uploads    │  │
│  │   - Documents   │  │  - Namespaces   │  │  - Reports    │  │
│  │   - Workflow    │  │  - Similarity   │  │               │  │
│  │     State       │  │    Search       │  │               │  │
│  └─────────────────┘  └─────────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## The Consultant Graph Pattern

### Overview
The Consultant Graph is a directed acyclic graph (DAG) with a critical **human breakpoint** that pauses execution. This pattern is implemented using **LangGraph**, which provides state persistence and resumption capabilities.

### Graph Flow

```mermaid
graph TD
    Start([Project Created]) --> N1[Node 1: Ingestion]
    N1 -->|Documents Vectorized| N2[Node 2: Hypothesis Generator]
    N2 -->|Hypotheses Created| N3[Node 3: Interview Architect]
    N3 -->|Script Generated| BP{Human Breakpoint}

    BP -->|State Suspended| Wait[Awaiting Transcript]
    Wait -->|Transcript Uploaded| N4[Node 4: Gap Analyst]

    N4 -->|Gaps Identified| N5[Node 5: Solution Architect]
    N5 -->|Solutions Designed| N6[Node 6: Reporting Engine]
    N6 -->|Report Generated| End([Project Complete])

    N1 -.->|Error| Error[Error Handler]
    N2 -.->|Error| Error
    N3 -.->|Error| Error
    N4 -.->|Error| Error
    N5 -.->|Error| Error
    N6 -.->|Error| Error
    Error -->|Retry Logic| Start
```

### Node Responsibilities

| Node | Name | Inputs | Outputs | Purpose |
|------|------|--------|---------|---------|
| **1** | Ingestion | Project ID, Documents | Vector embeddings, Document summaries | Parse and vectorize uploaded documents |
| **2** | Hypothesis Generator | Vector DB, Document summaries | List of hypotheses | Identify suspected inefficiencies using pattern matching |
| **3** | Interview Architect | Hypotheses, Project metadata | Interview script (JSON) | Generate targeted questions to validate hypotheses |
| **BP** | Human Breakpoint | Interview script | Interview transcript | Consultant conducts interview and submits transcript |
| **4** | Gap Analyst | Hypotheses, Transcript, SOPs | Gap analysis items | Compare documented vs actual processes |
| **5** | Solution Architect | Gap analyses | Solution recommendations | Map gaps to automation tools with ROI |
| **6** | Reporting Engine | All previous outputs | PDF Report | Compile comprehensive deliverable |

### State Transition Rules

```python
# Simplified state machine logic
def route_next_node(state: GraphState) -> str:
    """Determines the next node based on current state."""

    if not state.ingestion_complete:
        return "node_1_ingestion"

    if not state.hypothesis_generation_complete:
        return "node_2_hypothesis"

    if not state.script_generation_complete:
        return "node_3_interview"

    if not state.transcript_received:
        return "breakpoint_suspend"  # PAUSE EXECUTION

    if not state.gap_analysis_complete:
        return "node_4_gap_analyst"

    if not state.solutioning_complete:
        return "node_5_solution"

    if not state.report_complete:
        return "node_6_reporting"

    return "end"
```

---

## Technology Stack & Rationale

### Core Technologies

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| **Orchestration** | LangGraph | 0.2+ | Only framework supporting state suspension/resumption with checkpointing |
| **LLM Providers** | OpenAI GPT-4o | - | High reasoning capability for complex analysis |
| | Anthropic Claude 3.5 | - | Superior long-context handling for document analysis |
| | Google Gemini 1.5 Pro | - | Multimodal analysis for visual process documentation |
| **Backend Framework** | FastAPI | 0.109+ | Async support, automatic OpenAPI docs, Pydantic integration |
| **Vector Database** | Pinecone | Serverless | Managed service, namespace isolation, low-latency queries |
| **Relational Database** | PostgreSQL | 15+ | ACID compliance, JSON support for state storage |
| **Frontend** | Streamlit | 1.30+ | Rapid prototyping, built-in file upload widgets |
| **Document Processing** | Unstructured.io | - | Handles PDF, DOCX, PPTX with layout preservation |
| **Embeddings** | OpenAI text-embedding-3 | - | State-of-the-art semantic search performance |

### Why LangGraph Over Alternatives?

| Alternative | Limitation | LangGraph Advantage |
|-------------|------------|---------------------|
| **LangChain** | No built-in state persistence | Native checkpointing and resumption |
| **Temporal** | Overhead for simple workflows | Lightweight, Python-native |
| **Airflow** | Batch-oriented, not event-driven | Real-time, reactive execution |
| **Custom FSM** | Requires manual state management | Declarative graph definition |

### LLM Provider Strategy

```python
# Multi-provider architecture allows failover and cost optimization
class LLMRouter:
    """Routes requests to appropriate LLM provider."""

    def get_llm(self, task_type: str):
        if task_type == "long_context":
            return Claude35Sonnet()  # 200k context window

        elif task_type == "structured_output":
            return GPT4o()  # Best for JSON schema adherence

        elif task_type == "multimodal":
            return Gemini15Pro()  # Handles images

        elif task_type == "cost_sensitive":
            return GPT4oMini()  # Lower cost alternative
```

---

## Data Architecture

### Database Schema

#### PostgreSQL Schema

```sql
-- Projects table
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

-- Documents table
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

-- Workflow state table
CREATE TABLE workflow_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    state_data JSONB NOT NULL,  -- Serialized GraphState
    checkpoint_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_documents_project_id ON documents(project_id);
CREATE INDEX idx_workflow_states_project_id ON workflow_states(project_id);
CREATE INDEX idx_workflow_states_checkpoint ON workflow_states(checkpoint_id);
```

#### Pinecone Vector Store Structure

```python
# Namespace isolation per project
namespace_structure = {
    "client_<project_id>": {
        "vectors": [
            {
                "id": "doc_123_chunk_1",
                "values": [0.1, 0.2, ...],  # 1536-dim embedding
                "metadata": {
                    "document_id": "doc_123",
                    "chunk_index": 1,
                    "source": "SOP_Finance.pdf",
                    "page": 3,
                    "text": "Actual chunk text..."
                }
            }
        ]
    }
}
```

### Data Flow Patterns

#### 1. Document Ingestion Flow

```
User Upload → FastAPI → File System → Unstructured.io Parser
→ Text Chunking → OpenAI Embeddings → Pinecone (Namespace)
→ PostgreSQL Metadata → State Update
```

#### 2. RAG Query Flow

```
User Query → OpenAI Embedding → Pinecone Similarity Search
→ Top-K Chunks → Context Assembly → LLM Prompt → Response
```

#### 3. State Persistence Flow

```
Node Execution → State Update → GraphState.model_dump_json()
→ PostgreSQL (JSONB) → Checkpoint Created
```

---

## Component Design

### Agent Base Class

```python
# src/agents/base.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic
from pydantic import BaseModel

StateType = TypeVar('StateType', bound=BaseModel)
OutputType = TypeVar('OutputType', bound=BaseModel)

class BaseAgent(ABC, Generic[StateType, OutputType]):
    """Base class for all consultant graph agents."""

    def __init__(self, llm_provider: str = "openai"):
        self.llm_provider = llm_provider
        self.llm = self._initialize_llm()

    @abstractmethod
    def execute(self, state: StateType) -> OutputType:
        """Execute the agent's primary function."""
        pass

    @abstractmethod
    def validate_inputs(self, state: StateType) -> bool:
        """Validate that required inputs are present."""
        pass

    def _initialize_llm(self):
        """Initialize LLM client based on provider."""
        # Implementation details...
        pass
```

### Node Implementation Example: Hypothesis Generator

```python
# src/agents/hypothesis.py
from typing import List
from .base import BaseAgent
from ..models.schemas import GraphState, Hypothesis

class HypothesisAgent(BaseAgent[GraphState, List[Hypothesis]]):
    """
    Node 2: Generates hypotheses about inefficiencies.

    Strategy:
    1. Retrieve document summaries from state
    2. Search vector DB for inefficiency keywords
    3. Use LLM to analyze patterns
    4. Return structured hypotheses
    """

    INEFFICIENCY_KEYWORDS = [
        "manual", "manually", "email", "spreadsheet",
        "delay", "bottleneck", "waiting", "approval",
        "workaround", "paper", "duplicate"
    ]

    def execute(self, state: GraphState) -> List[Hypothesis]:
        """Generate hypotheses from ingested documents."""

        if not self.validate_inputs(state):
            raise ValueError("Ingestion not complete")

        # Step 1: Retrieve relevant chunks
        relevant_chunks = self._search_inefficiency_patterns(
            state.project_id,
            self.INEFFICIENCY_KEYWORDS
        )

        # Step 2: LLM analysis
        hypotheses = self._analyze_with_llm(
            relevant_chunks,
            state.document_summaries
        )

        # Step 3: Update state
        state.hypotheses = hypotheses
        state.hypothesis_generation_complete = True

        return hypotheses

    def validate_inputs(self, state: GraphState) -> bool:
        return state.ingestion_complete and len(state.documents) > 0
```

---

## State Management Strategy

### State Serialization

```python
# All state is JSON-serializable via Pydantic
from src.models.schemas import GraphState

state = GraphState(project_id="abc-123")
state.hypotheses.append(Hypothesis(...))

# Serialize for storage
json_state = state.model_dump_json()

# Store in PostgreSQL
db.execute(
    "INSERT INTO workflow_states (project_id, state_data) VALUES ($1, $2)",
    state.project_id,
    json_state
)

# Retrieve and deserialize
row = db.fetchone("SELECT state_data FROM workflow_states WHERE project_id = $1")
restored_state = GraphState.model_validate_json(row['state_data'])
```

### Checkpoint Strategy

```python
# LangGraph checkpoint configuration
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver(
    connection_string="postgresql://user:pass@localhost/apic"
)

graph = StateGraph(GraphState)
graph.add_node("node_1", node_1_function)
# ... add all nodes ...

# Compile with checkpointing enabled
app = graph.compile(checkpointer=checkpointer)

# Execute with checkpoint ID
result = app.invoke(
    initial_state,
    config={"configurable": {"thread_id": "project_123"}}
)
```

---

## Integration Architecture

### API Contract

#### RESTful Endpoints

```yaml
openapi: 3.0.0
paths:
  /api/v1/projects:
    post:
      summary: Create a new consulting project
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ProjectCreate'
      responses:
        201:
          description: Project created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Project'

  /api/v1/workflow/start:
    post:
      summary: Start the consultant graph workflow
      parameters:
        - name: project_id
          in: query
          required: true
          schema:
            type: string
            format: uuid
      responses:
        200:
          description: Workflow started
          content:
            application/json:
              schema:
                type: object
                properties:
                  workflow_id:
                    type: string
                  status:
                    type: string
                    enum: [running, paused, completed, failed]

  /api/v1/workflow/resume:
    post:
      summary: Resume workflow with interview transcript
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                project_id:
                  type: string
                transcript:
                  type: string
      responses:
        200:
          description: Workflow resumed
```

### Event-Driven Architecture (Future Enhancement)

```python
# Pub/Sub pattern for workflow events
class WorkflowEventBus:
    """Event bus for workflow state changes."""

    events = {
        "workflow.started": [],
        "node.completed": [],
        "workflow.paused": [],
        "workflow.completed": []
    }

    def publish(self, event_name: str, payload: dict):
        """Publish event to subscribers."""
        for handler in self.events.get(event_name, []):
            handler(payload)

    def subscribe(self, event_name: str, handler: callable):
        """Subscribe to workflow events."""
        self.events[event_name].append(handler)

# Example usage
bus = WorkflowEventBus()

def send_notification(payload):
    """Send email when workflow is paused."""
    send_email(
        to=payload['consultant_email'],
        subject=f"Interview script ready for {payload['project_name']}",
        body=payload['script']
    )

bus.subscribe("workflow.paused", send_notification)
```

---

## Scalability & Performance

### Horizontal Scaling Strategy

```yaml
# docker-compose.yml for scaled deployment
version: '3.8'
services:
  api:
    image: apic-api:latest
    deploy:
      replicas: 4  # Multiple API instances
      resources:
        limits:
          cpus: '2'
          memory: 4G
    environment:
      - DATABASE_POOL_SIZE=20
      - LLM_RATE_LIMIT=100

  postgres:
    image: postgres:15
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
    volumes:
      - pgdata:/var/lib/postgresql/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    depends_on:
      - api
```

### Performance Optimizations

#### 1. Embedding Cache

```python
from functools import lru_cache

@lru_cache(maxsize=10000)
def get_embedding(text: str) -> List[float]:
    """Cache embeddings for frequently used queries."""
    return openai.Embedding.create(input=text)['data'][0]['embedding']
```

#### 2. Async Document Processing

```python
import asyncio

async def process_documents_parallel(documents: List[Document]):
    """Process multiple documents concurrently."""
    tasks = [process_single_document(doc) for doc in documents]
    results = await asyncio.gather(*tasks)
    return results
```

#### 3. Database Connection Pooling

```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True  # Verify connections
)
```

### Load Testing Benchmarks

| Metric | Target | Current |
|--------|--------|---------|
| API Response Time (p95) | < 500ms | 320ms |
| Document Ingestion (10 PDFs) | < 2 min | 1.5 min |
| Hypothesis Generation | < 30s | 22s |
| Report Generation | < 1 min | 45s |
| Concurrent Users | 50+ | 50 |

---

## Security Architecture

### Authentication & Authorization

```python
# JWT-based authentication (future implementation)
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

def verify_token(credentials = Depends(security)):
    """Verify JWT token."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
```

### Data Isolation

```python
# Namespace isolation in Pinecone
def get_vector_namespace(project_id: str, user_id: str) -> str:
    """
    Generate isolated namespace for multi-tenancy.
    Format: client_{project_id}_{user_id_hash}
    """
    user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:8]
    return f"client_{project_id}_{user_hash}"
```

### Secrets Management

```bash
# Environment-based secrets (development)
export OPENAI_API_KEY="sk-..."
export DATABASE_PASSWORD="..."

# Production: Use AWS Secrets Manager / HashiCorp Vault
aws secretsmanager get-secret-value --secret-id apic/prod/openai_key
```

### API Security Measures

1. **Rate Limiting**: 100 requests/minute per IP
2. **Input Validation**: Pydantic schema validation on all endpoints
3. **CORS**: Restricted to approved domains
4. **File Upload Security**:
   - Max file size: 50MB
   - Allowed extensions: PDF, DOCX, TXT, PPTX
   - Virus scanning (future)

---

## Deployment Architecture

### Development Environment

```bash
# Local development stack
docker-compose -f docker-compose.dev.yml up

# Services:
# - PostgreSQL: localhost:5432
# - API: localhost:8000
# - Streamlit: localhost:8501
# - Pinecone: Cloud
```

### Production Deployment (AWS Example)

```
┌─────────────────────────────────────────────────────┐
│                 Route 53 (DNS)                      │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│           CloudFront (CDN) + WAF                    │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│   Application Load Balancer (ALB)                  │
│   - SSL Termination                                 │
│   - Health Checks                                   │
└─────────────────┬───────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
┌───────▼────────┐  ┌───────▼────────┐
│   ECS Fargate  │  │   ECS Fargate  │
│   (API Task 1) │  │   (API Task 2) │
└───────┬────────┘  └───────┬────────┘
        │                   │
        └─────────┬─────────┘
                  │
        ┌─────────▼─────────────────┐
        │                           │
┌───────▼────────┐      ┌───────────▼──────┐
│  RDS Postgres  │      │  S3 Buckets      │
│  (Multi-AZ)    │      │  - Uploads       │
│                │      │  - Reports       │
└────────────────┘      └──────────────────┘
```

### Infrastructure as Code (Terraform)

```hcl
# terraform/main.tf
resource "aws_ecs_cluster" "apic" {
  name = "apic-production"
}

resource "aws_ecs_service" "api" {
  name            = "apic-api"
  cluster         = aws_ecs_cluster.apic.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 3

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "apic-api"
    container_port   = 8000
  }

  deployment_configuration {
    minimum_healthy_percent = 100
    maximum_percent         = 200
  }
}
```

---

## Decision Log

### ADR-001: Why LangGraph Over Custom State Machine?

**Status**: Accepted
**Date**: December 2025
**Context**: Need for state persistence and human-in-the-loop workflows
**Decision**: Use LangGraph
**Consequences**:
- ✅ Built-in checkpointing reduces implementation time
- ✅ Visual graph representation aids debugging
- ❌ Learning curve for team
- ❌ Dependency on LangChain ecosystem

### ADR-002: Multi-Provider LLM Strategy

**Status**: Accepted
**Date**: December 2025
**Context**: Different LLMs excel at different tasks
**Decision**: Abstract LLM calls behind router interface
**Consequences**:
- ✅ Flexibility to optimize for cost/performance
- ✅ Resilience against provider outages
- ❌ Increased testing complexity

### ADR-003: Pinecone vs Self-Hosted Vector DB

**Status**: Accepted
**Date**: December 2025
**Context**: Need for scalable vector search
**Decision**: Use Pinecone Serverless
**Consequences**:
- ✅ Zero operational overhead
- ✅ Automatic scaling
- ❌ Vendor lock-in
- ❌ Higher cost at scale

### ADR-004: PostgreSQL JSONB for State Storage

**Status**: Accepted
**Date**: January 2026
**Context**: Need to store complex state objects
**Decision**: Use JSONB columns instead of NoSQL
**Consequences**:
- ✅ Single database technology
- ✅ ACID guarantees
- ✅ Queryable JSON with GIN indexes
- ❌ Less flexible than document DB

---

## Appendix: Key Metrics & SLAs

### Service Level Objectives (SLOs)

| Metric | Target |
|--------|--------|
| API Availability | 99.5% |
| Document Ingestion Success Rate | 99% |
| LLM Response Time (p95) | < 10s |
| End-to-End Workflow Completion | 95% |

### Monitoring & Observability

```python
# Structured logging example
import structlog

logger = structlog.get_logger()

logger.info(
    "node_executed",
    node_name="hypothesis_generator",
    project_id=state.project_id,
    execution_time_ms=123,
    hypotheses_generated=len(state.hypotheses)
)
```

### Key Performance Indicators (KPIs)

- Average time to generate interview script: < 5 minutes
- Average gap analysis accuracy: > 85% (validated against human review)
- User satisfaction score: > 4.5/5
- Cost per project analysis: < $20 (LLM API costs)

---

## Glossary

- **Consultant Graph**: The LangGraph state machine implementing the workflow
- **Human Breakpoint**: The pause point where interview transcript is required
- **Hypothesis**: A suspected inefficiency generated from document analysis
- **Gap Analysis**: Comparison of SOP (documented) vs reality (transcript)
- **RAG**: Retrieval-Augmented Generation - using vector search to provide LLM context
- **Namespace**: Pinecone's data isolation mechanism for multi-tenancy

---

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Pinecone Vector Database](https://www.pinecone.io/docs/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [APIC GitHub Repository](https://github.com/your-org/apic)

---

**Document Maintenance**
This document should be updated whenever architectural decisions change. Version history tracked in Git.
