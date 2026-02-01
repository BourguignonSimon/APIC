# APIC - Agentic Process Improvement Consultant

An autonomous multi-agent system that acts as a digital management consultant. APIC ingests corporate data, identifies operational inefficiencies, conducts "Human-in-the-Loop" validation via interview scripts, and generates actionable automation roadmaps.

**Core Philosophy:** "Reality-Grounded AI" — The system validates hypotheses through human feedback before recommending solutions, not hallucinating improvements based solely on theory.

## How It Works

APIC uses a State Graph architecture (LangGraph) with a critical "Human Breakpoint" for interview validation:

```
Upload Docs → Ingestion → Hypothesis Generation → Interview Script
                                                        ↓
                                            [HUMAN BREAKPOINT]
                                            Conduct Interview
                                                        ↓
                              Gap Analysis ← Submit Transcript
                                    ↓
                           Solution Architect
                                    ↓
                            Final PDF Report
```

**The 6 Workflow Nodes:**
1. **Ingestion** — Parse documents, store in vector database
2. **Hypothesis Generator** — Identify potential inefficiencies
3. **Interview Architect** — Create role-specific interview questions
4. **Gap Analyst** — Compare SOPs vs actual practice from transcript
5. **Solution Architect** — Map gaps to automation tools with ROI
6. **Reporting Engine** — Generate professional PDF deliverable

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- OpenAI API key or Anthropic API key
- Pinecone API key (optional, for vector storage)

### Installation

```bash
# Clone and enter directory
git clone https://github.com/your-org/apic.git
cd apic

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Running the Application

**Option 1: Direct Python**
```bash
# Terminal 1: API backend
python main.py api

# Terminal 2: Frontend
python main.py frontend
```

**Option 2: Docker Compose**
```bash
docker-compose up --build
```

### Access Points

| Service | URL |
|---------|-----|
| Frontend | http://localhost:8501 |
| API Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

## Usage Guide

### 1. Create a Project
Navigate to "New Project" and provide client name, project name, description, and target departments.

### 2. Upload Documents
Upload relevant documents (SOPs, process documentation, policy documents, training materials).

**Supported formats:** PDF, DOCX, DOC, TXT, PPTX, XLSX

### 3. Start Analysis
Click "Start Analysis" to ingest documents, generate hypotheses, and create a tailored interview script.

### 4. Conduct Interview
Use the generated interview script to interview key stakeholders. Export options: PDF, DOCX, Markdown.

### 5. Submit Transcript
Paste the interview transcript to resume analysis (gap analysis, solutions, ROI calculations).

### 6. Download Report
Access the final deliverable with executive summary, current vs future state comparison, and implementation roadmap.

## Technology Stack

| Component | Technology |
|-----------|------------|
| Orchestration | LangGraph (Python) |
| LLM Inference | GPT-4o / Claude 3.5 Sonnet |
| Backend API | FastAPI |
| Vector DB | Pinecone (Serverless) |
| Database | PostgreSQL |
| Frontend | Streamlit |

## API Overview

### Projects
- `POST /api/v1/projects` — Create project
- `GET /api/v1/projects` — List projects
- `GET /api/v1/projects/{id}` — Get project details

### Documents
- `POST /api/v1/projects/{id}/documents` — Upload documents
- `GET /api/v1/projects/{id}/documents` — List documents

### Workflow
- `POST /api/v1/workflow/start` — Start analysis (runs to interview breakpoint)
- `POST /api/v1/workflow/resume` — Resume with transcript
- `GET /api/v1/workflow/{id}/status` — Get workflow status
- `GET /api/v1/workflow/{id}/interview-script` — Get interview script
- `GET /api/v1/workflow/{id}/report` — Get final report

Full API documentation available at `/docs` when running the server.

## Agent Configuration

Configure each agent with custom models and prompts in `config/agents.yaml`:

```yaml
agents:
  hypothesis:
    model:
      provider: "openai"
      model: "gpt-4o"
      temperature: 0.7

  reporting:
    model:
      provider: "anthropic"
      model: "claude-3-5-sonnet-20241022"
      temperature: 0.5
```

**Available agents:** `ingestion`, `hypothesis`, `interview`, `gap_analyst`, `solution`, `reporting`

## Project Structure

```
apic/
├── config/
│   └── settings.py          # Configuration management
├── src/
│   ├── agents/              # Workflow nodes (ingestion, hypothesis, etc.)
│   ├── api/                 # FastAPI application and routes
│   ├── models/              # Pydantic schemas
│   ├── services/            # Workflow orchestration, state management
│   └── utils/               # Helpers, logging
├── frontend/
│   └── app.py               # Streamlit application
├── tests/                   # Test suite
├── uploads/                 # Document uploads
├── reports/                 # Generated reports
├── main.py                  # Entry point
├── requirements.txt
└── docker-compose.yml
```

## Development

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Code Style

```bash
# Format code
black src/ tests/

# Type checking
mypy src/
```

### Key Data Models

```python
# Interview Script (Node 3 output)
class InterviewScript(BaseModel):
    project_id: str
    target_departments: List[str]
    questions: List[Dict]  # role, question, intent, follow_ups

# Gap Analysis Result (Node 4/5 output)
class AnalysisResult(BaseModel):
    process_step: str
    observed_behavior: str
    pain_point_severity: Literal["Low", "Medium", "High"]
    proposed_solution: str
    tech_stack_recommendation: List[str]
    estimated_roi_hours: int
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
