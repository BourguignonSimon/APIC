"""
Node 3: Interview Architect Agent
Generates dynamic interview scripts based on hypotheses.
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate

from .base import BaseAgent, get_llm, extract_json
from src.models.schemas import (
    Hypothesis,
    InterviewQuestion,
    InterviewScript,
    GraphState,
)
from config.settings import settings




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
        Generate interview script based on hypotheses.

        Args:
            state: Current graph state with hypotheses

        Returns:
            Updated state with interview script (SUSPENDED for human interview)
        """
        try:
            project_id = state.get("project_id")
            hypotheses_data = state.get("hypotheses", [])
            target_departments = state.get("project", {}).get("target_departments", [])

            hypotheses = [
                Hypothesis(**h) if isinstance(h, dict) else h
                for h in hypotheses_data
            ]

            if not hypotheses:
                state["interview_script"] = None
                state["script_generation_complete"] = True
                state["messages"].append("No hypotheses available for interview generation")
                return state

            analysis = await self._analyze_hypotheses(hypotheses, target_departments)

            target_roles = await self._determine_target_roles(
                hypotheses,
                target_departments,
                analysis,
            )

            questions = await self._generate_questions(
                hypotheses,
                target_roles,
                analysis,
            )

            introduction = await self._generate_introduction(
                hypotheses,
                target_departments,
                analysis,
            )

            closing_notes = await self._generate_closing_notes(
                hypotheses,
                questions,
                analysis,
            )

            estimated_duration = await self._estimate_duration(
                questions,
                analysis,
            )

            interview_script = InterviewScript(
                project_id=project_id,
                target_departments=target_departments or self._extract_departments(hypotheses),
                target_roles=target_roles,
                introduction=introduction,
                questions=questions,
                closing_notes=closing_notes,
                estimated_duration_minutes=estimated_duration,
                generated_at=datetime.utcnow(),
            )

            state["interview_script"] = interview_script.model_dump()
            state["script_generation_complete"] = True
            state["is_suspended"] = True
            state["suspension_reason"] = "Awaiting interview transcript"
            state["current_node"] = "interview"
            state["messages"].append(
                f"Generated interview script with {len(questions)} questions. "
                "Awaiting interview transcript."
            )

            return state

        except Exception as e:
            self.log_error("Interview script generation failed", e)
            state["errors"].append(f"Interview script error: {str(e)}")
            state["script_generation_complete"] = False
            return state

    async def _analyze_hypotheses(
        self,
        hypotheses: List[Hypothesis],
        departments: List[str],
    ) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of hypotheses to identify key themes,
        priorities, and focus areas for the interview script.

        Args:
            hypotheses: List of hypotheses to analyze
            departments: Target departments

        Returns:
            Analysis dictionary with themes, priorities, and recommendations
        """
        system_prompt = """You are an expert management consultant analyzing operational
inefficiencies. Perform a comprehensive analysis of the provided hypotheses to identify:

1. Key themes and patterns across the hypotheses
2. Priority areas that require the deepest investigation
3. Potential root causes and interconnections between issues
4. Risk areas that could indicate systemic problems
5. Specific "Dull, Dirty, Dangerous" work patterns (repetitive, unpleasant, risky tasks)

Your analysis will guide the creation of a targeted interview script."""

        human_template = """Analyze the following hypotheses and provide a structured analysis:

HYPOTHESES:
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
                hypotheses=hypotheses_text,
                departments=", ".join(departments) if departments else "Not specified",
            )
        )

        try:
            return extract_json(response.content)
        except Exception:
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
            roles = extract_json(response.content)
            if isinstance(roles, list):
                return [str(role) for role in roles]
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
            questions_data = extract_json(response.content)

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

        except Exception:
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
