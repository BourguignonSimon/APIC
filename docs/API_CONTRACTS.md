# APIC API Contracts Documentation

This document provides comprehensive documentation for the APIC (Agentic Process Improvement Consultant) REST API contracts, including request/response models and integration guidelines for the web interface.

## Table of Contents

- [Overview](#overview)
- [Base URL](#base-url)
- [Authentication](#authentication)
- [Common Response Codes](#common-response-codes)
- [API Endpoints](#api-endpoints)
  - [Projects](#projects)
  - [Documents](#documents)
  - [Workflow](#workflow)
  - [Health](#health)
- [Data Models](#data-models)
- [Frontend Integration Guide](#frontend-integration-guide)
- [Error Handling](#error-handling)

---

## Overview

The APIC API provides RESTful endpoints for managing consulting projects, uploading documents, and orchestrating the multi-agent analysis workflow. The API follows standard REST conventions and uses JSON for request/response bodies.

**Technology Stack:**
- Framework: FastAPI
- Serialization: Pydantic v2
- Database: PostgreSQL
- Documentation: OpenAPI/Swagger (available at `/docs`)

---

## Base URL

```
Development: http://localhost:8000/api/v1
Production:  https://your-domain.com/api/v1
```

---

## Authentication

> **Note:** The current implementation does not include authentication. For production deployments, implement JWT or OAuth2 authentication.

---

## Common Response Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `201` | Created |
| `202` | Accepted (async operation started) |
| `204` | No Content (successful deletion) |
| `400` | Bad Request (validation error) |
| `404` | Not Found |
| `500` | Internal Server Error |

---

## API Endpoints

### Projects

#### Create Project

Creates a new consulting project.

```
POST /api/v1/projects
```

**Request Body:**
```json
{
  "client_name": "string (required)",
  "project_name": "string (required)",
  "description": "string (optional)",
  "target_departments": ["string"] (optional, default: [])
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "client_name": "string",
  "project_name": "string",
  "description": "string | null",
  "target_departments": ["string"],
  "status": "created",
  "vector_namespace": "client_{id}",
  "thread_id": "uuid | null",
  "created_at": "ISO 8601 datetime",
  "updated_at": "ISO 8601 datetime | null"
}
```

**Frontend Usage:**
```javascript
const response = await fetch(`${API_BASE_URL}/projects`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    client_name: 'Acme Corp',
    project_name: 'Q1 Process Optimization',
    description: 'Optional description',
    target_departments: ['Finance', 'Operations']
  })
});
```

---

#### List Projects

Returns all projects ordered by creation date (descending).

```
GET /api/v1/projects
```

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "client_name": "string",
    "project_name": "string",
    "status": "string",
    "created_at": "ISO 8601 datetime"
  }
]
```

**Status Values:**
- `created` - Project created, no documents
- `ingesting` - Documents being processed
- `analyzing` - Analysis in progress
- `interview_ready` - Interview script generated
- `awaiting_transcript` - Waiting for transcript
- `processing_transcript` - Processing transcript
- `solutioning` - Generating solutions
- `reporting` - Generating report
- `completed` - Workflow complete
- `failed` - Error occurred

---

#### Get Project Details

```
GET /api/v1/projects/{project_id}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "client_name": "string",
  "project_name": "string",
  "description": "string | null",
  "target_departments": ["string"],
  "status": "string",
  "vector_namespace": "string",
  "thread_id": "uuid | null",
  "created_at": "ISO 8601 datetime",
  "updated_at": "ISO 8601 datetime | null"
}
```

**Errors:**
- `404` - Project not found

---

#### Get Suspended Projects

Returns projects waiting at the human breakpoint (interview step).

```
GET /api/v1/projects/suspended
```

**Response:** `200 OK`
```json
[
  {
    "project_id": "uuid",
    "thread_id": "uuid",
    "project_name": "string",
    "client_name": "string",
    "current_node": "string",
    "suspension_reason": "string | null",
    "suspended_at": "ISO 8601 datetime"
  }
]
```

---

#### Update Project Status

```
PATCH /api/v1/projects/{project_id}/status?status={status}
```

**Query Parameters:**
- `status` (required): New status value

**Response:** `200 OK`
```json
{
  "message": "Project status updated to {status}"
}
```

**Errors:**
- `404` - Project not found

---

### Documents

#### Upload Documents

Upload one or more documents for analysis.

```
POST /api/v1/projects/{project_id}/documents
```

**Request:** `multipart/form-data`
- `files`: One or more files

**Supported File Types:**
- PDF (`.pdf`)
- Word Documents (`.docx`, `.doc`)
- Text Files (`.txt`)
- PowerPoint (`.pptx`)
- Excel (`.xlsx`)

**Maximum File Size:** 50MB per file

**Response:** `201 Created`
```json
{
  "message": "Successfully uploaded {n} document(s)",
  "documents": [
    {
      "id": "uuid",
      "project_id": "uuid",
      "filename": "string",
      "file_type": "string",
      "file_size": "integer (bytes)",
      "processed": false,
      "chunk_count": 0,
      "uploaded_at": "ISO 8601 datetime"
    }
  ]
}
```

**Frontend Usage:**
```javascript
const formData = new FormData();
files.forEach(file => formData.append('files', file));

const response = await fetch(
  `${API_BASE_URL}/projects/${projectId}/documents`,
  { method: 'POST', body: formData }
);
```

**Errors:**
- `400` - Invalid file type or file too large
- `404` - Project not found

---

#### List Documents

```
GET /api/v1/projects/{project_id}/documents
```

**Response:** `200 OK`
```json
{
  "documents": [
    {
      "id": "uuid",
      "project_id": "uuid",
      "filename": "string",
      "file_type": "string",
      "file_size": "integer",
      "processed": "boolean",
      "chunk_count": "integer",
      "uploaded_at": "ISO 8601 datetime"
    }
  ],
  "total_count": "integer"
}
```

---

#### Get Document Details

```
GET /api/v1/projects/{project_id}/documents/{document_id}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "project_id": "uuid",
  "filename": "string",
  "file_type": "string",
  "file_size": "integer",
  "processed": "boolean",
  "chunk_count": "integer",
  "uploaded_at": "ISO 8601 datetime"
}
```

---

#### Delete Document

```
DELETE /api/v1/projects/{project_id}/documents/{document_id}
```

**Response:** `204 No Content`

---

### Workflow

#### Start Analysis

Starts the analysis workflow. Processes documents through nodes 1-3 and suspends at the interview breakpoint.

```
POST /api/v1/workflow/start
```

**Request Body:**
```json
{
  "project_id": "uuid (required)"
}
```

**Response:** `202 Accepted`
```json
{
  "message": "Analysis complete. Interview script generated. Awaiting transcript.",
  "project_id": "uuid",
  "thread_id": "uuid",
  "status": "suspended",
  "interview_script": {
    "project_id": "uuid",
    "target_departments": ["string"],
    "target_roles": ["string"],
    "introduction": "string",
    "questions": [
      {
        "role": "string",
        "question": "string",
        "intent": "string",
        "follow_ups": ["string"],
        "related_hypothesis_id": "uuid | null"
      }
    ],
    "closing_notes": "string",
    "estimated_duration_minutes": "integer",
    "generated_at": "ISO 8601 datetime"
  }
}
```

**Errors:**
- `400` - No documents uploaded
- `404` - Project not found
- `500` - Analysis failed

---

#### Resume Workflow with Transcript

Submits the interview transcript and resumes analysis (nodes 4-6).

```
POST /api/v1/workflow/resume
```

**Request Body:**
```json
{
  "project_id": "uuid (required)",
  "transcript": "string (required)"
}
```

**Response:** `202 Accepted`
```json
{
  "message": "Analysis resumed and completed. Report generated.",
  "project_id": "uuid",
  "status": "completed"
}
```

**Errors:**
- `400` - Workflow not suspended or no active workflow
- `404` - Project not found
- `500` - Resume failed

---

#### Get Workflow Status

```
GET /api/v1/workflow/{project_id}/status
```

**Response:** `200 OK`
```json
{
  "project_id": "uuid",
  "thread_id": "uuid | null",
  "current_node": "string",
  "is_suspended": "boolean",
  "suspension_reason": "string | null",
  "messages": ["string"],
  "errors": ["string"]
}
```

**Node Values:**
- `not_started` - Workflow not started
- `ingestion` - Document ingestion (Node 1)
- `hypothesis` - Hypothesis generation (Node 2)
- `interview` - Interview script generation (Node 3)
- `gap_analysis` - Gap analysis (Node 4)
- `solutioning` - Solution generation (Node 5)
- `reporting` - Report generation (Node 6)
- `completed` - Workflow complete

---

#### Get Interview Script

```
GET /api/v1/workflow/{project_id}/interview-script
```

**Response:** `200 OK`
```json
{
  "project_id": "uuid",
  "interview_script": {
    "project_id": "uuid",
    "target_departments": ["string"],
    "target_roles": ["string"],
    "introduction": "string",
    "questions": [
      {
        "role": "string",
        "question": "string",
        "intent": "string",
        "follow_ups": ["string"],
        "related_hypothesis_id": "uuid | null"
      }
    ],
    "closing_notes": "string",
    "estimated_duration_minutes": "integer",
    "generated_at": "ISO 8601 datetime"
  },
  "target_roles": ["string"],
  "estimated_duration_minutes": "integer"
}
```

**Errors:**
- `404` - No workflow state or script not generated

---

#### Get Hypotheses

```
GET /api/v1/workflow/{project_id}/hypotheses
```

**Response:** `200 OK`
```json
{
  "project_id": "uuid",
  "hypotheses": [
    {
      "id": "uuid",
      "process_area": "string",
      "description": "string",
      "evidence": ["string"],
      "indicators": ["string"],
      "confidence": "float (0-1)",
      "category": "string"
    }
  ],
  "count": "integer"
}
```

---

#### Get Gap Analysis

```
GET /api/v1/workflow/{project_id}/gaps
```

**Response:** `200 OK`
```json
{
  "project_id": "uuid",
  "gap_analyses": [
    {
      "id": "uuid",
      "process_step": "string",
      "sop_description": "string",
      "observed_behavior": "string",
      "gap_description": "string",
      "root_cause": "string | null",
      "impact": "string",
      "task_category": "Automatable | Partially Automatable | Human Only"
    }
  ],
  "count": "integer"
}
```

---

#### Get Solutions

```
GET /api/v1/workflow/{project_id}/solutions
```

**Response:** `200 OK`
```json
{
  "project_id": "uuid",
  "solutions": [
    {
      "process_step": "string",
      "observed_behavior": "string",
      "pain_point_severity": "Low | Medium | High | Critical",
      "proposed_solution": "string",
      "tech_stack_recommendation": ["string"],
      "estimated_roi_hours": "integer",
      "implementation_complexity": "Low | Medium | High",
      "priority_score": "float (0-100)"
    }
  ],
  "recommendations": [
    {
      "id": "uuid",
      "gap_id": "uuid",
      "solution_name": "string",
      "solution_description": "string",
      "technology_stack": ["string"],
      "implementation_steps": ["string"],
      "estimated_effort_hours": "integer",
      "estimated_cost_range": "string",
      "estimated_monthly_savings": "float",
      "payback_period_months": "float",
      "risks": ["string"],
      "prerequisites": ["string"]
    }
  ],
  "count": "integer"
}
```

---

#### Get Report

```
GET /api/v1/workflow/{project_id}/report
```

**Response:** `200 OK`
```json
{
  "project_id": "uuid",
  "report_pdf_path": "string | null",
  "report": {
    "id": "uuid",
    "project_id": "uuid",
    "title": "string",
    "executive_summary": {
      "overview": "string",
      "key_findings": ["string"],
      "top_recommendations": ["string"],
      "total_potential_savings": "float",
      "total_implementation_cost": "float",
      "overall_roi_percentage": "float"
    },
    "hypotheses": [...],
    "interview_insights": ["string"],
    "gap_analyses": [...],
    "solutions": [...],
    "current_vs_future": [
      {
        "process_area": "string",
        "current_state": "string",
        "future_state": "string",
        "improvement_description": "string"
      }
    ],
    "implementation_roadmap": [...],
    "appendix": {...},
    "generated_at": "ISO 8601 datetime"
  },
  "status": "completed"
}
```

**Errors:**
- `400` - Report not yet generated
- `404` - No workflow state found

---

### Health

#### Health Check

```
GET /health
```

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "service": "APIC API",
  "version": "0.1.0"
}
```

---

#### Root

```
GET /
```

**Response:** `200 OK`
```json
{
  "message": "Welcome to APIC - Agentic Process Improvement Consultant",
  "docs": "/docs",
  "version": "0.1.0"
}
```

---

## Data Models

### Enums

#### ProjectStatus
```
created | ingesting | analyzing | interview_ready |
awaiting_transcript | processing_transcript | solutioning |
reporting | completed | failed
```

#### Severity
```
Low | Medium | High | Critical
```

#### Complexity
```
Low | Medium | High
```

#### TaskCategory
```
Automatable | Partially Automatable | Human Only
```

---

## Frontend Integration Guide

### API Client Setup (Streamlit Example)

```python
import requests

API_BASE_URL = "http://localhost:8000/api/v1"

def api_request(method: str, endpoint: str, **kwargs) -> dict:
    """Make API request with error handling."""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Error: {str(e)}")
        return None
```

### Typical Workflow Integration

```python
# 1. Create a project
project = api_request("POST", "/projects", json={
    "client_name": "Acme Corp",
    "project_name": "Q1 Optimization",
    "target_departments": ["Finance"]
})
project_id = project["id"]

# 2. Upload documents
files = [("files", (file.name, file, file.type)) for file in uploaded_files]
response = requests.post(
    f"{API_BASE_URL}/projects/{project_id}/documents",
    files=files
)

# 3. Start analysis
result = api_request("POST", "/workflow/start", json={
    "project_id": project_id
})
interview_script = result["interview_script"]

# 4. Poll for status (optional)
status = api_request("GET", f"/workflow/{project_id}/status")

# 5. Submit transcript
result = api_request("POST", "/workflow/resume", json={
    "project_id": project_id,
    "transcript": transcript_text
})

# 6. Get final report
report = api_request("GET", f"/workflow/{project_id}/report")
```

---

## Error Handling

### Error Response Format

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Error Scenarios

| Scenario | Code | Response |
|----------|------|----------|
| Project not found | 404 | `{"detail": "Project {id} not found"}` |
| No documents uploaded | 400 | `{"detail": "No documents uploaded for this project"}` |
| Invalid file type | 400 | `{"detail": "File type not allowed: {filename}. Allowed types: [...]"}` |
| File too large | 400 | `{"detail": "File too large: {filename}. Maximum size: 50MB"}` |
| Workflow not suspended | 400 | `{"detail": "Workflow is not suspended. Cannot submit transcript."}` |
| No active workflow | 400 | `{"detail": "No active workflow found. Start analysis first."}` |
| Analysis failed | 500 | `{"detail": "Analysis failed: {error}"}` |

### Frontend Error Handling Example

```python
def handle_api_error(response):
    """Handle API error responses."""
    if response.status_code == 404:
        st.error("Resource not found. Please refresh and try again.")
    elif response.status_code == 400:
        error = response.json().get("detail", "Invalid request")
        st.error(f"Validation Error: {error}")
    elif response.status_code == 500:
        st.error("Server error. Please try again later.")
    else:
        st.error(f"Unexpected error: {response.status_code}")
```

---

## Contract Validation Checklist

When integrating with the frontend, ensure:

- [ ] All required fields are provided in requests
- [ ] Dates are in ISO 8601 format
- [ ] UUIDs are valid v4 UUIDs
- [ ] File types are in the allowed list
- [ ] File sizes are under 50MB
- [ ] Project exists before document upload
- [ ] Documents exist before starting analysis
- [ ] Workflow is suspended before submitting transcript
- [ ] Report is complete before downloading

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2024-01-21 | Initial API documentation |

---

*Generated for APIC v0.1.0*
