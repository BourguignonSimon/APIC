"""
Node 3: Interview Architect Agent
Generates dynamic interview scripts based on hypotheses.
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate

from .base import BaseAgent, get_llm
from src.models.schemas import (
    Hypothesis,
    InterviewQuestion,
    InterviewScript,
    GraphState,
)
from config.settings import settings


# Role-specific question templates
ROLE_TEMPLATES = {
    "executive": {
        "focus_areas": ["strategic priorities", "business outcomes", "resource allocation"],
        "question_style": "high-level, strategic, outcome-focused",
    },
    "manager": {
        "focus_areas": ["team processes", "bottlenecks", "resource constraints"],
        "question_style": "operational, process-oriented, team-focused",
    },
    "operational": {
        "focus_areas": ["daily tasks", "pain points", "workarounds"],
        "question_style": "detailed, task-specific, practical",
    },
    "technical": {
        "focus_areas": ["systems", "integrations", "data flows"],
        "question_style": "technical, system-oriented, data-focused",
    },
}


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
        self.log_info("Starting interview script generation")

        try:
            project_id = state.get("project_id")
            hypotheses_data = state.get("hypotheses", [])
            target_departments = state.get("project", {}).get("target_departments", [])

            # Convert hypothesis dicts to objects
            hypotheses = [
                Hypothesis(**h) if isinstance(h, dict) else h
                for h in hypotheses_data
            ]

            if not hypotheses:
                self.log_info("No hypotheses to base interview on")
                state["interview_script"] = None
                state["script_generation_complete"] = True
                state["messages"].append("No hypotheses available for interview generation")
                return state

            # Determine roles to interview
            target_roles = await self._determine_target_roles(
                hypotheses,
                target_departments,
            )

            # Generate questions for each role
            questions = await self._generate_questions(
                hypotheses,
                target_roles,
            )

            # Create the interview script
            interview_script = InterviewScript(
                project_id=project_id,
                target_departments=target_departments or self._extract_departments(hypotheses),
                target_roles=target_roles,
                introduction=self._generate_introduction(hypotheses),
                questions=questions,
                closing_notes=self._generate_closing_notes(),
                estimated_duration_minutes=self._estimate_duration(len(questions)),
                generated_at=datetime.utcnow(),
            )

            # Update state - SUSPEND for human interview
            state["interview_script"] = interview_script.model_dump()
            state["script_generation_complete"] = True
            state["is_suspended"] = True
            state["suspension_reason"] = "Awaiting interview transcript"
            state["current_node"] = "interview"
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

    async def _determine_target_roles(
        self,
        hypotheses: List[Hypothesis],
        departments: List[str],
    ) -> List[str]:
        """
        Determine which roles should be interviewed based on hypotheses.

        Args:
            hypotheses: List of hypotheses
            departments: Target departments

        Returns:
            List of recommended roles to interview
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert management consultant. Based on the
            hypotheses about operational inefficiencies, determine which roles
            should be interviewed to validate these hypotheses.

            Consider roles that:
            1. Are directly involved in the suspected inefficient processes
            2. Have visibility into the day-to-day operations
            3. Can provide insight into workarounds and pain points
            4. Have decision-making authority over process changes
            """),
            ("human", """Based on these hypotheses, recommend 3-5 roles to interview:

            HYPOTHESES:
            {hypotheses}

            TARGET DEPARTMENTS: {departments}

            Return a JSON array of role titles (e.g., ["CFO", "Operations Manager", "Data Entry Clerk"]).
            Return ONLY the JSON array."""),
        ])

        hypotheses_text = "\n".join([
            f"- {h.process_area}: {h.description}"
            for h in hypotheses
        ])

        response = await self.llm.ainvoke(
            prompt.format_messages(
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
    ) -> List[InterviewQuestion]:
        """
        Generate interview questions based on hypotheses and target roles.

        Args:
            hypotheses: List of hypotheses to validate
            target_roles: Roles to be interviewed

        Returns:
            List of interview questions
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert management consultant preparing for
            client interviews. Generate targeted questions that will:

            1. Validate or invalidate the hypotheses about inefficiencies
            2. Uncover the "Dull, Dirty, Dangerous" tasks (repetitive, unpleasant, risky)
            3. Identify hidden workarounds and unofficial processes
            4. Understand the gap between documented procedures (SOPs) and reality
            5. Quantify the impact of current pain points

            For each question, specify:
            - The target role
            - The question itself (open-ended)
            - The intent (what we're trying to learn)
            - Potential follow-up questions

            Make questions conversational and non-leading. Focus on understanding
            the actual workflow, not just confirming assumptions.
            """),
            ("human", """Generate interview questions for the following context:

            HYPOTHESES TO VALIDATE:
            {hypotheses}

            ROLES TO INTERVIEW: {roles}

            Generate 8-15 questions total, distributed across roles.

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

            Return ONLY the JSON array."""),
        ])

        hypotheses_text = "\n".join([
            f"[{h.id}] {h.process_area}: {h.description} (Category: {h.category})"
            for h in hypotheses
        ])

        response = await self.llm.ainvoke(
            prompt.format_messages(
                hypotheses=hypotheses_text,
                roles=", ".join(target_roles),
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

    def _generate_introduction(self, hypotheses: List[Hypothesis]) -> str:
        """Generate introduction for the interview."""
        categories = set(h.category for h in hypotheses)
        focus_areas = ", ".join(categories)

        return f"""Thank you for taking the time to speak with us today. We're conducting
this interview as part of a process improvement initiative. Our goal is to understand
how work actually gets done day-to-day, identify any challenges or pain points, and
find opportunities for improvement.

Based on our initial document review, we're particularly interested in exploring areas
related to: {focus_areas}.

There are no wrong answers - we want to understand your real experience. Everything
discussed will be used to help improve processes and make your work easier.

Do you have any questions before we begin?"""

    def _generate_closing_notes(self) -> str:
        """Generate closing notes for the interview."""
        return """Thank you for sharing your insights today. Your input is invaluable
for understanding how we can improve processes.

A few final questions:
- Is there anything else you'd like to share that we haven't covered?
- Who else would you recommend we speak with?
- What would be your top priority for process improvement?

We'll be synthesizing this feedback along with other interviews and will share our
findings and recommendations. Please feel free to reach out if you think of anything
else you'd like to add."""

    def _estimate_duration(self, num_questions: int) -> int:
        """Estimate interview duration based on question count."""
        base_time = 15  # intro and closing
        per_question = 5  # minutes per question with follow-ups
        return base_time + (num_questions * per_question)

    def _extract_departments(self, hypotheses: List[Hypothesis]) -> List[str]:
        """Extract department names from hypothesis process areas."""
        departments = set()
        for h in hypotheses:
            # Simple extraction - could be enhanced
            area = h.process_area.split()[0] if h.process_area else "Operations"
            departments.add(area)
        return list(departments)
