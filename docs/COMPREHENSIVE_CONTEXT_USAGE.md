# Comprehensive Context Usage in Interview Script Generation

## Overview

The Interview Architect Agent now uses **ALL available information** when generating interview scripts, not just hypotheses. This ensures richer, more contextual interviews that leverage the full depth of uploaded documents and project information.

---

## 🎯 What Changed

### Before: Hypothesis-Only Approach
```
Hypotheses → Analysis → Interview Script
```

The agent primarily relied on hypotheses, potentially missing valuable context from:
- Original document summaries
- Project metadata
- Document types and sources (files vs URLs)
- Industry-specific context

### After: Comprehensive Context Approach
```
ALL Information → Comprehensive Context → Enhanced Analysis → Rich Interview Script
    │
    ├─ Documents (metadata, types, sources)
    ├─ Document Summaries (full text content)
    ├─ Project Information (client, industry, departments)
    ├─ Hypotheses (identified issues)
    └─ Workflow State (messages, progress)
```

---

## 📊 Information Now Used

### 1. **Document Information**
```python
{
    'documents_count': 5,
    'documents': [
        {
            'filename': 'sales_process.pdf',
            'file_type': 'pdf',
            'source_type': 'file',
            'processed': True,
            'chunk_count': 42
        },
        {
            'filename': 'www.company.com_docs',
            'file_type': 'url',
            'source_type': 'url',
            'source_url': 'https://www.company.com/docs',
            'processed': True,
            'chunk_count': 18
        }
    ],
    'has_urls': True  # Flag for URL-based documents
}
```

**Used for:**
- Understanding document diversity
- Identifying online vs offline sources
- Recognizing document coverage gaps

### 2. **Document Summaries** (NEW!)
```python
{
    'summaries_count': 5,
    'document_summaries': [
        "Summary 1: Sales process involves manual data entry...",
        "Summary 2: Customer onboarding requires multiple approvals...",
        "Summary 3: Reporting is done manually in Excel..."
    ],
    'combined_summaries': "Summary 1...\n\n---\n\nSummary 2...\n\n---\n\nSummary 3..."
}
```

**Used for:**
- Capturing nuances not in hypotheses
- Understanding actual process details
- Identifying terminology and language used
- Finding additional pain points

### 3. **Project Context** (ENHANCED!)
```python
{
    'project': {
        'client_name': 'Acme Corporation',
        'industry': 'Manufacturing',
        'target_departments': ['Sales', 'Operations', 'Customer Service'],
        'description': 'Process improvement for manufacturing operations',
        'created_at': '2024-01-15'
    }
}
```

**Used for:**
- Industry-specific question framing
- Department-aware role identification
- Context-appropriate terminology

### 4. **Hypothesis Insights** (ORGANIZED!)
```python
{
    'hypotheses_summary': {
        'total_count': 7,
        'high_confidence': [hypotheses with confidence >= 0.7],
        'by_automation_potential': {
            'high': [3 hypotheses],
            'medium': [2 hypotheses],
            'low': [2 hypotheses]
        },
        'process_areas': ['Sales', 'Data Entry', 'Approvals', 'Reporting']
    },
    'hypotheses_full': [full hypothesis objects]
}
```

**Used for:**
- Prioritizing interview focus
- Identifying automation opportunities
- Understanding issue distribution

### 5. **Workflow State**
```python
{
    'workflow_messages': [
        "Ingestion complete",
        "Generated 7 hypotheses",
        "Interview script generation started"
    ]
}
```

**Used for:**
- Understanding data quality
- Tracking processing status

---

## 🔧 Implementation

### New Method: `_gather_comprehensive_context()`

```python
def _gather_comprehensive_context(state, hypotheses):
    """
    Gather ALL available information for interview generation.

    Returns:
        {
            'documents_count': int,
            'documents': [doc metadata],
            'summaries_count': int,
            'document_summaries': [summaries],
            'combined_summaries': str,
            'project': {client, industry, departments},
            'hypotheses_summary': {organized hypothesis data},
            'hypotheses_full': [full hypotheses],
            'workflow_messages': [messages],
            'has_urls': bool
        }
    """
```

This method:
1. ✅ Collects all documents and metadata
2. ✅ Gathers all summaries and combines them
3. ✅ Extracts project information
4. ✅ Organizes hypotheses by confidence and potential
5. ✅ Identifies document types (files vs URLs)
6. ✅ Captures workflow state

### Enhanced Method: `_analyze_hypotheses()`

**Before:**
```python
async def _analyze_hypotheses(hypotheses, departments):
    # Only used hypotheses
    prompt = "Analyze hypotheses..."
```

**After:**
```python
async def _analyze_hypotheses(hypotheses, departments, comprehensive_context):
    # Uses EVERYTHING
    prompt = f"""
    CLIENT CONTEXT:
    - Client: {client_name}
    - Industry: {industry}

    DOCUMENT ANALYSIS:
    - Total Documents: {doc_count}
    - Includes URLs: {has_urls}

    DOCUMENT SUMMARIES:
    {combined_summaries}

    IDENTIFIED HYPOTHESES:
    {hypotheses}

    Analyze ALL this information...
    """
```

**Now includes:**
- ✅ Client and industry context
- ✅ Document summaries (up to 2000 chars)
- ✅ Document metadata
- ✅ Project information
- ✅ Hypotheses with full details

---

## 📈 Benefits

### 1. **Richer Interview Questions**

**Before (Hypothesis-Only):**
```
Question: "What manual processes slow down your work?"
(Generic, based only on hypothesis about manual work)
```

**After (Comprehensive Context):**
```
Question: "The documentation mentions that sales orders require
manual entry into three different systems. Can you walk me through
this process and identify which steps are most time-consuming?"
(Specific, references actual document content)
```

### 2. **Better Role Identification**

**Before:**
```python
# Roles identified only from hypothesis process areas
target_roles = ["Manager", "Team Lead"]
```

**After:**
```python
# Roles identified from documents, industry, and hypotheses
target_roles = [
    "Sales Operations Manager",  # From document analysis
    "Order Processing Specialist",  # From summaries
    "IT Integration Lead",  # From system mentions
    "Customer Service Supervisor"  # From dept context
]
```

### 3. **Industry-Appropriate Language**

**Manufacturing Industry Example:**

**Before:**
```
"What reports do you generate?"
```

**After (with industry context):**
```
"What production reports, quality metrics, or OEE (Overall Equipment
Effectiveness) tracking do you currently generate manually?"
```

### 4. **URL vs File Awareness**

**When URLs are included:**
```
Question: "I noticed from the online documentation that the system
should handle approvals automatically. Does that match your actual
experience, or are there manual steps not documented online?"
```

This creates opportunities to identify gaps between documented (URLs) and actual (files) processes.

---

## 🔍 Example: Before vs After

### Scenario
**Documents:**
- `sales_sop.pdf` (file)
- `https://company.com/api-docs` (URL)
- `customer_complaints.docx` (file)

**Summaries:**
- "Sales SOP describes 7-step manual approval process"
- "API documentation shows automated order submission available"
- "Customer complaints mention delays in order processing"

**Hypotheses:**
- Manual approval process causes delays (confidence: 0.8)

### Before (Hypothesis-Only)

**Analysis Input:**
```
HYPOTHESES:
- Manual approval process causes delays

Analyze...
```

**Generated Question:**
```
"Can you describe your approval process?"
```

### After (Comprehensive Context)

**Analysis Input:**
```
CLIENT CONTEXT:
- Client: Acme Corp
- Industry: Manufacturing

DOCUMENT ANALYSIS:
- 3 documents (1 URL, 2 files)

DOCUMENT SUMMARIES:
- SOP describes 7-step manual approval
- API docs show automated submission exists
- Complaints mention order delays

IDENTIFIED HYPOTHESES:
- Manual approval causes delays (0.8 confidence)

Analyze ALL this information...
```

**Generated Question:**
```
"The SOP describes a 7-step manual approval process, but the API
documentation suggests automated order submission is available.
Are you aware of this automation capability? If so, why isn't it
being used? What barriers exist to implementing the automated
approval workflow?"
```

**Why Better:**
- ✅ References specific content (7-step process)
- ✅ Identifies gap (manual vs automated)
- ✅ Probes for barriers
- ✅ More likely to uncover root causes

---

## 🎓 Best Practices

### 1. Upload Comprehensive Documentation

**Good:**
- ✅ Current SOPs (files)
- ✅ System documentation (URLs)
- ✅ Process diagrams (files)
- ✅ User guides (URLs or files)
- ✅ Issue logs or complaints (files)

**Why:** More information → Better context → Richer interviews

### 2. Provide Clear Project Context

**Good:**
```python
project = {
    'client_name': 'Acme Manufacturing',
    'industry': 'Automotive Parts Manufacturing',
    'target_departments': ['Production', 'Quality Assurance', 'Logistics'],
    'description': 'Optimize production scheduling and quality tracking'
}
```

**Why:** Industry and department context enables specific terminology

### 3. Mix File Types

**Good Mix:**
- PDFs (formal docs)
- DOCX (editable docs)
- URLs (online systems, wikis, portals)
- TXT (logs, notes)

**Why:** Different sources reveal different aspects of processes

---

## 🔄 Technical Flow

```
┌─────────────────────────────────────────────┐
│  Interview Architect Process() Method       │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  _gather_comprehensive_context()            │
│                                             │
│  Collects:                                  │
│  ✓ Documents (files + URLs)                 │
│  ✓ Summaries (all text content)             │
│  ✓ Project info (client, industry)          │
│  ✓ Hypotheses (organized by confidence)     │
│  ✓ Workflow state (messages, status)        │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  _analyze_hypotheses(..., context)          │
│                                             │
│  AI receives:                               │
│  • Client name & industry                   │
│  • Document summaries (up to 2000 chars)    │
│  • Document metadata                        │
│  • All hypotheses with evidence             │
│                                             │
│  Produces:                                  │
│  • Key themes from ALL sources              │
│  • Priority areas based on context          │
│  • Root causes with evidence                │
│  • Interview focus recommendations          │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  Subsequent Methods Use Enhanced Analysis   │
│                                             │
│  • _generate_customer_context()             │
│  • _determine_target_roles()                │
│  • _generate_questions()                    │
│  • _generate_discovery_questions()          │
│                                             │
│  All benefit from comprehensive context!     │
└─────────────────────────────────────────────┘
```

---

## 📊 Logging and Monitoring

The system now logs context usage:

```
INFO: Starting interview script generation
INFO: Gathering comprehensive context from all available sources
INFO: Context gathered: 5 documents, 5 summaries, 7 hypotheses
INFO: Analyzing hypotheses to identify key themes and priorities
INFO: Analysis complete: identified 4 key themes
...
```

**What to monitor:**
- Document count vs summaries count (should match)
- Hypothesis count (should be > 0 even with AI generation)
- Context richness (more documents = better interviews)

---

## 🎯 Summary

**Key Improvements:**

1. ✅ **Comprehensive Context Gathering**
   - New `_gather_comprehensive_context()` method
   - Collects ALL available information
   - Organizes data for easy consumption

2. ✅ **Enhanced Analysis**
   - `_analyze_hypotheses()` now receives full context
   - AI analyzes documents + hypotheses together
   - Produces richer, more informed analysis

3. ✅ **Better Interview Questions**
   - Reference actual document content
   - Industry-appropriate terminology
   - Identify gaps between documented and actual processes

4. ✅ **Complete Information Usage**
   - Nothing is ignored
   - URLs and files both considered
   - Project context shapes questions

**Result:**
More targeted, contextual, and effective stakeholder interviews that uncover the real issues, not just surface-level problems.

---

**Files Modified:**
- [src/agents/interview.py](../src/agents/interview.py) - Added comprehensive context usage
- Lines 78-89: Added context gathering
- Lines 214-270: Enhanced analysis method
- Lines 1312-1382: New `_gather_comprehensive_context()` method

**The Interview Architect now uses every piece of information at its disposal!** 🎉
