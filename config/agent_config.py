"""
Agent Configuration Schema and Loading
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import yaml
from pathlib import Path


class ModelConfig(BaseModel):
    """Configuration for LLM model settings"""
    provider: Optional[str] = Field(None, description="LLM provider (openai, anthropic, google)")
    model: Optional[str] = Field(None, description="Model name/identifier")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Temperature for sampling")
    max_tokens: Optional[int] = Field(None, gt=0, description="Maximum tokens to generate")


class PromptConfig(BaseModel):
    """Configuration for agent prompts"""
    system: Optional[str] = Field(None, description="System prompt/role definition")
    templates: Optional[Dict[str, str]] = Field(default_factory=dict, description="Named prompt templates")


class AgentConfig(BaseModel):
    """Configuration for a single agent"""
    name: str = Field(..., description="Agent name")
    enabled: bool = Field(True, description="Whether the agent is enabled")
    model: Optional[ModelConfig] = Field(None, description="Model configuration for this agent")
    prompts: Optional[PromptConfig] = Field(None, description="Prompt configuration for this agent")

    class Config:
        extra = "allow"  # Allow additional configuration fields


class AgentConfigRegistry(BaseModel):
    """Registry of all agent configurations"""
    version: str = Field("1.0", description="Configuration schema version")
    agents: Dict[str, AgentConfig] = Field(default_factory=dict, description="Agent configurations by name")

    @classmethod
    def load_from_file(cls, config_path: Path) -> "AgentConfigRegistry":
        """Load agent configurations from YAML file"""
        if not config_path.exists():
            return cls()

        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)

        return cls(**data) if data else cls()

    def get_agent_config(self, agent_name: str) -> Optional[AgentConfig]:
        """Get configuration for a specific agent"""
        return self.agents.get(agent_name)

    def save_to_file(self, config_path: Path):
        """Save agent configurations to YAML file"""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(self.model_dump(exclude_none=True), f, default_flow_style=False, sort_keys=False)
