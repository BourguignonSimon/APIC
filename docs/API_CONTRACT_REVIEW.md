# API Contract Review Report

This document summarizes the review of API contracts and their integration with the web interface (Streamlit frontend).

## Review Date: 2024-01-21

---

## Executive Summary

The APIC API contracts were reviewed for correctness, consistency, and proper integration with the Streamlit frontend. Several issues were identified and fixed. This document catalogs the findings and remediation actions.

---

## Issues Found and Fixed

### 1. Critical: Route Ordering Bug (FIXED)

**Location:** `src/api/routes/projects.py:118-156`

**Issue:** The `/projects/{project_id}` route was defined before `/projects/suspended`, causing FastAPI to match requests to `/projects/suspended` with `project_id="suspended"`.

**Impact:** The `GET /projects/suspended` endpoint would always return a 404 error because it tried to find a project with ID "suspended".

**Fix Applied:**
```python
# BEFORE (incorrect order):
@router.get("/projects/{project_id}", ...)
async def get_project(project_id: str): ...

@router.get("/projects/suspended", ...)  # Never reached!
async def get_suspended_projects(): ...

# AFTER (correct order):
@router.get("/projects/suspended", ...)  # Static route first
async def get_suspended_projects(): ...

@router.get("/projects/{project_id}", ...)  # Dynamic route after
async def get_project(project_id: str): ...
```

**Status:** :white_check_mark: Fixed

---

### 2. Missing Response Models (FIXED)

**Location:** `src/api/routes/workflow.py:333-397`

**Issue:** Three endpoints were returning untyped dictionaries instead of Pydantic response models:
- `GET /workflow/{project_id}/hypotheses`
- `GET /workflow/{project_id}/gaps`
- `GET /workflow/{project_id}/solutions`

**Impact:**
- No automatic validation of response data
- Missing OpenAPI schema documentation
- Inconsistent contract with other endpoints

**Fix Applied:** Added proper response models:
```python
class HypothesesResponse(BaseModel):
    project_id: str
    hypotheses: List[Dict[str, Any]]
    count: int

class GapsResponse(BaseModel):
    project_id: str
    gap_analyses: List[Dict[str, Any]]
    count: int

class SolutionsResponse(BaseModel):
    project_id: str
    solutions: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    count: int
```

**Status:** :white_check_mark: Fixed

---

## Issues Identified (Not Fixed - Recommendations)

### 3. Type Inconsistencies in Database Schema

**Location:** `src/services/state_manager.py:57-72`

**Issue:** `DocumentRecord` stores `file_size` and `chunk_count` as `String` columns but returns them as `int`.

```python
# Database definition (String):
file_size = Column(String(50), nullable=False)
chunk_count = Column(String(50), default="0")

# Return conversion (int):
"file_size": int(d.file_size),
"chunk_count": int(d.chunk_count),
```

**Impact:** Potential data corruption if non-numeric values are stored.

**Recommendation:** Change column types to `Integer`:
```python
from sqlalchemy import Integer

file_size = Column(Integer, nullable=False)
chunk_count = Column(Integer, default=0)
```

**Status:** :warning: Documented (requires migration)

---

### 4. Missing Document Deletion in StateManager

**Location:** `src/api/routes/documents.py:195-222`

**Issue:** The `DELETE /projects/{project_id}/documents/{document_id}` endpoint deletes the file but does not remove the database record.

```python
# Current implementation:
if os.path.exists(file_path):
    os.remove(file_path)
# Note: Would need to add delete method to state_manager  # <-- Missing!
return
```

**Impact:** Database contains orphan records after document deletion.

**Recommendation:** Add `delete_document` method to StateManager:
```python
def delete_document(self, document_id: str) -> bool:
    with self.get_session() as session:
        doc = session.query(DocumentRecord).filter_by(id=document_id).first()
        if doc:
            session.delete(doc)
            session.commit()
            return True
        return False
```

**Status:** :warning: Documented (feature incomplete)

---

### 5. Missing Status Validation

**Location:** `src/api/routes/projects.py:158-179`

**Issue:** The `PATCH /projects/{project_id}/status` endpoint accepts any string as status without validating against `ProjectStatus` enum.

```python
# Current (no validation):
async def update_project_status(project_id: str, status: str):
    state_manager.update_project_status(project_id, status)
```

**Impact:** Invalid status values can be stored in the database.

**Recommendation:** Add validation:
```python
from src.models.schemas import ProjectStatus

class StatusUpdateRequest(BaseModel):
    status: ProjectStatus

@router.patch("/projects/{project_id}/status")
async def update_project_status(project_id: str, request: StatusUpdateRequest):
    state_manager.update_project_status(project_id, request.status.value)
```

**Status:** :warning: Documented (enhancement)

---

### 6. CORS Configuration

**Location:** `src/api/main.py:77-84`

**Issue:** CORS allows all origins (`allow_origins=["*"]`).

**Impact:** Security vulnerability in production environments.

**Recommendation:** Configure allowed origins:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",  # Streamlit dev
        "https://your-production-domain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)
```

**Status:** :warning: Documented (security hardening)

---

### 7. Missing Authentication

**Location:** All API routes

**Issue:** No authentication mechanism implemented.

**Impact:** API is publicly accessible without authorization.

**Recommendation:** Implement FastAPI security:
```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

@router.post("/projects")
async def create_project(
    request: ProjectCreateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Validate JWT token
    user = validate_token(credentials.credentials)
    ...
```

**Status:** :warning: Documented (security feature)

---

## Frontend Integration Verification

### Verified Integrations

| Frontend Action | API Endpoint | Contract Match |
|-----------------|--------------|----------------|
| Create Project | `POST /projects` | :white_check_mark: |
| List Projects | `GET /projects` | :white_check_mark: |
| Get Project | `GET /projects/{id}` | :white_check_mark: |
| Upload Documents | `POST /projects/{id}/documents` | :white_check_mark: |
| List Documents | `GET /projects/{id}/documents` | :white_check_mark: |
| Start Analysis | `POST /workflow/start` | :white_check_mark: |
| Get Status | `GET /workflow/{id}/status` | :white_check_mark: |
| Get Interview Script | `GET /workflow/{id}/interview-script` | :white_check_mark: |
| Submit Transcript | `POST /workflow/resume` | :white_check_mark: |
| Get Hypotheses | `GET /workflow/{id}/hypotheses` | :white_check_mark: |
| Get Gaps | `GET /workflow/{id}/gaps` | :white_check_mark: |
| Get Solutions | `GET /workflow/{id}/solutions` | :white_check_mark: |
| Get Report | `GET /workflow/{id}/report` | :white_check_mark: |

### Frontend Request/Response Mappings

#### Project Creation
```python
# Frontend (app.py:235-244)
result = api_request(
    "POST",
    "/projects",
    json={
        "client_name": client_name,      # Maps to ProjectCreateRequest.client_name
        "project_name": project_name,    # Maps to ProjectCreateRequest.project_name
        "description": description,       # Maps to ProjectCreateRequest.description
        "target_departments": dept_list,  # Maps to ProjectCreateRequest.target_departments
    }
)

# Expected Response (ProjectResponse)
{
    "id": "...",
    "client_name": "...",
    "project_name": "...",
    "status": "created",
    ...
}
```

#### Document Upload
```python
# Frontend (app.py:329-338)
files = [("files", (f.name, f, f.type)) for f in uploaded_files]
response = requests.post(
    f"{API_BASE_URL}/projects/{project_id}/documents",
    files=files,
)

# Expected Response (UploadResponse)
{
    "message": "Successfully uploaded N document(s)",
    "documents": [...]
}
```

#### Workflow Start
```python
# Frontend (app.py:367-371)
result = api_request(
    "POST",
    "/workflow/start",
    json={"project_id": project_id},
)

# Expected Response (StartAnalysisResponse)
{
    "message": "Analysis complete...",
    "project_id": "...",
    "thread_id": "...",
    "status": "suspended",
    "interview_script": {...}
}
```

---

## Summary

| Category | Found | Fixed | Documented |
|----------|-------|-------|------------|
| Critical Bugs | 1 | 1 | 0 |
| Missing Models | 3 | 3 | 0 |
| Type Issues | 1 | 0 | 1 |
| Missing Features | 1 | 0 | 1 |
| Validation Issues | 1 | 0 | 1 |
| Security Issues | 2 | 0 | 2 |
| **Total** | **9** | **4** | **5** |

---

## Files Modified

1. `src/api/routes/projects.py` - Fixed route ordering
2. `src/api/routes/workflow.py` - Added response models

## Documentation Created

1. `docs/API_CONTRACTS.md` - Comprehensive API documentation
2. `docs/API_CONTRACT_REVIEW.md` - This review report

---

## Recommendations for Future Work

1. **Database Migration:** Fix `file_size` and `chunk_count` column types
2. **Complete Document Deletion:** Implement database record removal
3. **Status Validation:** Add enum validation for status updates
4. **Security Hardening:** Implement authentication and restrict CORS
5. **Error Types:** Create custom exception classes for better error handling
6. **Rate Limiting:** Add request throttling for production

---

*Review completed by Claude Code - 2024-01-21*
