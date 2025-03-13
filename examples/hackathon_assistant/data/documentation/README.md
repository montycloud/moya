# Moya Framework Documentation

## Overview

MOYA is a reference implementation of a flexible framework for building and orchestrating AI agents, based on the research paper "Engineering LLM Powered Multi-agent Framework for Autonomous CloudOps". 

### Core Features

- **Agent Management**: Create, register, and manage multiple AI agents (OpenAI, Bedrock, Ollama, Remote)
- **Orchestration**: Route conversations and tasks across multiple specialized agents
- **Memory System**: Maintain conversation context and history 
- **Tool System**: Extend agent capabilities through a pluggable tool architecture
- **CloudOps Integration**: Built-in support for cloud service automation and management

## Quick Links

- [Installation Guide](installation.md) - Get started with Moya
- [Core Concepts](core-concepts.md) - Learn about Moya's architecture and components  
- [Guides](guides.md) - Tutorials and how-to guides
- [API Reference](reference.md) - Detailed API documentation
- [CloudOps](cloudops.md) - Cloud operations integration guide

## Quick Start

```bash
# Install Moya
pip install moya-framework

# Set up environment
export OPENAI_API_KEY="your-api-key"
```

```python
from moya.agents import OpenAIAgent
from moya.tools import ToolRegistry

# Initialize agent
agent = OpenAIAgent(
    agent_name="my_assistant",
    description="Basic Moya agent"
)

# Send a message
response = agent.handle_message("Hello!")
print(response)
```

## Prerequisites

- Python 3.10+
- OpenAI API key (for OpenAI agents)
- AWS credentials (for Bedrock agents)
- Ollama installation (for local models)

See the [Installation Guide](installation.md) for detailed setup instructions.