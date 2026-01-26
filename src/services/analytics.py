"""
Analytics Service for generating metrics and summaries.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from src.models.schemas import AnalyticsSummary, ProjectStatus

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for generating analytics and metrics."""

    def __init__(self):
        """Initialize the analytics service."""
        self.state_manager = None  # Will be injected

    async def generate_summary(
        self,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None
    ) -> AnalyticsSummary:
        """
        Generate analytics summary for dashboard.

        Args:
            period_start: Start of the period to analyze
            period_end: End of the period to analyze

        Returns:
            AnalyticsSummary object
        """
        if not self.state_manager:
            raise ValueError("StateManager not initialized")

        # Get all projects
        projects = await self.state_manager.get_all_projects()

        # Filter by period if specified
        if period_start or period_end:
            filtered_projects = []
            for project in projects:
                created_at = project.get('created_at')
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at)

                if period_start and created_at < period_start:
                    continue
                if period_end and created_at > period_end:
                    continue

                filtered_projects.append(project)
            projects = filtered_projects

        # Calculate statistics
        total_projects = len(projects)
        completed_projects = sum(
            1 for p in projects
            if p.get('status') == ProjectStatus.COMPLETED.value
        )
        active_projects = sum(
            1 for p in projects
            if p.get('status') in [
                ProjectStatus.ANALYZING.value,
                ProjectStatus.INGESTING.value,
                ProjectStatus.SOLUTIONING.value,
                ProjectStatus.REPORTING.value,
            ]
        )
        failed_projects = sum(
            1 for p in projects
            if p.get('status') == ProjectStatus.FAILED.value
        )

        # Calculate average completion time
        completion_times = []
        for project in projects:
            if project.get('status') == ProjectStatus.COMPLETED.value:
                created_at = project.get('created_at')
                updated_at = project.get('updated_at')

                if created_at and updated_at:
                    if isinstance(created_at, str):
                        created_at = datetime.fromisoformat(created_at)
                    if isinstance(updated_at, str):
                        updated_at = datetime.fromisoformat(updated_at)

                    duration = (updated_at - created_at).total_seconds()
                    completion_times.append(duration)

        average_completion_time = (
            sum(completion_times) / len(completion_times)
            if completion_times else None
        )

        return AnalyticsSummary(
            total_projects=total_projects,
            completed_projects=completed_projects,
            active_projects=active_projects,
            failed_projects=failed_projects,
            average_completion_time=average_completion_time,
            total_hours_saved=None,  # TODO: Calculate from solutions
            total_solutions_recommended=0,  # TODO: Calculate from solutions
            period_start=period_start,
            period_end=period_end
        )

    async def get_workflow_metrics(self, project_id: str) -> Dict[str, Any]:
        """
        Get detailed metrics for a specific workflow.

        Args:
            project_id: ID of the project

        Returns:
            Dictionary with workflow metrics
        """
        if not self.state_manager:
            raise ValueError("StateManager not initialized")

        # Mock implementation - in real scenario, would query from state_manager
        return {
            "total_execution_time": 3600,
            "node_execution_times": {
                "ingestion": 600,
                "hypothesis": 900,
                "interview": 300,
                "gap_analysis": 800,
                "solution": 700,
                "reporting": 300,
            },
            "document_count": 5,
            "hypothesis_count": 8,
        }

    async def calculate_total_roi(self, project_id: str) -> Dict[str, Any]:
        """
        Calculate total ROI across all solutions for a project.

        Args:
            project_id: ID of the project

        Returns:
            Dictionary with ROI summary
        """
        if not self.state_manager:
            raise ValueError("StateManager not initialized")

        # Get solution recommendations (mock for now)
        solutions = [
            {"estimated_roi_hours": 40, "implementation_complexity": "Low"},
            {"estimated_roi_hours": 60, "implementation_complexity": "Medium"},
            {"estimated_roi_hours": 100, "implementation_complexity": "High"},
        ]

        total_hours_saved = sum(s["estimated_roi_hours"] for s in solutions)
        total_solutions = len(solutions)

        return {
            "total_hours_saved": total_hours_saved,
            "total_solutions": total_solutions,
            "average_roi_per_solution": total_hours_saved / total_solutions if total_solutions > 0 else 0,
        }
