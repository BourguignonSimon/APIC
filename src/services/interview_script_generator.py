"""
Interview Script Document Generator Service

Generates interview scripts in Markdown format
and stores them in project-specific directories.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from config.settings import settings

logger = logging.getLogger(__name__)


class InterviewScriptGenerator:
    """
    Service for generating interview script documents in Markdown format.

    Users can convert the Markdown output to other formats (PDF, DOCX) as needed
    using external tools like pandoc.
    """

    def __init__(self):
        """Initialize the generator with configured scripts directory."""
        self.scripts_dir = Path(settings.SCRIPTS_DIR)
        self.scripts_dir.mkdir(parents=True, exist_ok=True)

    def _extract_customer_context(self, interview_script: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract customer context from flattened interview script fields.

        Args:
            interview_script: The interview script data with flattened customer fields

        Returns:
            Dict with customer context data, or empty dict if no content
        """
        context = {
            "business_overview": interview_script.get("customer_business_overview", ""),
            "organization_structure": interview_script.get("customer_organization_structure", ""),
            "current_challenges": interview_script.get("customer_challenges", []),
            "key_processes": interview_script.get("customer_key_processes", []),
            "stakeholders": interview_script.get("customer_stakeholders", []),
            "industry_context": interview_script.get("customer_industry_context", ""),
            "data_sources_summary": interview_script.get("customer_data_sources_summary", ""),
        }
        # Return empty dict if no meaningful content
        has_content = any([
            context["business_overview"],
            context["organization_structure"],
            context["current_challenges"],
            context["key_processes"],
            context["stakeholders"],
            context["industry_context"],
            context["data_sources_summary"],
        ])
        return context if has_content else {}

    def get_project_scripts_dir(self, project_id: str) -> Path:
        """
        Get or create the scripts directory for a specific project.

        Args:
            project_id: The project ID

        Returns:
            Path to the project's scripts directory
        """
        project_dir = self.scripts_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir

    def generate(
        self,
        interview_script: Dict[str, Any],
        project: Dict[str, Any],
    ) -> str:
        """
        Generate interview script in Markdown format.

        Args:
            interview_script: The interview script data
            project: Project information

        Returns:
            Path to the generated Markdown file
        """
        return self.generate_markdown(interview_script, project)

    def generate_markdown(
        self,
        interview_script: Dict[str, Any],
        project: Dict[str, Any],
    ) -> str:
        """
        Generate interview script as a Markdown document.

        Args:
            interview_script: The interview script data
            project: Project information

        Returns:
            Path to the generated Markdown file
        """
        project_id = interview_script.get("project_id", project.get("id", "unknown"))
        project_dir = self.get_project_scripts_dir(project_id)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        client_name = project.get("client_name", "client").replace(" ", "_")
        filename = f"interview_script_{client_name}_{timestamp}.md"
        filepath = project_dir / filename

        # Build markdown content
        lines = []

        # Header
        lines.append("# Interview Script")
        lines.append("")
        lines.append(f"**Project:** {project.get('project_name', 'N/A')}")
        lines.append(f"**Client:** {project.get('client_name', 'N/A')}")
        lines.append("")

        # Metadata
        lines.append("## Overview")
        lines.append("")
        lines.append(f"| Field | Value |")
        lines.append(f"|-------|-------|")
        lines.append(f"| Target Departments | {', '.join(interview_script.get('target_departments', []))} |")
        lines.append(f"| Target Roles | {', '.join(interview_script.get('target_roles', []))} |")
        lines.append(f"| Estimated Duration | {interview_script.get('estimated_duration_minutes', 60)} minutes |")
        lines.append(f"| Generated | {datetime.now().strftime('%B %d, %Y at %I:%M %p')} |")
        lines.append("")

        # Purpose
        lines.append("## Purpose")
        lines.append("")
        lines.append("This interview script is designed to help identify improvement opportunities "
                    "and potential cost savings in the organization's processes. The questions focus on "
                    "uncovering inefficiencies, workarounds, and areas where automation could provide value.")
        lines.append("")

        # Customer Context Section
        customer_context = self._extract_customer_context(interview_script)
        if customer_context:
            lines.append("## Customer Context")
            lines.append("")

            if customer_context.get("business_overview"):
                lines.append("**Business Overview:**")
                lines.append(customer_context.get("business_overview", ""))
                lines.append("")

            if customer_context.get("organization_structure"):
                lines.append("**Organization Structure:**")
                lines.append(customer_context.get("organization_structure", ""))
                lines.append("")

            if customer_context.get("industry_context"):
                lines.append("**Industry Context:**")
                lines.append(customer_context.get("industry_context", ""))
                lines.append("")

            current_challenges = customer_context.get("current_challenges", [])
            if current_challenges:
                lines.append("**Current Challenges Identified:**")
                for challenge in current_challenges:
                    lines.append(f"- {challenge}")
                lines.append("")

            key_processes = customer_context.get("key_processes", [])
            if key_processes:
                lines.append("**Key Processes Under Review:**")
                for process in key_processes:
                    lines.append(f"- {process}")
                lines.append("")

            stakeholders = customer_context.get("stakeholders", [])
            if stakeholders:
                lines.append(f"**Key Stakeholders:** {', '.join(stakeholders)}")
                lines.append("")

            if customer_context.get("data_sources_summary"):
                lines.append("**Data Sources Analyzed:**")
                lines.append(customer_context.get("data_sources_summary", ""))
                lines.append("")

        # Introduction
        lines.append("## Introduction")
        lines.append("")
        introduction = interview_script.get("introduction", "")
        lines.append(introduction)
        lines.append("")

        # Diagnostic Form - Leads to Validate
        diagnostic_leads = interview_script.get("diagnostic_leads", [])
        if diagnostic_leads:
            lines.append("---")
            lines.append("")
            lines.append("## Diagnostic Form: AI-Generated Leads to Validate")
            lines.append("")
            lines.append("The following leads were identified through AI analysis of the customer's data. "
                        "Use this form to validate or invalidate each lead during interviews.")
            lines.append("")

            lead_num = 1
            for lead in diagnostic_leads:
                confidence = lead.get("confidence", 0.5)
                confidence_pct = int(confidence * 100)

                lines.append(f"### Lead #{lead_num}: {lead.get('lead_summary', '')}")
                lines.append("")
                lines.append(f"*Confidence: {confidence_pct}% | Category: {lead.get('category', 'General')}*")
                lines.append("")

                validation_questions = lead.get("validation_questions", [])
                if validation_questions:
                    lines.append("**Validation Questions:**")
                    for vq in validation_questions:
                        lines.append(f"- [ ] {vq}")
                    lines.append("")

                expected_evidence = lead.get("expected_evidence", [])
                if expected_evidence:
                    lines.append("**Expected Evidence (if lead is valid):**")
                    for ev in expected_evidence:
                        lines.append(f"- {ev}")
                    lines.append("")

                lines.append("**Validation Result:**")
                lines.append("- [ ] Confirmed")
                lines.append("- [ ] Partially Confirmed")
                lines.append("- [ ] Not Confirmed")
                lines.append("- [ ] Needs More Info")
                lines.append("")
                lines.append("**Notes:** _______________________________________________")
                lines.append("")
                lines.append("---")
                lines.append("")
                lead_num += 1

        # Part A: Validation Questions
        lines.append("---")
        lines.append("")
        lines.append("## Part A: Validation Questions")
        lines.append("")
        lines.append("These questions are designed to validate or invalidate the AI-generated leads above.")
        lines.append("")

        questions = interview_script.get("questions", [])

        # Group questions by role
        questions_by_role: Dict[str, List] = {}
        for q in questions:
            role = q.get("role", "General")
            if role not in questions_by_role:
                questions_by_role[role] = []
            questions_by_role[role].append(q)

        question_num = 1
        for role, role_questions in questions_by_role.items():
            lines.append(f"### Questions for: {role}")
            lines.append("")

            for q in role_questions:
                # Main question
                lines.append(f"**Q{question_num}: {q.get('question', '')}**")
                lines.append("")

                # Intent
                intent = q.get("intent", "")
                if intent:
                    lines.append(f"*Intent: {intent}*")
                    lines.append("")

                # Follow-ups
                follow_ups = q.get("follow_ups", [])
                if follow_ups:
                    lines.append("Follow-up questions:")
                    for fu in follow_ups:
                        lines.append(f"- {fu}")
                    lines.append("")

                lines.append("---")
                lines.append("")
                question_num += 1

        # Part B: Discovery Questions
        discovery_questions = interview_script.get("discovery_questions", [])
        if discovery_questions:
            lines.append("## Part B: Discovery Questions")
            lines.append("")
            lines.append("These open-ended questions are designed to identify NEW improvement opportunities "
                        "specific to this customer that may not have been captured in the data analysis.")
            lines.append("")

            # Group discovery questions by role
            disc_by_role: Dict[str, List] = {}
            for q in discovery_questions:
                role = q.get("role", "General")
                if role not in disc_by_role:
                    disc_by_role[role] = []
                disc_by_role[role].append(q)

            disc_num = 1
            for role, role_questions in disc_by_role.items():
                lines.append(f"### Discovery Questions for: {role}")
                lines.append("")

                for q in role_questions:
                    lines.append(f"**D{disc_num}: {q.get('question', '')}**")
                    lines.append("")

                    intent = q.get("intent", "")
                    if intent:
                        lines.append(f"*Intent: {intent}*")
                        lines.append("")

                    follow_ups = q.get("follow_ups", [])
                    if follow_ups:
                        lines.append("Follow-up questions:")
                        for fu in follow_ups:
                            lines.append(f"- {fu}")
                        lines.append("")

                    lines.append("---")
                    lines.append("")
                    disc_num += 1

        # Closing Notes
        lines.append("## Closing Notes")
        lines.append("")
        closing_notes = interview_script.get("closing_notes", "")
        lines.append(closing_notes)
        lines.append("")

        # Tips
        lines.append("## Tips for Interviewers")
        lines.append("")
        tips = [
            "Listen actively and take detailed notes on specific examples provided.",
            "Look for quantifiable impacts - hours spent, frequency of issues, number of people affected.",
            "Ask for concrete examples when interviewees describe problems.",
            "Note any workarounds or unofficial processes mentioned.",
            "Pay attention to emotional responses - frustration often indicates significant pain points.",
            "Ask 'why' multiple times to get to root causes.",
        ]
        for tip in tips:
            lines.append(f"- {tip}")
        lines.append("")

        # Notes section
        lines.append("---")
        lines.append("")
        lines.append("## Interview Notes")
        lines.append("")
        lines.append("*Use this section to capture notes during the interview:*")
        lines.append("")
        lines.append("### Key Pain Points Identified")
        lines.append("")
        lines.append("1. ")
        lines.append("2. ")
        lines.append("3. ")
        lines.append("")
        lines.append("### Potential Improvements")
        lines.append("")
        lines.append("1. ")
        lines.append("2. ")
        lines.append("3. ")
        lines.append("")
        lines.append("### Cost/Time Savings Opportunities")
        lines.append("")
        lines.append("| Area | Current Time/Cost | Potential Savings |")
        lines.append("|------|-------------------|-------------------|")
        lines.append("|      |                   |                   |")
        lines.append("|      |                   |                   |")
        lines.append("|      |                   |                   |")
        lines.append("")

        # Write to file
        content = "\n".join(lines)
        filepath.write_text(content, encoding="utf-8")

        logger.info(f"Markdown interview script generated: {filepath}")
        return str(filepath)

    def get_script_file(self, project_id: str) -> Optional[str]:
        """
        Get path to the most recent interview script file for a project.

        Args:
            project_id: The project ID

        Returns:
            Path to the most recent Markdown file, or None if not found
        """
        project_dir = self.get_project_scripts_dir(project_id)

        files = list(project_dir.glob("*.md"))
        if files:
            # Get most recent file
            most_recent = max(files, key=lambda f: f.stat().st_mtime)
            return str(most_recent)

        return None

    def list_all_scripts(self, project_id: str) -> List[Dict[str, Any]]:
        """
        List all interview script files for a project.

        Args:
            project_id: The project ID

        Returns:
            List of script file metadata
        """
        project_dir = self.get_project_scripts_dir(project_id)

        scripts = []

        for file_path in project_dir.glob("*.md"):
            stat = file_path.stat()
            scripts.append({
                "filename": file_path.name,
                "path": str(file_path),
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })

        # Sort by modification time, most recent first
        scripts.sort(key=lambda x: x["modified_at"], reverse=True)

        return scripts


# Global instance
interview_script_generator = InterviewScriptGenerator()


def get_interview_script_generator() -> InterviewScriptGenerator:
    """Get the global interview script generator instance."""
    return interview_script_generator
