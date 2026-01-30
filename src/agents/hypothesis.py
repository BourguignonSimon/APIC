"""
Node 2: Hypothesis Generator Agent
Analyzes ingested data to identify suspected inefficiencies.
"""

import json
from typing import Any, Dict, List
import uuid

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from .base import BaseAgent
from src.models.schemas import Hypothesis


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
            document_summaries = state.get("document_summaries", [])

            if not document_summaries:
                self.log_info("No document summaries available")
                state["hypotheses"] = []
                state["hypothesis_generation_complete"] = True
                state["messages"].append("No documents to analyze for hypotheses")
                return state

            # Combine summaries for analysis
            combined_summaries = "\n\n---\n\n".join(document_summaries)

            # Generate hypotheses using LLM
            hypotheses = await self._generate_hypotheses(combined_summaries)

            # Filter and sort hypotheses
            validated_hypotheses = self._validate_hypotheses(hypotheses)

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

    async def _generate_hypotheses(
        self,
        summaries: str,
    ) -> List[Hypothesis]:
        """
        Use LLM to generate hypotheses from document analysis.

        Args:
            summaries: Combined document summaries

        Returns:
            List of generated hypotheses
        """
        default_system = """You are an expert management consultant specializing in
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
            """

        default_human = """Analyze the following documents and generate hypotheses about
            operational inefficiencies.

            DOCUMENT SUMMARIES:
            {summaries}

            Generate a JSON array of hypotheses. Each hypothesis should have:
            - process_area: string
            - description: string
            - evidence: array of strings (quotes from documents)
            - indicators: array of strings (keywords that triggered this)
            - confidence: number between 0 and 1
            - category: string

            Return ONLY the JSON array, no additional text."""

        system_prompt = self.get_prompt("system", default_system)
        human_template = self.get_prompt("generate_hypotheses", default_human)

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_template),
        ])

        formatted_prompt = prompt.format_messages(
            summaries=summaries,
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

    def _validate_hypotheses(
        self,
        hypotheses: List[Hypothesis],
    ) -> List[Hypothesis]:
        """
        Filter and sort hypotheses by confidence.

        Args:
            hypotheses: List of generated hypotheses

        Returns:
            Filtered and sorted hypotheses
        """
        # Filter low confidence hypotheses and sort by confidence
        validated = [h for h in hypotheses if h.confidence >= 0.2]
        validated.sort(key=lambda h: h.confidence, reverse=True)
        return validated
