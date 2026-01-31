"""
LangGraph Workflow Orchestration
The Consultant Graph - manages the multi-agent workflow with human breakpoint.

State persistence is handled by LangGraph's built-in checkpointing.
"""

import logging
from typing import Any, Dict, Optional, TypedDict

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.agents import (
    IngestionAgent,
    HypothesisGeneratorAgent,
    InterviewArchitectAgent,
    GapAnalystAgent,
    SolutionArchitectAgent,
    ReportingAgent,
)
from config.settings import get_agent_config

logger = logging.getLogger(__name__)


class WorkflowState(TypedDict):
    """TypedDict for LangGraph state management."""
    # Project context
    project_id: str
    project: Optional[Dict[str, Any]]

    # Node 1 outputs
    documents: list
    ingestion_complete: bool
    document_summaries: list

    # Node 2 outputs
    hypotheses: list
    hypothesis_generation_complete: bool

    # Node 3 outputs
    interview_script: Optional[Dict[str, Any]]
    script_generation_complete: bool

    # Human breakpoint data
    is_suspended: bool
    suspension_reason: Optional[str]
    transcript: Optional[str]
    transcript_received: bool

    # Node 4 outputs
    gap_analyses: list
    gap_analysis_complete: bool

    # Node 5 outputs
    solutions: list
    solution_recommendations: list
    solutioning_complete: bool

    # Node 6 outputs
    report: Optional[Dict[str, Any]]
    report_complete: bool
    report_pdf_path: Optional[str]

    # Workflow metadata
    current_node: str
    errors: list
    messages: list


class ConsultantGraph:
    """
    The Consultant Graph workflow orchestrator.

    Implements the 6-node state machine with human breakpoint:
    1. Knowledge Ingestion (RAG)
    2. Hypothesis Generator
    3. Interview Architect
    [HUMAN BREAKPOINT - Interview]
    4. Gap Analyst
    5. Solution Architect
    6. Reporting Engine

    State persistence is handled by LangGraph's built-in checkpointing.
    """

    def __init__(self, checkpointer: Optional[MemorySaver] = None):
        """Initialize the Consultant Graph."""
        self.checkpointer = checkpointer or MemorySaver()

        # Load agent configurations
        agent_config_registry = get_agent_config()

        # Initialize agents
        self.ingestion_agent = IngestionAgent(
            agent_config=agent_config_registry.get_agent_config("ingestion")
        )
        self.hypothesis_agent = HypothesisGeneratorAgent(
            agent_config=agent_config_registry.get_agent_config("hypothesis")
        )
        self.interview_agent = InterviewArchitectAgent(
            agent_config=agent_config_registry.get_agent_config("interview")
        )
        self.gap_analyst = GapAnalystAgent(
            agent_config=agent_config_registry.get_agent_config("gap_analyst")
        )
        self.solution_agent = SolutionArchitectAgent(
            agent_config=agent_config_registry.get_agent_config("solution")
        )
        self.reporting_agent = ReportingAgent(
            agent_config=agent_config_registry.get_agent_config("reporting")
        )

        self.workflow = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine."""
        builder = StateGraph(WorkflowState)

        # Add nodes
        builder.add_node("ingestion", self._run_ingestion)
        builder.add_node("hypothesis", self._run_hypothesis)
        builder.add_node("interview", self._run_interview)
        builder.add_node("gap_analysis", self._run_gap_analysis)
        builder.add_node("solution", self._run_solution)
        builder.add_node("reporting", self._run_reporting)

        # Define edges
        builder.set_entry_point("ingestion")
        builder.add_edge("ingestion", "hypothesis")
        builder.add_edge("hypothesis", "interview")

        # Conditional edge after interview (human breakpoint)
        builder.add_conditional_edges(
            "interview",
            self._should_wait_for_transcript,
            {"wait": END, "continue": "gap_analysis"},
        )

        builder.add_edge("gap_analysis", "solution")
        builder.add_edge("solution", "reporting")
        builder.add_edge("reporting", END)

        return builder.compile(checkpointer=self.checkpointer)

    async def _run_ingestion(self, state: WorkflowState) -> WorkflowState:
        """Run the ingestion node."""
        return await self.ingestion_agent.process(dict(state))

    async def _run_hypothesis(self, state: WorkflowState) -> WorkflowState:
        """Run the hypothesis generation node."""
        return await self.hypothesis_agent.process(dict(state))

    async def _run_interview(self, state: WorkflowState) -> WorkflowState:
        """Run the interview architect node."""
        return await self.interview_agent.process(dict(state))

    async def _run_gap_analysis(self, state: WorkflowState) -> WorkflowState:
        """Run the gap analysis node."""
        return await self.gap_analyst.process(dict(state))

    async def _run_solution(self, state: WorkflowState) -> WorkflowState:
        """Run the solution architect node."""
        return await self.solution_agent.process(dict(state))

    async def _run_reporting(self, state: WorkflowState) -> WorkflowState:
        """Run the reporting engine node."""
        return await self.reporting_agent.process(dict(state))

    def _should_wait_for_transcript(self, state: WorkflowState) -> str:
        """Determine if workflow should wait for transcript."""
        if state.get("is_suspended") and not state.get("transcript_received"):
            return "wait"
        return "continue"

    def get_initial_state(
        self,
        project_id: str,
        project: Optional[Dict[str, Any]] = None,
        documents: Optional[list] = None,
    ) -> WorkflowState:
        """Create initial workflow state."""
        return WorkflowState(
            project_id=project_id,
            project=project,
            documents=documents or [],
            ingestion_complete=False,
            document_summaries=[],
            hypotheses=[],
            hypothesis_generation_complete=False,
            interview_script=None,
            script_generation_complete=False,
            is_suspended=False,
            suspension_reason=None,
            transcript=None,
            transcript_received=False,
            gap_analyses=[],
            gap_analysis_complete=False,
            solutions=[],
            solution_recommendations=[],
            solutioning_complete=False,
            report=None,
            report_complete=False,
            report_pdf_path=None,
            current_node="start",
            errors=[],
            messages=[],
        )

    async def run_to_interview(
        self,
        project_id: str,
        project: Dict[str, Any],
        documents: list,
        thread_id: str,
    ) -> Dict[str, Any]:
        """Run workflow from start to interview script (human breakpoint)."""
        initial_state = self.get_initial_state(
            project_id=project_id,
            project=project,
            documents=documents,
        )
        config = {"configurable": {"thread_id": thread_id}}
        final_state = await self.workflow.ainvoke(initial_state, config)
        return dict(final_state)

    async def resume_with_transcript(
        self,
        thread_id: str,
        transcript: str,
    ) -> Dict[str, Any]:
        """Resume workflow after receiving interview transcript."""
        config = {"configurable": {"thread_id": thread_id}}

        # Get current state from checkpointer
        state_snapshot = self.workflow.get_state(config)
        current_state = dict(state_snapshot.values)

        # Update state with transcript
        current_state["transcript"] = transcript
        current_state["transcript_received"] = True
        current_state["is_suspended"] = False

        # Resume workflow
        final_state = await self.workflow.ainvoke(current_state, config)
        return dict(final_state)

    def get_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get current workflow state for a thread."""
        config = {"configurable": {"thread_id": thread_id}}
        try:
            state_snapshot = self.workflow.get_state(config)
            return dict(state_snapshot.values) if state_snapshot.values else None
        except Exception as e:
            logger.error(f"Error getting state: {e}")
            return None


# Singleton workflow instance for the application
_workflow_instance: Optional[ConsultantGraph] = None


def get_workflow() -> ConsultantGraph:
    """Get the singleton workflow instance."""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = ConsultantGraph()
    return _workflow_instance


def create_workflow() -> ConsultantGraph:
    """Create a new ConsultantGraph instance."""
    return ConsultantGraph()
