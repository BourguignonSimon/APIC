"""
Prompt Manager Utility

Centralized management of AI prompts for all agents.
Loads prompts from YAML configuration files.

KEY BENEFITS:
-------------
1. MAINTAINABILITY: Prompts separated from code - easy to update
2. VERSION CONTROL: Track prompt changes independently from code changes
3. NON-DEVELOPER FRIENDLY: YAML is human-readable, no coding required
4. CONSISTENCY: Standardized format across all agents
5. PERFORMANCE: Caching reduces file I/O overhead
6. EXPERIMENTATION: Test different prompts without code modifications

USAGE EXAMPLE:
--------------
from src.utils.prompt_manager import get_prompt_manager

pm = get_prompt_manager()  # Singleton instance

# Get a prompt with variable substitution
prompt = pm.get_prompt(
    'interview_architect',
    'hypothesis_generation',
    variables={'client_name': 'Acme Corp', 'industry': 'Manufacturing'}
)

# Get full prompt with system role
full_prompt = pm.get_full_prompt('interview_architect', 'hypothesis_generation', variables)
messages = [
    SystemMessage(content=full_prompt['system_role']),
    HumanMessage(content=full_prompt['user_prompt'])
]
response = await llm.ainvoke(messages)

FILE STRUCTURE:
---------------
config/prompts/
├── interview_architect_prompts.yaml  # Interview Architect prompts (10 prompts)
├── hypothesis_generator_prompts.yaml # (Future) Hypothesis Generator prompts
└── gap_analyst_prompts.yaml          # (Future) Gap Analyst prompts

YAML FORMAT:
------------
prompt_name:
  system_role: "You are an expert..."  # Optional: Sets AI persona
  user_prompt: |                        # Required: Task description
    Analyze {variable1} and {variable2}.
    Return JSON format: [...]
  constraints:  # Optional: Quality guidelines
    - Constraint 1
    - Constraint 2

settings:  # Optional: LLM configuration
  temperature: 0.7
  max_tokens: 4096
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml


class PromptManager:
    """
    Manages loading and formatting of AI prompts from YAML configuration.

    This class provides centralized prompt management with the following features:
    - Loads prompts from YAML files in config/prompts/ directory
    - Caches loaded prompts for performance
    - Supports template variable substitution using {variable_name} syntax
    - Provides both system roles and user prompts for chat models
    - Retrieves LLM settings and quality constraints from configuration

    Prompts are organized by agent name:
    - interview_architect_prompts.yaml → Interview Architect Agent prompts
    - hypothesis_generator_prompts.yaml → Hypothesis Generator prompts (future)
    - gap_analyst_prompts.yaml → Gap Analyst prompts (future)

    The singleton pattern (via get_prompt_manager()) ensures a single instance
    is shared across the application, maximizing cache efficiency.
    """

    def __init__(self, prompts_dir: Optional[str] = None):
        """
        Initialize the prompt manager.

        Args:
            prompts_dir: Directory containing prompt YAML files
                        If None, defaults to config/prompts/ relative to project root
                        Custom path useful for testing with different prompt sets

        Attributes:
            prompts_dir: Path object pointing to prompts directory
            _cache: Internal cache storing loaded prompts by agent name
                   Format: {agent_name: {prompt_key: prompt_config, ...}, ...}
        """
        if prompts_dir is None:
            # Default to config/prompts/ relative to project root
            # Navigate from src/utils/prompt_manager.py → project root → config/prompts
            project_root = Path(__file__).parent.parent.parent
            prompts_dir = project_root / "config" / "prompts"

        self.prompts_dir = Path(prompts_dir)

        # Cache structure: {agent_name: {prompt_data}}
        # Caching reduces file I/O and improves performance
        # Cache is cleared when reload_prompts() is called
        self._cache: Dict[str, Dict[str, Any]] = {}

    def load_prompts(self, agent_name: str) -> Dict[str, Any]:
        """
        Load prompts for a specific agent from YAML file.

        This method handles the low-level loading and caching of prompt YAML files.
        It's called internally by other methods (get_prompt, get_full_prompt, etc.)
        and typically doesn't need to be called directly.

        File Naming Convention:
        ----------------------
        Agent prompts are stored in files named: {agent_name}_prompts.yaml
        Example: 'interview_architect' → 'interview_architect_prompts.yaml'

        Caching Behavior:
        ----------------
        - First call: Reads file from disk, parses YAML, caches result
        - Subsequent calls: Returns cached data (no file I/O)
        - Cache persists for lifetime of PromptManager instance
        - Call reload_prompts(agent_name) to invalidate cache and reload

        YAML Structure:
        ---------------
        prompt_key_1:
          system_role: "..."
          user_prompt: "..."
          constraints: [...]
        prompt_key_2:
          ...
        settings:
          temperature: 0.7
          max_tokens: 4096

        Args:
            agent_name: Name of the agent (e.g., 'interview_architect')
                       Used to construct filename: {agent_name}_prompts.yaml

        Returns:
            Dictionary containing all prompts and configuration for the agent
            Structure: {
                'prompt_key_1': {system_role, user_prompt, constraints},
                'prompt_key_2': {...},
                'settings': {temperature, max_tokens, ...}
            }

        Raises:
            FileNotFoundError: If the prompts file doesn't exist
                              Check that config/prompts/{agent_name}_prompts.yaml exists
            yaml.YAMLError: If the file is not valid YAML
                           Validate YAML syntax at https://www.yamllint.com/
        """
        # ============================================================
        # CHECK CACHE FIRST
        # ============================================================
        # Avoid re-reading file if already loaded
        # Cache key is the agent_name string
        if agent_name in self._cache:
            return self._cache[agent_name]

        # ============================================================
        # CONSTRUCT FILE PATH
        # ============================================================
        # Convert agent name to filename using convention: {agent}_prompts.yaml
        filename = f"{agent_name}_prompts.yaml"
        file_path = self.prompts_dir / filename

        # ============================================================
        # VALIDATE FILE EXISTS
        # ============================================================
        # Provide helpful error message if file not found
        if not file_path.exists():
            raise FileNotFoundError(
                f"Prompts file not found for agent '{agent_name}': {file_path}\n"
                f"Expected location: {file_path}\n"
                f"Create this file or check the agent name spelling."
            )

        # ============================================================
        # LOAD AND PARSE YAML
        # ============================================================
        # Use safe_load to prevent arbitrary code execution
        # Opens with UTF-8 encoding to support international characters
        with open(file_path, 'r', encoding='utf-8') as f:
            prompts = yaml.safe_load(f)

        # ============================================================
        # CACHE FOR FUTURE USE
        # ============================================================
        # Store in cache to avoid re-reading file on subsequent calls
        # Cache persists until reload_prompts() is called or instance is destroyed
        self._cache[agent_name] = prompts

        return prompts

    def get_prompt(
        self,
        agent_name: str,
        prompt_key: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get a specific prompt with variable substitution.

        Args:
            agent_name: Name of the agent
            prompt_key: Key of the prompt in the YAML file
            variables: Dictionary of variables to substitute in the prompt

        Returns:
            Formatted prompt string with variables substituted

        Example:
            >>> pm = PromptManager()
            >>> prompt = pm.get_prompt(
            ...     'interview_architect',
            ...     'hypothesis_generation',
            ...     {'client_name': 'Acme Corp', 'target_departments': 'Sales, IT'}
            ... )
        """
        prompts = self.load_prompts(agent_name)

        if prompt_key not in prompts:
            raise KeyError(
                f"Prompt key '{prompt_key}' not found in {agent_name} prompts"
            )

        prompt_config = prompts[prompt_key]

        # Get the user prompt template
        if isinstance(prompt_config, dict):
            user_prompt = prompt_config.get('user_prompt', '')
            system_role = prompt_config.get('system_role', '')
        else:
            user_prompt = prompt_config
            system_role = ''

        # Substitute variables if provided
        if variables:
            user_prompt = user_prompt.format(**variables)

        return user_prompt

    def get_system_role(self, agent_name: str, prompt_key: str) -> str:
        """
        Get the system role for a specific prompt.

        Args:
            agent_name: Name of the agent
            prompt_key: Key of the prompt in the YAML file

        Returns:
            System role string (empty if not defined)
        """
        prompts = self.load_prompts(agent_name)

        if prompt_key not in prompts:
            return ""

        prompt_config = prompts[prompt_key]

        if isinstance(prompt_config, dict):
            return prompt_config.get('system_role', '')

        return ""

    def get_full_prompt(
        self,
        agent_name: str,
        prompt_key: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Get both system role and user prompt for chat-based LLMs.

        This is the PRIMARY method for using prompts with chat models like:
        - OpenAI GPT-4/GPT-3.5 (ChatOpenAI)
        - Anthropic Claude (ChatAnthropic)
        - Google Gemini (ChatGoogleGenerativeAI)

        Chat models perform better with separate system and user messages:
        - System role: Sets the AI's expertise, persona, and behavior
        - User prompt: Provides the specific task with context and data

        Usage Pattern with LangChain:
        -----------------------------
        from langchain_core.messages import SystemMessage, HumanMessage

        pm = get_prompt_manager()
        full_prompt = pm.get_full_prompt(
            'interview_architect',
            'hypothesis_generation',
            {'client_name': 'Acme', 'industry': 'Manufacturing'}
        )

        messages = [
            SystemMessage(content=full_prompt['system_role']),
            HumanMessage(content=full_prompt['user_prompt'])
        ]
        response = await llm.ainvoke(messages)

        Why Separate System Role and User Prompt?
        -----------------------------------------
        Research shows chat models perform better when:
        1. System role defines expertise and constraints
        2. User prompt focuses on the specific task
        3. Variables are substituted in user prompt (not system role)

        This separation also allows:
        - Reusing system roles across similar prompts
        - Testing different system roles without changing task description
        - Clearer separation of "who the AI is" vs "what to do"

        Args:
            agent_name: Name of the agent (e.g., 'interview_architect')
            prompt_key: Key of the prompt in the YAML file (e.g., 'hypothesis_generation')
            variables: Dictionary of variables to substitute in user_prompt
                      Example: {'client_name': 'Acme', 'industry': 'Tech'}
                      Variables use {variable_name} syntax in YAML

        Returns:
            Dictionary with two keys:
            {
                'system_role': System message content (defines AI persona)
                'user_prompt': User message content (task with variables substituted)
            }

        Example:
            >>> pm = PromptManager()
            >>> full_prompt = pm.get_full_prompt(
            ...     'interview_architect',
            ...     'hypothesis_generation',
            ...     {'client_name': 'Acme Corp', 'industry': 'Manufacturing'}
            ... )
            >>> print(full_prompt['system_role'])
            'You are an expert business process consultant with 15+ years...'
            >>> print(full_prompt['user_prompt'])
            'Analyze the following for Acme Corp in Manufacturing industry...'
        """
        return {
            'system_role': self.get_system_role(agent_name, prompt_key),
            'user_prompt': self.get_prompt(agent_name, prompt_key, variables)
        }

    def get_settings(self, agent_name: str) -> Dict[str, Any]:
        """
        Get configuration settings for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Dictionary of settings (temperature, max_tokens, etc.)
        """
        prompts = self.load_prompts(agent_name)
        return prompts.get('settings', {})

    def get_constraints(
        self,
        agent_name: str,
        prompt_key: str
    ) -> list:
        """
        Get constraints for a specific prompt.

        Args:
            agent_name: Name of the agent
            prompt_key: Key of the prompt in the YAML file

        Returns:
            List of constraint strings (empty if not defined)
        """
        prompts = self.load_prompts(agent_name)

        if prompt_key not in prompts:
            return []

        prompt_config = prompts[prompt_key]

        if isinstance(prompt_config, dict):
            return prompt_config.get('constraints', [])

        return []

    def reload_prompts(self, agent_name: Optional[str] = None):
        """
        Reload prompts from disk, clearing the cache.

        Args:
            agent_name: Specific agent to reload (or None to reload all)
        """
        if agent_name:
            if agent_name in self._cache:
                del self._cache[agent_name]
        else:
            self._cache.clear()


# ============================================================
# SINGLETON PATTERN IMPLEMENTATION
# ============================================================
# Global variable stores the single PromptManager instance
# This ensures all agents share the same cache for efficiency
_prompt_manager_instance = None


def get_prompt_manager() -> PromptManager:
    """
    Get the global PromptManager instance (singleton pattern).

    This is the RECOMMENDED way to access the PromptManager throughout the application.
    Using a singleton ensures:
    - Single shared cache across all agents (memory efficient)
    - Consistent prompt loading behavior
    - No redundant file I/O
    - Easy to use - no need to pass instance around

    Singleton Pattern:
    -----------------
    - First call: Creates new PromptManager instance, stores in global variable
    - Subsequent calls: Returns the existing instance
    - Instance persists for lifetime of the application process
    - All agents and components share the same instance and cache

    Thread Safety:
    -------------
    Note: This implementation is NOT thread-safe. If using in a multi-threaded
    environment (e.g., with threading module), consider using a lock:

    import threading
    _lock = threading.Lock()

    def get_prompt_manager():
        global _prompt_manager_instance
        if _prompt_manager_instance is None:
            with _lock:
                if _prompt_manager_instance is None:  # Double-check
                    _prompt_manager_instance = PromptManager()
        return _prompt_manager_instance

    However, for typical FastAPI/async usage (single event loop), this
    simple implementation is sufficient.

    Usage Example:
    -------------
    from src.utils.prompt_manager import get_prompt_manager

    # In any agent or module
    pm = get_prompt_manager()  # Always returns the same instance
    prompt = pm.get_prompt('interview_architect', 'hypothesis_generation', {...})

    # In another agent
    pm2 = get_prompt_manager()  # pm2 is the SAME instance as pm
    assert pm is pm2  # True!

    Returns:
        Shared PromptManager instance (creates one if none exists)
    """
    global _prompt_manager_instance

    # Create instance if it doesn't exist yet
    if _prompt_manager_instance is None:
        _prompt_manager_instance = PromptManager()

    return _prompt_manager_instance
