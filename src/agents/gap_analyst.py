"""
Node 4: Gap Analyst Agent
Compares SOPs (documented procedures) vs Interview Transcripts (actual reality).
"""

import json
from typing import Any, Dict, List, Optional
import uuid

from langchain_core.prompts import ChatPromptTemplate

from .base import BaseAgent
from .ingestion import IngestionAgent
from src.models.schemas import (
    Hypothesis,
    GapAnalysisItem,
    TaskCategory,
    GraphState,
)
from config.settings import settings


class GapAnalystAgent(BaseAgent):
    """
    Node 4: Gap Analyst Agent

    Responsibilities:
    - Compare SOPs (how they say they work) vs Transcript (how they actually work)
    - Identify contradictions and discrepancies
    - Classify tasks as Automatable, Partially Automatable, or Human-Only
    - Assess severity and business impact of each gap
    """

    def __init__(self, **kwargs):
        super().__init__(name="GapAnalyst", **kwargs)
        self.ingestion_agent = IngestionAgent()

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform gap analysis between documented and actual processes.

        Args:
            state: Current graph state with transcript

        Returns:
            Updated state with gap analysis results
        """
        self.log_info("Starting gap analysis")

        try:
            project_id = state.get("project_id")
            transcript = state.get("transcript")
            hypotheses_data = state.get("hypotheses", [])
            document_summaries = state.get("document_summaries", [])

            if not transcript:
                self.log_error("No transcript provided for gap analysis")
                state["errors"].append("No transcript available for gap analysis")
                state["gap_analysis_complete"] = False
                return state

            # Convert hypotheses
            hypotheses = [
                Hypothesis(**h) if isinstance(h, dict) else h
                for h in hypotheses_data
            ]

            # Get SOP content from vector DB
            sop_content = await self._retrieve_sop_content(project_id)

            # Perform gap analysis
            gaps = await self._analyze_gaps(
                sop_content=sop_content,
                transcript=transcript,
                hypotheses=hypotheses,
                document_summaries=document_summaries,
            )

            # Classify tasks for automation potential
            classified_gaps = await self._classify_automation_potential(gaps)

            # Assess severity and impact
            assessed_gaps = await self._assess_severity(classified_gaps)

            # Update state
            state["gap_analyses"] = [g.model_dump() for g in assessed_gaps]
            state["gap_analysis_complete"] = True
            state["transcript_received"] = True
            state["is_suspended"] = False
            state["current_node"] = "gap_analysis"
            state["messages"].append(
                f"Identified {len(assessed_gaps)} gaps between documented and actual processes"
            )

            self.log_info(f"Gap analysis complete: {len(assessed_gaps)} gaps identified")
            return state

        except Exception as e:
            self.log_error("Error during gap analysis", e)
            state["errors"].append(f"Gap analysis error: {str(e)}")
            state["gap_analysis_complete"] = False
            return state

    async def _retrieve_sop_content(self, project_id: str) -> str:
        """
        Retrieve SOP content from vector database.

        Args:
            project_id: Project ID for namespace

        Returns:
            Combined SOP content
        """
        namespace = f"client_{project_id}"

        # Query for SOP-related content
        sop_queries = [
            "standard operating procedure process steps workflow",
            "documented procedure guidelines instructions",
            "process flow how to guide steps",
        ]

        sop_content = []

        for query in sop_queries:
            try:
                results = await self.ingestion_agent.query_knowledge_base(
                    query=query,
                    namespace=namespace,
                    top_k=5,
                )
                for doc in results:
                    sop_content.append(doc.page_content)
            except Exception as e:
                self.log_error(f"SOP query failed: {e}")

        return "\n\n".join(sop_content) if sop_content else "No SOP content retrieved"

    async def _analyze_gaps(
        self,
        sop_content: str,
        transcript: str,
        hypotheses: List[Hypothesis],
        document_summaries: List[str],
    ) -> List[GapAnalysisItem]:
        """
        Analyze gaps between documented procedures and actual practice.

        Args:
            sop_content: Retrieved SOP content
            transcript: Interview transcript
            hypotheses: Original hypotheses
            document_summaries: Document summaries

        Returns:
            List of identified gaps
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert process analyst specializing in gap analysis.
            Your task is to compare documented procedures (SOPs) with actual practice
            revealed in interview transcripts.

            For each gap, identify:
            1. The specific process step where the gap occurs
            2. How the SOP says it should be done
            3. How it's actually being done (from interview)
            4. The nature of the discrepancy
            5. The suspected root cause
            6. The business impact

            Focus on:
            - Workarounds that bypass official procedures
            - Manual steps that should be automated
            - Communication breakdowns
            - Data handling inefficiencies
            - Approval bottlenecks
            - Quality/error issues
            """),
            ("human", """Analyze the gaps between documented and actual processes:

            DOCUMENTED PROCEDURES (SOPs):
            {sop_content}

            DOCUMENT SUMMARIES:
            {summaries}

            INTERVIEW TRANSCRIPT (Actual Practice):
            {transcript}

            ORIGINAL HYPOTHESES (for context):
            {hypotheses}

            Return a JSON array of gap analysis items:
            [
                {{
                    "process_step": "specific step name",
                    "sop_description": "how SOP says it should work",
                    "observed_behavior": "how it actually works per interview",
                    "gap_description": "the discrepancy",
                    "root_cause": "suspected cause",
                    "impact": "business impact"
                }}
            ]

            Identify 5-15 significant gaps. Return ONLY the JSON array."""),
        ])

        hypotheses_text = "\n".join([
            f"- {h.process_area}: {h.description}"
            for h in hypotheses
        ])

        summaries_text = "\n\n".join(document_summaries[:5])

        response = await self.llm.ainvoke(
            prompt.format_messages(
                sop_content=sop_content[:5000],
                summaries=summaries_text[:3000],
                transcript=transcript[:8000],
                hypotheses=hypotheses_text,
            )
        )

        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            gaps_data = json.loads(content)

            gaps = []
            for g_data in gaps_data:
                gap = GapAnalysisItem(
                    id=str(uuid.uuid4()),
                    process_step=g_data.get("process_step", "Unknown"),
                    sop_description=g_data.get("sop_description", "Not documented"),
                    observed_behavior=g_data.get("observed_behavior", ""),
                    gap_description=g_data.get("gap_description", ""),
                    root_cause=g_data.get("root_cause"),
                    impact=g_data.get("impact", "Unknown impact"),
                )
                gaps.append(gap)

            return gaps

        except json.JSONDecodeError as e:
            self.log_error(f"Failed to parse gap analysis: {e}")
            return [
                GapAnalysisItem(
                    id=str(uuid.uuid4()),
                    process_step="General Process",
                    sop_description="Documented procedures",
                    observed_behavior="Actual practice differs from documentation",
                    gap_description="Gap between documented and actual processes",
                    root_cause="Unable to determine specific cause",
                    impact="Requires further investigation",
                )
            ]

    async def _classify_automation_potential(
        self,
        gaps: List[GapAnalysisItem],
    ) -> List[GapAnalysisItem]:
        """
        Classify each gap for automation potential.

        Args:
            gaps: List of identified gaps

        Returns:
            Gaps with automation classification
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an automation expert. Classify each process gap
            into one of these categories:

            1. AUTOMATABLE - Can be fully automated with current technology
               Examples: data entry, report generation, file transfers, notifications

            2. PARTIALLY_AUTOMATABLE - Requires human oversight but can be assisted
               Examples: document review with AI suggestions, approval workflows

            3. HUMAN_ONLY - Requires human judgment, creativity, or relationships
               Examples: strategic decisions, client negotiations, creative work
            """),
            ("human", """Classify each gap for automation potential:

            {gaps}

            Return a JSON array with each gap and its classification:
            [
                {{
                    "process_step": "step name",
                    "task_category": "Automatable" | "Partially Automatable" | "Human Only"
                }}
            ]

            Return ONLY the JSON array."""),
        ])

        gaps_text = "\n".join([
            f"- {g.process_step}: {g.gap_description}"
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

            classifications = json.loads(content)
            classification_map = {
                c["process_step"]: c["task_category"]
                for c in classifications
            }

            for gap in gaps:
                category_str = classification_map.get(
                    gap.process_step,
                    "Automatable"
                )
                # Map string to enum
                if "Human" in category_str:
                    gap.task_category = TaskCategory.HUMAN_ONLY
                elif "Partial" in category_str:
                    gap.task_category = TaskCategory.PARTIALLY_AUTOMATABLE
                else:
                    gap.task_category = TaskCategory.AUTOMATABLE

            return gaps

        except Exception as e:
            self.log_error(f"Classification parsing failed: {e}")
            return gaps

    async def _assess_severity(
        self,
        gaps: List[GapAnalysisItem],
    ) -> List[GapAnalysisItem]:
        """
        Pass-through method for severity assessment.

        Note: GapAnalysisItem doesn't have a severity field.
        Severity is assessed in Node 5 (Solution Architect) where it's used for prioritization.
        """
        return gaps
