# AI Prompts Configuration

This directory contains centralized AI prompts for all agents in the APIC system.

## 📁 Structure

```
config/prompts/
├── README.md                          # This file
├── interview_architect_prompts.yaml   # Interview Architect prompts
├── hypothesis_generator_prompts.yaml  # (Future) Hypothesis Generator prompts
└── gap_analyst_prompts.yaml          # (Future) Gap Analyst prompts
```

## 🎯 Purpose

**Why separate prompt files?**

1. **Maintainability**: Easy to update prompts without touching code
2. **Version Control**: Track prompt changes independently
3. **Experimentation**: Test different prompts without code changes
4. **Collaboration**: Non-developers can improve prompts
5. **Consistency**: Standardized format across agents
6. **Documentation**: Built-in documentation for each prompt

## 📖 YAML Format

Each agent's prompts file follows this structure:

```yaml
prompt_name:
  system_role: "You are an expert..."  # Optional: System message
  user_prompt: |                        # Required: User message
    Your prompt template here.
    Variables in {curly_braces}.

  constraints:  # Optional: Quality guidelines
    - Constraint 1
    - Constraint 2

settings:  # Optional: LLM configuration
  temperature: 0.7
  max_tokens: 4096
```

## 🔧 Using Prompts in Code

### Basic Usage

```python
from src.utils.prompt_manager import get_prompt_manager

# Get prompt manager instance
pm = get_prompt_manager()

# Load prompts for an agent
prompts = pm.load_prompts('interview_architect')

# Get a specific prompt with variables
prompt = pm.get_prompt(
    agent_name='interview_architect',
    prompt_key='hypothesis_generation',
    variables={
        'client_name': 'Acme Corp',
        'target_departments': 'Sales, IT',
        'document_summaries': '...'
    }
)
```

### With System Role

```python
# Get both system role and user prompt
full_prompt = pm.get_full_prompt(
    agent_name='interview_architect',
    prompt_key='hypothesis_generation',
    variables={'client_name': 'Acme Corp'}
)

# Use with LangChain
from langchain_core.messages import SystemMessage, HumanMessage

messages = [
    SystemMessage(content=full_prompt['system_role']),
    HumanMessage(content=full_prompt['user_prompt'])
]
response = await llm.ainvoke(messages)
```

### Get Agent Settings

```python
# Get LLM configuration
settings = pm.get_settings('interview_architect')
# Returns: {'temperature': 0.7, 'max_tokens': 4096, ...}

# Get constraints
constraints = pm.get_constraints('interview_architect', 'hypothesis_generation')
# Returns: ['Be specific', 'Base on document content', ...]
```

## 📝 Available Prompts

### Interview Architect (`interview_architect_prompts.yaml`)

| Prompt Key | Purpose | Variables Required |
|------------|---------|-------------------|
| `hypothesis_generation` | Generate hypotheses from documents (AI fallback) | `client_name`, `target_departments`, `industry`, `document_summaries` |
| `hypothesis_analysis` | Analyze existing hypotheses for themes | `target_departments`, `hypotheses_list` |
| `customer_context_generation` | Create customer profile | `client_name`, `target_departments`, `document_summaries`, `hypotheses_summary` |
| `diagnostic_leads_generation` | Convert hypotheses to diagnostic leads | `hypotheses_list`, `analysis_summary` |
| `target_roles_identification` | Determine interview targets | `target_departments`, `process_areas_list`, `analysis_summary` |
| `validation_questions_generation` | Create validation questions | `target_roles`, `hypotheses_list`, `analysis_summary` |
| `discovery_questions_generation` | Create discovery questions | `target_roles`, `hypotheses_summary`, `analysis_summary` |
| `interview_introduction` | Generate interview intro | `client_name`, `target_departments`, `analysis_summary` |
| `interview_closing` | Generate interview closing | `question_count`, `topics_summary` |
| `duration_estimation` | Estimate interview duration | `question_count`, `validation_count`, `discovery_count`, `analysis_summary` |

## ✏️ Customizing Prompts

### 1. Modify Existing Prompts

Simply edit the YAML file:

```yaml
hypothesis_generation:
  system_role: "You are an expert in {your_domain}..."
  user_prompt: |
    Your custom prompt here.
    Add {new_variables} as needed.
```

**No code changes required!** The PromptManager automatically reloads.

### 2. Add New Variables

Add variables to the prompt template:

```yaml
user_prompt: |
  CLIENT: {client_name}
  INDUSTRY: {industry}      # New variable
  TEAM SIZE: {team_size}    # New variable
```

Then pass them when calling:

```python
pm.get_prompt(
    'interview_architect',
    'hypothesis_generation',
    variables={
        'client_name': 'Acme',
        'industry': 'Healthcare',
        'team_size': '50-100'
    }
)
```

### 3. Add New Prompts

Add a new section to the YAML:

```yaml
custom_analysis:
  system_role: "You are an analyst..."
  user_prompt: |
    Analyze {data} and provide insights.

  constraints:
    - Be data-driven
    - Provide actionable recommendations
```

Use it immediately:

```python
prompt = pm.get_prompt(
    'interview_architect',
    'custom_analysis',
    variables={'data': '...'}
)
```

### 4. Adjust LLM Settings

Modify the `settings` section:

```yaml
settings:
  temperature: 0.9      # More creative
  max_tokens: 8192      # Longer responses
  top_p: 0.95          # Nucleus sampling
```

Retrieve in code:

```python
settings = pm.get_settings('interview_architect')
llm = ChatOpenAI(
    temperature=settings['temperature'],
    max_tokens=settings['max_tokens']
)
```

## 🧪 Testing Prompts

### Test Individual Prompts

```python
from src.utils.prompt_manager import get_prompt_manager

pm = get_prompt_manager()

# Test prompt generation
prompt = pm.get_prompt(
    'interview_architect',
    'hypothesis_generation',
    variables={
        'client_name': 'Test Corp',
        'target_departments': 'Sales',
        'industry': 'Tech',
        'document_summaries': 'Test summary...'
    }
)

print(prompt)
```

### Validate All Prompts

```python
import yaml
from pathlib import Path

prompts_dir = Path('config/prompts')

for yaml_file in prompts_dir.glob('*_prompts.yaml'):
    print(f"Validating {yaml_file.name}...")
    with open(yaml_file) as f:
        prompts = yaml.safe_load(f)
    print(f"  ✓ Contains {len(prompts)} prompt sections")
```

## 📚 Best Practices

### 1. Clear System Roles

```yaml
# Good ✓
system_role: "You are an expert business process consultant with 15+ years of experience in manufacturing optimization."

# Avoid ✗
system_role: "You are helpful."
```

### 2. Specific Instructions

```yaml
# Good ✓
user_prompt: |
  Analyze the document summaries and identify 3-5 specific process inefficiencies.
  For each, provide evidence and confidence scores.

# Avoid ✗
user_prompt: |
  Analyze the documents.
```

### 3. Structured Output

```yaml
# Good ✓
user_prompt: |
  Return as JSON array:
  [{"process": "string", "issue": "string", "confidence": 0.8}]

# Avoid ✗
user_prompt: |
  List the issues.
```

### 4. Use Constraints

```yaml
validation_questions_generation:
  # ... prompt ...

  constraints:
    - Use "How", "What", "Describe" starters
    - Avoid yes/no questions
    - Focus on current state, not ideal
    - Probe for concrete examples
```

### 5. Variable Naming

```yaml
# Good ✓
variables: {client_name}, {target_departments}, {document_summaries}

# Avoid ✗
variables: {x}, {data}, {input}
```

## 🔄 Reload Prompts

Prompts are cached for performance. To reload after changes:

```python
pm = get_prompt_manager()

# Reload specific agent
pm.reload_prompts('interview_architect')

# Reload all
pm.reload_prompts()
```

**Note**: In development, prompts reload automatically on each request.

## 🚀 Advanced Usage

### Dynamic Prompt Selection

```python
# Choose prompt based on context
prompt_key = 'hypothesis_generation' if not hypotheses else 'hypothesis_analysis'

prompt = pm.get_prompt(
    'interview_architect',
    prompt_key,
    variables=context_vars
)
```

### Prompt Chaining

```python
# Use output of one prompt as input to another
analysis = await generate_analysis(...)

questions = pm.get_prompt(
    'interview_architect',
    'validation_questions_generation',
    variables={'analysis_summary': analysis}
)
```

### Multi-Language Support

```yaml
# Store prompts for different languages
hypothesis_generation_en:
  system_role: "You are an expert business consultant..."

hypothesis_generation_fr:
  system_role: "Vous êtes un consultant expert..."
```

## 📊 Monitoring Prompt Performance

Track which prompts work best:

```python
import logging

logger = logging.getLogger(__name__)

prompt_key = 'hypothesis_generation'
prompt = pm.get_prompt('interview_architect', prompt_key, variables)

logger.info(f"Using prompt: {prompt_key}")

response = await llm.ainvoke(prompt)

logger.info(f"Prompt {prompt_key} generated {len(response)} hypotheses")
```

## 🎓 Learning Resources

- **LangChain Prompts**: https://python.langchain.com/docs/modules/model_io/prompts/
- **Prompt Engineering Guide**: https://www.promptingguide.ai/
- **OpenAI Best Practices**: https://platform.openai.com/docs/guides/prompt-engineering

## 🤝 Contributing

When adding new prompts:

1. ✅ Follow the YAML structure
2. ✅ Include system role and constraints
3. ✅ Document required variables
4. ✅ Test with actual data
5. ✅ Update this README

## 📄 License

These prompts are part of the APIC system and follow the same license.

---

**Questions?** Check the main documentation or create an issue.
