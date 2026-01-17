"""
Node 2: Hypothesis Generator Agent
Analyzes ingested data to identify suspected inefficiencies.
"""

import json
from typing import Any, Dict, List, Optional
import uuid

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from .base import BaseAgent, get_llm
from .ingestion import IngestionAgent
from src.models.schemas import Hypothesis, GraphState
from config.settings import settings


# Keywords that indicate potential inefficiencies
INEFFICIENCY_INDICATORS = {
    "manual_process": [
        "manual", "manually", "by hand", "paper", "physical copy",
        "print", "printed", "handwritten", "fill out", "fill in"
    ],
    "communication_gaps": [
        "email", "phone call", "follow up", "remind", "waiting for",
        "unclear", "miscommunication", "lost", "missing information"
    ],
    "data_silos": [
        "spreadsheet", "excel", "separate system", "copy paste",
        "re-enter", "duplicate", "different database", "no integration"
    ],
    "delays": [
        "delay", "delayed", "slow", "takes time", "wait", "waiting",
        "backlog", "bottleneck", "queue", "pending"
    ],
    "errors": [
        "error", "mistake", "incorrect", "wrong", "fix", "correction",
        "rework", "redo", "quality issue", "defect"
    ],
    "approvals": [
        "approval", "approve", "sign off", "signature", "authorize",
        "permission", "escalate", "manager review"
    ],
    "hidden_factories": [
        "workaround", "unofficial", "shadow", "personal process",
        "my own way", "work around", "bypass", "shortcut"
    ],
}


class HypothesisGeneratorAgent(BaseAgent):
    """
    Node 2: Hypothesis Generator Agent

    Responsibilities:
    - Analyze document summaries and content
    - Identify patterns indicating operational inefficiencies
    - Generate hypotheses about process bottlenecks
    - Detect "Hidden Factories" (unofficial workarounds)
    """

    def __init__(self, **kwargs):
        super().__init__(name="HypothesisGenerator", **kwargs)
        self.ingestion_agent = IngestionAgent()
        self.output_parser = JsonOutputParser()

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate hypotheses about operational inefficiencies.

        Args:
            state: Current graph state with ingested documents

        Returns:
            Updated state with generated hypotheses
        """
        self.log_info("Starting hypothesis generation")

        try:
            project_id = state.get("project_id")
            document_summaries = state.get("document_summaries", [])

            if not document_summaries:
                self.log_info("No document summaries available")
                state["hypotheses"] = []
                state["hypothesis_generation_complete"] = True
                state["messages"].append("No documents to analyze for hypotheses")
                return state

            # Combine summaries for analysis
            combined_summaries = "\n\n---\n\n".join(document_summaries)

            # Query vector DB for additional context if available
            additional_context = await self._query_for_inefficiency_patterns(
                project_id
            )

            # Generate hypotheses using LLM
            hypotheses = await self._generate_hypotheses(
                combined_summaries,
                additional_context,
            )

            # Validate and enhance hypotheses
            validated_hypotheses = await self._validate_hypotheses(
                hypotheses,
                project_id,
            )

            # Update state
            state["hypotheses"] = [h.model_dump() for h in validated_hypotheses]
            state["hypothesis_generation_complete"] = True
            state["current_node"] = "hypothesis"
            state["messages"].append(
                f"Generated {len(validated_hypotheses)} hypotheses about potential inefficiencies"
            )

            self.log_info(f"Generated {len(validated_hypotheses)} hypotheses")
            return state

        except Exception as e:
            self.log_error("Error generating hypotheses", e)
            state["errors"].append(f"Hypothesis generation error: {str(e)}")
            state["hypothesis_generation_complete"] = False
            return state

    async def _query_for_inefficiency_patterns(
        self,
        project_id: str,
    ) -> str:
        """
        Query vector DB for content related to inefficiency patterns.

        Args:
            project_id: Project ID for namespace

        Returns:
            Relevant context from vector DB
        """
        namespace = f"client_{project_id}"
        context_parts = []

        # Query for each category of inefficiency
        for category, keywords in INEFFICIENCY_INDICATORS.items():
            query = f"Find processes involving: {', '.join(keywords[:5])}"
            try:
                results = await self.ingestion_agent.query_knowledge_base(
                    query=query,
                    namespace=namespace,
                    top_k=3,
                )
                for doc in results:
                    context_parts.append(f"[{category}] {doc.page_content}")
            except Exception as e:
                self.log_debug(f"Query failed for {category}: {e}")

        return "\n\n".join(context_parts) if context_parts else ""

    async def _generate_hypotheses(
        self,
        summaries: str,
        additional_context: str,
    ) -> List[Hypothesis]:
        """
        Use LLM to generate hypotheses from document analysis.

        Args:
            summaries: Combined document summaries
            additional_context: Additional context from vector search

        Returns:
            List of generated hypotheses
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert management consultant specializing in
            process improvement and operational efficiency. Your task is to analyze
            corporate documents and identify potential areas of inefficiency.

            Focus on identifying:
            1. Manual processes that could be automated
            2. Communication bottlenecks
            3. Data silos and integration gaps
            4. Approval delays
            5. Hidden factories (unofficial workarounds)
            6. Repetitive tasks
            7. Error-prone processes

            For each hypothesis, provide:
            - The process area affected
            - A clear description of the suspected inefficiency
            - Evidence from the documents (quotes or references)
            - Keywords/patterns that triggered this hypothesis
            - A confidence score (0.0 to 1.0)
            - A category (manual_process, communication_gap, data_silos, delays, errors, approvals, hidden_factories, general)
            """),
            ("human", """Analyze the following documents and generate hypotheses about
            operational inefficiencies.

            DOCUMENT SUMMARIES:
            {summaries}

            ADDITIONAL CONTEXT (patterns found in documents):
            {context}

            Generate a JSON array of hypotheses. Each hypothesis should have:
            - process_area: string
            - description: string
            - evidence: array of strings (quotes from documents)
            - indicators: array of strings (keywords that triggered this)
            - confidence: number between 0 and 1
            - category: string

            Return ONLY the JSON array, no additional text."""),
        ])

        formatted_prompt = prompt.format_messages(
            summaries=summaries,
            context=additional_context or "No additional patterns found",
        )

        response = await self.llm.ainvoke(formatted_prompt)

        # Parse the response
        try:
            # Extract JSON from response
            content = response.content.strip()
            if content.startswith("```"):
                # Remove markdown code blocks
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            hypotheses_data = json.loads(content)

            hypotheses = []
            for h_data in hypotheses_data:
                hypothesis = Hypothesis(
                    id=str(uuid.uuid4()),
                    process_area=h_data.get("process_area", "Unknown"),
                    description=h_data.get("description", ""),
                    evidence=h_data.get("evidence", []),
                    indicators=h_data.get("indicators", []),
                    confidence=float(h_data.get("confidence", 0.5)),
                    category=h_data.get("category", "general"),
                )
                hypotheses.append(hypothesis)

            return hypotheses

        except json.JSONDecodeError as e:
            self.log_error(f"Failed to parse LLM response as JSON: {e}")
            # Create a single general hypothesis if parsing fails
            return [
                Hypothesis(
                    id=str(uuid.uuid4()),
                    process_area="General Operations",
                    description="Document analysis suggests potential process inefficiencies",
                    evidence=["Unable to parse specific evidence"],
                    indicators=["analysis_error"],
                    confidence=0.3,
                    category="general",
                )
            ]

    async def _validate_hypotheses(
        self,
        hypotheses: List[Hypothesis],
        project_id: str,
    ) -> List[Hypothesis]:
        """
        Validate and enhance hypotheses with additional context.

        Args:
            hypotheses: List of generated hypotheses
            project_id: Project ID for vector search

        Returns:
            Validated and enhanced hypotheses
        """
        validated = []
        namespace = f"client_{project_id}"

        for hypothesis in hypotheses:
            # Skip hypotheses with very low confidence
            if hypothesis.confidence < 0.2:
                continue

            # Try to find additional supporting evidence
            try:
                results = await self.ingestion_agent.query_knowledge_base(
                    query=hypothesis.description,
                    namespace=namespace,
                    top_k=2,
                )

                if results:
                    # Add additional evidence
                    for doc in results:
                        if len(doc.page_content) > 50:
                            hypothesis.evidence.append(
                                doc.page_content[:200] + "..."
                            )

                    # Boost confidence if we found supporting evidence
                    hypothesis.confidence = min(1.0, hypothesis.confidence + 0.1)

            except Exception as e:
                self.log_debug(f"Could not find additional evidence: {e}")

            validated.append(hypothesis)

        # Sort by confidence
        validated.sort(key=lambda h: h.confidence, reverse=True)

        return validated
