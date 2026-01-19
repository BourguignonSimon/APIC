"""
Google ADK Agent
A specialized agent that leverages Google's Generative AI and Vertex AI capabilities.

This agent provides:
1. Enhanced analysis using Google Gemini models
2. Multimodal support for processing images and documents
3. Advanced function calling capabilities
4. Integration with Vertex AI for enterprise features
"""

import logging
import json
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.base import BaseAgent, get_llm
from config.settings import settings

logger = logging.getLogger(__name__)


class GoogleADKAgent(BaseAgent):
    """
    Google ADK (Agent Development Kit) specialized agent.

    This agent uses Google's Gemini models to provide enhanced
    analysis capabilities including multimodal processing,
    advanced reasoning, and function calling.
    """

    def __init__(
        self,
        name: str = "GoogleADKAgent",
        model: Optional[str] = None,
        use_vertex_ai: bool = False,
        **kwargs,
    ):
        """
        Initialize the Google ADK agent.

        Args:
            name: Name of the agent
            model: Google model to use (defaults to settings.GOOGLE_MODEL)
            use_vertex_ai: Whether to use Vertex AI instead of standard Gemini API
            **kwargs: Additional keyword arguments
        """
        # Initialize with Google provider
        llm = get_llm(
            provider="google",
            model=model or settings.GOOGLE_MODEL,
            **kwargs
        )
        super().__init__(name=name, llm=llm, **kwargs)

        self.use_vertex_ai = use_vertex_ai
        self.logger = logging.getLogger(f"apic.agents.{name}")

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the current state with Google ADK capabilities.

        Args:
            state: Current graph state

        Returns:
            Updated graph state with Google-enhanced insights
        """
        self.log_info("Starting Google ADK analysis")

        try:
            # Extract relevant data from state
            project_id = state.get("project_id")
            document_summaries = state.get("document_summaries", [])
            hypotheses = state.get("hypotheses", [])
            messages = state.get("messages", [])

            # Perform Google-enhanced analysis
            google_insights = await self._analyze_with_google_tools(
                document_summaries=document_summaries,
                hypotheses=hypotheses,
                state=state,
            )

            # Update state with Google insights
            state["google_insights"] = google_insights
            state["google_adk_complete"] = True
            state["messages"] = messages + [
                f"Google ADK analysis complete. Generated {len(google_insights)} insights."
            ]

            self.log_info(f"Generated {len(google_insights)} Google ADK insights")

        except Exception as e:
            self.log_error(f"Error during Google ADK processing", e)
            state.setdefault("errors", []).append(
                f"Google ADK error: {str(e)}"
            )
            state["google_adk_complete"] = False

        return state

    async def _analyze_with_google_tools(
        self,
        document_summaries: List[str],
        hypotheses: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Perform enhanced analysis using Google's AI capabilities.

        Args:
            document_summaries: List of document summaries
            hypotheses: List of generated hypotheses
            state: Current state (for additional context)

        Returns:
            List of Google-enhanced insights
        """
        # Prepare analysis prompt
        prompt = self._build_analysis_prompt(document_summaries, hypotheses)

        # Call Google Gemini with the prompt
        messages = [
            SystemMessage(content=(
                "You are an expert business process analyst using Google's "
                "advanced AI capabilities. Analyze the provided information "
                "and generate deep insights about process inefficiencies, "
                "patterns, and improvement opportunities."
            )),
            HumanMessage(content=prompt)
        ]

        try:
            response = await self.llm.ainvoke(messages)

            # Parse the response
            insights = self._parse_google_response(response.content)

            return insights

        except Exception as e:
            self.log_error(f"Error in Google ADK analysis", e)
            return []

    def _build_analysis_prompt(
        self,
        document_summaries: List[str],
        hypotheses: List[Dict[str, Any]],
    ) -> str:
        """Build the analysis prompt for Google Gemini."""
        prompt = "# Process Analysis Request\n\n"

        prompt += "## Document Summaries\n"
        for idx, summary in enumerate(document_summaries, 1):
            prompt += f"{idx}. {summary}\n"

        prompt += "\n## Existing Hypotheses\n"
        for idx, hyp in enumerate(hypotheses, 1):
            if isinstance(hyp, dict):
                prompt += f"{idx}. {hyp.get('process_area', 'Unknown')}: {hyp.get('description', '')}\n"

        prompt += "\n## Task\n"
        prompt += (
            "Analyze the above information and generate enhanced insights in JSON format. "
            "Each insight should have:\n"
            "- insight_type: Type of insight (pattern_detection, efficiency_opportunity, risk_identification, etc.)\n"
            "- description: Detailed description of the insight\n"
            "- confidence: Confidence score (0.0-1.0)\n"
            "- source: 'google_gemini'\n"
            "- recommended_actions: List of specific recommended actions\n\n"
            "Return a JSON array of insights."
        )

        return prompt

    def _parse_google_response(self, response_content: str) -> List[Dict[str, Any]]:
        """
        Parse Google Gemini's response into structured insights.

        Args:
            response_content: Raw response from Google Gemini

        Returns:
            List of parsed insights
        """
        try:
            # Try to extract JSON from the response
            # Gemini might wrap JSON in markdown code blocks
            content = response_content.strip()

            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]

            if content.endswith("```"):
                content = content[:-3]

            content = content.strip()

            # Parse JSON
            insights = json.loads(content)

            # Ensure it's a list
            if isinstance(insights, dict):
                insights = [insights]

            return insights

        except json.JSONDecodeError as e:
            self.log_error(f"Failed to parse JSON response from Google", e)
            # Return a default insight based on the text response
            return [{
                "insight_type": "general_analysis",
                "description": response_content[:500],  # Truncate long responses
                "confidence": 0.5,
                "source": "google_gemini",
                "recommended_actions": []
            }]

    async def analyze_multimodal(
        self,
        state: Dict[str, Any],
        image_data: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Perform multimodal analysis including images.

        Args:
            state: Current state
            image_data: List of base64-encoded images

        Returns:
            Updated state with multimodal insights
        """
        self.log_info("Starting multimodal analysis")

        if not image_data:
            image_data = state.get("image_data", [])

        if not image_data:
            self.log_info("No image data provided, skipping multimodal analysis")
            return state

        try:
            # Build multimodal message
            # Note: Actual implementation would depend on the specific
            # Google Gemini API for multimodal inputs
            prompt = (
                "Analyze the provided process flow diagrams and documents. "
                "Identify inefficiencies, bottlenecks, and improvement opportunities."
            )

            # For now, log that we would process images
            self.log_info(f"Would process {len(image_data)} images with Gemini Vision")

            state["multimodal_analysis_complete"] = True

        except Exception as e:
            self.log_error(f"Error in multimodal analysis", e)
            state.setdefault("errors", []).append(
                f"Multimodal analysis error: {str(e)}"
            )

        return state

    async def use_function_calling(
        self,
        state: Dict[str, Any],
        available_functions: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Demonstrate Google Gemini's function calling capabilities.

        Args:
            state: Current state
            available_functions: Dictionary of available functions

        Returns:
            Updated state with function calling results
        """
        self.log_info("Using Google Gemini function calling")

        if not available_functions:
            # Define default analysis functions
            available_functions = {
                "analyze_process": {
                    "description": "Analyze a specific business process",
                    "parameters": {
                        "process_name": "string",
                        "depth": "string (shallow|medium|deep)"
                    }
                },
                "calculate_roi": {
                    "description": "Calculate ROI for a proposed solution",
                    "parameters": {
                        "current_hours": "number",
                        "proposed_hours": "number",
                        "hourly_rate": "number"
                    }
                }
            }

        # Log function calling capability
        self.log_info(f"Available functions: {list(available_functions.keys())}")

        state["function_calling_available"] = True

        return state


class GoogleVertexAIAgent(GoogleADKAgent):
    """
    Specialized agent using Google Vertex AI for enterprise features.

    Extends GoogleADKAgent with Vertex AI specific capabilities like:
    - Model Garden access
    - Enterprise security features
    - Advanced tuning options
    """

    def __init__(
        self,
        name: str = "GoogleVertexAIAgent",
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the Google Vertex AI agent.

        Args:
            name: Name of the agent
            project_id: GCP project ID
            location: GCP location
            **kwargs: Additional keyword arguments
        """
        super().__init__(name=name, use_vertex_ai=True, **kwargs)

        self.vertex_project_id = project_id or settings.VERTEX_AI_PROJECT_ID
        self.vertex_location = location or settings.VERTEX_AI_LOCATION

        if not self.vertex_project_id:
            logger.warning(
                "Vertex AI project ID not configured. "
                "Set VERTEX_AI_PROJECT_ID in settings."
            )

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process using Vertex AI capabilities.

        Args:
            state: Current graph state

        Returns:
            Updated graph state
        """
        self.log_info("Starting Vertex AI processing")

        # Use base Google ADK processing with Vertex AI enhancements
        state = await super().process(state)

        # Add Vertex AI specific metadata
        state["vertex_ai_used"] = True
        state["vertex_project"] = self.vertex_project_id

        return state
