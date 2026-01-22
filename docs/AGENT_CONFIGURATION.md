# Agent Configuration Guide

This guide explains how to configure individual agents in the APIC system with custom prompts and model settings.

## Overview

APIC allows you to configure each agent independently with:
- **Custom LLM models and providers** (OpenAI, Anthropic, Google)
- **Model parameters** (temperature, max_tokens)
- **Custom prompts** for different agent behaviors
- **Per-agent enabling/disabling**

## Configuration File

Agent configurations are stored in `config/agents.yaml`. This file is loaded at startup and used to configure each agent in the workflow.

### Configuration Structure

```yaml
version: "1.0"

agents:
  <agent_name>:
    name: "AgentName"
    enabled: true
    model:
      provider: "openai"  # openai, anthropic, or google
      model: "gpt-4o"
      temperature: 0.7
      max_tokens: 4096
    prompts:
      system: "System prompt/role definition"
      templates:
        template_name: "Template content with {variables}"
```

## Agent Names

The following agent names are available for configuration:

| Agent Name | Description |
|------------|-------------|
| `ingestion` | Knowledge Ingestion Agent - Processes and summarizes documents |
| `hypothesis` | Hypothesis Generator Agent - Identifies potential inefficiencies |
| `interview` | Interview Architect Agent - Creates interview scripts |
| `gap_analyst` | Gap Analyst Agent - Compares SOPs with reality |
| `solution` | Solution Architect Agent - Recommends solutions |
| `reporting` | Reporting Agent - Generates final reports |

## Model Configuration

### Provider Options

- **openai**: OpenAI models (GPT-4, GPT-3.5, etc.)
- **anthropic**: Anthropic Claude models
- **google**: Google Gemini models

### Model Parameters

- **provider**: LLM provider identifier
- **model**: Specific model name/identifier
- **temperature**: Controls randomness (0.0 = deterministic, 2.0 = very creative)
- **max_tokens**: Maximum tokens to generate in responses

### Example: Using Different Models for Different Agents

```yaml
agents:
  hypothesis:
    model:
      provider: "openai"
      model: "gpt-4o"
      temperature: 0.7

  reporting:
    model:
      provider: "anthropic"
      model: "claude-3-5-sonnet-20241022"
      temperature: 0.5
      max_tokens: 8000
```

## Prompt Configuration

### System Prompts

The `system` prompt defines the agent's role and behavior. This is used across all operations for that agent.

```yaml
agents:
  hypothesis:
    prompts:
      system: |
        You are an expert management consultant specializing in process optimization.
        Your expertise includes identifying inefficiencies and improvement opportunities.
```

### Prompt Templates

Named templates are used for specific operations within an agent. Templates can include variables using `{variable_name}` syntax.

```yaml
agents:
  hypothesis:
    prompts:
      templates:
        generate_hypotheses: |
          Based on the following documents, identify potential inefficiencies:

          Documents:
          {documents}

          Generate structured hypotheses about improvement opportunities.
```

### Available Prompt Templates by Agent

#### Ingestion Agent
- `summary`: Document summarization prompt

#### Hypothesis Agent
- `generate_hypotheses`: Prompt for generating inefficiency hypotheses

#### Interview Agent
- `determine_roles`: Prompt for determining interview targets
- `generate_questions`: Prompt for generating interview questions

#### Gap Analyst Agent
- `analyze_gaps`: Prompt for comparing SOPs vs reality

#### Solution Agent
- `recommend_solutions`: Prompt for solution recommendations

#### Reporting Agent
- `executive_summary`: Prompt for executive summary generation
- `roadmap`: Prompt for implementation roadmap creation

## Environment Variables

Agent configuration can be controlled via environment variables:

```bash
# Specify custom agent configuration file path
AGENT_CONFIG_PATH=config/agents.yaml

# Default LLM settings (used when not specified in agent config)
DEFAULT_LLM_PROVIDER=openai
OPENAI_MODEL=gpt-4o
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
GOOGLE_MODEL=gemini-1.5-flash
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
```

## Usage Examples

### Example 1: Using Claude for Reporting

```yaml
agents:
  reporting:
    name: "ReportingAgent"
    model:
      provider: "anthropic"
      model: "claude-3-5-sonnet-20241022"
      temperature: 0.5
      max_tokens: 8000
```

### Example 2: Custom Hypothesis Generation

```yaml
agents:
  hypothesis:
    name: "HypothesisGeneratorAgent"
    model:
      provider: "openai"
      model: "gpt-4o"
      temperature: 0.8
    prompts:
      system: |
        You are an expert process analyst with 20+ years of experience.
        Focus on identifying automation opportunities and cost savings.
      templates:
        generate_hypotheses: |
          Analyze these documents for automation opportunities:

          {documents}

          Focus specifically on:
          1. Repetitive manual tasks
          2. Data entry processes
          3. Report generation workflows
          4. Approval bottlenecks
```

### Example 3: Disabling an Agent

```yaml
agents:
  hypothesis:
    enabled: false  # Skip hypothesis generation
```

### Example 4: Budget-Conscious Configuration

Use faster, cheaper models for non-critical agents:

```yaml
agents:
  ingestion:
    model:
      provider: "openai"
      model: "gpt-4o-mini"  # Cheaper model for document processing
      temperature: 0.3

  reporting:
    model:
      provider: "anthropic"
      model: "claude-3-5-sonnet-20241022"  # Premium model for final report
      temperature: 0.5
```

## Fallback Behavior

If an agent configuration is not found in `agents.yaml`:
1. The agent will use **default settings** from environment variables
2. Built-in prompts will be used
3. The agent will still function normally

This ensures backward compatibility with existing deployments.

## Best Practices

1. **Version Control**: Keep `agents.yaml` in version control
2. **Testing**: Test configuration changes with sample projects first
3. **Temperature Settings**:
   - Use lower temperatures (0.3-0.5) for analytical tasks
   - Use higher temperatures (0.7-0.9) for creative tasks
4. **Model Selection**:
   - Use premium models (GPT-4, Claude) for critical reasoning
   - Use faster models (GPT-3.5, Gemini Flash) for simple tasks
5. **Prompt Engineering**:
   - Be specific about expected output format
   - Include examples in prompts when possible
   - Test prompts individually before deployment

## Troubleshooting

### Configuration Not Loading

Check:
- YAML syntax is valid (no tab characters, proper indentation)
- `AGENT_CONFIG_PATH` points to correct file
- File has read permissions

### Agent Using Wrong Model

Check:
- Agent name matches exactly (case-sensitive)
- Provider is one of: openai, anthropic, google
- API keys are configured in environment

### Prompts Not Applied

Check:
- Template names match what agent expects
- Variables in templates use `{variable}` syntax
- System prompt is in `prompts.system`, not `prompts.templates.system`

## API Reference

### AgentConfig Schema

```python
class ModelConfig:
    provider: Optional[str]
    model: Optional[str]
    temperature: Optional[float]  # 0.0-2.0
    max_tokens: Optional[int]

class PromptConfig:
    system: Optional[str]
    templates: Optional[Dict[str, str]]

class AgentConfig:
    name: str
    enabled: bool = True
    model: Optional[ModelConfig]
    prompts: Optional[PromptConfig]
```

### Loading Configuration

```python
from config.settings import get_agent_config

# Load all agent configurations
config_registry = get_agent_config()

# Get specific agent configuration
hypothesis_config = config_registry.get_agent_config("hypothesis")
```

## Migration Guide

### From Global Configuration

Before (using global settings):
```python
# All agents use same model
DEFAULT_LLM_PROVIDER=openai
OPENAI_MODEL=gpt-4o
```

After (per-agent configuration):
```yaml
# Different models per agent
agents:
  hypothesis:
    model:
      provider: "openai"
      model: "gpt-4o"

  ingestion:
    model:
      provider: "openai"
      model: "gpt-4o-mini"  # Faster, cheaper
```

## Additional Resources

- [APIC Architecture](README.md)
- [API Documentation](API_CONTRACTS.md)
- [Environment Variables](.env.example)
