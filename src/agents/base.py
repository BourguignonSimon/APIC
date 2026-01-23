"""
Base Agent Class
Provides common functionality for all APIC agents.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from config.settings import settings
from config.agent_config import AgentConfig, ModelConfig

logger = logging.getLogger(__name__)


def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> BaseChatModel:
    """
    Factory function to get the appropriate LLM instance.

    Args:
        provider: LLM provider ("openai", "anthropic", or "google")
        model: Model name to use
        temperature: Temperature for generation
        max_tokens: Maximum tokens for generation

    Returns:
        Configured LLM instance
    """
    provider = provider or settings.DEFAULT_LLM_PROVIDER
    temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
    max_tokens = max_tokens or settings.LLM_MAX_TOKENS

    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is not configured. "
                "Please set the OPENAI_API_KEY environment variable or use a different LLM provider."
            )
        model = model or settings.OPENAI_MODEL
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=settings.OPENAI_API_KEY,
        )
    elif provider == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY is not configured. "
                "Please set the ANTHROPIC_API_KEY environment variable or use a different LLM provider."
            )
        model = model or settings.ANTHROPIC_MODEL
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=settings.ANTHROPIC_API_KEY,
        )
    elif provider == "google":
        if not settings.GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY is not configured. "
                "Please set the GOOGLE_API_KEY environment variable or use a different LLM provider."
            )
        model = model or settings.GOOGLE_MODEL
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            max_output_tokens=max_tokens,
            google_api_key=settings.GOOGLE_API_KEY,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def get_embeddings(provider: Optional[str] = None) -> Embeddings:
    """
    Factory function to get the appropriate embeddings instance.

    Args:
        provider: Embeddings provider ("openai" or "google")
                  Note: Anthropic doesn't provide embeddings, falls back to OpenAI

    Returns:
        Configured embeddings instance

    Raises:
        ValueError: If the required API key is not configured
    """
    provider = provider or settings.DEFAULT_LLM_PROVIDER

    # Anthropic doesn't have embeddings, fall back to OpenAI or Google
    if provider == "anthropic":
        if settings.OPENAI_API_KEY:
            provider = "openai"
        elif settings.GOOGLE_API_KEY:
            provider = "google"
        else:
            raise ValueError(
                "Embeddings require either OPENAI_API_KEY or GOOGLE_API_KEY. "
                "Anthropic does not provide an embeddings API."
            )

    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is not configured. "
                "Please set the OPENAI_API_KEY environment variable for embeddings."
            )
        return OpenAIEmbeddings(
            api_key=settings.OPENAI_API_KEY,
            model="text-embedding-3-small",
        )
    elif provider == "google":
        if not settings.GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY is not configured. "
                "Please set the GOOGLE_API_KEY environment variable for embeddings."
            )
        return GoogleGenerativeAIEmbeddings(
            google_api_key=settings.GOOGLE_API_KEY,
            model="models/embedding-001",
        )
    else:
        raise ValueError(f"Unsupported embeddings provider: {provider}")


class BaseAgent(ABC):
    """
    Base class for all APIC agents.
    Provides common functionality and interface.
    """

    def __init__(
        self,
        name: str,
        llm: Optional[BaseChatModel] = None,
        agent_config: Optional[AgentConfig] = None,
        **kwargs,
    ):
        """
        Initialize the base agent.

        Args:
            name: Name of the agent
            llm: LLM instance to use (optional, will create default if not provided)
            agent_config: Agent-specific configuration (optional)
            **kwargs: Additional keyword arguments
        """
        self.name = name
        self.agent_config = agent_config

        # Initialize LLM based on agent configuration or defaults
        if llm:
            self.llm = llm
        elif agent_config and agent_config.model:
            # Use agent-specific model configuration
            self.llm = get_llm(
                provider=agent_config.model.provider,
                model=agent_config.model.model,
                temperature=agent_config.model.temperature,
                max_tokens=agent_config.model.max_tokens,
            )
        else:
            # Use default LLM
            self.llm = get_llm()

        self.logger = logging.getLogger(f"apic.agents.{name}")

        # Log configuration info
        if agent_config:
            self.log_debug(f"Initialized with custom configuration")
            if agent_config.model:
                self.log_debug(
                    f"Using model: {agent_config.model.provider}/{agent_config.model.model}"
                )

    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the current state and return updated state.

        Args:
            state: Current graph state

        Returns:
            Updated graph state
        """
        pass

    def log_info(self, message: str) -> None:
        """Log an info message."""
        self.logger.info(f"[{self.name}] {message}")

    def log_error(self, message: str, error: Optional[Exception] = None) -> None:
        """Log an error message."""
        if error:
            self.logger.error(f"[{self.name}] {message}: {error}")
        else:
            self.logger.error(f"[{self.name}] {message}")

    def log_debug(self, message: str) -> None:
        """Log a debug message."""
        self.logger.debug(f"[{self.name}] {message}")

    def get_prompt(self, prompt_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a prompt template from agent configuration.

        Args:
            prompt_name: Name of the prompt template to retrieve
            default: Default prompt to use if not configured

        Returns:
            Prompt template string or None
        """
        if self.agent_config and self.agent_config.prompts:
            if prompt_name == "system" and self.agent_config.prompts.system:
                return self.agent_config.prompts.system
            if self.agent_config.prompts.templates and prompt_name in self.agent_config.prompts.templates:
                return self.agent_config.prompts.templates[prompt_name]
        return default
