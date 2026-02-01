# Interview Script Generation with AI Fallback

## Overview

The Interview Architect Agent now has intelligent fallback mechanisms to ensure interview scripts are always generated, even when the Hypothesis Generator doesn't find any hypotheses.

## How It Works

### 1. Normal Flow (With Hypotheses)
```
Hypothesis Generator → Finds hypotheses → Interview Architect → Generates script → Human Breakpoint
```

### 2. Fallback Flow (No Hypotheses)
```
Hypothesis Generator → No hypotheses found
    ↓
Interview Architect detects no hypotheses
    ↓
AI-Powered Hypothesis Generation (using Gemini)
    ↓ (if successful)
Generated Hypotheses → Interview Script → Human Breakpoint
    ↓ (if fails)
Generic Hypotheses Template → Interview Script → Human Breakpoint
```

## Three-Tier System

### Tier 1: Document-Based Hypotheses (Primary)
- **Source**: Hypothesis Generator Agent
- **Method**: Analyzes document summaries, extracts patterns, identifies inefficiencies
- **Quality**: Highest - specific to client's actual documentation

### Tier 2: AI-Generated Hypotheses (Fallback)
- **Source**: Interview Architect using Gemini API
- **Method**: AI analyzes document summaries to generate hypotheses
- **Quality**: Good - contextual but AI-inferred
- **Trigger**: Activated when Tier 1 returns no hypotheses

### Tier 3: Generic Hypotheses (Last Resort)
- **Source**: Hardcoded template in Interview Architect
- **Method**: Uses common business process inefficiencies
- **Quality**: Generic but actionable
- **Trigger**: Activated when both Tier 1 and Tier 2 fail

## AI-Generated Hypotheses (Tier 2)

### Process

The Interview Architect sends the following to Gemini:

1. **Client Context**: Name, departments, project info
2. **Document Summaries**: All ingested document summaries
3. **Task**: Generate 3-5 hypotheses about inefficiencies

### AI Prompt Structure

```
You are an expert business process consultant.

Based on document summaries, identify:
- Process inefficiencies
- Automation opportunities
- Areas for improvement

For each hypothesis provide:
- process_area: Affected process/department
- description: Clear description of inefficiency
- evidence: Quotes from documents
- indicators: Keywords/patterns
- confidence_score: 0.0-1.0
- automation_potential: high/medium/low
```

### Example AI-Generated Hypothesis

```json
{
  "process_area": "Invoice Processing",
  "description": "Manual invoice entry and routing causes delays and errors",
  "evidence": ["Document mentions 'manual data entry'", "References to 'approval delays'"],
  "indicators": ["manual", "invoice", "delays", "errors"],
  "confidence_score": 0.75,
  "automation_potential": "high",
  "task_category": "automatable"
}
```

## Generic Hypotheses Template (Tier 3)

When all else fails, the system uses these proven, common inefficiency patterns:

### 1. Data Entry and Documentation
- Manual data entry and repetitive documentation
- High automation potential
- Common in all organizations

### 2. Communication and Coordination
- Information silos and inefficient channels
- Medium automation potential
- Typical organizational challenge

### 3. Approval and Review Processes
- Multi-step approvals with manual routing
- High automation potential
- Common workflow bottleneck

### 4. Report Generation
- Manual report compilation and distribution
- High automation potential
- Frequently reported pain point

## Human Breakpoint Always Required

**CRITICAL**: Regardless of which tier generates the hypotheses, the workflow **always**:

1. ✅ Generates an interview script
2. ✅ Reaches the human breakpoint
3. ✅ Suspends for stakeholder interviews
4. ✅ Waits for transcript submission

This ensures:
- Every analysis produces actionable interview questions
- Consultants always have guidance for stakeholder interviews
- Process doesn't fail silently
- Human validation is always required

## Benefits

### For Consultants
- ✅ Never left without interview guidance
- ✅ AI assists when document analysis is thin
- ✅ Generic questions ensure baseline coverage
- ✅ Interview quality maintained

### For Clients
- ✅ Analysis always proceeds to interview stage
- ✅ Stakeholder input always captured
- ✅ Process improvement opportunities identified even with limited documentation
- ✅ Consistent experience regardless of input quality

### For System Reliability
- ✅ No silent failures
- ✅ Graceful degradation from specific → generic
- ✅ AI amplifies limited data
- ✅ Human validation checkpoint always enforced

## Configuration

The Interview Architect uses the configured LLM provider for AI generation:

```python
# In .env or config/settings.py
DEFAULT_LLM_PROVIDER=google  # Uses Gemini
GOOGLE_API_KEY=your-api-key
GOOGLE_MODEL=gemini-1.5-flash
```

Or specify in `config/agents.yaml`:

```yaml
InterviewArchitect:
  llm:
    provider: google
    model: gemini-1.5-flash
    temperature: 0.7
```

## Example Scenarios

### Scenario 1: Rich Documentation
```
10 documents uploaded → Hypothesis Generator finds 12 hypotheses
→ Interview script with 12 specific, evidence-based questions
→ High-quality, targeted interview
```

### Scenario 2: Limited Documentation
```
2 documents uploaded → Hypothesis Generator finds 0 hypotheses
→ AI analyzes summaries → Generates 4 contextual hypotheses
→ Interview script with 4 AI-inferred questions
→ Good quality, contextual interview
```

### Scenario 3: No Documentation Analysis
```
Documents uploaded but summaries incomplete → No hypotheses generated
→ AI generation fails or unavailable
→ Generic template loaded → 4 generic hypotheses
→ Interview script with fundamental business process questions
→ Baseline interview ensuring minimum coverage
```

## Logging and Monitoring

The system logs each tier activation:

```
INFO: Starting interview script generation
INFO: No hypotheses found - generating using AI
INFO: Generated 5 hypotheses using AI
INFO: Successfully stored 5 hypotheses in state
INFO: Generated interview script with 15 questions
INFO: System suspended - awaiting interview transcript
```

Or with fallback:

```
INFO: Starting interview script generation
INFO: No hypotheses found - generating using AI
ERROR: AI hypothesis generation failed - using generic interview template
INFO: Loaded 4 generic hypotheses
INFO: Generated interview script with 12 questions
INFO: System suspended - awaiting interview transcript
```

## Testing the Feature

### Test Case 1: AI Generation
1. Upload minimal documentation (1-2 files)
2. Start analysis
3. Check logs for "generating using AI"
4. Verify interview script contains AI-generated hypotheses
5. Confirm human breakpoint reached

### Test Case 2: Generic Fallback
1. Disable AI API key temporarily
2. Upload documents
3. Start analysis
4. Check logs for "using generic interview template"
5. Verify interview script contains generic hypotheses
6. Confirm human breakpoint reached

### Test Case 3: Normal Flow
1. Upload comprehensive documentation (5+ files)
2. Start analysis
3. Verify Hypothesis Generator finds hypotheses
4. Confirm interview script uses original hypotheses
5. Check human breakpoint reached

## Summary

The Interview Architect now ensures:
- ✅ Interview scripts are **always** generated
- ✅ AI assists when document analysis is thin
- ✅ Generic questions provide baseline coverage
- ✅ Human breakpoint is **always** required
- ✅ Quality degrades gracefully (specific → contextual → generic)
- ✅ Consultants never left without guidance
- ✅ Process improvement analysis always proceeds

This three-tier approach maximizes the value of AI while maintaining human oversight and ensuring robust, reliable interview generation regardless of input quality.
