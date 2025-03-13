# Moya Quickstart Guide

## Basic Usage

### 1. Single Agent Setup
```python
from moya.agents import OpenAIAgent
from moya.tools import ToolRegistry
from moya.memory import InMemoryRepository

# Set up agent with memory
tool_registry = ToolRegistry()
memory_repo = InMemoryRepository()
memory_tool = MemoryTool(memory_repo)
tool_registry.register_tool(memory_tool)

agent = OpenAIAgent(
    agent_name="assistant",
    description="General purpose assistant",
    tool_registry=tool_registry
)

# Use the agent
response = agent.handle_message("Tell me about Moya")
```

### 2. Multi-Agent Setup
```python
from moya.orchestrators import MultiAgentOrchestrator
from moya.registry import AgentRegistry

# Create specialized agents
tech_agent = OpenAIAgent(name="tech_support")
docs_agent = OpenAIAgent(name="documentation")

# Set up orchestration
registry = AgentRegistry()
registry.register_agent(tech_agent)
registry.register_agent(docs_agent)

orchestrator = MultiAgentOrchestrator(
    agent_registry=registry
)

# Use orchestrator
response = orchestrator.orchestrate(
    thread_id="chat_1",
    user_message="How do I create a custom agent?"
)
```

### 3. Adding Custom Tools
```python
from moya.tools import BaseTool

class MyTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="MyTool",
            description="Custom functionality"
        )
    
    def my_method(self, param: str) -> str:
        return f"Processed: {param}"

# Register and use tool
tool_registry.register_tool(MyTool())
```
