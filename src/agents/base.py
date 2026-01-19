"""
Base Agent Class
Provides common functionality for all APIC agents.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

from config.settings import settings

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
        provider: LLM provider ("openai" or "anthropic")
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
        model = model or settings.OPENAI_MODEL
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=settings.OPENAI_API_KEY,
        )
    elif provider == "anthropic":
        model = model or settings.ANTHROPIC_MODEL
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=settings.ANTHROPIC_API_KEY,
        )
    elif provider == "google":
        if not GOOGLE_AVAILABLE:
            raise ImportError(
                "Google Generative AI not available. "
                "Install with: pip install langchain-google-genai"
            )
        if not settings.GOOGLE_API_KEY:
            raise ValueError(
                "Google API key not found. "
                "Set GOOGLE_API_KEY in your environment variables."
            )
        model = model or settings.GOOGLE_MODEL
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            google_api_key=settings.GOOGLE_API_KEY,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


class BaseAgent(ABC):
    """
    Base class for all APIC agents.
    Provides common functionality and interface.
    """

    def __init__(
        self,
        name: str,
        llm: Optional[BaseChatModel] = None,
        **kwargs,
    ):
        """
        Initialize the base agent.

        Args:
            name: Name of the agent
            llm: LLM instance to use (optional, will create default if not provided)
            **kwargs: Additional keyword arguments
        """
        self.name = name
        self.llm = llm or get_llm()
        self.logger = logging.getLogger(f"apic.agents.{name}")

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
