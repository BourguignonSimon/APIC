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

## Usage Guide

### 1. Create a Project

Navigate to "New Project" and provide:
- Client name
- Project name
- Description
- Target departments

### 2. Upload Documents

Upload relevant documents:
- Standard Operating Procedures (SOPs)
- Process documentation
- Policy documents
- Training materials

Supported formats: PDF, DOCX, DOC, TXT, PPTX, XLSX

### 3. Start Analysis

Click "Start Analysis" to:
- Ingest and process documents
- Generate hypotheses about inefficiencies
- Create a tailored interview script

### 4. Conduct Interview

Use the generated interview script to:
- Interview key stakeholders
- Capture actual processes and pain points
- Document workarounds and hidden processes

### 5. Submit Transcript

Paste the interview transcript to resume analysis:
- Gap analysis (SOP vs Reality)
- Solution recommendations
- ROI calculations

### 6. Download Report

Access the final deliverable:
- Executive summary
- Current vs Future state comparison
- Implementation roadmap
- PDF report

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
