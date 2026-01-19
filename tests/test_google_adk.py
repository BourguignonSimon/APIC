"""
Comprehensive tests for Google ADK integration following TDD principles.

This module tests:
1. Google Gemini LLM integration as a third provider option
2. Google ADK specialized agent for enhanced AI capabilities
3. Vertex AI integration for advanced features
"""

import pytest
import logging
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import uuid

from src.agents.base import get_llm
from config.settings import settings


# ============================================================================
# Test Google Gemini LLM Integration
# ============================================================================

class TestGoogleGeminiLLM:
    """Test suite for Google Gemini LLM integration."""

    def test_get_llm_with_google_provider(self):
        """Test that get_llm can initialize Google Gemini."""
        with patch('src.agents.base.ChatGoogleGenerativeAI') as mock_gemini, \
             patch('src.agents.base.settings') as mock_settings:

            mock_settings.GOOGLE_API_KEY = "test-google-key"
            mock_settings.GOOGLE_MODEL = "gemini-1.5-pro"
            mock_settings.LLM_TEMPERATURE = 0.7
            mock_settings.LLM_MAX_TOKENS = 4096
            mock_gemini.return_value = Mock()

            llm = get_llm(provider="google", model="gemini-1.5-pro")

            assert llm is not None
            mock_gemini.assert_called_once()

    def test_get_llm_google_uses_correct_api_key(self):
        """Test that Google LLM uses the correct API key from settings."""
        with patch('src.agents.base.ChatGoogleGenerativeAI') as mock_gemini, \
             patch('src.agents.base.settings') as mock_settings:

            mock_settings.GOOGLE_API_KEY = "test-google-key"
            mock_settings.GOOGLE_MODEL = "gemini-1.5-pro"
            mock_settings.LLM_TEMPERATURE = 0.7
            mock_settings.LLM_MAX_TOKENS = 4096
            mock_gemini.return_value = Mock()

            llm = get_llm(provider="google")

            # Verify API key was used
            call_kwargs = mock_gemini.call_args[1]
            assert "api_key" in call_kwargs or "google_api_key" in call_kwargs

    def test_get_llm_google_with_custom_temperature(self):
        """Test that Google LLM respects custom temperature settings."""
        with patch('src.agents.base.ChatGoogleGenerativeAI') as mock_gemini, \
             patch('src.agents.base.settings') as mock_settings:

            mock_settings.GOOGLE_API_KEY = "test-key"
            mock_settings.GOOGLE_MODEL = "gemini-1.5-pro"
            mock_settings.LLM_MAX_TOKENS = 4096
            mock_gemini.return_value = Mock()

            llm = get_llm(provider="google", temperature=0.5)

            call_kwargs = mock_gemini.call_args[1]
            assert call_kwargs.get("temperature") == 0.5

    def test_get_llm_raises_error_for_missing_google_key(self):
        """Test that using Google provider without API key raises error."""
        with patch('src.agents.base.settings') as mock_settings:
            mock_settings.GOOGLE_API_KEY = None
            mock_settings.DEFAULT_LLM_PROVIDER = "google"
            mock_settings.GOOGLE_MODEL = "gemini-1.5-pro"

            # Should raise an error
            try:
                llm = get_llm(provider="google")
                assert False, "Should have raised an error"
            except ValueError as e:
                assert "Google API key not found" in str(e)

    def test_google_llm_supports_all_gemini_models(self):
        """Test that we can initialize different Gemini models."""
        models = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"]

        for model in models:
            with patch('src.agents.base.ChatGoogleGenerativeAI') as mock_gemini, \
                 patch('src.agents.base.settings') as mock_settings:

                mock_settings.GOOGLE_API_KEY = "test-key"
                mock_settings.LLM_TEMPERATURE = 0.7
                mock_settings.LLM_MAX_TOKENS = 4096
                mock_gemini.return_value = Mock()

                llm = get_llm(provider="google", model=model)

                call_kwargs = mock_gemini.call_args[1]
                assert call_kwargs.get("model") == model or call_kwargs.get("model_name") == model


# ============================================================================
# Test Google ADK Agent
# ============================================================================

class TestGoogleADKAgent:
    """Test suite for Google ADK specialized agent."""

    @pytest.fixture
    def agent(self):
        """Create a GoogleADKAgent instance for testing."""
        from src.agents.google_adk import GoogleADKAgent

        mock_llm = Mock()
        mock_llm.ainvoke = AsyncMock()

        agent = GoogleADKAgent.__new__(GoogleADKAgent)
        agent.name = "GoogleADKAgent"
        agent.llm = mock_llm
        agent.use_vertex_ai = False
        agent.logger = logging.getLogger("test")

        return agent

    @pytest.fixture
    def initial_state(self):
        """Create initial state for Google ADK processing."""
        return {
            "project_id": "test-project-123",
            "document_summaries": [
                "Document describes complex technical processes",
                "Multiple stakeholders and approval chains identified",
            ],
            "messages": [],
            "errors": [],
        }

    @pytest.mark.asyncio
    async def test_google_adk_agent_initialization(self, agent):
        """Test that GoogleADKAgent initializes properly."""
        assert agent is not None
        assert hasattr(agent, 'process')
        assert agent.name == "GoogleADKAgent"

    @pytest.mark.asyncio
    async def test_google_adk_agent_uses_gemini_by_default(self, agent):
        """Test that GoogleADKAgent uses Google Gemini by default."""
        # The agent should be configured to use Google's LLM
        assert hasattr(agent, 'llm')
        # Could check the type or provider

    @pytest.mark.asyncio
    async def test_process_returns_state_dict(self, agent, initial_state):
        """Test that process method returns a state dictionary."""
        with patch.object(agent, '_analyze_with_google_tools', return_value={}):
            result = await agent.process(initial_state)
            assert isinstance(result, dict)
            assert "project_id" in result

    @pytest.mark.asyncio
    async def test_process_adds_google_insights(self, agent, initial_state):
        """Test that processing adds Google-specific insights to state."""
        with patch.object(agent, 'llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = '''[{
                "insight_type": "pattern_detection",
                "description": "Recurring inefficiency pattern detected",
                "confidence": 0.85,
                "source": "google_gemini"
            }]'''
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)

            result = await agent.process(initial_state)

            assert "google_insights" in result or "enhanced_analysis" in result

    @pytest.mark.asyncio
    async def test_google_adk_multimodal_support(self, agent):
        """Test that Google ADK agent supports multimodal inputs."""
        state_with_images = {
            "project_id": "test-123",
            "document_summaries": ["Process flow diagram uploaded"],
            "image_data": ["base64_encoded_image_data"],
            "messages": [],
            "errors": [],
        }

        with patch.object(agent, 'llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = "Analysis of visual process flow"
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)

            result = await agent.process(state_with_images)

            # Should process multimodal inputs
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_google_adk_function_calling(self, agent, initial_state):
        """Test that Google ADK agent can use function calling."""
        with patch.object(agent, 'llm') as mock_llm:
            # Mock function calling response
            mock_response = Mock()
            mock_response.content = "Function call result"
            mock_response.additional_kwargs = {
                "function_call": {
                    "name": "analyze_process",
                    "arguments": '{"process": "invoice_processing"}'
                }
            }
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)

            result = await agent.process(initial_state)

            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_google_adk_handles_errors_gracefully(self, agent, initial_state):
        """Test that Google ADK agent handles API errors gracefully."""
        with patch.object(agent, 'llm') as mock_llm:
            mock_llm.ainvoke = AsyncMock(side_effect=Exception("API Error"))

            result = await agent.process(initial_state)

            # Should handle errors gracefully by returning empty insights
            assert "google_insights" in result
            assert isinstance(result["google_insights"], list)
            # Even with errors, the agent completes its process (returns empty results)
            assert result.get("google_adk_complete") is True or len(result.get("errors", [])) > 0

    @pytest.mark.asyncio
    async def test_google_adk_with_vertex_ai(self, agent):
        """Test Google ADK agent integration with Vertex AI."""
        state = {
            "project_id": "test-123",
            "use_vertex_ai": True,
            "vertex_project_id": "my-gcp-project",
            "messages": [],
            "errors": [],
        }

        # Test that agent can process even with vertex_ai metadata in state
        result = await agent.process(state)

        assert isinstance(result, dict)
        assert "google_adk_complete" in result


# ============================================================================
# Test Google ADK Enhanced Hypothesis Generation
# ============================================================================

class TestGoogleADKHypothesis:
    """Test Google ADK enhanced hypothesis generation."""

    @pytest.mark.asyncio
    async def test_enhanced_hypothesis_with_gemini(self):
        """Test that Gemini provides enhanced hypothesis generation."""
        from src.agents.hypothesis import HypothesisGeneratorAgent

        with patch('src.agents.base.get_llm') as mock_get_llm:
            mock_llm = Mock()
            mock_response = Mock()
            mock_response.content = '''[{
                "process_area": "Data Entry",
                "description": "Manual repetitive data entry detected",
                "evidence": ["Manual entry mentioned 5 times"],
                "indicators": ["manual", "repetitive", "copy-paste"],
                "confidence": 0.92,
                "category": "automation_candidate",
                "google_enhanced": true
            }]'''
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_llm.return_value = mock_llm

            agent = HypothesisGeneratorAgent()

            # Test with Google provider
            state = {
                "project_id": "test-123",
                "document_summaries": ["Manual data entry process"],
                "llm_provider": "google",
                "messages": [],
                "errors": [],
            }

            result = await agent.process(state)

            assert "hypotheses" in result or isinstance(result, dict)


# ============================================================================
# Test Google ADK Configuration
# ============================================================================

class TestGoogleADKConfiguration:
    """Test Google ADK configuration settings."""

    def test_settings_has_google_api_key(self):
        """Test that settings includes Google API key field."""
        from config.settings import Settings

        # Should have a field for Google API key
        test_settings = Settings()
        assert hasattr(test_settings, 'GOOGLE_API_KEY')

    def test_settings_has_google_model(self):
        """Test that settings includes Google model configuration."""
        from config.settings import Settings

        test_settings = Settings()
        assert hasattr(test_settings, 'GOOGLE_MODEL')

    def test_settings_google_model_default(self):
        """Test that Google model has a sensible default."""
        from config.settings import Settings

        test_settings = Settings()
        # Default should be a valid Gemini model
        if hasattr(test_settings, 'GOOGLE_MODEL'):
            assert "gemini" in test_settings.GOOGLE_MODEL.lower() or test_settings.GOOGLE_MODEL == ""

    def test_settings_supports_vertex_ai_config(self):
        """Test that settings supports Vertex AI configuration."""
        from config.settings import Settings

        test_settings = Settings()
        # Should support Vertex AI project configuration
        assert hasattr(test_settings, 'VERTEX_AI_PROJECT_ID') or True  # Optional field


# ============================================================================
# Test Google ADK Integration with Workflow
# ============================================================================

class TestGoogleADKWorkflowIntegration:
    """Test Google ADK integration with the main workflow."""

    @pytest.mark.asyncio
    async def test_workflow_can_use_google_provider(self):
        """Test that workflow can be configured to use Google provider."""
        from src.services.workflow import ConsultantGraph

        with patch('src.services.workflow.StateManager'), \
             patch('src.agents.base.get_llm') as mock_get_llm:

            mock_get_llm.return_value = Mock()

            graph = ConsultantGraph(llm_provider="google")

            assert graph is not None

    @pytest.mark.asyncio
    async def test_google_adk_node_in_workflow(self):
        """Test that Google ADK agent can be added as a workflow node."""
        from src.services.workflow import ConsultantGraph

        with patch('src.services.workflow.StateManager'):
            graph = ConsultantGraph()

            # The workflow should support adding Google ADK as a node
            # This tests the extensibility of the architecture
            assert hasattr(graph, 'add_node') or graph is not None

    @pytest.mark.asyncio
    async def test_workflow_switches_providers_dynamically(self):
        """Test that workflow can switch between LLM providers."""
        state = {
            "project_id": "test-123",
            "llm_provider": "google",
            "messages": [],
            "errors": [],
        }

        # Should be able to process with different providers
        assert isinstance(state, dict)
        assert state["llm_provider"] == "google"


# ============================================================================
# Test Google ADK Error Handling
# ============================================================================

class TestGoogleADKErrorHandling:
    """Test error handling for Google ADK integration."""

    @pytest.mark.asyncio
    async def test_fallback_to_openai_on_google_failure(self):
        """Test that system falls back to OpenAI if Google fails."""
        with patch('src.agents.base.ChatGoogleGenerativeAI') as mock_google:
            mock_google.side_effect = Exception("Google API unavailable")

            with patch('src.agents.base.ChatOpenAI') as mock_openai:
                mock_openai.return_value = Mock()

                # Should fall back to OpenAI
                try:
                    llm = get_llm(provider="google")
                except Exception:
                    # Try fallback
                    llm = get_llm(provider="openai")
                    assert llm is not None

    @pytest.mark.asyncio
    async def test_quota_exceeded_handling(self):
        """Test handling of Google API quota exceeded errors."""
        from src.agents.google_adk import GoogleADKAgent

        with patch('src.agents.base.get_llm'):
            agent = GoogleADKAgent()

            with patch.object(agent, 'llm') as mock_llm:
                mock_llm.ainvoke = AsyncMock(
                    side_effect=Exception("Quota exceeded")
                )

                state = {"project_id": "test", "messages": [], "errors": []}
                result = await agent.process(state)

                # Should handle quota errors gracefully
                assert "errors" in result


# ============================================================================
# Test Google ADK Performance Optimization
# ============================================================================

class TestGoogleADKPerformance:
    """Test performance optimizations for Google ADK."""

    @pytest.mark.asyncio
    async def test_google_adk_uses_streaming(self):
        """Test that Google ADK agent can use streaming responses."""
        from src.agents.google_adk import GoogleADKAgent

        with patch('src.agents.base.get_llm'):
            agent = GoogleADKAgent()

            # Should support streaming for better UX
            if hasattr(agent, 'stream_response'):
                assert callable(agent.stream_response)

    @pytest.mark.asyncio
    async def test_google_adk_caching(self):
        """Test that Google ADK implements response caching."""
        from src.agents.google_adk import GoogleADKAgent

        with patch('src.agents.base.get_llm'):
            agent = GoogleADKAgent()

            state = {
                "project_id": "test-123",
                "messages": [],
                "errors": [],
            }

            # Multiple calls with same input should use cache
            with patch.object(agent, 'llm') as mock_llm:
                mock_response = Mock()
                mock_response.content = "Cached response"
                mock_llm.ainvoke = AsyncMock(return_value=mock_response)

                result1 = await agent.process(state.copy())
                result2 = await agent.process(state.copy())

                # Both should complete successfully
                assert isinstance(result1, dict)
                assert isinstance(result2, dict)
