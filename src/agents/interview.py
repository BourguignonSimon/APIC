"""
Node 3: Interview Architect Agent
Generates dynamic interview scripts based on hypotheses.
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate

from .base import BaseAgent
from src.models.schemas import (
    Hypothesis,
    InterviewQuestion,
    InterviewScript,
    GraphState,
    DiagnosticLead,
)
from src.services.interview_script_generator import get_interview_script_generator
from config.settings import settings


# =============================================================================
# Hypothesis Generation Prompt (Tier 2 AI Fallback)
# =============================================================================
# Used when Hypothesis Generator returns no hypotheses.
# Analyzes document summaries to generate process improvement hypotheses.

HYPOTHESIS_GENERATION_SYSTEM_PROMPT = """You are an expert business process consultant with 15+ years of experience analyzing organizational workflows, identifying inefficiencies, and recommending process improvements."""

HYPOTHESIS_GENERATION_USER_PROMPT = """Analyze the following document summaries and identify potential process inefficiencies, automation opportunities, or areas for improvement.

CLIENT INFORMATION:
- Client Name: {client_name}
- Target Departments: {target_departments}
- Industry: {industry}

DOCUMENT SUMMARIES:
{document_summaries}

YOUR TASK:
Generate 3-5 hypotheses about potential inefficiencies in the client's processes. Focus on:
1. Repetitive manual tasks that could be automated
2. Communication bottlenecks or information silos
3. Approval delays or multi-step processes
4. Data entry, documentation, or reporting inefficiencies
5. Process gaps or workarounds

For each hypothesis, provide:
- process_area: The specific process or department affected
- description: Clear, specific description of the suspected inefficiency
- evidence: Specific quotes or references from the documents (use actual text when available)
- indicators: Keywords or patterns that triggered this hypothesis
- confidence_score: Your confidence level (0.0-1.0) that this is a real issue
- automation_potential: Likelihood this could be automated (high/medium/low)
- task_category: Classification (automatable/partially_automatable/human_only)

CRITICAL: Return ONLY a valid JSON array with no additional text or explanation.

FORMAT (JSON array only):
[
  {{
    "process_area": "string",
    "description": "string",
    "evidence": ["quote1", "quote2"],
    "indicators": ["keyword1", "keyword2"],
    "confidence_score": 0.8,
    "automation_potential": "high",
    "task_category": "automatable"
  }}
]"""




class InterviewArchitectAgent(BaseAgent):
    """
    Node 3: Interview Architect Agent

    Responsibilities:
    - Generate targeted interview questions based on hypotheses
    - Create role-specific question sets
    - Focus on "Dull, Dirty, Dangerous" task identification
    - Prepare a structured interview script
    """

    def __init__(self, **kwargs):
        super().__init__(name="InterviewArchitect", **kwargs)

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate interview script based on hypotheses using 3-tier fallback system.

        This is the main entry point for interview script generation. It implements a
        robust 3-tier hypothesis generation system that ensures an interview script is
        ALWAYS generated, even when document analysis produces no hypotheses.

        3-Tier Hypothesis Generation:
        ------------------------------
        Tier 1: Document-based hypotheses (from Hypothesis Generator Agent)
                - Primary method: Uses analyzed documents to identify real inefficiencies
                - Most accurate and context-specific

        Tier 2: AI-generated hypotheses (using Gemini/OpenAI/Anthropic LLM)
                - Fallback when Tier 1 produces no results
                - Uses document summaries to generate likely hypotheses
                - Still context-aware but relies on AI inference

        Tier 3: Generic hypotheses (hardcoded common patterns)
                - Last resort when both Tier 1 and Tier 2 fail
                - Uses common process inefficiency patterns
                - Ensures baseline interview quality

        After hypothesis acquisition, the method:
        - Gathers comprehensive context (documents, summaries, project info)
        - Analyzes hypotheses to identify key themes and priorities
        - Generates targeted interview questions based on analysis
        - Creates a complete interview script ready for human execution

        Args:
            state: Current graph state containing:
                   - project_id: Unique identifier for the project
                   - hypotheses: List of process improvement hypotheses (may be empty)
                   - documents: Uploaded documents and their metadata
                   - document_summaries: Text summaries of all documents
                   - project: Client/industry/department information

        Returns:
            Updated state with:
                - interview_script: Complete interview script with questions
                - script_generation_complete: True if successful
                - next_step: "SUSPENDED" (human interview required)
                - hypotheses: Updated with AI-generated hypotheses if Tier 2 was used
        """
        self.log_info("Starting interview script generation")

        try:
            # Extract core information from state
            project_id = state.get("project_id")
            hypotheses_data = state.get("hypotheses", [])  # May be empty if Hypothesis Generator failed
            target_departments = state.get("project", {}).get("target_departments", [])

            # Convert hypothesis dictionaries to Hypothesis objects for type safety
            # Handles both dict and object formats to ensure compatibility
            hypotheses = [
                Hypothesis(**h) if isinstance(h, dict) else h
                for h in hypotheses_data
            ]

            # ============================================================
            # 3-TIER HYPOTHESIS GENERATION SYSTEM
            # ============================================================
            # If no hypotheses found from Hypothesis Generator (Tier 1),
            # attempt AI generation (Tier 2), then fall back to generic (Tier 3)
            if not hypotheses:
                self.log_info("No hypotheses found from Hypothesis Generator - activating Tier 2: AI generation")

                # TIER 2: AI-Generated Hypotheses
                # Uses document summaries + project context to generate hypotheses via LLM
                hypotheses = await self._generate_hypotheses_from_documents(state)

                if hypotheses:
                    self.log_info(f"Tier 2 SUCCESS: Generated {len(hypotheses)} hypotheses using AI (Gemini/OpenAI/Anthropic)")
                    # Update state with AI-generated hypotheses so they're available downstream
                    state["hypotheses"] = [h.model_dump() for h in hypotheses]
                else:
                    # TIER 3: Generic Hypotheses Fallback
                    # Even if AI generation fails, continue with generic interview template
                    # This ensures the workflow NEVER fails completely
                    self.log_info("Tier 2 FAILED: AI hypothesis generation unsuccessful - activating Tier 3: Generic template")
                    hypotheses = self._get_generic_hypotheses()
                    self.log_info(f"Tier 3 ACTIVATED: Using {len(hypotheses)} generic hypotheses to ensure interview generation")

            # Gather ALL available information for rich interview generation
            comprehensive_context = self._gather_comprehensive_context(state, hypotheses)

            # Analyze hypotheses to identify key themes and priorities
            analysis = await self._analyze_hypotheses(
                hypotheses,
                target_departments,
                comprehensive_context  # Includes documents, summaries, project info
            )

            # Generate customer context from project data and document analysis
            customer_context = await self._generate_customer_context(
                state,
                hypotheses,
                analysis,
            )

            # Convert hypotheses into actionable diagnostic leads
            diagnostic_leads = await self._generate_diagnostic_leads(
                hypotheses,
                analysis,
            )

            # Determine target roles for interviews
            target_roles = await self._determine_target_roles(
                hypotheses,
                target_departments,
                analysis,
            )

            # Generate validation questions
            questions = await self._generate_questions(
                hypotheses,
                target_roles,
                analysis,
            )

            # Generate discovery questions
            discovery_questions = await self._generate_discovery_questions(
                hypotheses,
                target_roles,
                analysis,
            )

            # Generate interview introduction
            introduction = await self._generate_introduction(
                hypotheses,
                target_departments,
                analysis,
            )

            # Generate tailored closing notes based on analysis
            closing_notes = await self._generate_closing_notes(
                hypotheses,
                questions,
                analysis,
            )

            # Estimate duration based on question complexity (including discovery questions)
            all_questions = questions + discovery_questions
            estimated_duration = await self._estimate_duration(
                all_questions,
                analysis,
            )

            # Create the interview script with flattened customer context fields
            interview_script = InterviewScript(
                project_id=project_id,
                target_departments=target_departments or self._extract_departments(hypotheses),
                target_roles=target_roles,
                customer_business_overview=customer_context["business_overview"],
                customer_organization_structure=customer_context["organization_structure"],
                customer_challenges=customer_context["current_challenges"],
                customer_key_processes=customer_context["key_processes"],
                customer_stakeholders=customer_context["stakeholders"],
                customer_industry_context=customer_context["industry_context"],
                customer_data_sources_summary=customer_context["data_sources_summary"],
                diagnostic_leads=diagnostic_leads,
                introduction=introduction,
                questions=questions,
                discovery_questions=discovery_questions,
                closing_notes=closing_notes,
                estimated_duration_minutes=estimated_duration,
                generated_at=datetime.utcnow(),
            )

            # Update state - SUSPEND for human interview
            script_data = interview_script.model_dump()
            state["interview_script"] = script_data
            state["script_generation_complete"] = True
            state["is_suspended"] = True
            state["suspension_reason"] = "Awaiting interview transcript"
            state["current_node"] = "interview"

            # Generate interview script file (Markdown)
            script_file_path = None
            try:
                generator = get_interview_script_generator()
                project_data = state.get("project", {})
                if isinstance(project_data, dict):
                    script_file_path = generator.generate(
                        script_data,
                        project_data
                    )
                    state["interview_script_file"] = script_file_path
            except Exception as e:
                self.log_error(f"Failed to generate script file: {e}")
                state["interview_script_file"] = None

            state["messages"].append(
                f"Generated interview script with {len(questions)} questions "
                f"for roles: {', '.join(target_roles)}. "
                "System suspended - awaiting interview transcript."
            )

            self.log_info(
                f"Interview script generated with {len(questions)} questions. "
                "Workflow suspended for human interview."
            )

            return state

        except Exception as e:
            self.log_error("Error generating interview script", e)
            state["errors"].append(f"Interview script error: {str(e)}")
            state["script_generation_complete"] = False
            return state

    async def _analyze_hypotheses(
        self,
        hypotheses: List[Hypothesis],
        departments: List[str],
        comprehensive_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive analysis using ALL available information.

        Analyzes hypotheses in context of document summaries, project information,
        and all other available data to create a holistic understanding.

        Args:
            hypotheses: List of hypotheses to analyze
            departments: Target departments
            comprehensive_context: All available context (documents, summaries, project info)

        Returns:
            Analysis dictionary with themes, priorities, and recommendations
        """
        system_prompt = """You are an expert management consultant analyzing operational
inefficiencies. Perform a comprehensive analysis using ALL available information including:
- Hypotheses about process issues
- Original document summaries
- Project context and industry
- Document metadata

Identify:
1. Key themes and patterns across all information
2. Priority areas that require the deepest investigation
3. Potential root causes and interconnections between issues
4. Risk areas that could indicate systemic problems
5. Specific "Dull, Dirty, Dangerous" work patterns (repetitive, unpleasant, risky tasks)
6. Insights from document content that may not be captured in hypotheses

Your analysis will guide the creation of a targeted interview script."""

        # Build context from all available information
        context_summary = ""
        if comprehensive_context:
            project = comprehensive_context.get('project', {})
            context_summary = f"""
CLIENT CONTEXT:
- Client: {project.get('client_name', 'Unknown')}
- Industry: {project.get('industry', 'General')}
- Departments: {', '.join(project.get('target_departments', []))}

DOCUMENT ANALYSIS:
- Total Documents: {comprehensive_context.get('documents_count', 0)}
- Documents with Summaries: {comprehensive_context.get('summaries_count', 0)}
- Includes URLs: {comprehensive_context.get('has_urls', False)}

DOCUMENT SUMMARIES:
{comprehensive_context.get('combined_summaries', 'None available')[:2000]}
"""

        human_template = """Analyze ALL the following information and provide a structured analysis:

{context_summary}

IDENTIFIED HYPOTHESES:
{hypotheses}

TARGET DEPARTMENTS: {departments}

Provide your analysis as a JSON object with the following structure:
{{
    "key_themes": ["theme1", "theme2", ...],
    "priority_areas": [
        {{"area": "area name", "reason": "why this is high priority", "severity": "high/medium/low"}}
    ],
    "root_cause_patterns": ["pattern1", "pattern2", ...],
    "interconnections": ["description of how issues connect"],
    "ddd_indicators": {{
        "dull_tasks": ["repetitive task indicators"],
        "dirty_tasks": ["unpleasant work indicators"],
        "dangerous_tasks": ["risky task indicators"]
    }},
    "interview_focus_recommendations": ["what to focus on in interviews"],
    "risk_areas": ["areas that may indicate systemic problems"]
}}

Return ONLY the JSON object."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_template),
        ])

        hypotheses_text = "\n".join([
            f"[{h.id}] Category: {h.category}\n"
            f"   Process Area: {h.process_area}\n"
            f"   Description: {h.description}\n"
            f"   Evidence: {', '.join(h.evidence[:3]) if h.evidence else 'None'}\n"
            f"   Confidence: {h.confidence}"
            for h in hypotheses
        ])

        response = await self.llm.ainvoke(
            prompt.format_messages(
                context_summary=context_summary,
                hypotheses=hypotheses_text,
                departments=", ".join(departments) if departments else "Not specified",
            )
        )

        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            return json.loads(content)

        except Exception as e:
            self.log_error(f"Failed to parse analysis: {e}")
            # Return default analysis structure
            return {
                "key_themes": [h.category for h in hypotheses],
                "priority_areas": [{"area": h.process_area, "reason": h.description, "severity": "medium"} for h in hypotheses[:3]],
                "root_cause_patterns": [],
                "interconnections": [],
                "ddd_indicators": {"dull_tasks": [], "dirty_tasks": [], "dangerous_tasks": []},
                "interview_focus_recommendations": ["Understand daily workflows", "Identify pain points"],
                "risk_areas": [],
            }

    async def _determine_target_roles(
        self,
        hypotheses: List[Hypothesis],
        departments: List[str],
        analysis: Dict[str, Any],
    ) -> List[str]:
        """
        Determine which roles should be interviewed based on hypotheses and analysis.

        Args:
            hypotheses: List of hypotheses
            departments: Target departments
            analysis: Analysis of hypotheses with key themes and priorities

        Returns:
            List of recommended roles to interview
        """
        # Get configurable prompts or use defaults
        default_system = """You are an expert management consultant. Based on the
            hypotheses about operational inefficiencies and the analysis of key themes,
            determine which roles should be interviewed to validate these hypotheses.

            Consider roles that:
            1. Are directly involved in the suspected inefficient processes
            2. Have visibility into the day-to-day operations
            3. Can provide insight into workarounds and pain points
            4. Have decision-making authority over process changes
            5. Can speak to the identified priority areas and root cause patterns
            """

        default_human = """Based on these hypotheses and analysis, recommend 3-5 roles to interview:

            HYPOTHESES:
            {hypotheses}

            KEY THEMES FROM ANALYSIS:
            {key_themes}

            PRIORITY AREAS:
            {priority_areas}

            INTERVIEW FOCUS RECOMMENDATIONS:
            {focus_recommendations}

            TARGET DEPARTMENTS: {departments}

            Return a JSON array of role titles (e.g., ["CFO", "Operations Manager", "Data Entry Clerk"]).
            Return ONLY the JSON array."""

        system_prompt = self.get_prompt("system", default_system)
        human_template = self.get_prompt("determine_roles", default_human)

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_template),
        ])

        hypotheses_text = "\n".join([
            f"- {h.process_area}: {h.description}"
            for h in hypotheses
        ])

        # Format analysis data
        key_themes = ", ".join(analysis.get("key_themes", []))
        priority_areas = "\n".join([
            f"- {p.get('area', 'Unknown')}: {p.get('reason', 'No reason')} (Severity: {p.get('severity', 'medium')})"
            for p in analysis.get("priority_areas", [])
        ])
        focus_recommendations = "\n".join([
            f"- {r}" for r in analysis.get("interview_focus_recommendations", [])
        ])

        response = await self.llm.ainvoke(
            prompt.format_messages(
                hypotheses=hypotheses_text,
                departments=", ".join(departments) if departments else "Not specified",
                key_themes=key_themes or "Not identified",
                priority_areas=priority_areas or "Not identified",
                focus_recommendations=focus_recommendations or "Not identified",
            )
        )

        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            roles = json.loads(content)
            # Ensure all roles are strings
            if isinstance(roles, list):
                roles = [str(role) if not isinstance(role, str) else role for role in roles]
                return roles
            else:
                return ["Operations Manager"]
        except Exception:
            return ["Operations Manager", "Department Head", "Process Owner"]

    async def _generate_questions(
        self,
        hypotheses: List[Hypothesis],
        target_roles: List[str],
        analysis: Dict[str, Any],
    ) -> List[InterviewQuestion]:
        """
        Generate interview questions based on hypotheses, target roles, and analysis.

        Args:
            hypotheses: List of hypotheses to validate
            target_roles: Roles to be interviewed
            analysis: Analysis of hypotheses with key themes and priorities

        Returns:
            List of interview questions
        """
        # Get configurable prompts or use defaults
        default_system = """You are an expert management consultant preparing for
            client interviews. Generate targeted questions that will:

            1. Validate or invalidate the hypotheses about inefficiencies
            2. Uncover the "Dull, Dirty, Dangerous" tasks (repetitive, unpleasant, risky)
            3. Identify hidden workarounds and unofficial processes
            4. Understand the gap between documented procedures (SOPs) and reality
            5. Quantify the impact of current pain points
            6. Explore the root cause patterns identified in the analysis
            7. Investigate the interconnections between different issues

            For each question, specify:
            - The target role
            - The question itself (open-ended)
            - The intent (what we're trying to learn)
            - Potential follow-up questions

            Make questions conversational and non-leading. Focus on understanding
            the actual workflow, not just confirming assumptions.
            """

        default_human = """Generate interview questions for the following context:

            HYPOTHESES TO VALIDATE:
            {hypotheses}

            ROLES TO INTERVIEW: {roles}

            KEY THEMES IDENTIFIED:
            {key_themes}

            PRIORITY AREAS TO INVESTIGATE:
            {priority_areas}

            ROOT CAUSE PATTERNS TO EXPLORE:
            {root_cause_patterns}

            "DULL, DIRTY, DANGEROUS" INDICATORS:
            - Dull (repetitive): {dull_tasks}
            - Dirty (unpleasant): {dirty_tasks}
            - Dangerous (risky): {dangerous_tasks}

            RISK AREAS:
            {risk_areas}

            Generate 8-15 questions total, distributed across roles. Ensure questions
            specifically target the priority areas and root cause patterns identified.

            Return a JSON array of question objects:
            [
                {{
                    "role": "role title",
                    "question": "the question text",
                    "intent": "why we're asking",
                    "follow_ups": ["follow up 1", "follow up 2"],
                    "related_hypothesis_id": "hypothesis id or null"
                }}
            ]

            Return ONLY the JSON array."""

        system_prompt = self.get_prompt("system", default_system)
        human_template = self.get_prompt("generate_questions", default_human)

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_template),
        ])

        hypotheses_text = "\n".join([
            f"[{h.id}] {h.process_area}: {h.description} (Category: {h.category})"
            for h in hypotheses
        ])

        # Format analysis data
        key_themes = ", ".join(analysis.get("key_themes", []))
        priority_areas = "\n".join([
            f"- {p.get('area', 'Unknown')}: {p.get('reason', 'No reason')}"
            for p in analysis.get("priority_areas", [])
        ])
        root_cause_patterns = ", ".join(analysis.get("root_cause_patterns", ["None identified"]))
        ddd = analysis.get("ddd_indicators", {})
        dull_tasks = ", ".join(ddd.get("dull_tasks", ["None identified"]))
        dirty_tasks = ", ".join(ddd.get("dirty_tasks", ["None identified"]))
        dangerous_tasks = ", ".join(ddd.get("dangerous_tasks", ["None identified"]))
        risk_areas = ", ".join(analysis.get("risk_areas", ["None identified"]))

        response = await self.llm.ainvoke(
            prompt.format_messages(
                hypotheses=hypotheses_text,
                roles=", ".join(target_roles),
                key_themes=key_themes or "Not identified",
                priority_areas=priority_areas or "Not identified",
                root_cause_patterns=root_cause_patterns,
                dull_tasks=dull_tasks,
                dirty_tasks=dirty_tasks,
                dangerous_tasks=dangerous_tasks,
                risk_areas=risk_areas,
            )
        )

        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            questions_data = json.loads(content)

            questions = []
            for q_data in questions_data:
                question = InterviewQuestion(
                    role=q_data.get("role", "General"),
                    question=q_data.get("question", ""),
                    intent=q_data.get("intent", ""),
                    follow_ups=q_data.get("follow_ups", []),
                    related_hypothesis_id=q_data.get("related_hypothesis_id"),
                )
                questions.append(question)

            return questions

        except Exception as e:
            self.log_error(f"Failed to parse questions: {e}")
            # Return default questions
            return self._get_default_questions(target_roles, hypotheses)

    def _get_default_questions(
        self,
        roles: List[str],
        hypotheses: List[Hypothesis],
    ) -> List[InterviewQuestion]:
        """Generate default questions if LLM parsing fails."""
        default_questions = [
            InterviewQuestion(
                role=roles[0] if roles else "Manager",
                question="Can you walk me through a typical day in your role?",
                intent="Understand daily workflow and identify pain points",
                follow_ups=[
                    "What takes up most of your time?",
                    "What tasks do you find most frustrating?",
                ],
            ),
            InterviewQuestion(
                role=roles[0] if roles else "Manager",
                question="What processes require the most manual effort?",
                intent="Identify automation opportunities",
                follow_ups=[
                    "How much time does this take weekly?",
                    "Are there any workarounds you've developed?",
                ],
            ),
            InterviewQuestion(
                role=roles[0] if roles else "Manager",
                question="Where do you see delays or bottlenecks in your workflows?",
                intent="Identify process bottlenecks",
                follow_ups=[
                    "What causes these delays?",
                    "How do you currently handle these situations?",
                ],
            ),
            InterviewQuestion(
                role=roles[0] if roles else "Manager",
                question="How well do your actual processes match documented procedures?",
                intent="Identify gap between SOPs and reality",
                follow_ups=[
                    "Where do you deviate from standard procedures?",
                    "Why do these deviations occur?",
                ],
            ),
        ]
        return default_questions

    async def _generate_introduction(
        self,
        hypotheses: List[Hypothesis],
        departments: List[str],
        analysis: Dict[str, Any],
    ) -> str:
        """
        Generate a tailored introduction for the interview based on analysis.

        Args:
            hypotheses: List of hypotheses
            departments: Target departments
            analysis: Analysis of hypotheses

        Returns:
            Tailored introduction text
        """
        system_prompt = """You are an expert management consultant preparing to conduct
an interview as part of a process improvement initiative. Write a warm, professional
introduction that:

1. Thanks the interviewee for their time
2. Explains the purpose of the interview (process improvement)
3. Mentions the key areas of focus without being leading or biased
4. Reassures them there are no wrong answers
5. Sets expectations for confidentiality and how feedback will be used
6. Invites any questions before beginning

Keep the tone conversational and approachable. The introduction should be 3-4 paragraphs."""

        human_template = """Create an interview introduction based on this context:

KEY THEMES TO EXPLORE: {key_themes}

PRIORITY AREAS: {priority_areas}

TARGET DEPARTMENTS: {departments}

HYPOTHESIS CATEGORIES: {categories}

Write a professional, warm introduction that naturally references the areas of focus
without revealing specific hypotheses or biasing the interviewee.

Return ONLY the introduction text, no JSON or formatting."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_template),
        ])

        categories = ", ".join(set(h.category for h in hypotheses))
        key_themes = ", ".join(analysis.get("key_themes", []))
        priority_areas = ", ".join([
            p.get("area", "") for p in analysis.get("priority_areas", [])
        ])

        response = await self.llm.ainvoke(
            prompt.format_messages(
                key_themes=key_themes or "operational efficiency",
                priority_areas=priority_areas or "day-to-day workflows",
                departments=", ".join(departments) if departments else "various departments",
                categories=categories or "process improvement",
            )
        )

        introduction = response.content.strip()

        # Ensure we have a valid introduction
        if not introduction or len(introduction) < 100:
            # Fallback to a basic introduction
            focus_areas = ", ".join(set(h.category for h in hypotheses))
            return f"""Thank you for taking the time to speak with us today. We're conducting
this interview as part of a process improvement initiative. Our goal is to understand
how work actually gets done day-to-day, identify any challenges or pain points, and
find opportunities for improvement.

Based on our initial document review, we're particularly interested in exploring areas
related to: {focus_areas}.

There are no wrong answers - we want to understand your real experience. Everything
discussed will be used to help improve processes and make your work easier.

Do you have any questions before we begin?"""

        return introduction

    async def _generate_closing_notes(
        self,
        hypotheses: List[Hypothesis],
        questions: List[InterviewQuestion],
        analysis: Dict[str, Any],
    ) -> str:
        """
        Generate tailored closing notes for the interview based on analysis.

        Args:
            hypotheses: List of hypotheses
            questions: Generated interview questions
            analysis: Analysis of hypotheses

        Returns:
            Tailored closing notes text
        """
        system_prompt = """You are an expert management consultant wrapping up an interview
as part of a process improvement initiative. Write professional closing notes that:

1. Thank the interviewee for their time and insights
2. Include 2-3 open-ended final questions that might capture anything missed
3. Ask for recommendations on who else to speak with
4. Explain next steps in the process
5. Leave the door open for follow-up

Keep the tone warm and appreciative. The closing should be 2-3 paragraphs."""

        human_template = """Create interview closing notes based on this context:

KEY THEMES COVERED: {key_themes}

TOPICS COVERED IN QUESTIONS: {question_topics}

RISK AREAS EXPLORED: {risk_areas}

Write professional closing notes that:
1. Acknowledge the areas discussed
2. Include strategic final questions that might reveal additional insights
3. Set expectations for next steps

Return ONLY the closing notes text, no JSON or formatting."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_template),
        ])

        key_themes = ", ".join(analysis.get("key_themes", []))
        question_topics = ", ".join(set([q.role + ": " + q.intent[:50] for q in questions[:5]]))
        risk_areas = ", ".join(analysis.get("risk_areas", []))

        response = await self.llm.ainvoke(
            prompt.format_messages(
                key_themes=key_themes or "operational efficiency",
                question_topics=question_topics or "workflows and processes",
                risk_areas=risk_areas or "process improvement opportunities",
            )
        )

        closing_notes = response.content.strip()

        # Ensure we have valid closing notes
        if not closing_notes or len(closing_notes) < 100:
            return """Thank you for sharing your insights today. Your input is invaluable
for understanding how we can improve processes.

A few final questions:
- Is there anything else you'd like to share that we haven't covered?
- Who else would you recommend we speak with?
- What would be your top priority for process improvement?

We'll be synthesizing this feedback along with other interviews and will share our
findings and recommendations. Please feel free to reach out if you think of anything
else you'd like to add."""

        return closing_notes

    async def _estimate_duration(
        self,
        questions: List[InterviewQuestion],
        analysis: Dict[str, Any],
    ) -> int:
        """
        Estimate interview duration based on questions and complexity analysis.

        Args:
            questions: List of interview questions
            analysis: Analysis of hypotheses

        Returns:
            Estimated duration in minutes
        """
        system_prompt = """You are an expert interviewer estimating the duration of a
business process improvement interview. Consider:

1. Number of questions and their complexity
2. Number of follow-up questions
3. Complexity of topics being discussed
4. Need for rapport building and context gathering
5. Time for interviewee to provide detailed answers

Provide a realistic estimate in minutes."""

        human_template = """Estimate the duration for this interview:

NUMBER OF QUESTIONS: {num_questions}

TOTAL FOLLOW-UP QUESTIONS: {num_followups}

QUESTION COMPLEXITY:
- Questions targeting high-priority areas: {high_priority_count}
- Questions exploring multiple themes: {multi_theme_count}

KEY THEMES: {key_themes}

RISK AREAS TO EXPLORE: {risk_areas}

Return ONLY a single integer representing the estimated duration in minutes.
Consider 3-5 minutes per main question, plus time for follow-ups, introduction, and closing."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_template),
        ])

        # Calculate metrics
        num_questions = len(questions)
        num_followups = sum(len(q.follow_ups) for q in questions)
        priority_areas = [p.get("area", "").lower() for p in analysis.get("priority_areas", [])]
        high_priority_count = sum(
            1 for q in questions
            if any(area in q.question.lower() or area in q.intent.lower() for area in priority_areas)
        )
        key_themes = analysis.get("key_themes", [])
        multi_theme_count = sum(
            1 for q in questions
            if sum(1 for theme in key_themes if theme.lower() in q.question.lower()) > 1
        )
        risk_areas = ", ".join(analysis.get("risk_areas", []))

        response = await self.llm.ainvoke(
            prompt.format_messages(
                num_questions=num_questions,
                num_followups=num_followups,
                high_priority_count=high_priority_count,
                multi_theme_count=multi_theme_count,
                key_themes=", ".join(key_themes) if key_themes else "general process improvement",
                risk_areas=risk_areas or "standard operational areas",
            )
        )

        try:
            # Extract just the number from the response
            content = response.content.strip()
            # Remove any non-numeric characters
            duration = int("".join(filter(str.isdigit, content.split()[0] if content.split() else "60")))
            # Ensure reasonable bounds
            return max(30, min(duration, 120))
        except (ValueError, IndexError):
            # Fallback calculation
            base_time = 15
            per_question = 5
            return base_time + (num_questions * per_question)

    def _extract_departments(self, hypotheses: List[Hypothesis]) -> List[str]:
        """Extract department names from hypothesis process areas."""
        departments = set()
        for h in hypotheses:
            # Simple extraction - could be enhanced
            area = h.process_area.split()[0] if h.process_area else "Operations"
            departments.add(area)
        return list(departments)

    async def _generate_customer_context(
        self,
        state: Dict[str, Any],
        hypotheses: List[Hypothesis],
        analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate customer context from ingested data and analysis.

        Args:
            state: Current graph state with project and document data
            hypotheses: List of hypotheses generated from data
            analysis: Analysis of hypotheses

        Returns:
            Dict with customer context fields
        """
        system_prompt = """You are an expert management consultant preparing a customer context summary
for an interview script. Based on the provided project information and analysis, create a comprehensive
context summary that will help interviewers understand the customer's situation.

Focus on:
1. Business overview - what the company does and its industry
2. Organizational structure relevant to the analysis
3. Key challenges identified from the data
4. Main processes that were analyzed
5. Key stakeholders mentioned in documents
6. Industry-specific context that may influence recommendations"""

        human_template = """Create a customer context summary based on:

PROJECT INFORMATION:
- Client Name: {client_name}
- Project Name: {project_name}
- Description: {description}
- Target Departments: {departments}

DOCUMENT SUMMARIES:
{document_summaries}

KEY THEMES IDENTIFIED:
{key_themes}

PRIORITY AREAS:
{priority_areas}

HYPOTHESES CATEGORIES:
{categories}

Return a JSON object with this structure:
{{
    "business_overview": "Overview of the customer's business and industry",
    "organization_structure": "Summary of relevant organizational structure",
    "current_challenges": ["challenge1", "challenge2", ...],
    "key_processes": ["process1", "process2", ...],
    "stakeholders": ["stakeholder/role1", "stakeholder/role2", ...],
    "industry_context": "Industry-specific context",
    "data_sources_summary": "Summary of what data was analyzed"
}}

Return ONLY the JSON object."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_template),
        ])

        project = state.get("project", {})
        get_val = lambda obj, key, default: obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)
        client_name = get_val(project, "client_name", "Unknown Client")
        project_name = get_val(project, "project_name", "Unknown Project")
        description = get_val(project, "description", "No description provided")
        departments = get_val(project, "target_departments", [])

        document_summaries = state.get("document_summaries", [])
        summaries_text = "\n".join(document_summaries[:5]) if document_summaries else "No document summaries available"

        key_themes = ", ".join(analysis.get("key_themes", []))
        priority_areas = "\n".join([
            f"- {p.get('area', '')}: {p.get('reason', '')}"
            for p in analysis.get("priority_areas", [])
        ])
        categories = ", ".join(set(h.category for h in hypotheses))

        response = await self.llm.ainvoke(
            prompt.format_messages(
                client_name=client_name,
                project_name=project_name,
                description=description or "Not provided",
                departments=", ".join(departments) if departments else "Not specified",
                document_summaries=summaries_text,
                key_themes=key_themes or "Not yet identified",
                priority_areas=priority_areas or "Not yet identified",
                categories=categories or "General process improvement",
            )
        )

        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            context_data = json.loads(content)
            return {
                "business_overview": context_data.get("business_overview", ""),
                "organization_structure": context_data.get("organization_structure", ""),
                "current_challenges": context_data.get("current_challenges", []),
                "key_processes": context_data.get("key_processes", []),
                "stakeholders": context_data.get("stakeholders", []),
                "industry_context": context_data.get("industry_context", ""),
                "data_sources_summary": context_data.get("data_sources_summary", ""),
            }

        except Exception as e:
            self.log_error(f"Failed to parse customer context: {e}")
            # Return basic context
            return {
                "business_overview": f"{client_name} - {project_name}",
                "organization_structure": "See organizational charts",
                "current_challenges": [h.description for h in hypotheses[:3]],
                "key_processes": [h.process_area for h in hypotheses],
                "stakeholders": departments if isinstance(departments, list) else [],
                "industry_context": "Industry context to be determined during interviews",
                "data_sources_summary": "Analysis based on uploaded documents",
            }

    async def _generate_diagnostic_leads(
        self,
        hypotheses: List[Hypothesis],
        analysis: Dict[str, Any],
    ) -> List[DiagnosticLead]:
        """
        Transform hypotheses into diagnostic leads with validation questions.

        Args:
            hypotheses: List of hypotheses to convert to leads
            analysis: Analysis of hypotheses

        Returns:
            List of DiagnosticLead objects for the interview diagnostic form
        """
        system_prompt = """You are an expert management consultant creating a diagnostic form
for interview validation. For each hypothesis/lead, generate:
1. A clear summary of the suspected inefficiency
2. Specific questions to validate or invalidate the lead
3. What evidence would confirm this lead is accurate

Focus on creating actionable validation questions that are:
- Open-ended to encourage detailed responses
- Non-leading to avoid bias
- Specific enough to generate concrete evidence"""

        human_template = """Convert these hypotheses into diagnostic leads:

HYPOTHESES:
{hypotheses}

KEY THEMES FOR CONTEXT:
{key_themes}

PRIORITY AREAS:
{priority_areas}

For each hypothesis, return a JSON array of diagnostic leads:
[
    {{
        "hypothesis_id": "the hypothesis ID",
        "lead_summary": "Brief summary of the suspected inefficiency",
        "category": "the category",
        "confidence": 0.7,
        "validation_questions": [
            "Question to validate this lead",
            "Another validation question"
        ],
        "expected_evidence": [
            "Evidence that would confirm this lead",
            "Other confirming evidence"
        ]
    }}
]

Return ONLY the JSON array."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_template),
        ])

        hypotheses_text = "\n".join([
            f"[{h.id}] Category: {h.category}\n"
            f"   Process Area: {h.process_area}\n"
            f"   Description: {h.description}\n"
            f"   Evidence: {', '.join(h.evidence[:2]) if h.evidence else 'None'}\n"
            f"   Confidence: {h.confidence}"
            for h in hypotheses
        ])

        key_themes = ", ".join(analysis.get("key_themes", []))
        priority_areas = "\n".join([
            f"- {p.get('area', '')}: {p.get('reason', '')}"
            for p in analysis.get("priority_areas", [])
        ])

        response = await self.llm.ainvoke(
            prompt.format_messages(
                hypotheses=hypotheses_text,
                key_themes=key_themes or "Not specified",
                priority_areas=priority_areas or "Not specified",
            )
        )

        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            leads_data = json.loads(content)

            leads = []
            for lead_data in leads_data:
                lead = DiagnosticLead(
                    hypothesis_id=lead_data.get("hypothesis_id", ""),
                    lead_summary=lead_data.get("lead_summary", ""),
                    category=lead_data.get("category", "general"),
                    confidence=lead_data.get("confidence", 0.5),
                    validation_questions=lead_data.get("validation_questions", []),
                    expected_evidence=lead_data.get("expected_evidence", []),
                )
                leads.append(lead)

            return leads

        except Exception as e:
            self.log_error(f"Failed to parse diagnostic leads: {e}")
            # Return basic leads from hypotheses
            return [
                DiagnosticLead(
                    hypothesis_id=h.id,
                    lead_summary=h.description,
                    category=h.category,
                    confidence=h.confidence,
                    validation_questions=[
                        f"Can you describe how {h.process_area} currently works?",
                        f"What challenges do you face with {h.process_area}?",
                    ],
                    expected_evidence=h.evidence[:2] if h.evidence else [],
                )
                for h in hypotheses
            ]

    async def _generate_discovery_questions(
        self,
        hypotheses: List[Hypothesis],
        target_roles: List[str],
        analysis: Dict[str, Any],
    ) -> List[InterviewQuestion]:
        """
        Generate open-ended discovery questions to identify new customer-specific opportunities.

        Args:
            hypotheses: List of hypotheses for context
            target_roles: Roles to be interviewed
            analysis: Analysis of hypotheses

        Returns:
            List of discovery-focused InterviewQuestion objects
        """
        system_prompt = """You are an expert management consultant creating discovery questions
for identifying NEW improvement opportunities that may not have been captured in the initial
data analysis. These questions should:

1. Be open-ended and exploratory
2. Encourage interviewees to share pain points beyond what was analyzed
3. Uncover hidden inefficiencies and workarounds
4. Identify opportunities unique to this customer's context
5. Explore areas the data analysis might have missed

Focus on questions that reveal:
- Unofficial workarounds and shadow processes
- Frustrations not documented in formal procedures
- Opportunities for automation or AI assistance
- Cross-departmental friction points
- Time-consuming tasks that could be improved"""

        human_template = """Generate discovery questions for finding NEW opportunities:

ALREADY IDENTIFIED AREAS (from data analysis):
{identified_areas}

ROLES TO INTERVIEW: {roles}

KEY THEMES ALREADY COVERED:
{key_themes}

Generate 5-8 discovery questions that explore BEYOND the already identified areas.
These should uncover new customer-specific opportunities.

Return a JSON array:
[
    {{
        "role": "target role",
        "question": "the discovery question",
        "intent": "what new insights we're seeking",
        "follow_ups": ["follow-up 1", "follow-up 2"]
    }}
]

Return ONLY the JSON array."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_template),
        ])

        identified_areas = "\n".join([
            f"- {h.process_area}: {h.description[:100]}"
            for h in hypotheses[:5]
        ])
        key_themes = ", ".join(analysis.get("key_themes", []))

        response = await self.llm.ainvoke(
            prompt.format_messages(
                identified_areas=identified_areas or "No specific areas identified yet",
                roles=", ".join(target_roles),
                key_themes=key_themes or "General process improvement",
            )
        )

        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            questions_data = json.loads(content)

            questions = []
            for q_data in questions_data:
                question = InterviewQuestion(
                    role=q_data.get("role", target_roles[0] if target_roles else "General"),
                    question=q_data.get("question", ""),
                    intent=q_data.get("intent", ""),
                    follow_ups=q_data.get("follow_ups", []),
                    related_hypothesis_id=None,  # Discovery questions aren't tied to hypotheses
                    question_type="discovery",
                )
                questions.append(question)

            return questions

        except Exception as e:
            self.log_error(f"Failed to parse discovery questions: {e}")
            # Return default discovery questions
            return [
                InterviewQuestion(
                    role=target_roles[0] if target_roles else "Manager",
                    question="What tasks or processes take up more of your time than you think they should?",
                    intent="Identify unrecognized inefficiencies",
                    follow_ups=["Why do you think it takes so long?", "What would make it faster?"],
                    question_type="discovery",
                ),
                InterviewQuestion(
                    role=target_roles[0] if target_roles else "Manager",
                    question="If you could change one thing about how work gets done here, what would it be?",
                    intent="Uncover priority improvement areas from employee perspective",
                    follow_ups=["What's preventing that change?", "Who would benefit most?"],
                    question_type="discovery",
                ),
                InterviewQuestion(
                    role=target_roles[0] if target_roles else "Manager",
                    question="Are there any informal workarounds or shortcuts you've developed to get work done?",
                    intent="Discover shadow processes and unofficial procedures",
                    follow_ups=["Why did you develop this workaround?", "Do others use it too?"],
                    question_type="discovery",
                ),
            ]

    async def _generate_hypotheses_from_documents(
        self, state: Dict[str, Any]
    ) -> List[Hypothesis]:
        """
        TIER 2: Generate hypotheses using AI when none were found by Hypothesis Generator.

        This is the second tier in the 3-tier hypothesis generation system. It's activated
        when the Hypothesis Generator Agent (Tier 1) produces no hypotheses from document
        analysis. This method uses an LLM (Gemini, OpenAI, or Anthropic) to analyze document
        summaries and infer likely process inefficiencies.

        Supported LLMs:
        ---------------
        - Google Gemini (default, free tier available)
        - OpenAI GPT-4/GPT-3.5 (requires API key)
        - Anthropic Claude (requires API key)
        Configured in config/settings.py via LLM_PROVIDER setting

        Args:
            state: Current workflow state containing:
                   - document_summaries: List of text summaries from all uploaded documents
                   - project: Client/industry/department information

        Returns:
            List of AI-generated Hypothesis objects, or empty list if generation fails
            Each hypothesis includes:
            - process_area: The business area affected
            - description: Detailed issue description
            - evidence: Supporting evidence from documents
            - confidence: 0.0-1.0 (typically 0.5-0.7 for AI-generated)
            - category: Type of inefficiency
        """
        try:
            # Extract document summaries (generated by Ingestion Agent)
            document_summaries = state.get("document_summaries", [])
            project_data = state.get("project", {})

            # Safety check: Cannot generate hypotheses without document content
            if not document_summaries:
                self.log_info("No document summaries available for AI hypothesis generation")
                return []

            # Format the user prompt with variables
            user_prompt = HYPOTHESIS_GENERATION_USER_PROMPT.format(
                client_name=project_data.get('client_name', 'Unknown'),
                target_departments=', '.join(project_data.get('target_departments', ['All Departments'])),
                industry=project_data.get('industry', 'General'),
                document_summaries='\n\n'.join(document_summaries)
            )

            # Use SystemMessage + HumanMessage for chat models
            from langchain_core.messages import SystemMessage, HumanMessage
            messages = [
                SystemMessage(content=HYPOTHESIS_GENERATION_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt)
            ]
            response = await self.llm.ainvoke(messages)

            content = response.content.strip()

            # ============================================================
            # EXTRACT JSON FROM LLM RESPONSE
            # ============================================================
            # LLMs often wrap JSON in markdown code blocks
            # Handle both ```json and ``` formats
            if "```json" in content:
                # Extract content between ```json and ```
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                # Extract content between ``` and ```
                content = content.split("```")[1].split("```")[0].strip()

            # Parse JSON array of hypotheses
            hypotheses_data = json.loads(content)

            # ============================================================
            # CONVERT JSON TO HYPOTHESIS OBJECTS
            # ============================================================
            # Transform raw AI output into structured Hypothesis objects
            # Provides defaults for missing fields to ensure robustness
            hypotheses = []
            for h_data in hypotheses_data:
                hypothesis = Hypothesis(
                    process_area=h_data.get("process_area", "Unknown"),
                    description=h_data.get("description", ""),
                    evidence=h_data.get("evidence", []),
                    confidence=h_data.get("confidence_score", 0.5),  # AI-generated typically 0.5-0.7
                    category=h_data.get("task_category", "general"),
                )
                hypotheses.append(hypothesis)

            return hypotheses

        except Exception as e:
            # If AI generation fails (network issue, JSON parse error, etc.),
            # return empty list and fall back to Tier 3 (generic hypotheses)
            self.log_error(f"Failed to generate hypotheses from documents: {e}")
            return []

    def _gather_comprehensive_context(
        self,
        state: Dict[str, Any],
        hypotheses: List[Hypothesis]
    ) -> Dict[str, Any]:
        """
        Gather ALL available information for comprehensive interview generation.

        This method is a KEY ENHANCEMENT that ensures the Interview Architect uses
        EVERY piece of available information, not just hypotheses. This creates
        richer, more contextual interview questions that reference actual document
        content and are appropriate for the client's industry and situation.

        What Gets Collected:
        --------------------
        1. DOCUMENTS: Metadata about all uploaded files and URLs
           - Filename, file type (PDF, DOCX, URL, etc.)
           - Source type (file vs URL) - helps identify doc vs reality gaps
           - Processing status and chunk counts

        2. DOCUMENT SUMMARIES: Full text summaries of document content
           - Combined into single text for AI context
           - Provides actual process details not captured in hypotheses
           - Up to 2000 characters included in analysis prompts

        3. PROJECT CONTEXT: Client and business information
           - Client name, industry, target departments
           - Description and creation date
           - Enables industry-appropriate language and terminology

        4. HYPOTHESIS INSIGHTS: Organized hypothesis data
           - High-confidence hypotheses (>= 0.7)
           - Grouped by automation potential (high/medium/low)
           - Process areas covered
           - Full hypothesis objects with all details

        5. WORKFLOW STATE: Messages and progress information
           - Workflow messages from previous agents
           - Helps understand data quality and processing status

        Why This Matters:
        -----------------
        Before this enhancement, interview questions were generated from hypotheses only.
        Now they leverage:
        - Actual document content → Reference specific processes mentioned
        - Industry context → Use appropriate terminology
        - URL vs file distinction → Identify doc vs reality gaps
        - Project details → Personalized questions

        Example Impact:
        ---------------
        OLD (hypothesis-only):
          "What manual processes slow down your work?"

        NEW (comprehensive context):
          "The documentation mentions sales orders require manual entry into
           three different systems. Can you walk me through this process and
           identify which steps are most time-consuming?"

        Args:
            state: Current workflow state with all information collected so far
            hypotheses: List of hypotheses (from any of the 3 tiers)

        Returns:
            Dictionary with organized context containing:
            - documents_count: Number of uploaded documents
            - documents: List of document metadata
            - summaries_count: Number of document summaries
            - document_summaries: List of summary texts
            - combined_summaries: All summaries joined with separators
            - project: Project metadata (client, industry, departments)
            - hypotheses_summary: Organized hypothesis insights
            - hypotheses_full: Complete hypothesis objects
            - workflow_messages: State messages from workflow
            - has_urls: Boolean flag indicating if URLs are included
        """
        # Extract all data from state
        documents = state.get("documents", [])
        document_summaries = state.get("document_summaries", [])
        project_data = state.get("project", {})
        messages = state.get("messages", [])

        # ============================================================
        # ORGANIZE DOCUMENT METADATA
        # ============================================================
        # Extract key metadata from each document for context
        # Distinguishes between uploaded files and web URLs
        doc_details = []
        for doc in documents:
            if isinstance(doc, dict):
                doc_details.append({
                    'filename': doc.get('filename', 'Unknown'),
                    'file_type': doc.get('file_type', 'unknown'),
                    'source_type': doc.get('source_type', 'file'),  # "file" or "url"
                    'source_url': doc.get('source_url'),  # URL if source_type is "url"
                    'processed': doc.get('processed', False),
                    'chunk_count': doc.get('chunk_count', 0)
                })

        # ============================================================
        # COMBINE DOCUMENT SUMMARIES
        # ============================================================
        # Join all summaries with clear separators
        # This combined text is passed to AI analysis for context
        # Limited to 2000 chars in prompts to fit within token limits
        combined_summaries = "\n\n---\n\n".join(document_summaries) if document_summaries else ""

        # ============================================================
        # ORGANIZE PROJECT CONTEXT
        # ============================================================
        # Structure project metadata for easy access
        # This information personalizes interview questions
        project_context = {
            'client_name': project_data.get('client_name', 'Unknown Client'),
            'industry': project_data.get('industry', 'General'),
            'target_departments': project_data.get('target_departments', []),
            'description': project_data.get('description', ''),
            'created_at': project_data.get('created_at', ''),
        }

        # ============================================================
        # ORGANIZE HYPOTHESIS INSIGHTS
        # ============================================================
        # Create structured summary of hypothesis data
        # Organizes by confidence and category
        hypothesis_summary = {
            'total_count': len(hypotheses),
            'high_confidence': [h for h in hypotheses if h.confidence >= 0.7],  # Focus areas
            'by_category': {},  # Grouped by category
            'process_areas': list(set(h.process_area for h in hypotheses))  # Unique areas
        }

        # Group hypotheses by category
        # This helps prioritize interview focus on different types of inefficiencies
        for h in hypotheses:
            cat = h.category
            if cat not in hypothesis_summary['by_category']:
                hypothesis_summary['by_category'][cat] = []
            hypothesis_summary['by_category'][cat].append(h)

        # ============================================================
        # RETURN COMPREHENSIVE CONTEXT
        # ============================================================
        # This dictionary is passed to _analyze_hypotheses and other methods
        # Ensures ALL available information is used in interview generation
        return {
            'documents_count': len(documents),
            'documents': doc_details,
            'summaries_count': len(document_summaries),
            'document_summaries': document_summaries,  # Full list for detailed analysis
            'combined_summaries': combined_summaries,  # Combined text for AI context
            'project': project_context,
            'hypotheses_summary': hypothesis_summary,
            'hypotheses_full': hypotheses,  # Complete hypothesis objects
            'workflow_messages': messages,
            'has_urls': any(d.get('source_type') == 'url' for d in documents if isinstance(d, dict)),  # URL flag
        }

    def _get_generic_hypotheses(self) -> List[Hypothesis]:
        """
        TIER 3: Return generic hypotheses as a last resort fallback.

        This is the final tier in the 3-tier hypothesis generation system. It's activated
        when BOTH Tier 1 (Hypothesis Generator) and Tier 2 (AI generation) fail to produce
        hypotheses. This ensures the workflow NEVER fails completely - even in worst-case
        scenarios, a meaningful interview can still be conducted.

        Why Generic Hypotheses?
        -----------------------
        These represent UNIVERSAL process inefficiencies found in almost all organizations:
        - Manual data entry and documentation
        - Communication silos
        - Approval bottlenecks
        - Manual reporting

        These patterns are so common that even without any document analysis, they provide
        a solid foundation for discovering real issues during stakeholder interviews.

        Hypothesis Characteristics:
        --------------------------
        - Confidence Score: 0.6 (lower than document-based or AI-generated)
        - Evidence: Generic patterns, not document-specific
        - Automation Potential: Based on industry best practices
        - Process Areas: Cover major operational categories

        When Is This Used?
        ------------------
        This tier is activated only when:
        1. No documents were uploaded OR Hypothesis Generator failed (Tier 1 fails)
        2. AND AI generation failed due to:
           - No document summaries available
           - LLM API error (network, auth, rate limit)
           - JSON parsing failure from LLM response

        Interview Quality:
        -----------------
        Even with generic hypotheses, the interview will still be valuable because:
        - Questions probe for common pain points
        - Discovery questions find issues not in hypotheses
        - Human interviewers can adapt based on responses
        - Stakeholders often reveal real issues when prompted about common patterns

        Future Enhancement:
        -------------------
        Could add industry-specific generic hypotheses:
        - Manufacturing: Equipment downtime tracking, quality control
        - Healthcare: Patient intake, insurance verification
        - Finance: Reconciliation, compliance reporting
        Configure via industry setting in project metadata.

        Returns:
            List of 4 generic Hypothesis objects covering common inefficiency patterns
        """
        return [
            # ============================================================
            # HYPOTHESIS 1: Data Entry and Documentation
            # ============================================================
            # RATIONALE: Manual data entry is one of the most common sources
            # of inefficiency and error across all industries
            Hypothesis(
                process_area="Data Entry and Documentation",
                description="Manual data entry and repetitive documentation tasks consume significant time and are prone to errors",
                evidence=["Common pattern in most organizations"],
                confidence=0.6,
                category="manual_process",
            ),

            # ============================================================
            # HYPOTHESIS 2: Communication and Coordination
            # ============================================================
            # RATIONALE: Information silos are a universal organizational challenge
            Hypothesis(
                process_area="Communication and Coordination",
                description="Information silos and inefficient communication channels cause delays and rework",
                evidence=["Typical organizational challenge"],
                confidence=0.6,
                category="communication_gap",
            ),

            # ============================================================
            # HYPOTHESIS 3: Approval and Review Processes
            # ============================================================
            # RATIONALE: Multi-step approvals are common bottlenecks
            Hypothesis(
                process_area="Approval and Review Processes",
                description="Multi-step approval processes with manual routing slow down operations",
                evidence=["Common workflow bottleneck"],
                confidence=0.6,
                category="approvals",
            ),

            # ============================================================
            # HYPOTHESIS 4: Report Generation
            # ============================================================
            # RATIONALE: Manual reporting is time-consuming and error-prone
            Hypothesis(
                process_area="Report Generation",
                description="Manual report compilation and distribution takes valuable time from strategic work",
                evidence=["Frequently reported pain point"],
                confidence=0.6,
                category="manual_process",
            ),
        ]
