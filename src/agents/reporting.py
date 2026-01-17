"""
Node 6: Reporting Engine Agent
Compiles all data into a professional deliverable (PDF Report).
"""

import json
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

from langchain_core.prompts import ChatPromptTemplate

from .base import BaseAgent, get_llm
from src.models.schemas import (
    Report,
    ExecutiveSummary,
    CurrentVsFutureState,
    Hypothesis,
    GapAnalysisItem,
    AnalysisResult,
    SolutionRecommendation,
    GraphState,
)
from config.settings import settings


class ReportingAgent(BaseAgent):
    """
    Node 6: Reporting Engine Agent

    Responsibilities:
    - Compile all analysis into a comprehensive report
    - Generate executive summary
    - Create current vs future state comparisons
    - Build implementation roadmap
    - Generate professional PDF deliverable
    """

    def __init__(self, **kwargs):
        super().__init__(name="ReportingEngine", **kwargs)

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate the final report.

        Args:
            state: Current graph state with all analysis

        Returns:
            Updated state with final report
        """
        self.log_info("Starting report generation")

        try:
            project_id = state.get("project_id")
            project = state.get("project", {})

            # Gather all components
            hypotheses = [
                Hypothesis(**h) if isinstance(h, dict) else h
                for h in state.get("hypotheses", [])
            ]
            gaps = [
                GapAnalysisItem(**g) if isinstance(g, dict) else g
                for g in state.get("gap_analyses", [])
            ]
            solutions = [
                AnalysisResult(**s) if isinstance(s, dict) else s
                for s in state.get("solutions", [])
            ]
            recommendations = [
                SolutionRecommendation(**r) if isinstance(r, dict) else r
                for r in state.get("solution_recommendations", [])
            ]

            # Generate executive summary
            executive_summary = await self._generate_executive_summary(
                hypotheses, gaps, solutions, recommendations
            )

            # Generate current vs future state
            current_vs_future = await self._generate_current_vs_future(
                gaps, solutions
            )

            # Generate implementation roadmap
            roadmap = await self._generate_roadmap(recommendations)

            # Extract interview insights
            interview_insights = await self._extract_insights(
                state.get("transcript", "")
            )

            # Create the report
            report = Report(
                id=str(uuid.uuid4()),
                project_id=project_id,
                title=f"Process Improvement Analysis - {project.get('client_name', 'Client')}",
                executive_summary=executive_summary,
                hypotheses=hypotheses,
                interview_insights=interview_insights,
                gap_analyses=gaps,
                solutions=solutions,
                current_vs_future=current_vs_future,
                implementation_roadmap=roadmap,
                appendix={
                    "methodology": "APIC Consultant Graph Analysis",
                    "documents_analyzed": len(state.get("documents", [])),
                    "confidence_scores": {
                        h.process_area: h.confidence for h in hypotheses
                    },
                },
                generated_at=datetime.utcnow(),
            )

            # Generate PDF
            pdf_path = await self._generate_pdf(report, project)

            # Update state
            state["report"] = report.model_dump()
            state["report_complete"] = True
            state["report_pdf_path"] = pdf_path
            state["current_node"] = "reporting"
            state["messages"].append(
                f"Report generated successfully. PDF available at: {pdf_path}"
            )

            self.log_info("Report generation complete")
            return state

        except Exception as e:
            self.log_error("Error generating report", e)
            state["errors"].append(f"Report generation error: {str(e)}")
            state["report_complete"] = False
            return state

    async def _generate_executive_summary(
        self,
        hypotheses: List[Hypothesis],
        gaps: List[GapAnalysisItem],
        solutions: List[AnalysisResult],
        recommendations: List[SolutionRecommendation],
    ) -> ExecutiveSummary:
        """
        Generate the executive summary section.

        Args:
            hypotheses: List of hypotheses
            gaps: List of gap analyses
            solutions: List of solutions
            recommendations: List of recommendations

        Returns:
            Executive summary
        """
        # Calculate financial metrics
        total_monthly_savings = sum(r.estimated_monthly_savings for r in recommendations)
        total_annual_savings = total_monthly_savings * 12

        # Estimate implementation costs
        cost_estimate_low = 0
        cost_estimate_high = 0
        for r in recommendations:
            range_parts = r.estimated_cost_range.replace("$", "").replace(",", "").split(" - ")
            if len(range_parts) == 2:
                cost_estimate_low += int(range_parts[0])
                cost_estimate_high += int(range_parts[1])

        avg_cost = (cost_estimate_low + cost_estimate_high) / 2

        # Calculate ROI
        roi_percentage = ((total_annual_savings - avg_cost) / avg_cost * 100) if avg_cost > 0 else 0

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a management consultant writing an executive summary.
            Be concise, professional, and focus on business value."""),
            ("human", """Write a brief executive summary (2-3 paragraphs) based on:

            - {num_hypotheses} initial hypotheses about inefficiencies
            - {num_gaps} gaps identified between documented and actual processes
            - {num_solutions} automation opportunities identified
            - Potential annual savings: ${annual_savings:,.0f}
            - Estimated implementation cost: ${implementation_cost:,.0f}
            - Projected ROI: {roi:.1f}%

            Key findings:
            {key_findings}

            Write a professional summary suitable for C-level executives."""),
        ])

        key_findings = "\n".join([
            f"- {s.process_step}: {s.proposed_solution}"
            for s in solutions[:5]
        ])

        response = await self.llm.ainvoke(
            prompt.format_messages(
                num_hypotheses=len(hypotheses),
                num_gaps=len(gaps),
                num_solutions=len(solutions),
                annual_savings=total_annual_savings,
                implementation_cost=avg_cost,
                roi=roi_percentage,
                key_findings=key_findings,
            )
        )

        # Extract key findings and recommendations
        top_findings = [
            f"{h.process_area}: {h.description}"
            for h in sorted(hypotheses, key=lambda x: x.confidence, reverse=True)[:5]
        ]

        top_recommendations = [
            f"{s.process_step}: {s.proposed_solution}"
            for s in sorted(solutions, key=lambda x: x.priority_score, reverse=True)[:5]
        ]

        return ExecutiveSummary(
            overview=response.content,
            key_findings=top_findings,
            top_recommendations=top_recommendations,
            total_potential_savings=total_annual_savings,
            total_implementation_cost=avg_cost,
            overall_roi_percentage=roi_percentage,
        )

    async def _generate_current_vs_future(
        self,
        gaps: List[GapAnalysisItem],
        solutions: List[AnalysisResult],
    ) -> List[CurrentVsFutureState]:
        """
        Generate current vs future state comparisons.

        Args:
            gaps: List of gap analyses
            solutions: List of solutions

        Returns:
            List of current vs future state comparisons
        """
        comparisons = []

        # Create solution lookup
        solution_lookup = {s.process_step: s for s in solutions}

        for gap in gaps[:10]:  # Top 10 gaps
            solution = solution_lookup.get(gap.process_step)

            future_state = "Optimized workflow"
            improvement = "Process efficiency improvement"

            if solution:
                future_state = solution.proposed_solution
                improvement = f"Estimated {solution.estimated_roi_hours} hours saved monthly"

            comparison = CurrentVsFutureState(
                process_area=gap.process_step,
                current_state=gap.observed_behavior,
                future_state=future_state,
                improvement_description=improvement,
            )
            comparisons.append(comparison)

        return comparisons

    async def _generate_roadmap(
        self,
        recommendations: List[SolutionRecommendation],
    ) -> List[Dict[str, Any]]:
        """
        Generate implementation roadmap.

        Args:
            recommendations: List of recommendations

        Returns:
            Implementation roadmap
        """
        roadmap = []

        # Phase 1: Quick Wins (Low complexity, high ROI)
        quick_wins = [
            r for r in recommendations
            if "Low" in r.estimated_cost_range.split(" - ")[0][:20]
        ][:3]

        if quick_wins:
            roadmap.append({
                "phase": "Phase 1: Quick Wins",
                "description": "Low-effort, high-impact improvements",
                "initiatives": [
                    {
                        "name": r.solution_name,
                        "description": r.solution_description,
                        "estimated_effort": f"{r.estimated_effort_hours} hours",
                        "estimated_savings": f"${r.estimated_monthly_savings:,.0f}/month",
                    }
                    for r in quick_wins
                ],
            })

        # Phase 2: Foundation (Medium complexity)
        foundation = [
            r for r in recommendations
            if r not in quick_wins
        ][:4]

        if foundation:
            roadmap.append({
                "phase": "Phase 2: Foundation",
                "description": "Core automation and integration projects",
                "initiatives": [
                    {
                        "name": r.solution_name,
                        "description": r.solution_description,
                        "estimated_effort": f"{r.estimated_effort_hours} hours",
                        "estimated_savings": f"${r.estimated_monthly_savings:,.0f}/month",
                    }
                    for r in foundation
                ],
            })

        # Phase 3: Transformation (Remaining high-impact items)
        remaining = [
            r for r in recommendations
            if r not in quick_wins and r not in foundation
        ][:3]

        if remaining:
            roadmap.append({
                "phase": "Phase 3: Transformation",
                "description": "Strategic transformation initiatives",
                "initiatives": [
                    {
                        "name": r.solution_name,
                        "description": r.solution_description,
                        "estimated_effort": f"{r.estimated_effort_hours} hours",
                        "estimated_savings": f"${r.estimated_monthly_savings:,.0f}/month",
                    }
                    for r in remaining
                ],
            })

        return roadmap

    async def _extract_insights(self, transcript: str) -> List[str]:
        """
        Extract key insights from the interview transcript.

        Args:
            transcript: Interview transcript

        Returns:
            List of key insights
        """
        if not transcript:
            return ["No interview transcript available"]

        prompt = ChatPromptTemplate.from_messages([
            ("system", """Extract key insights from the interview transcript.
            Focus on:
            - Pain points mentioned
            - Workarounds described
            - Process inefficiencies
            - Improvement suggestions from interviewees
            """),
            ("human", """Extract 5-8 key insights from this transcript:

            {transcript}

            Return a JSON array of strings.
            Return ONLY the JSON array."""),
        ])

        response = await self.llm.ainvoke(
            prompt.format_messages(transcript=transcript[:5000])
        )

        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            insights = json.loads(content)
            return insights if isinstance(insights, list) else [response.content]
        except Exception:
            return [response.content]

    async def _generate_pdf(
        self,
        report: Report,
        project: Dict[str, Any],
    ) -> str:
        """
        Generate PDF report.

        Args:
            report: Report data
            project: Project information

        Returns:
            Path to generated PDF
        """
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            PageBreak
        )
        from reportlab.lib import colors

        # Ensure reports directory exists
        os.makedirs(settings.REPORTS_DIR, exist_ok=True)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        client_name = project.get("client_name", "client").replace(" ", "_")
        filename = f"{client_name}_report_{timestamp}.pdf"
        filepath = os.path.join(settings.REPORTS_DIR, filename)

        # Create document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
        )

        # Build content
        content = []

        # Title
        content.append(Paragraph(report.title, title_style))
        content.append(Spacer(1, 12))
        content.append(Paragraph(
            f"Generated: {report.generated_at.strftime('%B %d, %Y')}",
            styles['Normal']
        ))
        content.append(Spacer(1, 24))

        # Executive Summary
        content.append(Paragraph("Executive Summary", heading_style))
        content.append(Paragraph(report.executive_summary.overview, styles['Normal']))
        content.append(Spacer(1, 12))

        # Key Metrics Table
        metrics_data = [
            ["Metric", "Value"],
            ["Potential Annual Savings", f"${report.executive_summary.total_potential_savings:,.0f}"],
            ["Implementation Cost", f"${report.executive_summary.total_implementation_cost:,.0f}"],
            ["Projected ROI", f"{report.executive_summary.overall_roi_percentage:.1f}%"],
        ]
        metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        content.append(metrics_table)
        content.append(PageBreak())

        # Key Findings
        content.append(Paragraph("Key Findings", heading_style))
        for finding in report.executive_summary.key_findings:
            content.append(Paragraph(f"• {finding}", styles['Normal']))
        content.append(Spacer(1, 24))

        # Recommendations
        content.append(Paragraph("Top Recommendations", heading_style))
        for rec in report.executive_summary.top_recommendations:
            content.append(Paragraph(f"• {rec}", styles['Normal']))
        content.append(PageBreak())

        # Current vs Future State
        content.append(Paragraph("Current vs Future State", heading_style))
        for comparison in report.current_vs_future:
            content.append(Paragraph(f"<b>{comparison.process_area}</b>", styles['Normal']))
            content.append(Paragraph(f"Current: {comparison.current_state}", styles['Normal']))
            content.append(Paragraph(f"Future: {comparison.future_state}", styles['Normal']))
            content.append(Paragraph(f"Improvement: {comparison.improvement_description}", styles['Normal']))
            content.append(Spacer(1, 12))

        # Implementation Roadmap
        content.append(PageBreak())
        content.append(Paragraph("Implementation Roadmap", heading_style))
        for phase in report.implementation_roadmap:
            content.append(Paragraph(f"<b>{phase.get('phase', 'Phase')}</b>", styles['Normal']))
            content.append(Paragraph(phase.get('description', ''), styles['Normal']))
            for initiative in phase.get('initiatives', []):
                content.append(Paragraph(
                    f"  • {initiative.get('name', '')}: {initiative.get('description', '')}",
                    styles['Normal']
                ))
            content.append(Spacer(1, 12))

        # Build PDF
        doc.build(content)

        self.log_info(f"PDF report generated: {filepath}")
        return filepath
