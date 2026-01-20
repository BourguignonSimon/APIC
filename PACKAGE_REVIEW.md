# Package Installation Review

**Date:** 2026-01-20
**Branch:** claude/review-installation-packages-kHLnG
**Reviewed by:** Claude Code

## Executive Summary

This review analyzed all packages in `requirements.txt` and `requirements-dev.txt` to identify unnecessary, redundant, or unused dependencies. The analysis found **11 packages that should be removed** and **several duplications** between production and development requirements.

**Impact of removing unnecessary packages:**
- Faster installation times
- Reduced Docker image size
- Lower security surface area
- Easier dependency maintenance
- Reduced potential for version conflicts

---

## Critical Issues

### 1. Development Tools in Production Requirements ❌

**Problem:** Testing and type-checking tools are listed in `requirements.txt` (production dependencies), causing them to be installed in production environments unnecessarily.

**Packages to REMOVE from `requirements.txt`:**
- `pytest>=8.0.0` (lines 54-56)
- `pytest-asyncio>=0.24.0`
- `pytest-cov>=4.1.0`
- `mypy>=1.8.0` (line 60)

**Reason:** These packages are already in `requirements-dev.txt` and should NEVER be installed in production.

---

### 2. Duplicate Package Declaration ❌

**Problem:** `unstructured` package is declared twice in `requirements.txt`.

**Lines 19-20:**
```
unstructured>=0.15.0
unstructured[pdf]>=0.15.0
```

**Fix:** Consolidate to a single line:
```
unstructured[pdf]>=0.15.0
```

---

### 3. Unused Google AI Packages ❌

**Problem:** Multiple Google AI packages are installed but NOT all are used.

**Packages that are NEVER imported:**
- `langchain-google-vertexai>=2.0.0` (line 10) - ❌ NOT USED
- `google-generativeai>=0.8.0` (line 12) - ❌ NOT USED
- `langchain-community>=0.3.0` (line 11) - ❌ NOT USED

**Packages that ARE used:**
- `langchain-google-genai>=2.0.0` ✅ (used in `src/agents/base.py:15`)

**Findings:**
- The codebase uses `langchain_google_genai.ChatGoogleGenerativeAI` for Google Gemini integration
- `langchain-google-vertexai` is referenced in `requirements.txt` but the actual import for Vertex AI is NEVER used
- The `GoogleVertexAIAgent` class exists but doesn't actually import `langchain_google_vertexai`
- `google-generativeai` SDK is not directly imported (LangChain wrappers are used instead)
- `langchain-community` is not imported anywhere in the src/ directory

**Recommendation:**
- REMOVE `langchain-google-vertexai` (not used)
- REMOVE `google-generativeai` (not used, langchain-google-genai provides the wrapper)
- REMOVE `langchain-community` (not used)

---

### 4. Unused Utility Packages ❌

**Problem:** Several utility packages are declared but never imported in the source code.

**Packages to REMOVE:**
- `httpx>=0.27.0` (line 49) - NOT used in `src/`, only in tests (already in requirements-dev.txt)
- `aiofiles>=24.1.0` (line 50) - NOT used anywhere
- `tenacity>=8.2.0` (line 51) - NOT used anywhere

**Note:** `httpx` is duplicated in both `requirements.txt` and `requirements-dev.txt`. It should only be in `requirements-dev.txt` since it's only used in tests (`tests/` via `respx` for mocking).

---

### 5. Unused PDF Generation Package ⚠️

**Problem:** Two PDF generation libraries are installed but only one is used.

**Packages:**
- `reportlab>=4.2.0` ✅ - Used in `src/agents/reporting.py:411-418`
- `weasyprint>=62.0` ❌ - NOT used anywhere

**Recommendation:** REMOVE `weasyprint` unless there's a planned feature requiring HTML-to-PDF conversion.

---

### 6. Duplicate PostgreSQL Drivers ⚠️

**Problem:** Both sync and async PostgreSQL drivers are installed.

**Packages:**
- `asyncpg>=0.29.0` (line 32) - Async driver
- `psycopg2-binary>=2.9.9` (line 33) - Sync driver

**Current Usage:**
- `src/services/state_manager.py` uses SQLAlchemy with both sync and async sessions
- Code uses `create_async_engine` for async operations
- Some utilities (`db_health.py`, migration tools) use sync `create_engine`

**Recommendation:**
- **KEEP BOTH** if sync operations are required for migrations/admin tasks
- **CONSIDER:** Migrating all database operations to async-only to remove `psycopg2-binary`
- Document why both are needed if keeping both

---

### 7. Unused Document Processing Packages ⚠️

**Current Packages:**
- `pypdf>=4.0.0` ✅ - Used in `src/agents/ingestion.py:161`
- `python-docx>=1.0.0` ✅ - Used in `src/agents/ingestion.py:171` (imported as `docx`)
- `python-pptx>=0.6.23` ✅ - Used in `src/agents/ingestion.py:184` (imported as `pptx`)

**Status:** All document processing packages are properly used. ✅ KEEP ALL

---

### 8. Duplicate Packages in requirements-dev.txt ❌

**Problem:** Several packages are listed in BOTH `requirements.txt` AND `requirements-dev.txt`.

**Duplicated packages:**
- `pytest>=8.0.0`
- `pytest-asyncio>=0.24.0`
- `pytest-cov>=4.1.0`
- `httpx>=0.27.0`
- `mypy>=1.8.0`

**Fix:** Remove these from `requirements.txt`, keep only in `requirements-dev.txt`.

---

## Summary of Recommendations

### Packages to REMOVE from requirements.txt (11 total):

1. ❌ `langchain-google-vertexai>=2.0.0` - Not used
2. ❌ `google-generativeai>=0.8.0` - Not used (langchain wrapper used instead)
3. ❌ `langchain-community>=0.3.0` - Not used
4. ❌ `weasyprint>=62.0` - Not used
5. ❌ `httpx>=0.27.0` - Only used in tests (keep in requirements-dev.txt)
6. ❌ `aiofiles>=24.1.0` - Not used
7. ❌ `tenacity>=8.2.0` - Not used
8. ❌ `pytest>=8.0.0` - Development tool (keep in requirements-dev.txt)
9. ❌ `pytest-asyncio>=0.24.0` - Development tool (keep in requirements-dev.txt)
10. ❌ `pytest-cov>=4.1.0` - Development tool (keep in requirements-dev.txt)
11. ❌ `mypy>=1.8.0` - Development tool (keep in requirements-dev.txt)

### Duplicates to FIX:

1. Lines 19-20: Consolidate `unstructured>=0.15.0` and `unstructured[pdf]>=0.15.0` into single declaration

### Packages to INVESTIGATE:

1. ⚠️ `python-multipart>=0.0.9` - Verify if file uploads are actually used in FastAPI endpoints
2. ⚠️ `psycopg2-binary>=2.9.9` - Consider if both sync and async PostgreSQL drivers are needed

### Packages to KEEP (Verified as Used):

✅ All LLM packages (langgraph, langchain-*, except ones listed above)
✅ `langchain-google-genai` (used for Google Gemini)
✅ `pinecone-client` and `langchain-pinecone` (used in ingestion)
✅ `pypdf`, `python-docx`, `python-pptx` (used in document parsing)
✅ `reportlab` (used in reporting agent)
✅ `fastapi`, `uvicorn`, `streamlit` (core application frameworks)
✅ `sqlalchemy`, `alembic` (database ORM and migrations)
✅ `pydantic`, `pydantic-settings` (data validation)
✅ `python-dotenv` (environment configuration)

---

## Implementation Impact

### Before Changes:
- **Production dependencies:** ~60 packages
- **Development dependencies:** ~43 packages (including duplicates)

### After Changes:
- **Production dependencies:** ~49 packages (-11)
- **Development dependencies:** ~43 packages (no change, already includes test/dev tools)
- **Estimated installation time reduction:** 15-25%
- **Estimated Docker image size reduction:** 50-100 MB

---

## Testing Requirements

After removing packages, verify:

1. ✅ All tests pass: `make test`
2. ✅ Installation completes: `make install`
3. ✅ Development installation works: `make install-dev`
4. ✅ Application starts: `make docker-up`
5. ✅ Type checking works: `make typecheck`
6. ✅ Linting works: `make lint`

---

## Additional Notes

### Why These Packages Were Likely Added:

1. **langchain-google-vertexai**: Possibly added for future Vertex AI support but never implemented
2. **google-generativeai**: May have been added thinking it was needed for langchain-google-genai
3. **langchain-community**: Commonly added "just in case" but not needed for core LangChain functionality
4. **weasyprint**: Likely added as alternative to reportlab but never used
5. **httpx, aiofiles, tenacity**: Common utility packages often added preemptively
6. **Test packages in production**: Common mistake in Python projects

### Best Practices Going Forward:

1. Only add packages when they are actually imported in code
2. Keep development/testing packages in `requirements-dev.txt` only
3. Regularly audit dependencies (quarterly recommended)
4. Use `pip-compile` or similar tools to manage dependency trees
5. Document why less-obvious packages are needed

---

## Files to Update

1. `requirements.txt` - Remove 11 packages, fix duplicate
2. `pyproject.toml` - Update dependencies list to match cleaned requirements.txt
3. `tests/test_installation.py` - Update package verification tests
4. `src/utils/install_verifier.py` - Update required packages list

---

## Conclusion

Removing the 11 unnecessary packages will:
- ✅ Reduce installation complexity
- ✅ Decrease security attack surface
- ✅ Improve build times
- ✅ Reduce Docker image size
- ✅ Make dependency management easier
- ✅ Follow Python best practices

**Recommendation:** Proceed with package removal and test thoroughly.
