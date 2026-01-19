# APIC - User Guide

**Document Version:** 1.0
**Last Updated:** January 2026
**Audience:** Management Consultants, Business Analysts, Process Improvement Teams

---

## Table of Contents

1. [Welcome to APIC](#welcome-to-apic)
2. [Getting Started](#getting-started)
3. [Creating Your First Project](#creating-your-first-project)
4. [Uploading Documents](#uploading-documents)
5. [Starting the Analysis](#starting-the-analysis)
6. [Conducting the Interview](#conducting-the-interview)
7. [Reviewing Results](#reviewing-results)
8. [Downloading Reports](#downloading-reports)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)
11. [FAQs](#faqs)

---

## Welcome to APIC

### What is APIC?

APIC (Agentic Process Improvement Consultant) is your AI-powered digital management consultant. It helps you identify operational inefficiencies in your organization, validate findings through structured interviews, and generate actionable automation roadmaps.

### What Makes APIC Different?

Unlike traditional AI tools that might hallucinate solutions, APIC follows a **"Reality-Grounded AI"** approach:

1. **It reads your documentation** (SOPs, process docs, policies)
2. **It generates hypotheses** about where inefficiencies might exist
3. **It creates interview questions** to validate these hypotheses
4. **You conduct the interview** with stakeholders to gather real-world insights
5. **It analyzes the gap** between documented processes and reality
6. **It recommends solutions** with ROI estimates and implementation plans

### Who Should Use APIC?

- **Management Consultants**: Accelerate client discovery and analysis phases
- **Business Process Analysts**: Identify automation opportunities systematically
- **Operations Managers**: Find hidden inefficiencies in your processes
- **Digital Transformation Leaders**: Build data-driven transformation roadmaps
- **Six Sigma Practitioners**: Enhance process mining with AI insights

### Typical Use Cases

| Use Case | Example |
|----------|---------|
| **Process Audit** | "Review our accounts payable process and identify bottlenecks" |
| **Digital Transformation** | "Which manual processes should we automate first?" |
| **Compliance Gap Analysis** | "Where are we deviating from our documented procedures?" |
| **Cost Reduction** | "Find time-consuming manual tasks that could be automated" |
| **Merger Integration** | "Compare processes between two organizations" |

---

## Getting Started

### System Requirements

To use APIC, you need:

- **Web Browser**: Chrome, Firefox, Safari, or Edge (latest versions)
- **Internet Connection**: Stable connection for document uploads and analysis
- **Documents**: SOPs, process documentation, policies (PDF, DOCX, TXT, PPTX formats)
- **Access**: Login credentials provided by your administrator

### Accessing APIC

#### Option 1: Web Interface (Recommended for Most Users)

1. Navigate to the APIC URL provided by your administrator
   - Example: `https://apic.yourcompany.com`
2. The Streamlit interface will load automatically
3. No installation required

#### Option 2: Desktop Installation (Advanced Users)

If you're running APIC locally:

```bash
# Navigate to the APIC directory
cd /path/to/apic

# Activate the virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Start APIC
python main.py frontend
```

Access the interface at: `http://localhost:8501`

### First-Time Setup

When you first access APIC:

1. **Check System Status**: The sidebar should show "System Online" with a green indicator
2. **Verify API Keys**: If you see warnings about missing API keys, contact your administrator
3. **Review Getting Started Guide**: The home page provides quick tips

---

## Creating Your First Project

### Step-by-Step: Project Creation

#### 1. Navigate to "New Project"

Click the **"New Project"** button in the sidebar or main navigation.

#### 2. Fill in Project Details

| Field | Description | Example | Required |
|-------|-------------|---------|----------|
| **Client Name** | Name of the organization being analyzed | "Acme Corporation" | Yes |
| **Project Name** | Descriptive name for this engagement | "Q1 2026 Process Audit" | Yes |
| **Description** | Overview of the project goals | "Identify automation opportunities in finance department" | No |
| **Target Departments** | Departments to focus on (one per line) | Finance<br>Operations<br>HR | Yes |

#### 3. Create Project

Click **"Create Project"** button. You'll see:
- ✅ Project created successfully
- A unique Project ID (e.g., `abc-123-def-456`)
- Project status: **Created**

### Understanding Project Status

Your project will move through these stages:

```
Created → Ingesting → Analyzing → Interview Ready → Awaiting Transcript
→ Processing Transcript → Solutioning → Reporting → Completed
```

| Status | What It Means | Your Action |
|--------|---------------|-------------|
| **Created** | Project initialized, ready for documents | Upload documents |
| **Ingesting** | APIC is processing your documents | Wait (1-5 minutes) |
| **Analyzing** | APIC is generating hypotheses | Wait (1-2 minutes) |
| **Interview Ready** | Interview script is ready | Download script and conduct interview |
| **Awaiting Transcript** | Waiting for interview results | Upload transcript |
| **Processing Transcript** | Analyzing interview data | Wait (2-3 minutes) |
| **Solutioning** | Generating recommendations | Wait (2-3 minutes) |
| **Reporting** | Creating final report | Wait (1-2 minutes) |
| **Completed** | Analysis finished | Download report |

---

## Uploading Documents

### What Documents to Upload

For best results, upload documents that describe **how your organization operates**:

#### Recommended Documents

✅ **Standard Operating Procedures (SOPs)**
- Step-by-step process guides
- Work instructions
- Policy manuals

✅ **Process Documentation**
- Workflow diagrams (if embedded in PDFs)
- Process maps
- Procedure guides

✅ **Policy Documents**
- Company policies
- Compliance documentation
- Regulatory requirements

✅ **Training Materials**
- Employee handbooks
- Training guides
- Onboarding documentation

✅ **Organizational Charts**
- Reporting structures
- Role descriptions
- Responsibility matrices

#### What NOT to Upload

❌ **Confidential Employee Data**: Personal information, salary data
❌ **Financial Records**: Actual invoices, bank statements (use anonymized examples instead)
❌ **Proprietary Code**: Source code files (unless process-related)
❌ **Large Datasets**: Raw data files, database dumps

### Supported File Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| PDF | `.pdf` | Most common format, well-supported |
| Word Document | `.docx`, `.doc` | Text and tables extracted |
| PowerPoint | `.pptx` | Text from slides extracted |
| Text File | `.txt` | Plain text only |
| Excel | `.xlsx` | Text and table data extracted |

**File Size Limit**: 50MB per file

### How to Upload Documents

#### Step-by-Step Upload Process

1. **Select Your Project**
   - From the sidebar, choose your project from the dropdown

2. **Navigate to Upload Section**
   - Click **"Upload Documents"** tab

3. **Choose Files**
   - Click **"Browse files"** button
   - Select one or multiple files (hold Ctrl/Cmd for multiple)
   - Or drag and drop files into the upload area

4. **Upload**
   - Click **"Upload"** button
   - Wait for confirmation: "✅ X files uploaded successfully"

5. **Verify Upload**
   - Check the "Uploaded Documents" table
   - Confirm all files appear with correct names and sizes

### Upload Best Practices

#### Organize Documents Before Upload

```
Recommended folder structure:
├── SOPs/
│   ├── Finance_AP_SOP.pdf
│   ├── Finance_AR_SOP.pdf
│   └── Procurement_SOP.pdf
├── Policies/
│   ├── Approval_Policy.pdf
│   └── Data_Entry_Guidelines.pdf
└── Training/
    └── New_Hire_Guide.pdf
```

#### Naming Conventions

Use descriptive filenames:
- ✅ Good: `Finance_AP_Invoice_Processing_SOP_v2.pdf`
- ❌ Bad: `Document1.pdf`

#### Quality Matters

- Use **searchable PDFs** (not scanned images when possible)
- Ensure documents are **up-to-date** (check version dates)
- Include **complete processes** (not partial snippets)

### What Happens After Upload?

APIC automatically:

1. **Parses** each document to extract text
2. **Chunks** the text into manageable sections
3. **Creates embeddings** (numerical representations for AI analysis)
4. **Stores** embeddings in a vector database
5. **Generates summaries** of each document

This process takes **1-5 minutes** depending on document size and count.

---

## Starting the Analysis

### When to Start Analysis

Start the analysis after:
- ✅ All relevant documents are uploaded
- ✅ Document status shows "Processed" for all files
- ✅ You've reviewed the document list for completeness

### How to Start

1. **Navigate to Workflow Section**
   - Click **"Start Analysis"** tab

2. **Click "Start Analysis" Button**
   - Project status changes to **"Ingesting"**
   - Progress bar appears

3. **Wait for Processing**
   - **Ingestion Phase**: 1-5 minutes (depends on document count)
   - **Hypothesis Generation**: 1-2 minutes
   - **Interview Script Creation**: 1-2 minutes

4. **Status Changes to "Interview Ready"**
   - You'll see: "✅ Interview script is ready!"
   - Download button appears

### Understanding the Analysis Phases

#### Phase 1: Document Ingestion (Node 1)

**What APIC is doing:**
- Reading all uploaded documents
- Extracting key information
- Building a knowledge base

**You see:** Progress bar with "Ingesting documents..."

#### Phase 2: Hypothesis Generation (Node 2)

**What APIC is doing:**
- Scanning for inefficiency keywords ("manual", "email", "delay", etc.)
- Identifying potential bottlenecks
- Creating a list of suspected problems

**You see:** "Generating hypotheses..."

**Example Output:**
```
Hypothesis #1: Invoice Approval Delays
- Evidence: "Invoices require manual email approval from 3 managers"
- Confidence: 85%

Hypothesis #2: Data Entry Redundancy
- Evidence: "Same customer data entered in both CRM and ERP manually"
- Confidence: 78%
```

#### Phase 3: Interview Script Creation (Node 3)

**What APIC is doing:**
- Crafting targeted questions to validate each hypothesis
- Organizing questions by role (CFO, Operations Manager, etc.)
- Creating follow-up questions

**You see:** "Generating interview script..."

**Example Output:**
```
For: Chief Financial Officer (CFO)

Question 1: "How does an invoice get approved once it's received?"
Intent: Validate the manual approval process hypothesis
Follow-ups:
- "How long does this typically take?"
- "What happens if a manager is unavailable?"
```

---

## Conducting the Interview

### Overview

This is the **most critical step** in the APIC process. The interview is where APIC pauses execution to gather real-world insights from your organization's stakeholders.

### Downloading the Interview Script

1. **Navigate to Interview Section**
   - Project status should be **"Interview Ready"**
   - Click **"Download Interview Script"** button

2. **Review the Script**
   - Open the downloaded file (PDF or JSON format)
   - Review questions for clarity and relevance
   - Add or modify questions if needed (optional)

### Interview Script Structure

The script contains:

#### 1. Introduction
- Purpose of the interview
- How the data will be used
- Estimated duration

#### 2. Questions by Role
- Organized by target roles (CFO, Operations Manager, etc.)
- Each question includes:
  - The question itself
  - Intent (why we're asking)
  - Suggested follow-ups

#### 3. Closing Notes
- Thank you message
- Next steps

### Interview Best Practices

#### Before the Interview

✅ **Schedule Properly**
- Book 60-90 minutes (interview scripts typically take 45-75 minutes)
- Choose a quiet, private location
- Ensure the interviewee has time to think, not rushed

✅ **Prepare the Interviewee**
- Send the script 24 hours in advance (optional)
- Explain the purpose: "We're looking to improve processes, not evaluate people"
- Assure confidentiality

✅ **Gather Materials**
- Printed script or laptop with script open
- Recording device (with permission) or note-taking tools
- Water, comfortable seating

#### During the Interview

✅ **Build Rapport**
- Start with casual conversation
- Explain that you're seeking their expertise
- Emphasize: "There are no wrong answers"

✅ **Ask Open-Ended Questions**
- Use the script as a guide, not a rigid checklist
- Ask "How do you actually do this?" not "Do you follow the SOP?"
- Use follow-ups: "Can you walk me through an example?"

✅ **Listen for the "Hidden Factory"**

Key phrases that indicate inefficiencies:
- "Well, the SOP says X, but we actually do Y"
- "There's a workaround we use..."
- "We have to wait for..."
- "I manually enter this into three systems..."
- "We email back and forth until..."

✅ **Take Detailed Notes**
- Capture exact quotes (especially pain points)
- Note tone and emphasis (frustrated, resigned, etc.)
- Record actual numbers ("takes 2 hours per day")

✅ **Probe Deeper**
- When you hear "it's complicated," ask for specifics
- When you hear "it's fine," ask "On a scale of 1-10, how smooth is this?"

#### After the Interview

✅ **Create the Transcript**
- Transcribe recording or clean up notes within 24 hours
- Organize by question (use script as template)
- Include verbatim quotes for important insights

✅ **Transcript Format**

Example:
```
Q1: How does an invoice get approved once it's received?

A1: "So, the official process says we're supposed to get three
approvals through the system. But honestly, that system is so
clunky that we just email the invoice around. First to Sarah,
then to Mike, then to the CFO. The problem is, if anyone is out
of office, it just sits there. Last month we had invoices waiting
12 days because Mike was on vacation and nobody else could approve."

[Interviewer note: Interviewee sounded frustrated. Mentioned this
happens "all the time."]

Q2: How long does a typical invoice approval take?
A2: "If everyone is in the office and responsive, maybe 2-3 days.
But realistically, 5-7 days is normal. Sometimes longer."
```

### Uploading the Transcript

1. **Navigate to Transcript Upload Section**
   - Project status should be **"Awaiting Transcript"**

2. **Paste or Upload Transcript**
   - Option A: Paste text directly into the text area
   - Option B: Upload a TXT or DOCX file

3. **Click "Submit Transcript"**
   - Project status changes to **"Processing Transcript"**
   - Analysis resumes automatically

4. **Wait for Processing**
   - Gap analysis: 2-3 minutes
   - Solution generation: 2-3 minutes
   - Report creation: 1-2 minutes

---

## Reviewing Results

### Accessing Results

Once project status is **"Completed"**:

1. **Navigate to Results Tab**
2. **View Four Key Sections**:
   - Executive Summary
   - Gap Analysis
   - Solution Recommendations
   - ROI Calculations

### Understanding the Gap Analysis

The Gap Analysis compares **what the SOP says** vs **what actually happens**.

#### Example Gap Analysis Entry

| Process Step | SOP Description | Observed Behavior | Gap | Impact |
|--------------|-----------------|-------------------|-----|--------|
| **Invoice Approval** | "Use approval system with 3-click workflow" | "Email invoice to 3 managers manually, wait for replies" | Manual email process bypasses system | **12 hours/week wasted**, **compliance risk** |

#### Gap Severity Levels

- **🔴 Critical**: Severe impact, immediate action required
- **🟠 High**: Significant impact, address soon
- **🟡 Medium**: Moderate impact, plan improvement
- **🟢 Low**: Minor impact, low priority

### Understanding Solution Recommendations

For each gap, APIC provides:

#### Solution Structure

```
Gap: Manual invoice approval via email

Proposed Solution: Implement automated approval workflow

Technology Stack:
- Zapier or Make.com (workflow automation)
- DocuSign (digital signatures)
- Integration with existing accounting system

Implementation Steps:
1. Configure automated email triggers
2. Set up approval routing rules
3. Integrate with accounting system API
4. Train users on new workflow
5. Monitor adoption for 2 weeks

Estimated Implementation Effort: 40 hours
Estimated Cost: $5,000 - $8,000
Monthly Time Savings: 48 hours
Payback Period: 2.5 months

ROI: 380% (first year)

Risks:
- User resistance to new system
- Integration challenges with legacy accounting software

Prerequisites:
- Accounting system API access
- Manager buy-in
- Budget approval
```

### ROI Calculation Methodology

APIC calculates ROI using:

```
Monthly Savings = (Hours Saved × Hourly Rate)
Annual Savings = Monthly Savings × 12
Net Savings = Annual Savings - Implementation Cost
ROI % = (Net Savings / Implementation Cost) × 100
Payback Period = Implementation Cost / Monthly Savings
```

**Default Assumptions** (can be customized):
- Hourly rate: $50 (blended rate for affected roles)
- Implementation cost: Based on complexity (Low: $2-5K, Medium: $5-15K, High: $15-50K)

### Filtering and Sorting Results

Use the results interface to:

- **Filter by Department**: Focus on specific areas
- **Sort by ROI**: See highest-value opportunities first
- **Sort by Complexity**: Start with "quick wins" (low complexity, high ROI)
- **Filter by Severity**: Address critical gaps first

---

## Downloading Reports

### Report Formats

APIC generates reports in multiple formats:

#### 1. PDF Report (Recommended for Stakeholders)

**Contents:**
- Executive Summary (1 page)
- Methodology Overview (1 page)
- Gap Analysis Table (2-4 pages)
- Solution Recommendations (4-8 pages)
- Implementation Roadmap (1-2 pages)
- ROI Summary Dashboard (1 page)
- Appendix: Interview Questions & Hypotheses

**Best for:** Presenting to executives, board members, clients

#### 2. JSON Export (For Technical Teams)

**Contents:**
- Complete data structure
- All hypotheses, gaps, and solutions
- Metadata and confidence scores

**Best for:** Further analysis, integration with other tools, data pipelines

#### 3. Excel Export (For Analysis)

**Contents:**
- Gap analysis table
- Solution recommendations
- ROI calculations
- Sortable and filterable

**Best for:** Detailed analysis, prioritization workshops, budget planning

### How to Download

1. **Navigate to Reports Tab**
   - Project status must be **"Completed"**

2. **Select Format**
   - Choose PDF, JSON, or Excel from dropdown

3. **Click "Download Report"**
   - File downloads automatically
   - Default filename: `APIC_Report_{ProjectName}_{Date}.{format}`

### Customizing Reports

#### Before Generation

You can customize:
- Company logo (upload in settings)
- Hourly rate assumption (for ROI calculations)
- Report title and subtitle
- Included/excluded sections

#### After Generation

The PDF is designed for easy editing in:
- Adobe Acrobat
- Microsoft Word (convert PDF → DOCX)
- Google Docs (import PDF)

---

## Best Practices

### Document Preparation Tips

#### 1. Quality Over Quantity

Upload 10 high-quality, relevant documents rather than 100 tangentially related ones.

**Example:**
- ✅ Better: 5 detailed SOPs for the finance department
- ❌ Worse: 50 general company documents with brief mentions of finance

#### 2. Ensure Documents Are Current

Outdated SOPs lead to inaccurate analysis.

**Checklist:**
- [ ] Documents are from the last 12 months
- [ ] Documents reflect current processes
- [ ] Superseded versions are not included

#### 3. Include Context Documents

Help APIC understand your environment:
- Organizational charts (who reports to whom)
- System architecture diagrams (what tools are used)
- Glossaries (industry-specific terms)

### Interview Techniques

#### 1. The "Five Whys" Technique

When you uncover a problem, ask "why?" five times to get to the root cause.

**Example:**
```
Problem: Invoice approval takes 7 days

Why? → Because we have to email three managers
Why? → Because the system doesn't route automatically
Why? → Because it wasn't configured for our org structure
Why? → Because IT prioritized other projects
Why? → Because we didn't quantify the cost of delays

Root cause: Lack of ROI justification for system configuration
```

#### 2. Ask for Examples

Generic answers aren't useful. Ask for specific examples.

- ❌ "How do you handle exceptions?" → "It depends"
- ✅ "Tell me about the last exception you dealt with" → Detailed story

#### 3. Look for Emotion

When interviewees show frustration, excitement, or resignation, probe deeper. Emotion indicates pain points or opportunities.

### Project Planning Tips

#### 1. Pilot Before Full Rollout

For large organizations:
- Start with **one department** (e.g., finance)
- Validate results and refine process
- Then expand to other departments

#### 2. Timeline Expectations

Typical project timeline:

| Phase | Duration |
|-------|----------|
| Document gathering | 2-5 days |
| APIC processing | 10-15 minutes |
| Interview scheduling | 3-7 days |
| Conducting interviews | 1-2 days |
| APIC final analysis | 5-10 minutes |
| Report review and refinement | 1-2 days |
| **Total** | **~2 weeks** |

#### 3. Stakeholder Communication

Keep stakeholders informed:
- **Before**: "We're using AI to analyze our processes"
- **During**: Share the interview script in advance
- **After**: Share preliminary findings before the final report

---

## Troubleshooting

### Common Issues

#### Issue: "Document upload failed"

**Possible Causes:**
- File too large (> 50MB)
- Unsupported format
- Network timeout

**Solutions:**
1. Check file size: `ls -lh filename.pdf`
2. Compress large PDFs: Use Adobe Acrobat or online tools
3. Convert unsupported formats to PDF
4. Try uploading one file at a time
5. Check network connection

#### Issue: "Analysis stuck at 'Ingesting'"

**Possible Causes:**
- Very large documents (100+ pages)
- Scanned PDFs without OCR
- Backend processing error

**Solutions:**
1. Wait 10 minutes (some documents take time)
2. Check document quality (is text selectable in PDF?)
3. Refresh the page (processing may have completed)
4. Check system status indicator
5. Contact administrator if stuck > 15 minutes

#### Issue: "Interview script has irrelevant questions"

**Possible Causes:**
- Uploaded documents not focused on target processes
- Hypotheses based on tangential information

**Solutions:**
1. Review uploaded documents: Are they process-specific?
2. Manually edit the script before interview
3. Add more detailed SOPs
4. Restart project with better-focused documents

#### Issue: "No gaps identified in analysis"

**Possible Causes:**
- Interview transcript didn't reveal process deviations
- Transcript was too brief or generic

**Solutions:**
1. Review transcript quality: Did it include specific examples?
2. Conduct follow-up interview with more probing questions
3. Interview different stakeholders (front-line vs management perspectives differ)

#### Issue: "ROI calculations seem wrong"

**Possible Causes:**
- Default hourly rate doesn't match your organization
- Time savings estimates based on limited information

**Solutions:**
1. Adjust hourly rate in settings before analysis
2. Review solution details and refine estimates manually
3. Use the Excel export to recalculate with your assumptions

### Getting Help

#### Self-Service Resources

1. **System Status Page**: Check if services are operational
2. **API Documentation**: `http://your-apic-url:8000/docs`
3. **Log Files**: Check console for error messages (press F12 in browser)

#### Contacting Support

If you need assistance:

**Via Web Interface:**
- Click "Help" → "Contact Support"
- Include: Project ID, error message, steps to reproduce

**Via Email:**
- Email: support@apic.yourcompany.com
- Include: Screenshots, project ID, description

**Response Times:**
- Critical (system down): < 2 hours
- High (can't complete project): < 4 hours
- Medium (questions, clarifications): < 24 hours
- Low (feature requests): < 3 business days

---

## FAQs

### General Questions

**Q: How much does APIC cost to run per project?**

A: Costs depend on LLM usage (OpenAI/Anthropic API calls). Typical project:
- Small (5 documents, 1 interview): $5-10
- Medium (20 documents, 3 interviews): $15-25
- Large (50+ documents, 5+ interviews): $30-50

**Q: Is my data secure?**

A: Yes. APIC:
- Stores data in isolated namespaces (multi-tenancy)
- Encrypts data at rest and in transit
- Does not share your data with LLM providers for training
- Can be deployed on-premises for maximum security

**Q: Can I use APIC for industries with strict compliance requirements (healthcare, finance)?**

A: Yes, but ensure:
- Documents are anonymized (remove PII, PHI)
- Use self-hosted deployment (not cloud)
- Review your organization's AI usage policies
- Consult legal/compliance before uploading sensitive data

**Q: What languages does APIC support?**

A: Currently English only. Multi-language support planned for future releases.

### Technical Questions

**Q: Can I integrate APIC with my existing tools?**

A: Yes. APIC provides a REST API. You can:
- Trigger analyses from other systems
- Export results to BI tools (Power BI, Tableau)
- Integrate with project management tools (Jira, Asana)

**Q: Can I use APIC without internet access?**

A: Partially. You need internet for:
- LLM API calls (OpenAI, Anthropic)
- Pinecone vector database (if using cloud version)

For fully offline use, you need:
- Self-hosted LLM (e.g., Llama 2, Mistral)
- Local vector database (e.g., ChromaDB)
- Contact your administrator for offline setup

**Q: How accurate are the hypotheses and recommendations?**

A: Accuracy depends on:
- **Document quality**: Clear, detailed SOPs → better hypotheses
- **Interview quality**: Specific, candid responses → better gap analysis
- **Domain**: Well-documented industries → higher accuracy

Typical accuracy (validated against human consultant review):
- Hypothesis relevance: 80-90%
- Gap identification: 85-95%
- Solution appropriateness: 75-85%

Always review recommendations with domain experts before implementation.

### Project-Specific Questions

**Q: Can I analyze multiple departments in one project?**

A: Yes. When creating a project, list multiple departments. APIC will:
- Generate hypotheses for each department
- Create role-specific interview questions
- Organize recommendations by department

**Q: Can I restart a project if I'm not happy with results?**

A: Yes. You can:
- Upload additional documents to an existing project
- Re-run analysis with new documents
- Create a new project and start fresh

**Q: How many interviews should I conduct?**

A: Recommended:
- **Minimum**: 1 interview per department
- **Optimal**: 2-3 interviews per department (different roles/seniority levels)
- **Maximum**: Diminishing returns after 5 interviews per department

**Q: Can I combine transcripts from multiple interviews?**

A: Yes. Paste all transcripts into the transcript field, separated by headers:

```
=== Interview 1: Finance Manager ===
[Transcript here]

=== Interview 2: AP Clerk ===
[Transcript here]

=== Interview 3: CFO ===
[Transcript here]
```

---

## Appendix: Sample Project Walkthrough

### Scenario: Acme Corporation Finance Department Audit

**Goal**: Identify automation opportunities in accounts payable process

#### Step 1: Project Creation (2 minutes)
- Client Name: "Acme Corporation"
- Project Name: "Q1 2026 Finance AP Audit"
- Target Departments: Finance, Procurement
- Description: "Analyze AP process for inefficiencies and automation opportunities"

#### Step 2: Document Upload (10 minutes)
Documents uploaded:
- `AP_Standard_Operating_Procedure_v3.pdf` (25 pages)
- `Invoice_Approval_Policy.pdf` (8 pages)
- `Procurement_System_User_Guide.pdf` (40 pages)
- `Finance_Org_Chart.pdf` (1 page)

#### Step 3: Start Analysis (5 minutes processing)

APIC identified 5 hypotheses:
1. Manual invoice data entry (confidence: 92%)
2. Email-based approval workflow (confidence: 88%)
3. Lack of automated matching (PO to invoice) (confidence: 85%)
4. Paper-based receipt storage (confidence: 75%)
5. Manual reconciliation process (confidence: 70%)

#### Step 4: Interview Script Generated

Sample questions:
- "Walk me through what happens when an invoice arrives via email"
- "How do you verify that an invoice matches the purchase order?"
- "What do you do when there's a discrepancy?"

#### Step 5: Interview Conducted (60 minutes)

Interviewed: Jane Smith, AP Manager

Key insights:
- Invoices received via email are printed, then manually entered into ERP
- Approval requires emailing PDF to 3 managers, waiting for email replies
- No automated PO matching; done manually in Excel
- Takes 15-20 minutes per invoice, processing ~50 invoices/day

#### Step 6: Transcript Uploaded & Analysis Resumed (5 minutes processing)

APIC identified 4 critical gaps:
1. **Manual data entry**: SOP assumes system integration, but no integration exists
2. **Email approval workflow**: SOP references approval system, but it's not used
3. **Excel-based matching**: SOP doesn't mention Excel workaround
4. **Time per invoice**: SOP estimates 5 minutes, reality is 15-20 minutes

#### Step 7: Solutions Generated

Top recommendation:
- **Solution**: Automated invoice processing with OCR
- **Technology**: UiPath or Microsoft Power Automate + Azure Form Recognizer
- **Implementation**: 80 hours, $12,000-$18,000
- **Monthly savings**: 160 hours (50 invoices × 20 min saved × 20 workdays)
- **Annual savings**: $96,000 (160 hrs/month × $50/hr × 12 months)
- **ROI**: 433% (first year)
- **Payback**: 1.9 months

#### Step 8: Report Downloaded

Final deliverable: 18-page PDF report with executive summary, gap analysis, and roadmap

---

**Document Version Control**
This guide is updated quarterly. Check for the latest version in the APIC repository or contact your administrator.

**Feedback Welcome**
Help us improve this guide! Submit suggestions via the "Feedback" button in the APIC interface.
