# APIC User Guide

## Introduction

APIC (Agentic Process Improvement Consultant) is an AI-powered system that helps organizations identify and automate inefficient business processes. This guide explains how to use APIC to analyze your organization's workflows and receive actionable recommendations.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Understanding the Workflow](#understanding-the-workflow)
3. [Creating a Project](#creating-a-project)
4. [Uploading Documents](#uploading-documents)
5. [Running the Analysis](#running-the-analysis)
6. [Conducting Interviews](#conducting-interviews)
7. [Reviewing Results](#reviewing-results)
8. [Understanding the Report](#understanding-the-report)
9. [Best Practices](#best-practices)
10. [FAQ](#faq)

---

## Getting Started

### Accessing APIC

**Web Interface (Streamlit):**
- Open your browser to `http://localhost:8501`
- The interface provides a step-by-step workflow

**API Access:**
- Base URL: `http://localhost:8000/api/v1`
- API Documentation: `http://localhost:8000/docs`

### System Requirements

- Modern web browser (Chrome, Firefox, Safari, Edge)
- PDF, Word, PowerPoint, or text documents describing your processes

---

## Understanding the Workflow

APIC uses a 6-phase analysis process:

```
Phase 1: Document Ingestion
    ↓
Phase 2: Hypothesis Generation
    ↓
Phase 3: Interview Script Creation
    ↓
    ⏸️ HUMAN INPUT REQUIRED ⏸️
    ↓
Phase 4: Gap Analysis
    ↓
Phase 5: Solution Architecture
    ↓
Phase 6: Report Generation
```

### Key Concept: Human-in-the-Loop

APIC pauses after Phase 3 to allow you to conduct real interviews with your team. This ensures recommendations are grounded in reality, not just theory.

---

## Creating a Project

### Step 1: Navigate to Projects

Click "New Project" in the sidebar or navigate to the Projects page.

### Step 2: Fill Project Details

| Field | Description | Example |
|-------|-------------|---------|
| **Client Name** | Your organization's name | "Acme Corporation" |
| **Project Name** | Descriptive name for this analysis | "Q1 Finance Process Review" |
| **Description** | Brief overview of what you're analyzing | "Analyze invoice processing workflow" |
| **Target Departments** | Departments to focus on | ["Finance", "Accounts Payable"] |

### Step 3: Create Project

Click "Create Project" to initialize your analysis workspace.

---

## Uploading Documents

### Supported Document Types

| Type | Extension | Best For |
|------|-----------|----------|
| PDF | `.pdf` | Standard Operating Procedures, manuals |
| Word | `.docx`, `.doc` | Process documentation |
| PowerPoint | `.pptx` | Training materials, presentations |
| Text | `.txt` | Quick notes, logs |
| Excel | `.xlsx` | Process matrices, data tables |

### What Documents to Upload

**Recommended:**
- Standard Operating Procedures (SOPs)
- Process flowcharts
- Training documentation
- Compliance guidelines
- Role descriptions
- Current system documentation

**Maximum File Size:** 50MB per file

### Upload Process

1. Select your project
2. Click "Upload Documents"
3. Drag and drop files or click to browse
4. Wait for processing confirmation

---

## Running the Analysis

### Starting the Analysis

1. Ensure all documents are uploaded
2. Click "Start Analysis"
3. APIC will process your documents through Phases 1-3

### What Happens During Analysis

**Phase 1 - Document Ingestion:**
- Documents are parsed and chunked
- Text is converted to embeddings
- Content is stored in the vector database

**Phase 2 - Hypothesis Generation:**
- AI analyzes document content
- Identifies suspected inefficiencies
- Generates confidence-scored hypotheses

**Phase 3 - Interview Script Creation:**
- Creates role-specific interview questions
- Focuses on "Dull, Dirty, Dangerous" tasks
- Generates follow-up questions

### Analysis Completion

When analysis reaches the human breakpoint, you'll see:
- Generated interview script
- List of hypotheses to validate
- Instructions for next steps

---

## Conducting Interviews

### Why Interviews Matter

APIC generates hypotheses based on documentation, but real-world processes often differ from documented procedures. Interviews validate:

- How work is **actually** done
- Pain points employees experience
- Workarounds and unofficial processes
- Time spent on tasks

### Interview Guidelines

**Preparation:**
1. Download the interview script
2. Identify interviewees based on suggested roles
3. Schedule 30-60 minute sessions
4. Prepare recording equipment (with consent)

**During the Interview:**
1. Follow the script's introduction
2. Ask each question as written
3. Use follow-up questions when needed
4. Take detailed notes
5. Note any surprises or contradictions

**Key Questions to Explore:**
- "Walk me through a typical day"
- "What takes longer than it should?"
- "What would you automate if you could?"
- "Where do you see bottlenecks?"

### Creating the Transcript

After interviews, create a transcript document including:

```
Interview Transcript
====================

Participant: [Role/Title]
Date: [Date]
Department: [Department]

Q: [Question from script]
A: [Interviewee's response]

Q: [Follow-up question]
A: [Response]

Key Observations:
- [Notable insight 1]
- [Notable insight 2]
```

### Submitting the Transcript

1. Return to your project in APIC
2. Click "Resume Analysis"
3. Paste or upload your interview transcript
4. Click "Submit"

---

## Reviewing Results

### Phase 4 - Gap Analysis Results

After submitting transcripts, APIC identifies gaps between:
- **SOP (Documented):** What the documentation says should happen
- **Reality (Observed):** What actually happens based on interviews

Each gap is classified as:
| Category | Description |
|----------|-------------|
| **Automatable** | Can be fully automated with existing technology |
| **Partially Automatable** | Some steps can be automated, others need human judgment |
| **Human Only** | Requires human decision-making, creativity, or empathy |

### Phase 5 - Solution Recommendations

For each automatable gap, APIC provides:

- **Recommended Technology:** Specific tools/platforms
- **Implementation Approach:** Step-by-step implementation plan
- **ROI Estimate:** Expected time/cost savings
- **Complexity Rating:** Low/Medium/High implementation difficulty
- **Priority Score:** Based on impact and feasibility

### Viewing Results

Navigate to your project's "Results" tab to see:
- Gap analysis summary
- Solution recommendations
- Priority matrix
- ROI calculations

---

## Understanding the Report

### Report Sections

**1. Executive Summary**
- High-level findings
- Key recommendations
- Total ROI potential

**2. Current State Analysis**
- Process overview
- Identified inefficiencies
- Pain point mapping

**3. Gap Analysis**
- Detailed gap descriptions
- Evidence from documents and interviews
- Severity assessments

**4. Future State Vision**
- Recommended automations
- Process improvements
- Technology stack suggestions

**5. Implementation Roadmap**
- Phased approach
- Quick wins vs. long-term projects
- Resource requirements

**6. ROI Analysis**
- Cost savings projections
- Time savings estimates
- Implementation costs

### Downloading the Report

Click "Download Report" to get a PDF containing all findings and recommendations.

---

## Best Practices

### Document Preparation

✅ **Do:**
- Include all relevant SOPs
- Upload current versions only
- Include process flowcharts
- Add role descriptions

❌ **Don't:**
- Upload outdated documents
- Include sensitive personal data
- Mix unrelated processes
- Upload blank templates

### Interview Tips

✅ **Do:**
- Interview multiple people per role
- Ask open-ended questions
- Record specific examples
- Note time estimates

❌ **Don't:**
- Lead interviewees to answers
- Skip follow-up questions
- Dismiss "unofficial" processes
- Rush through interviews

### Getting the Most Value

1. **Be thorough with documents** - More context = better analysis
2. **Interview diverse roles** - Get perspectives from all levels
3. **Be honest in transcripts** - Include inefficiencies even if embarrassing
4. **Review recommendations critically** - AI suggestions need human validation
5. **Prioritize quick wins** - Start with high-impact, low-effort improvements

---

## FAQ

### General Questions

**Q: How long does the analysis take?**
A: Phases 1-3 typically complete in 5-15 minutes depending on document volume. The total timeline depends on how quickly you conduct interviews.

**Q: Can I analyze multiple departments at once?**
A: Yes, but we recommend focusing on related processes for better results.

**Q: Is my data secure?**
A: Documents are processed locally and not shared externally. Embeddings are stored in your Pinecone instance.

### Document Questions

**Q: What if my documents are outdated?**
A: Upload the most current versions. Outdated documents will lead to inaccurate hypothesis generation.

**Q: Can I add more documents later?**
A: Yes, you can add documents before starting the analysis. After starting, create a new project.

**Q: What if I have handwritten documents?**
A: APIC can process scanned documents with OCR, but typed documents provide better accuracy.

### Interview Questions

**Q: How many people should I interview?**
A: We recommend 3-5 people per role for comprehensive coverage.

**Q: What if the interview reveals sensitive issues?**
A: You control what goes in the transcript. Summarize sensitive information appropriately.

**Q: Can I use video call transcripts?**
A: Yes, automatic transcription works well. Clean up any obvious errors before submission.

### Results Questions

**Q: What if I disagree with a recommendation?**
A: Recommendations are suggestions based on analysis. Use your domain expertise to validate and prioritize.

**Q: How accurate are ROI estimates?**
A: Estimates are based on typical automation outcomes. Actual results depend on implementation quality.

**Q: Can I share the report with stakeholders?**
A: Yes, the PDF report is designed for executive presentation.

---

## Support

For technical issues or questions:
- Check the FAQ above
- Contact your system administrator
- Review the technical documentation

For feature requests or feedback:
- Submit through your organization's IT support channel
