# Getting Started with Moya

## Installation

```bash
# Install from PyPI
pip install moya-framework

# Or install from source
git clone https://github.com/your-org/moya.git
cd moya
pip install -e .
```

## Prerequisites
- Python 3.10+
- OpenAI API key (for OpenAI agents)
- AWS credentials (for Bedrock agents)
- Ollama installation (for local models)

## Basic Usage Example

```python
from moya.agents import OpenAIAgent
from moya.tools import ToolRegistry
from moya.memory import InMemoryRepository

# 1. Set up memory and tools
memory_repo = InMemoryRepository()
tool_registry = ToolRegistry()

# 2. Create and configure agent
agent = OpenAIAgent(
    agent_name="my_assistant",
    description="A helpful assistant",
    tool_registry=tool_registry
)

# 3. Send messages and get responses
response = agent.handle_message("Hello, how can Moya help me?")
```

## Common Configuration Options
- Model selection (GPT-4, Claude, local models)
- Temperature and token limits
- System prompts and constraints
- Tool integrations
