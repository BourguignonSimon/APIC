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
