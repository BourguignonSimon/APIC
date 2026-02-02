"""
Base Agent Class
Provides common functionality for all APIC agents.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from langchain_core.language_models import BaseChatModel

from config.settings import AgentConfig
from src.services.llm_factory import get_llm

logger = logging.getLogger(__name__)


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

        # Initialize LLM - uses global provider from settings
        if llm:
            self.llm = llm
        elif agent_config and agent_config.model:
            # Use agent-specific model parameters (temperature, max_tokens)
            self.llm = get_llm(
                temperature=agent_config.model.temperature,
                max_tokens=agent_config.model.max_tokens,
            )
        else:
            # Use default LLM configuration
            self.llm = get_llm()

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

    def get_prompt(self, prompt_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a prompt template from agent configuration.

        Args:
            prompt_name: Name of the prompt template to retrieve
            default: Default prompt to use if not configured

        Returns:
            Prompt template string or None
        """
        prompts = getattr(self.agent_config, 'prompts', None) if self.agent_config else None
        if not prompts:
            return default
        if prompt_name == "system" and prompts.system:
            return prompts.system
        if prompts.templates and prompt_name in prompts.templates:
            return prompts.templates[prompt_name]
        return default
