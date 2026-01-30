"""
Node 5: Solution Architect Agent
Maps identified gaps to specific AI/Automation tools and generates ROI estimates.
"""

import json
from typing import Any, Dict, List, Optional
import uuid

from langchain_core.prompts import ChatPromptTemplate

from .base import BaseAgent
from src.models.schemas import (
    GapAnalysisItem,
    AnalysisResult,
    SolutionRecommendation,
    TaskCategory,
    Severity,
    Complexity,
    GraphState,
)
from config.settings import settings


# Technology mapping for common automation scenarios
TECH_RECOMMENDATIONS = {
    "data_entry": {
        "tools": ["UiPath", "Automation Anywhere", "Power Automate"],
        "description": "Robotic Process Automation for repetitive data entry",
    },
    "document_processing": {
        "tools": ["Azure Form Recognizer", "AWS Textract", "Google Document AI"],
        "description": "AI-powered document extraction and processing",
    },
    "email_automation": {
        "tools": ["Power Automate", "Zapier", "Make (Integromat)"],
        "description": "Email workflow automation and routing",
    },
    "approval_workflow": {
        "tools": ["ServiceNow", "Jira", "Microsoft Power Automate"],
        "description": "Digital approval workflows with tracking",
    },
    "data_integration": {
        "tools": ["MuleSoft", "Dell Boomi", "Apache Airflow"],
        "description": "System integration and data synchronization",
    },
    "reporting": {
        "tools": ["Power BI", "Tableau", "Looker"],
        "description": "Automated reporting and dashboards",
    },
    "chatbot": {
        "tools": ["Azure Bot Service", "Dialogflow", "Amazon Lex"],
        "description": "Conversational AI for customer/employee queries",
    },
    "scheduling": {
        "tools": ["Calendly", "Microsoft Bookings", "Acuity"],
        "description": "Automated scheduling and calendar management",
    },
    "ocr": {
        "tools": ["ABBYY FineReader", "Tesseract OCR", "Amazon Textract"],
        "description": "Optical Character Recognition for paper documents",
    },
    "ml_classification": {
        "tools": ["Azure ML", "AWS SageMaker", "Google Vertex AI"],
        "description": "Machine learning for classification and prediction",
    },
}


class SolutionArchitectAgent(BaseAgent):
    """
    Node 5: Solution Architect Agent

    Responsibilities:
    - Map identified gaps to specific automation/AI tools
    - Generate implementation recommendations
    - Estimate ROI and implementation complexity
    - Create prioritized solution roadmap
    """

    def __init__(self, **kwargs):
        super().__init__(name="SolutionArchitect", **kwargs)

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate solutions for identified gaps.

        Args:
            state: Current graph state with gap analysis

        Returns:
            Updated state with solution recommendations
        """
        self.log_info("Starting solution architecture")

        try:
            project_id = state.get("project_id")
            gaps_data = state.get("gap_analyses", [])

            if not gaps_data:
                self.log_info("No gaps to generate solutions for")
                state["solutions"] = []
                state["solutioning_complete"] = True
                state["messages"].append("No gaps available for solutioning")
                return state

            # Convert gaps to objects
            gaps = [
                GapAnalysisItem(**g) if isinstance(g, dict) else g
                for g in gaps_data
            ]

            # Generate solutions for each gap
            solutions = await self._generate_solutions(gaps)

            # Calculate priority scores
            prioritized_solutions = self._calculate_priority(solutions)

            # Generate detailed recommendations
            detailed_recommendations = await self._generate_detailed_recommendations(
                prioritized_solutions,
                gaps,
            )

            # Update state
            state["solutions"] = [s.model_dump() for s in prioritized_solutions]
            state["solution_recommendations"] = [
                r.model_dump() for r in detailed_recommendations
            ]
            state["solutioning_complete"] = True
            state["current_node"] = "solution"
            state["messages"].append(
                f"Generated {len(prioritized_solutions)} solution recommendations "
                f"with estimated total monthly savings"
            )

            self.log_info(f"Solution architecture complete: {len(prioritized_solutions)} solutions")
            return state

        except Exception as e:
            self.log_error("Error during solutioning", e)
            state["errors"].append(f"Solutioning error: {str(e)}")
            state["solutioning_complete"] = False
            return state

    async def _generate_solutions(
        self,
        gaps: List[GapAnalysisItem],
    ) -> List[AnalysisResult]:
        """
        Generate solution recommendations for each gap.

        Args:
            gaps: List of identified gaps

        Returns:
            List of analysis results with solutions
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an automation and AI solution architect.
            For each process gap, recommend specific solutions including:

            1. Proposed solution approach
            2. Technology stack recommendations
            3. Estimated ROI (hours saved per month)
            4. Implementation complexity (Low/Medium/High)
            5. Pain point severity (Low/Medium/High/Critical)

            Consider these technology categories:
            - RPA (UiPath, Automation Anywhere, Power Automate)
            - Document AI (Azure Form Recognizer, AWS Textract)
            - Workflow Automation (ServiceNow, Jira, Monday.com)
            - Integration Platforms (MuleSoft, Zapier, Make)
            - Analytics (Power BI, Tableau)
            - Conversational AI (Chatbots, Virtual Assistants)
            - Custom Development (Python, APIs)

            Be realistic about ROI - estimate conservatively.
            """),
            ("human", """Generate solutions for these gaps:

            {gaps}

            Return a JSON array:
            [
                {{
                    "process_step": "the process step",
                    "observed_behavior": "current state",
                    "pain_point_severity": "Low" | "Medium" | "High" | "Critical",
                    "proposed_solution": "description of solution",
                    "tech_stack_recommendation": ["tool1", "tool2"],
                    "estimated_roi_hours": <hours saved per month>,
                    "implementation_complexity": "Low" | "Medium" | "High"
                }}
            ]

            Return ONLY the JSON array."""),
        ])

        gaps_text = "\n\n".join([
            f"""Process Step: {g.process_step}
            Current Behavior: {g.observed_behavior}
            Gap: {g.gap_description}
            Root Cause: {g.root_cause or 'Unknown'}
            Impact: {g.impact}
            Automation Potential: {g.task_category.value}"""
            for g in gaps
        ])

        response = await self.llm.ainvoke(
            prompt.format_messages(gaps=gaps_text)
        )

        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            solutions_data = json.loads(content)

            solutions = []
            for s_data in solutions_data:
                # Map severity string to enum
                severity_str = s_data.get("pain_point_severity", "Medium")
                severity = Severity.MEDIUM
                if severity_str == "Low":
                    severity = Severity.LOW
                elif severity_str == "High":
                    severity = Severity.HIGH
                elif severity_str == "Critical":
                    severity = Severity.CRITICAL

                # Map complexity string to enum
                complexity_str = s_data.get("implementation_complexity", "Medium")
                complexity = Complexity.MEDIUM
                if complexity_str == "Low":
                    complexity = Complexity.LOW
                elif complexity_str == "High":
                    complexity = Complexity.HIGH

                solution = AnalysisResult(
                    process_step=s_data.get("process_step", "Unknown"),
                    observed_behavior=s_data.get("observed_behavior", ""),
                    pain_point_severity=severity,
                    proposed_solution=s_data.get("proposed_solution", ""),
                    tech_stack_recommendation=s_data.get("tech_stack_recommendation", []),
                    estimated_roi_hours=int(s_data.get("estimated_roi_hours", 0)),
                    implementation_complexity=complexity,
                )
                solutions.append(solution)

            return solutions

        except json.JSONDecodeError as e:
            self.log_error(f"Failed to parse solutions: {e}")
            return []

    def _calculate_priority(
        self,
        solutions: List[AnalysisResult],
    ) -> List[AnalysisResult]:
        """
        Calculate priority score for each solution.

        Priority = (ROI * Severity Weight) / Complexity Weight

        Args:
            solutions: List of solutions

        Returns:
            Solutions with priority scores, sorted by priority
        """
        severity_weights = {
            Severity.LOW: 1,
            Severity.MEDIUM: 2,
            Severity.HIGH: 3,
            Severity.CRITICAL: 4,
        }

        complexity_weights = {
            Complexity.LOW: 1,
            Complexity.MEDIUM: 2,
            Complexity.HIGH: 3,
        }

        for solution in solutions:
            roi = solution.estimated_roi_hours
            severity_weight = severity_weights.get(solution.pain_point_severity, 2)
            complexity_weight = complexity_weights.get(solution.implementation_complexity, 2)

            # Priority formula: higher ROI and severity, lower complexity = higher priority
            priority = (roi * severity_weight) / (complexity_weight + 0.1)
            solution.priority_score = min(100, max(0, priority))

        # Sort by priority descending
        solutions.sort(key=lambda s: s.priority_score, reverse=True)

        return solutions

    async def _generate_detailed_recommendations(
        self,
        solutions: List[AnalysisResult],
        gaps: List[GapAnalysisItem],
    ) -> List[SolutionRecommendation]:
        """
        Generate detailed implementation recommendations.

        Args:
            solutions: Prioritized solutions
            gaps: Original gap analysis items

        Returns:
            Detailed solution recommendations
        """
        recommendations = []

        # Create gap lookup
        gap_lookup = {g.process_step: g for g in gaps}

        for solution in solutions[:10]:  # Top 10 solutions
            gap = gap_lookup.get(solution.process_step)
            gap_id = gap.id if gap else str(uuid.uuid4())

            # Estimate costs based on complexity
            cost_ranges = {
                Complexity.LOW: "$2,000 - $10,000",
                Complexity.MEDIUM: "$10,000 - $50,000",
                Complexity.HIGH: "$50,000 - $200,000",
            }

            effort_ranges = {
                Complexity.LOW: 40,
                Complexity.MEDIUM: 160,
                Complexity.HIGH: 480,
            }

            # Calculate financial metrics
            hourly_rate = 50  # Assumed average hourly cost
            monthly_savings = solution.estimated_roi_hours * hourly_rate
            implementation_cost_low = int(cost_ranges.get(
                solution.implementation_complexity, "$10,000 - $50,000"
            ).split(" - ")[0].replace("$", "").replace(",", ""))

            payback_months = implementation_cost_low / monthly_savings if monthly_savings > 0 else 12

            recommendation = SolutionRecommendation(
                id=str(uuid.uuid4()),
                gap_id=gap_id,
                solution_name=f"Automate {solution.process_step}",
                solution_description=solution.proposed_solution,
                technology_stack=solution.tech_stack_recommendation,
                implementation_steps=self._generate_implementation_steps(solution),
                estimated_effort_hours=effort_ranges.get(
                    solution.implementation_complexity, 160
                ),
                estimated_cost_range=cost_ranges.get(
                    solution.implementation_complexity, "$10,000 - $50,000"
                ),
                estimated_monthly_savings=monthly_savings,
                payback_period_months=round(payback_months, 1),
                risks=self._identify_risks(solution),
                prerequisites=self._identify_prerequisites(solution),
            )

            recommendations.append(recommendation)

        return recommendations

    def _generate_implementation_steps(
        self,
        solution: AnalysisResult,
    ) -> List[str]:
        """Generate high-level implementation steps."""
        base_steps = [
            "1. Conduct detailed requirements gathering",
            "2. Design solution architecture",
            "3. Set up development environment",
            "4. Develop and configure solution",
            "5. Perform unit and integration testing",
            "6. Conduct user acceptance testing (UAT)",
            "7. Create documentation and training materials",
            "8. Deploy to production",
            "9. Monitor and optimize",
        ]

        # Add technology-specific steps
        tech_steps = []
        for tech in solution.tech_stack_recommendation:
            tech_lower = tech.lower()
            if "uipath" in tech_lower or "automation" in tech_lower:
                tech_steps.append("Configure RPA bot and define workflow rules")
            elif "api" in tech_lower:
                tech_steps.append("Develop API integrations and error handling")
            elif "ai" in tech_lower or "ml" in tech_lower:
                tech_steps.append("Train and validate AI/ML models")

        return base_steps + tech_steps

    def _identify_risks(self, solution: AnalysisResult) -> List[str]:
        """Identify implementation risks."""
        risks = []

        if solution.implementation_complexity == Complexity.HIGH:
            risks.append("Complex implementation may require specialized expertise")
            risks.append("Higher risk of timeline delays")

        if solution.estimated_roi_hours > 100:
            risks.append("High ROI estimates should be validated during pilot")

        if len(solution.tech_stack_recommendation) > 2:
            risks.append("Multiple technology integrations increase complexity")

        # General risks
        risks.append("Change management required for user adoption")
        risks.append("Existing system dependencies may require updates")

        return risks

    def _identify_prerequisites(self, solution: AnalysisResult) -> List[str]:
        """Identify implementation prerequisites."""
        prerequisites = [
            "Executive sponsorship and budget approval",
            "Stakeholder alignment on requirements",
            "Access to existing systems and data",
        ]

        for tech in solution.tech_stack_recommendation:
            tech_lower = tech.lower()
            if "power" in tech_lower or "microsoft" in tech_lower:
                prerequisites.append("Microsoft 365 or Azure subscription")
            elif "aws" in tech_lower:
                prerequisites.append("AWS account and permissions")
            elif "uipath" in tech_lower:
                prerequisites.append("UiPath license and orchestrator setup")

        return prerequisites
