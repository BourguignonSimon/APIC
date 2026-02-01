# APIC - Agentic Process Improvement Consultant

An autonomous multi-agent system designed to act as a digital management consultant. APIC ingests corporate data, identifies operational inefficiencies, conducts "Human-in-the-Loop" validation via interview scripts, and generates actionable automation roadmaps.

## Core Philosophy

**"Reality-Grounded AI"** - The system does not hallucinate improvements based solely on theory; it validates hypotheses through human feedback before solutioning.

## Architecture: The Consultant Graph

APIC uses a **State Graph architecture** implemented with LangGraph, enabling complex workflows with a critical "Human Breakpoint" for interview validation.

```
                    ┌─────────────────┐
                    │  Upload Docs    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Node 1:        │
                    │  Ingestion      │
                    │  (RAG)          │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Node 2:        │
                    │  Hypothesis     │
                    │  Generator      │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Node 3:        │
                    │  Interview      │
                    │  Architect      │
                    └────────┬────────┘
                             │
              ╔══════════════╧══════════════╗
              ║   HUMAN BREAKPOINT          ║
              ║   (Conduct Interview)       ║
              ╚══════════════╤══════════════╝
                             │
                    ┌────────▼────────┐
                    │  Node 4:        │
                    │  Gap Analyst    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Node 5:        │
                    │  Solution       │
                    │  Architect      │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Node 6:        │
                    │  Reporting      │
                    │  Engine         │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Final Report   │
                    │  (PDF)          │
                    └─────────────────┘
```

## Features

- **Document Ingestion**: Parse PDFs, DOCX, TXT, PPTX files and store in vector database
- **Hypothesis Generation**: AI-powered analysis to identify potential inefficiencies
- **Interview Script Generation**: Dynamic, role-specific questions based on hypotheses
- **Gap Analysis**: Compare documented procedures (SOPs) vs actual practice
- **Solution Recommendations**: Map gaps to automation tools with ROI estimates
- **Professional Reports**: Generate comprehensive PDF deliverables

## Technology Stack

| Component | Technology |
|-----------|------------|
| Orchestration | LangGraph (Python) |
| LLM Inference | GPT-4o / Claude 3.5 Sonnet |
| Backend API | FastAPI |
| Vector DB | Pinecone (Serverless) |
| Database | PostgreSQL |
| Frontend | Streamlit (MVP) |

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- OpenAI API key or Anthropic API key
- Pinecone API key (optional, for vector storage)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/apic.git
cd apic
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

5. Initialize database:
```bash
# Ensure PostgreSQL is running
# The tables will be created automatically on first run
```

### Running the Application

#### Option 1: Direct Python

Run the API backend:
```bash
python main.py api
```

In a separate terminal, run the frontend:
```bash
python main.py frontend
```

#### Option 2: Docker Compose

```bash
docker-compose up --build
```

### Access the Application

- **Frontend**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health

## Usage Guide - The 5-Step Process

### Step 1: Document

Upload all available source data about the company:
- Company documents (SOPs, manuals, policies)
- Website content and public information
- Process documentation and training materials
- Any materials provided by the client

Supported formats: PDF, DOCX, DOC, TXT, PPTX, XLSX

### Step 2: Interview (Agent Analysis)

Click "Start Analysis" to have AI agents:
- Analyze all uploaded source documents
- Generate hypotheses about inefficiencies
- Create a tailored interview script for the customer

### Step 3: Interview Script

Review and use the generated interview script:
- Role-specific questions for stakeholder interviews
- Follow-up prompts for deeper insights
- Conduct real interviews with the customer

### Step 4: Results

Add interview results and generate analysis:
- Submit interview transcripts and notes
- Add any additional documents from interviews
- AI generates gap analysis and solution recommendations
- View ROI estimates and priority matrix

### Step 5: Report

Access the final deliverable:
- Executive summary with key metrics
- Current vs Future state comparison
- Implementation roadmap
- Download professional PDF report

## Agent Configuration

APIC allows you to configure each agent individually with custom models and prompts. This enables you to:

- **Use different LLM providers** for different agents (OpenAI, Anthropic, Google)
- **Optimize costs** by using faster models for simple tasks and premium models for complex analysis
- **Customize prompts** to match your specific use case or industry
- **Fine-tune model parameters** like temperature and token limits per agent

### Configuration File

Create or edit `config/agents.yaml` to configure agents:

```yaml
version: "1.0"

agents:
  hypothesis:
    model:
      provider: "openai"
      model: "gpt-4o"
      temperature: 0.7
    prompts:
      system: "You are an expert management consultant..."

  reporting:
    model:
      provider: "anthropic"
      model: "claude-3-5-sonnet-20241022"
      temperature: 0.5
```

### Available Agents

- `ingestion` - Document processing and summarization
- `hypothesis` - Inefficiency identification
- `interview` - Interview script generation
- `gap_analyst` - SOP vs reality comparison
- `solution` - Solution recommendations
- `reporting` - Report generation

### Example: Budget-Conscious Setup

```yaml
agents:
  ingestion:
    model:
      provider: "openai"
      model: "gpt-4o-mini"  # Fast, cheap for document processing

  reporting:
    model:
      provider: "anthropic"
      model: "claude-3-5-sonnet-20241022"  # Premium for final report
```

For detailed configuration options, see [Agent Configuration Guide](docs/AGENT_CONFIGURATION.md).

## API Endpoints

### Projects
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects` - List projects
- `GET /api/v1/projects/{id}` - Get project details

### Documents
- `POST /api/v1/projects/{id}/documents` - Upload documents
- `GET /api/v1/projects/{id}/documents` - List documents

### Workflow
- `POST /api/v1/workflow/start` - Start analysis
- `POST /api/v1/workflow/resume` - Resume with transcript
- `GET /api/v1/workflow/{id}/status` - Get workflow status
- `GET /api/v1/workflow/{id}/interview-script` - Get interview script
- `GET /api/v1/workflow/{id}/report` - Get final report

## Project Structure

```
apic/
├── config/
│   ├── __init__.py
│   └── settings.py          # Configuration management
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py           # Base agent class
│   │   ├── ingestion.py      # Node 1: Document ingestion
│   │   ├── hypothesis.py     # Node 2: Hypothesis generation
│   │   ├── interview.py      # Node 3: Interview architect
│   │   ├── gap_analyst.py    # Node 4: Gap analysis
│   │   ├── solution.py       # Node 5: Solution architect
│   │   └── reporting.py      # Node 6: Report generation
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI application
│   │   └── routes/
│   │       ├── projects.py   # Project endpoints
│   │       ├── documents.py  # Document endpoints
│   │       └── workflow.py   # Workflow endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py        # Pydantic models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── workflow.py       # LangGraph orchestration
│   │   └── state_manager.py  # State persistence
│   └── utils/
│       ├── __init__.py
│       ├── helpers.py        # Utility functions
│       └── logging_config.py # Logging setup
├── frontend/
│   └── app.py                # Streamlit application
├── tests/
├── uploads/                  # Document uploads
├── reports/                  # Generated reports
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── main.py                   # Entry point
├── requirements.txt
└── README.md
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Style

```bash
# Format code
black src/ tests/

# Type checking
mypy src/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details.

## Support

For issues and feature requests, please open a GitHub issue.

---

# Technical Deep Dive

## API Reference

### Complete API Routes & Payloads

All API routes use prefix `/api/v1` except health/root endpoints. Full OpenAPI documentation available at `/docs`.

#### Health & Root

**GET /health**
```json
Response 200:
{
  "status": "healthy",
  "service": "APIC API",
  "version": "1.0.0"
}
```

**GET /**
```json
Response 200:
{
  "message": "Welcome to APIC - Agentic Process Improvement Consultant",
  "docs": "/docs",
  "version": "1.0.0"
}
```

#### Projects API

**POST /api/v1/projects** - Create consulting project
```json
Request:
{
  "client_name": "Acme Corporation",      // required
  "project_name": "Finance Automation",    // required
  "description": "Analyze invoice processing",
  "target_departments": ["Finance", "Accounting"]
}

Response 201:
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "client_name": "Acme Corporation",
  "project_name": "Finance Automation",
  "description": "Analyze invoice processing",
  "target_departments": ["Finance", "Accounting"],
  "status": "created",
  "vector_namespace": null,
  "thread_id": null,
  "created_at": "2024-01-15T14:30:22Z",
  "updated_at": null
}
```

**GET /api/v1/projects** - List all projects
```json
Response 200:
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "client_name": "Acme Corporation",
    "project_name": "Finance Automation",
    "status": "created",
    "created_at": "2024-01-15T14:30:22Z"
  }
]
```

**GET /api/v1/projects/{project_id}** - Get project details
```json
Response 200: Same as POST /api/v1/projects response
Response 404: {"detail": "Project not found"}
```

**GET /api/v1/projects/suspended** - Get projects awaiting human input
```json
Response 200:
[
  {
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "thread_id": "thread-abc123",
    "project_name": "Finance Automation",
    "client_name": "Acme Corporation",
    "current_node": "interview",
    "suspension_reason": "Awaiting interview transcript",
    "suspended_at": "2024-01-15T15:45:00Z"
  }
]
```

**PATCH /api/v1/projects/{project_id}/status?status={status}** - Update status
```json
Response 200: {"message": "Project status updated to analyzing"}
```

#### Documents API

**POST /api/v1/projects/{project_id}/documents** - Upload documents
```
Request (multipart/form-data):
  files: [File, File, ...]  // PDF, DOCX, TXT, PPTX, XLSX (max 50MB each)

Response 201:
{
  "message": "Successfully uploaded 2 document(s)",
  "documents": [
    {
      "id": "doc-uuid-123",
      "project_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "sop_manual.pdf",
      "file_type": "pdf",
      "file_size": 2048576,
      "processed": false,
      "chunk_count": 0,
      "uploaded_at": "2024-01-15T14:35:00Z"
    }
  ]
}
```

**GET /api/v1/projects/{project_id}/documents** - List documents
```json
Response 200:
{
  "documents": [...],  // Same structure as upload response
  "total_count": 2
}
```

**DELETE /api/v1/projects/{project_id}/documents/{document_id}**
```
Response 204: No Content
Response 404: {"detail": "Document not found"}
```

#### Workflow API

**POST /api/v1/workflow/start** - Start analysis workflow
```json
Request:
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000"
}

Response 202:
{
  "message": "Analysis complete. Interview script generated. Awaiting transcript.",
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "thread_id": "thread-abc123",
  "status": "suspended",
  "interview_script": {
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "target_departments": ["Finance"],
    "target_roles": ["Finance Manager", "AP Clerk"],
    "introduction": "This interview will help us understand...",
    "questions": [
      {
        "role": "Finance Manager",
        "question": "How do you currently track invoice approvals?",
        "intent": "Understand approval workflow",
        "follow_ups": ["What happens when approvers are unavailable?"],
        "related_hypothesis_id": "hyp-uuid-456"
      }
    ],
    "closing_notes": "Thank you for your time...",
    "estimated_duration_minutes": 45,
    "generated_at": "2024-01-15T15:45:00Z"
  }
}
```

**POST /api/v1/workflow/resume** - Resume with transcript
```json
Request:
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "transcript": "Interview with John Smith, Finance Manager..."
}

Response 202:
{
  "message": "Analysis resumed and completed. Report generated.",
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed"
}
```

**GET /api/v1/workflow/{project_id}/status** - Get workflow status
```json
Response 200:
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "thread_id": "thread-abc123",
  "current_node": "interview",
  "is_suspended": true,
  "suspension_reason": "Awaiting interview transcript",
  "messages": ["Ingestion complete", "Hypotheses generated"],
  "errors": []
}
```

**GET /api/v1/workflow/{project_id}/interview-script** - Get interview script
```json
Response 200:
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "interview_script": { /* Same structure as /workflow/start */ },
  "target_roles": ["Finance Manager", "AP Clerk"],
  "estimated_duration_minutes": 45
}
```

**GET /api/v1/workflow/{project_id}/hypotheses** - Get generated hypotheses
```json
Response 200:
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "hypotheses": [
    {
      "id": "hyp-uuid-456",
      "process_area": "Invoice Processing",
      "description": "Manual data entry causing 2-3 day delays",
      "evidence": ["SOP mentions manual entry", "No automation tools listed"],
      "indicators": ["manual", "delay", "data entry"],
      "confidence": 0.85,
      "category": "manual_process"
    }
  ],
  "count": 5
}
```

**GET /api/v1/workflow/{project_id}/gaps** - Get gap analysis
```json
Response 200:
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "gap_analyses": [
    {
      "id": "gap-uuid-789",
      "process_step": "Invoice Approval",
      "sop_description": "Invoices approved within 24 hours",
      "observed_behavior": "Actual approval takes 3-5 days due to email delays",
      "gap_description": "2-4 day delay in approval process",
      "root_cause": "Manual email-based approval chain",
      "impact": "Cash flow delays, late payment fees",
      "task_category": "Automatable"
    }
  ],
  "count": 8
}
```

**GET /api/v1/workflow/{project_id}/solutions** - Get recommendations
```json
Response 200:
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "solutions": [
    {
      "process_step": "Invoice Approval",
      "observed_behavior": "Email-based approval taking 3-5 days",
      "pain_point_severity": "High",
      "proposed_solution": "Implement automated approval workflow with notifications",
      "tech_stack_recommendation": ["Power Automate", "ServiceNow", "Zapier"],
      "estimated_roi_hours": 160,
      "implementation_complexity": "Medium",
      "priority_score": 85.5
    }
  ],
  "recommendations": [
    {
      "id": "rec-uuid-012",
      "gap_id": "gap-uuid-789",
      "solution_name": "Automated Invoice Approval System",
      "solution_description": "Deploy workflow automation to route invoices...",
      "technology_stack": ["Power Automate", "SharePoint"],
      "implementation_steps": [
        "Configure Power Automate flows",
        "Set up approval routing logic",
        "Integrate with accounting system"
      ],
      "estimated_effort_hours": 80,
      "estimated_cost_range": "$5,000 - $10,000",
      "estimated_monthly_savings": 1200.0,
      "payback_period_months": 0.6,
      "risks": ["User adoption challenges", "Integration complexity"],
      "prerequisites": ["SharePoint access", "Power Automate license"]
    }
  ],
  "count": 6
}
```

**GET /api/v1/workflow/{project_id}/report** - Get final report
```json
Response 200:
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "report_pdf_path": "/reports/acme_corporation_20240115_160000.pdf",
  "report": {
    "id": "report-uuid-345",
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Process Improvement Analysis - Acme Corporation",
    "executive_summary": {
      "overview": "Analysis identified 8 automation opportunities...",
      "key_findings": [
        "Invoice processing has 3-5 day delays",
        "Manual data entry creates bottlenecks"
      ],
      "top_recommendations": [
        "Implement automated approval workflow",
        "Deploy OCR for invoice scanning"
      ],
      "total_potential_savings": 14400.0,
      "total_implementation_cost": 7500.0,
      "overall_roi_percentage": 92.0
    },
    "hypotheses": [...],
    "interview_insights": [
      "AP team spends 20 hours/week on manual entry",
      "Email approval chains cause visibility issues"
    ],
    "gap_analyses": [...],
    "solutions": [...],
    "current_vs_future": [
      {
        "process_area": "Invoice Approval",
        "current_state": "Manual email-based approval (3-5 days)",
        "future_state": "Automated workflow with instant notifications",
        "improvement_description": "Reduce approval time by 80%, save 160 hours/month"
      }
    ],
    "implementation_roadmap": [
      {
        "phase": "Quick Wins",
        "initiatives": [...]
      }
    ],
    "appendix": null,
    "generated_at": "2024-01-15T16:00:00Z"
  },
  "status": "completed"
}
```

#### Status Codes Summary

| Status | Meaning |
|--------|---------|
| 200 | OK - Request successful |
| 201 | Created - Resource created |
| 202 | Accepted - Async operation started |
| 204 | No Content - Successful deletion |
| 400 | Bad Request - Invalid input |
| 404 | Not Found - Resource doesn't exist |
| 500 | Server Error - Internal error |

#### Implementation Files

- `/src/api/main.py` - FastAPI app setup
- `/src/api/routes/projects.py` - Project endpoints
- `/src/api/routes/documents.py` - Document endpoints
- `/src/api/routes/workflow.py` - Workflow endpoints
- `/src/models/schemas.py` - Request/response models

---

## Database Schema

### Overview

**Database**: PostgreSQL 15+
**Schema File**: `/scripts/init_schema.sql`
**ORM Models**: `/src/services/state_manager.py`

### Tables

#### 1. `projects` - Project Metadata

Stores client project information and workflow status.

```sql
CREATE TABLE projects (
    id VARCHAR(36) PRIMARY KEY,
    client_name VARCHAR(255) NOT NULL,
    project_name VARCHAR(255) NOT NULL,
    description TEXT,
    target_departments JSONB DEFAULT '[]'::jsonb,
    status VARCHAR(50) CHECK (status IN (
        'created', 'ingesting', 'analyzing', 'interview_ready',
        'awaiting_transcript', 'processing_transcript', 'solutioning',
        'reporting', 'completed', 'failed'
    )),
    vector_namespace VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_client_name ON projects(client_name);
CREATE INDEX idx_projects_created_at ON projects(created_at);
```

**Columns:**
- `id`: UUID v4 primary key
- `client_name`: Organization name
- `project_name`: Project identifier
- `description`: Optional project description
- `target_departments`: JSONB array of department names
- `status`: Workflow state (enum constrained)
- `vector_namespace`: Pinecone namespace for data isolation
- `created_at`: Auto-generated creation timestamp
- `updated_at`: Auto-updated via trigger

#### 2. `project_states` - Workflow State Persistence

Stores complete LangGraph workflow state for checkpoint/resume capability.

```sql
CREATE TABLE project_states (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) UNIQUE NOT NULL,
    thread_id VARCHAR(36) UNIQUE NOT NULL,
    state_data JSONB NOT NULL,
    current_node VARCHAR(50) NOT NULL,
    is_suspended BOOLEAN DEFAULT FALSE,
    suspension_reason VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX idx_project_states_project_id ON project_states(project_id);
CREATE INDEX idx_project_states_is_suspended ON project_states(is_suspended);
CREATE INDEX idx_project_states_current_node ON project_states(current_node);
```

**Columns:**
- `id`: UUID v4 primary key
- `project_id`: Foreign key to projects (CASCADE delete)
- `thread_id`: LangGraph thread identifier
- `state_data`: Full GraphState serialized as JSONB
- `current_node`: Current workflow node (ingestion, hypothesis, interview, etc.)
- `is_suspended`: Whether workflow is paused at human breakpoint
- `suspension_reason`: Why workflow is suspended (e.g., "Awaiting interview transcript")
- Timestamps auto-managed by triggers

#### 3. `documents` - Uploaded Document Metadata

Tracks uploaded files and processing status.

```sql
CREATE TABLE documents (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) NOT NULL,
    filename VARCHAR(255),
    file_type VARCHAR(50) CHECK (file_type IN ('pdf', 'docx', 'doc', 'txt', 'pptx', 'xlsx')),
    file_size VARCHAR(50),
    file_path VARCHAR(500),
    chunk_count VARCHAR(50),
    processed BOOLEAN DEFAULT FALSE,
    content_summary TEXT,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX idx_documents_project_id ON documents(project_id);
CREATE INDEX idx_documents_file_type ON documents(file_type);
CREATE INDEX idx_documents_processed ON documents(processed);
```

**Columns:**
- `id`: UUID v4 primary key
- `project_id`: Foreign key to projects (CASCADE delete)
- `filename`: Original uploaded filename
- `file_type`: File extension (enum constrained)
- `file_size`: Size in bytes
- `file_path`: Local filesystem path
- `chunk_count`: Number of chunks after text splitting
- `processed`: Whether document has been ingested
- `content_summary`: LLM-generated summary
- `uploaded_at`: Upload timestamp

### Relationships

```
projects (1) ──< (many) documents
    │
    └──< (1) project_states
```

- One project has many documents (CASCADE delete)
- One project has one state record (CASCADE delete)
- Deleting a project removes all associated data

### Auto-Update Triggers

Both `projects` and `project_states` tables have triggers to update `updated_at`:

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Connection Configuration

Database URL format (`.env`):
```bash
DATABASE_URL=postgresql://user:password@host:port/database
# Default: postgresql://postgres:postgres@localhost:5432/apic
```

### Initialization

```bash
# Initialize schema
python scripts/init_db.py

# Or via Docker Compose
docker-compose up -d postgres
```

The `StateManager` class (`/src/services/state_manager.py`) provides:
- `create_project()` - Insert new project
- `save_state()` - Persist workflow state
- `load_state()` - Retrieve state for resumption
- `get_suspended_projects()` - Query projects at human breakpoint
- `update_project_status()` - Update workflow status

---

## Document Ingestion Deep Dive

### Overview

Ingestion is **Node 1** in the workflow, implemented in `/src/agents/ingestion.py`.

### Chunking Strategy

**Implementation**: RecursiveCharacterTextSplitter from LangChain

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

self.text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,          # Max characters per chunk
    chunk_overlap=200,        # Overlap between chunks
    length_function=len,
    separators=["\n\n", "\n", ". ", " ", ""]  # Hierarchical splitting
)
```

**Parameters:**
- **Chunk Size**: 1000 characters
  - Optimized for semantic coherence
  - Fits within embedding context windows
  - Balances granularity vs context
- **Overlap**: 200 characters
  - Maintains context across chunk boundaries
  - Prevents information loss at split points
  - Enables better semantic search recall
- **Separators**: Hierarchical preference
  1. Paragraph breaks (`\n\n`)
  2. Line breaks (`\n`)
  3. Sentence endings (`. `)
  4. Word boundaries (` `)
  5. Characters (fallback)

**Why This Approach?**
- Preserves semantic meaning by preferring natural boundaries
- Overlap ensures concepts spanning chunks aren't lost
- 1000 chars ≈ 250 tokens, well within embedding limits

### Embeddings Generation

**Model**: OpenAI `text-embedding-3-small`

```python
from langchain_openai import OpenAIEmbeddings

self.embeddings = OpenAIEmbeddings(
    api_key=settings.OPENAI_API_KEY,
    model="text-embedding-3-small",
)
```

**Specifications:**
- **Dimensions**: 1536
- **Cost**: $0.00002 per 1K tokens
- **Max Tokens**: 8191 per request
- **Similarity Metric**: Cosine similarity
- **Generation**: Automatic during Pinecone storage

### Metadata Handling

Each chunk includes rich metadata for filtering and traceability:

```python
from langchain.schema import Document as LCDocument

LCDocument(
    page_content=chunk,
    metadata={
        "document_id": doc.id,           # UUID of source document
        "project_id": doc.project_id,    # Client project namespace
        "filename": doc.filename,        # Original filename
        "file_type": doc.file_type,      # pdf, docx, txt, pptx, xlsx
        "chunk_index": i,                # Position in document (0-based)
        "chunk_hash": hashlib.md5(chunk.encode()).hexdigest()  # Content hash
    }
)
```

**Metadata Usage:**
- `project_id`: Enables multi-tenancy filtering
- `document_id`: Traces chunks back to source
- `chunk_index`: Reconstructs document order
- `chunk_hash`: Deduplication and change detection

### Complete Ingestion Pipeline

**File Location**: `/src/agents/ingestion.py:process()`

**Step 1: Document Parsing** (`_parse_*()` methods)

Supported formats with specialized parsers:

| Format | Library | Method |
|--------|---------|--------|
| PDF | pypdf | `_parse_pdf()` |
| DOCX/DOC | python-docx | `_parse_docx()` |
| TXT | Built-in | Direct read |
| PPTX | python-pptx | `_parse_pptx()` |
| XLSX | openpyxl | `_parse_excel()` |

```python
async def _parse_pdf(self, file_path: str) -> str:
    with open(file_path, "rb") as f:
        reader = PdfReader(f)
        text = "\n\n".join(page.extract_text() for page in reader.pages)
    return text
```

**Step 2: Text Chunking**

```python
chunks = self.text_splitter.split_text(raw_text)
chunk_docs = [
    LCDocument(page_content=chunk, metadata={...})
    for i, chunk in enumerate(chunks)
]
```

**Step 3: Summary Generation** (LLM-powered)

```python
summary_prompt = ChatPromptTemplate.from_messages([
    ("system", "Summarize this document, focusing on processes, inefficiencies, and pain points."),
    ("user", "{content}")
])

summary = await self.llm.ainvoke(
    summary_prompt.format(content=truncated_text[:10000])
)
```

Summaries stored in `documents.content_summary` for quick context retrieval.

**Step 4: Vector Storage** (Pinecone)

```python
from langchain_pinecone import PineconeVectorStore

vector_store = PineconeVectorStore.from_documents(
    documents=chunk_docs,
    embedding=self.embeddings,
    index_name="apic-knowledge",
    namespace=f"client_{project_id}"
)
```

**Pinecone Configuration:**
- **Index**: `apic-knowledge` (created if missing)
- **Dimensions**: 1536 (matches embedding model)
- **Metric**: Cosine similarity
- **Namespace**: `client_{project_id}` for data isolation
- **Type**: Serverless (auto-scaling)

**Step 5: Metadata Updates**

```python
await state_manager.update_document(
    document_id=doc.id,
    updates={
        "chunk_count": len(chunks),
        "processed": True,
        "content_summary": summary
    }
)
```

### Knowledge Base Querying

After ingestion, other agents query the knowledge base:

```python
def query_knowledge_base(self, query: str, project_id: str, top_k: int = 5):
    vector_store = PineconeVectorStore(
        index_name="apic-knowledge",
        embedding=self.embeddings,
        namespace=f"client_{project_id}"
    )
    results = vector_store.similarity_search(query, k=top_k)
    return results
```

**Query Flow:**
1. Embed query using same embedding model
2. Search Pinecone namespace for top-k similar chunks
3. Return chunks with metadata for context

**Example Usage in Hypothesis Agent:**
```python
context_chunks = self.query_knowledge_base(
    query="manual processes and inefficiencies",
    project_id=state["project_id"],
    top_k=10
)
context = "\n\n".join(chunk.page_content for chunk in context_chunks)
```

### Configuration

**Environment Variables** (`.env`):
```bash
# Embeddings
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-3-small

# Vector Database
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=apic-knowledge

# Upload Settings
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=50
ALLOWED_EXTENSIONS=pdf,docx,doc,txt,pptx,xlsx
```

### Performance Metrics

For a typical 50-page PDF:
- **Parsing**: ~2-5 seconds
- **Chunking**: ~1 second (yields ~50-75 chunks)
- **Embedding**: ~5-10 seconds (parallel batch requests)
- **Pinecone Upload**: ~3-5 seconds
- **Summary Generation**: ~3-5 seconds
- **Total**: ~15-30 seconds per document

### Data Flow Diagram

```
Upload API
    ↓
[Validate] → Check file type/size
    ↓
[Store] → Save to /uploads/{project_id}/
    ↓
[Parse] → Extract text by file type
    ↓
[Chunk] → RecursiveCharacterTextSplitter (1000/200)
    ↓
[Metadata] → Add document_id, chunk_index, hash
    ↓
[Embed] → OpenAI text-embedding-3-small (1536d)
    ↓
[Pinecone] → Store in namespace client_{project_id}
    ↓
[Summary] → LLM generates content summary
    ↓
[Update DB] → Mark processed=true, save chunk_count
```

This architecture enables semantic search across ingested documents while maintaining strong multi-tenant isolation through Pinecone namespacing.

---

## Human Breakpoint Implementation

### Overview

The "Human-in-the-Loop" breakpoint is the core differentiator of APIC. It pauses the workflow at **Node 3 (Interview Architect)** to require human validation before proceeding with solution recommendations.

### Workflow Suspension Mechanism

**Implementation**: LangGraph conditional edges

**File**: `/src/services/workflow.py`

```python
builder.add_conditional_edges(
    "interview",
    self._should_wait_for_transcript,
    {
        "wait": END,         # Suspend execution
        "continue": "gap_analysis"  # Resume to next node
    }
)

def _should_wait_for_transcript(self, state: WorkflowState) -> str:
    if state.get("is_suspended") and not state.get("transcript_received"):
        logger.info("Workflow suspended - awaiting interview transcript")
        return "wait"
    return "continue"
```

### State Persistence

**Multi-Layer Persistence:**

1. **LangGraph Checkpoint Layer** (`MemorySaver`)
   - Stores intermediate node outputs
   - Thread-based state tracking
   - Enables exact breakpoint resumption

2. **PostgreSQL Database Layer** (`project_states` table)
   ```python
   state_manager.save_state(
       project_id=project_id,
       thread_id=thread_id,
       state_data={
           "interview_script": script,
           "is_suspended": True,
           "suspension_reason": "Awaiting interview transcript",
           "current_node": "interview",
           # ... all other workflow state
       }
   )
   ```

3. **State Fields for Breakpoint**
   ```python
   class GraphState(BaseModel):
       # ... other fields
       is_suspended: bool = False
       suspension_reason: Optional[str] = None
       transcript: Optional[str] = None
       transcript_received: bool = False
   ```

### Approval Gating Logic

**Endpoint**: `POST /api/v1/workflow/resume`

**File**: `/src/api/routes/workflow.py`

```python
# Verify workflow is suspended (approval gate)
current_state = state_manager.load_state(project_id)
if not current_state or not current_state.get("is_suspended"):
    raise HTTPException(
        status_code=400,
        detail="Workflow is not suspended. Cannot submit transcript."
    )

# Validate transcript content
if not transcript or len(transcript) < 50:
    raise HTTPException(
        status_code=400,
        detail="Transcript must be at least 50 characters."
    )

# Resume workflow
final_state = await consultant_graph.resume_with_transcript(
    thread_id=thread_id,
    transcript=transcript
)
```

### UI Forms (Streamlit Frontend)

**File**: `/frontend/app.py`

**Interview Script Display:**
```python
st.markdown("### Interview Script")
st.info(f"Estimated duration: {script.get('estimated_duration_minutes', 60)} minutes")
st.markdown(f"**Target Roles:** {', '.join(script.get('target_roles', []))}")

# Display questions by role
for question in script.get('questions', []):
    st.markdown(f"**Q ({question['role']})**: {question['question']}")
    st.caption(f"*Intent: {question['intent']}*")
    if question.get('follow_ups'):
        st.markdown("**Follow-ups:**")
        for fu in question['follow_ups']:
            st.markdown(f"  - {fu}")
```

**Transcript Submission Form:**
```python
transcript = st.text_area(
    "Paste the interview transcript here",
    height=300,
    placeholder="Enter the interview notes or transcript..."
)

if st.button("Submit Transcript and Continue", use_container_width=True):
    if not transcript:
        st.error("Please enter the interview transcript.")
    else:
        result = api_request(
            "POST",
            "/workflow/resume",
            json={
                "project_id": project_id,
                "transcript": transcript,
            },
        )
        if result:
            st.success("Transcript submitted! Analysis resuming...")
```

### Resumption Flow

**File**: `/src/services/workflow.py:resume_with_transcript()`

```python
async def resume_with_transcript(self, thread_id: str, transcript: str) -> Dict[str, Any]:
    config = {"configurable": {"thread_id": thread_id}}

    # Get current state from LangGraph checkpoint
    state_snapshot = self.workflow.get_state(config)
    current_state = dict(state_snapshot.values)

    # Update state with transcript
    current_state["transcript"] = transcript
    current_state["transcript_received"] = True
    current_state["is_suspended"] = False

    # Resume workflow from gap_analysis node
    final_state = await self.workflow.ainvoke(current_state, config)

    return dict(final_state)
```

### Complete Breakpoint Flow

```
┌─────────────────────────────────────────────────────────┐
│ Node 1: Ingestion → Node 2: Hypothesis → Node 3: Interview │
└──────────────────────────┬──────────────────────────────┘
                           │
                  ┌────────▼────────┐
                  │ Set Suspension  │
                  │ is_suspended=True│
                  │ current_node=    │
                  │ "interview"     │
                  └────────┬────────┘
                           │
                  ┌────────▼────────┐
                  │ Save to Database│
                  │ Return 202      │
                  │ ACCEPTED        │
                  └────────┬────────┘
                           │
                    [WAIT FOR HUMAN]
                           │
                  ┌────────▼────────┐
                  │ POST /resume    │
                  │ with transcript │
                  └────────┬────────┘
                           │
                  ┌────────▼────────┐
                  │ Validate:       │
                  │ - is_suspended? │
                  │ - transcript?   │
                  └────────┬────────┘
                           │
                  ┌────────▼────────┐
                  │ Load State      │
                  │ Update transcript│
                  │ is_suspended=   │
                  │ False           │
                  └────────┬────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│ Node 4: Gap Analysis → Node 5: Solution → Node 6: Report │
└─────────────────────────────────────────────────────────┘
```

### Project Status Transitions

**Enum**: `ProjectStatus` (`/src/models/schemas.py`)

```python
class ProjectStatus(str, Enum):
    CREATED = "created"
    INGESTING = "ingesting"
    ANALYZING = "analyzing"
    INTERVIEW_READY = "interview_ready"      # ← Breakpoint reached
    AWAITING_TRANSCRIPT = "awaiting_transcript"  # ← Alternative status
    PROCESSING_TRANSCRIPT = "processing_transcript"
    SOLUTIONING = "solutioning"
    REPORTING = "reporting"
    COMPLETED = "completed"
    FAILED = "failed"
```

### Monitoring Suspended Projects

**Endpoint**: `GET /api/v1/projects/suspended`

```python
@router.get("/projects/suspended")
async def get_suspended_projects():
    """Get all projects awaiting human input."""
    suspended = await state_manager.get_suspended_projects()
    return [
        {
            "project_id": s["project_id"],
            "thread_id": s["thread_id"],
            "project_name": s["project_name"],
            "client_name": s["client_name"],
            "current_node": s["current_node"],
            "suspension_reason": s["suspension_reason"],
            "suspended_at": s["updated_at"]
        }
        for s in suspended
    ]
```

### Key Features

1. **Graceful Suspension**: Workflow cleanly exits at breakpoint without errors
2. **State Preservation**: Full GraphState persisted to PostgreSQL JSONB
3. **Thread Resumption**: LangGraph MemorySaver maintains execution context
4. **Validation Gates**: API prevents resumption without proper transcript
5. **Audit Trail**: Timestamps and reasons tracked in database
6. **Multi-Project Support**: Multiple projects can be suspended simultaneously

### Implementation Files

- `/src/services/workflow.py` - Conditional edges, resumption logic
- `/src/services/state_manager.py` - Database persistence
- `/src/agents/interview.py` - Sets suspension flags
- `/src/agents/gap_analyst.py` - Consumes transcript on resume
- `/src/api/routes/workflow.py` - Approval gating endpoints
- `/frontend/app.py` - Interview display and transcript submission

---

## Final Report Structure & Customization

### Overview

The final deliverable is a professionally formatted PDF report generated by **Node 6 (Reporting Engine)**.

**File**: `/src/agents/reporting.py`

### PDF Generation Framework

**Library**: reportlab (primary), weasyprint (alternative)

```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
```

**Configuration:**
- Page size: Letter (8.5" × 11")
- Margins: 1 inch all sides
- Output: `/reports/{client_name}_{timestamp}.pdf`

### Report Data Structure

**Model**: `/src/models/schemas.py:Report`

```python
class Report(BaseModel):
    id: str
    project_id: str
    title: str
    executive_summary: ExecutiveSummary
    hypotheses: List[Hypothesis]
    interview_insights: List[str]
    gap_analyses: List[GapAnalysisItem]
    solutions: List[AnalysisResult]
    current_vs_future: List[CurrentVsFutureState]
    implementation_roadmap: List[Dict[str, Any]]
    appendix: Optional[Dict[str, Any]]
    generated_at: datetime
```

### Executive Summary Components

```python
class ExecutiveSummary(BaseModel):
    overview: str  # LLM-generated summary
    key_findings: List[str]  # Top 5 hypotheses by confidence
    top_recommendations: List[str]  # Top 5 solutions by priority
    total_potential_savings: float  # Annual savings ($)
    total_implementation_cost: float  # Total investment ($)
    overall_roi_percentage: float  # Calculated ROI
```

**Calculation Logic** (`/src/agents/reporting.py:_generate_executive_summary()`):
```python
total_monthly_savings = sum(
    rec.get("estimated_monthly_savings", 0)
    for rec in recommendations
)
total_annual_savings = total_monthly_savings * 12

# Parse cost ranges (e.g., "$5,000 - $10,000")
avg_cost = sum(parse_cost_range(rec["estimated_cost_range"]) for rec in recommendations) / len(recommendations)

roi_percentage = ((total_annual_savings - avg_cost) / avg_cost * 100) if avg_cost > 0 else 0
```

### Current vs Future State

```python
class CurrentVsFutureState(BaseModel):
    process_area: str
    current_state: str  # From SOP documentation
    future_state: str   # Proposed solution
    improvement_description: str  # Expected benefit
```

**Example:**
```json
{
  "process_area": "Invoice Approval",
  "current_state": "Manual email-based approval (3-5 days)",
  "future_state": "Automated workflow with instant notifications",
  "improvement_description": "Reduce approval time by 80%, save 160 hours/month"
}
```

### Implementation Roadmap

**Structure**: 3-phase approach (Quick Wins → Foundation → Transformation)

```python
roadmap = [
    {
        "phase": "Phase 1: Quick Wins (0-3 months)",
        "description": "Low-cost, high-ROI initiatives",
        "initiatives": [
            {
                "solution_name": "Automated Invoice Routing",
                "description": "Deploy email-based workflow...",
                "estimated_effort_hours": 40,
                "estimated_monthly_savings": 800
            }
        ]
    },
    {
        "phase": "Phase 2: Foundation (3-6 months)",
        "description": "Core infrastructure improvements",
        "initiatives": [...]
    },
    {
        "phase": "Phase 3: Transformation (6-12 months)",
        "description": "Strategic automation initiatives",
        "initiatives": [...]
    }
]
```

### PDF Report Sections

**Generated Layout** (`_generate_pdf()` method):

1. **Title Page**
   ```python
   title_style = ParagraphStyle(
       'CustomTitle',
       fontSize=24,
       spaceAfter=30,
   )
   story.append(Paragraph(f"Process Improvement Analysis - {client_name}", title_style))
   story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", normal_style))
   ```

2. **Executive Summary**
   - LLM-generated overview paragraph
   - Metrics table (4 rows):
     - Potential Annual Savings
     - Implementation Cost
     - Projected ROI (%)
     - Styled with grey header, beige data cells

3. **Key Findings**
   - Bulleted list of top 5 hypotheses
   - Sorted by confidence score

4. **Top Recommendations**
   - Bulleted list of top 5 solutions
   - Sorted by priority score

5. **Current vs Future State**
   - Comparative table for each gap (up to 10)
   - Shows process area, current state, future state, improvement

6. **Implementation Roadmap**
   - 3-phase breakdown
   - Each phase includes:
     - Phase name and description
     - Initiative list with effort and savings
     - Page breaks between phases

### Customization Options

#### 1. Styling Customization

**File**: `/src/agents/reporting.py` (lines 440-451)

```python
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=24,           # ← Customize font size
    spaceAfter=30,         # ← Customize spacing
    textColor=colors.navy  # ← Add custom colors
)

heading_style = ParagraphStyle(
    'CustomHeading',
    parent=styles['Heading2'],
    fontSize=16,
    spaceAfter=12,
)
```

**Table Styling:**
```python
table_style = TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),     # Header background
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), # Header text
    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),   # Data background
    ('GRID', (0, 0), (-1, -1), 1, colors.black),      # Grid lines
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
])
```

#### 2. Content Customization

**Number of Items:**
```python
# Top findings (default: 5)
top_findings = sorted(hypotheses, key=lambda x: x.confidence, reverse=True)[:5]

# Top recommendations (default: 5)
top_recs = sorted(solutions, key=lambda x: x.priority_score, reverse=True)[:5]

# Current vs Future (default: 10)
cv_future = self._generate_current_vs_future(gaps, solutions)[:10]
```

#### 3. Roadmap Phase Customization

**File**: `/src/agents/reporting.py:_generate_roadmap()`

```python
# Customize initiative counts per phase
quick_wins = high_roi_low_complexity[:3]   # Phase 1: 3 items
foundation = medium_initiatives[:4]         # Phase 2: 4 items
transformation = strategic_initiatives[:3]  # Phase 3: 3 items
```

#### 4. Prompt Customization

**LLM-Generated Summary:**
```python
summary_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a senior management consultant.
    Summarize this analysis in a professional, executive-level tone.
    Focus on business impact and ROI.
    Keep it to 3-4 sentences."""),
    ("user", "{analysis_data}")
])
```

Customize the system message to change tone, detail level, or focus areas.

### Template System

**Role-Based Interview Templates** (`/src/agents/interview.py`):
```python
ROLE_TEMPLATES = {
    "executive": {
        "focus_areas": ["strategic priorities", "business outcomes", "resource allocation"],
        "question_style": "high-level, strategic, outcome-focused",
    },
    "manager": {
        "focus_areas": ["team processes", "bottlenecks", "resource constraints"],
        "question_style": "operational, process-oriented, team-focused",
    },
    "operational": {
        "focus_areas": ["daily tasks", "pain points", "workarounds"],
        "question_style": "detailed, task-specific, practical",
    },
    "technical": {
        "focus_areas": ["systems", "integrations", "data flows"],
        "question_style": "technical, system-oriented, data-focused",
    },
}
```

These templates guide interview question generation to tailor the human breakpoint interaction.

### Report Assembly Process

**Workflow Integration** (`/src/services/workflow.py`):
```
Ingestion → Hypothesis → Interview → [HUMAN BREAKPOINT] → Gap Analysis → Solution → Reporting
                                                                                        ↓
                                                                                   Report.pdf
```

**Assembly Steps** (`/src/agents/reporting.py:process()`):

1. **Data Collection** - Extract hypotheses, gaps, solutions from workflow state
2. **Executive Summary** - Calculate metrics, generate LLM summary
3. **Current vs Future** - Map gaps to solutions, calculate improvements
4. **Roadmap Generation** - Organize solutions into 3 phases
5. **Interview Insights** - LLM extracts key points from transcript
6. **PDF Generation** - Build reportlab document, render to file

### Accessing Reports

**API Endpoint**: `GET /api/v1/workflow/{project_id}/report`

**Static File Serving**:
```python
# /src/api/main.py
app.mount("/reports", StaticFiles(directory=settings.REPORTS_DIR))
```

**Download URL**: `http://localhost:8000/reports/acme_corporation_20240115_160000.pdf`

### Configuration

**Environment Variables** (`.env`):
```bash
REPORTS_DIR=./reports
UPLOAD_DIR=./uploads
```

### Performance

Typical report generation time:
- Data assembly: ~1-2 seconds
- LLM summary generation: ~3-5 seconds
- PDF rendering: ~2-3 seconds
- **Total**: ~6-10 seconds

### Customization Examples

**Change Report Colors:**
```python
# Edit /src/agents/reporting.py
table_style = TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.blue),  # Blue header
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
])
```

**Add Custom Section:**
```python
# In _generate_pdf() method
story.append(Paragraph("Custom Analysis", heading_style))
story.append(Paragraph("Your custom content here...", normal_style))
story.append(Spacer(1, 0.2*inch))
```

**Modify Roadmap Phases:**
```python
# In _generate_roadmap() method
phases = [
    {"name": "Immediate (0-1 month)", "items": urgent_items},
    {"name": "Short-term (1-3 months)", "items": quick_wins},
    {"name": "Medium-term (3-6 months)", "items": foundation},
    {"name": "Long-term (6-12 months)", "items": transformation},
]
```

---

## Testing the LangGraph Workflow

### Overview

APIC uses **pytest** with async support and comprehensive mocking to enable deterministic testing without live LLM API calls.

### Test Framework

**Dependencies** (`requirements-dev.txt`):
```
pytest>=8.0.0
pytest-asyncio>=0.24.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0
```

**Run Tests:**
```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_workflow.py -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Async tests only
pytest tests/ -k "async" -v
```

### Test Fixtures

**Main Test File**: `/tests/test_workflow.py`

```python
@pytest.fixture
def graph(self):
    """Create a ConsultantGraph instance for testing."""
    with patch('src.services.workflow.StateManager'):
        return ConsultantGraph()

@pytest.fixture
def initial_state(self):
    """Create an initial graph state for testing."""
    return GraphState(
        project_id=str(uuid.uuid4()),
        client_name="Test Corp",
        project_name="Test Project",
        target_departments=["Finance"],
        documents=[],
        messages=[],
        errors=[],
    )
```

### Mocked LLM Responses

**Pattern**: `AsyncMock` with deterministic response content

**Example** (`/tests/test_agents.py`):
```python
@pytest.mark.asyncio
async def test_generate_hypotheses_returns_list(self, agent):
    """Test that hypothesis generation returns a list of Hypothesis objects."""
    with patch.object(agent, 'llm') as mock_llm:
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = '''[{
            "process_area": "Invoice Processing",
            "description": "Manual data entry causing delays",
            "evidence": ["Manual invoice entry"],
            "indicators": ["manual", "delay"],
            "confidence": 0.8,
            "category": "manual_process"
        }]'''
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        # Test agent method
        hypotheses = await agent._generate_hypotheses("summaries", "context")

        # Assertions
        assert isinstance(hypotheses, list)
        assert len(hypotheses) == 1
        assert hypotheses[0].process_area == "Invoice Processing"
        assert hypotheses[0].confidence == 0.8
```

### Deterministic Testing Strategies

**No Random Seeds Required** - All tests use:
1. **Fixed UUIDs**: `str(uuid.uuid4())` generates predictable test IDs
2. **Hardcoded Data**: Specific test values like "Test Corp", "Finance"
3. **Mocked Async Operations**: All LLM calls return predetermined values
4. **Controlled State**: GraphState initialized with known values

**Example Workflow Progression Test:**
```python
@pytest.mark.asyncio
async def test_workflow_progression_through_nodes(self, graph, initial_state):
    """Test that workflow progresses through all nodes."""
    state_dict = initial_state.model_dump()

    with patch('src.agents.ingestion.IngestionAgent') as mock_ingestion, \
         patch('src.agents.hypothesis.HypothesisGeneratorAgent') as mock_hypothesis, \
         patch('src.agents.interview.InterviewArchitectAgent') as mock_interview:

        # Mock Node 1: Ingestion
        mock_ingestion.return_value.process = AsyncMock(return_value={
            **state_dict,
            "ingestion_complete": True,
            "document_summaries": ["Summary 1"],
        })

        # Mock Node 2: Hypothesis
        mock_hypothesis.return_value.process = AsyncMock(return_value={
            **state_dict,
            "hypothesis_generation_complete": True,
            "hypotheses": [{"process_area": "Test", "confidence": 0.9}],
        })

        # Mock Node 3: Interview (reaches breakpoint)
        mock_interview.return_value.process = AsyncMock(return_value={
            **state_dict,
            "interview_script_ready": True,
            "is_suspended": True,
            "interview_script": {"questions": []},
        })

        # Run workflow
        result = await graph.run_to_breakpoint(initial_state.project_id)

        # Assert progression
        assert result["ingestion_complete"] is True
        assert result["hypothesis_generation_complete"] is True
        assert result["is_suspended"] is True
```

### Testing Utilities & Patterns

#### 1. Service Layer Mocking

**Database Mocking** (`/tests/test_workflow.py`):
```python
with patch.object(state_manager, 'db_pool') as mock_pool:
    # Mock async connection
    mock_conn = AsyncMock()
    mock_conn.fetchrow = AsyncMock(return_value={
        "project_id": "test-123",
        "client_name": "Test Corp",
        "status": "created"
    })

    # Mock async context managers
    mock_pool.acquire = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock()

    # Test database operations
    result = await state_manager.get_project("test-123")
    assert result["client_name"] == "Test Corp"
```

#### 2. API Endpoint Testing

**FastAPI TestClient** (`/tests/test_api.py`):
```python
from fastapi.testclient import TestClient
from src.api.main import create_app

@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    app = create_app()
    return TestClient(app)

def test_create_project_returns_201(self, client):
    """Test that creating a project returns 201 Created."""
    with patch('src.api.routes.projects.StateManager') as mock_sm:
        mock_instance = Mock()
        mock_instance.create_project = AsyncMock(return_value={
            "id": str(uuid.uuid4()),
            "client_name": "Test Corp",
            "project_name": "Test Project",
            "status": ProjectStatus.CREATED.value,
        })
        mock_sm.return_value = mock_instance

        response = client.post("/api/v1/projects", json={
            "client_name": "Test Corp",
            "project_name": "Test Project"
        })

        assert response.status_code == 201
        assert response.json()["client_name"] == "Test Corp"
```

#### 3. Agent-Level Testing

**Individual Agent Tests** (`/tests/test_agents.py`):
```python
@pytest.fixture
def agent(self):
    """Create an IngestionAgent instance for testing."""
    with patch('src.agents.base.get_llm') as mock_llm, \
         patch('src.agents.ingestion.OpenAIEmbeddings'):
        mock_llm.return_value = Mock()
        return IngestionAgent()

@pytest.mark.asyncio
async def test_process_returns_state_dict(self, agent, initial_state):
    """Test that process method returns a state dictionary."""
    with patch.object(agent, '_parse_document') as mock_parse, \
         patch.object(agent, '_chunk_document') as mock_chunk, \
         patch.object(agent, '_store_in_vector_db') as mock_store:

        mock_parse.return_value = "Document text content"
        mock_chunk.return_value = [Mock(page_content="chunk1")]
        mock_store.return_value = None

        result = await agent.process(initial_state.model_dump())

        assert isinstance(result, dict)
        assert "project_id" in result
        assert result["ingestion_complete"] is True
```

#### 4. State Management Testing

**State Persistence Tests**:
```python
@pytest.mark.asyncio
async def test_state_persistence_across_workflow_steps(self):
    """Test that state is properly persisted across workflow steps."""
    project_id = str(uuid.uuid4())

    with patch('src.services.state_manager.asyncpg'):
        state_manager = StateManager()

        state_data = {
            "project_id": project_id,
            "current_node": "ingestion",
            "messages": [],
        }

        with patch.object(state_manager, 'db_pool') as mock_pool:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock()
            mock_conn.fetchrow = AsyncMock(return_value={
                "project_id": project_id,
                "state_data": json.dumps(state_data),
            })
            mock_pool.acquire = AsyncMock(return_value=mock_conn)
            mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_pool.acquire.return_value.__aexit__ = AsyncMock()

            # Test save and load
            await state_manager.save_state(project_id, "thread-123", state_data)
            retrieved_state = await state_manager.load_state(project_id)

            assert retrieved_state is not None
            assert retrieved_state["project_id"] == project_id
```

#### 5. Error Handling Testing

**Graceful Error Handling**:
```python
@pytest.mark.asyncio
async def test_workflow_handles_errors_gracefully(self, graph, initial_state):
    """Test that workflow handles errors without crashing."""
    with patch.object(graph, 'state_manager') as mock_sm:
        mock_sm.load_state = AsyncMock(side_effect=Exception("Database error"))

        try:
            result = await graph.run_to_breakpoint(initial_state.project_id)
            # Should handle error gracefully
            assert "errors" in result
        except Exception as e:
            # If exception propagates, verify it's the expected one
            assert "Database error" in str(e)
```

### Key Testing Patterns

| Pattern | Purpose | Example |
|---------|---------|---------|
| **AsyncMock** | Mock async LLM/DB calls | `mock_llm.ainvoke = AsyncMock(return_value=response)` |
| **Fixture Reuse** | Share test state | `@pytest.fixture def initial_state():` |
| **Context Managers** | Scope mocks | `with patch('module.Class') as mock:` |
| **Async Markers** | Enable async tests | `@pytest.mark.asyncio` |
| **Deterministic Data** | Reproducible tests | Fixed strings, UUIDs |
| **State Validation** | Verify transitions | `assert state["is_suspended"] is True` |

### Mock LLM Response Examples

**Hypothesis Generation:**
```python
mock_response.content = '''[
    {
        "process_area": "Invoice Processing",
        "description": "Manual data entry",
        "evidence": ["SOP manual entry"],
        "indicators": ["manual", "delay"],
        "confidence": 0.85,
        "category": "manual_process"
    }
]'''
```

**Interview Script:**
```python
mock_response.content = '''{
    "target_roles": ["Manager", "Clerk"],
    "questions": [
        {
            "role": "Manager",
            "question": "How do you approve invoices?",
            "intent": "Understand approval workflow",
            "follow_ups": ["What delays occur?"]
        }
    ]
}'''
```

**Gap Analysis:**
```python
mock_response.content = '''[
    {
        "process_step": "Approval",
        "sop_description": "24 hour approval",
        "observed_behavior": "3-5 day delays",
        "gap_description": "2-4 day delay",
        "root_cause": "Email bottleneck",
        "impact": "Cash flow issues",
        "task_category": "Automatable"
    }
]'''
```

### Test Organization

```
tests/
├── __init__.py
├── test_workflow.py       # LangGraph workflow tests
├── test_agents.py         # Individual agent tests
├── test_api.py            # FastAPI endpoint tests
├── test_models.py         # Pydantic model validation tests
├── test_state_manager.py  # Database persistence tests
└── conftest.py            # Shared fixtures
```

### Coverage Goals

```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=html

# Target coverage
- Agents: 85%+ coverage
- API routes: 90%+ coverage
- State management: 90%+ coverage
- Models: 95%+ coverage (schema validation)
```

### Running Specific Test Suites

```bash
# Workflow tests only
pytest tests/test_workflow.py -v

# Agent tests only
pytest tests/test_agents.py -v

# API tests only
pytest tests/test_api.py -v

# Tests matching pattern
pytest tests/ -k "suspension" -v

# Fast tests (exclude slow integrations)
pytest tests/ -m "not slow" -v
```

### Best Practices

1. **Always mock LLM calls** - Never make real API requests in tests
2. **Use AsyncMock for async functions** - Ensures proper await handling
3. **Test state transitions** - Verify workflow moves through nodes correctly
4. **Test error paths** - Ensure graceful error handling
5. **Use fixtures for common setup** - Reduces code duplication
6. **Validate Pydantic models** - Test serialization/deserialization
7. **Test breakpoint logic** - Verify suspension and resumption

This testing strategy ensures reliable, fast, deterministic tests without incurring LLM API costs or dealing with non-deterministic LLM outputs.
