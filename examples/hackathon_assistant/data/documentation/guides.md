# Guides and Tutorials

## Basic Usage

### Creating Your First Agent
```python
from moya.agents import OpenAIAgent
from moya.tools import ToolRegistry
from moya.memory import InMemoryRepository

# Set up memory and tools
memory_repo = InMemoryRepository()
tool_registry = ToolRegistry()

# Create agent
agent = OpenAIAgent(
    agent_name="my_assistant",
    description="A helpful assistant",
    tool_registry=tool_registry
)

# Use the agent
response = agent.handle_message("Hello!")
```

### Adding Memory Management
```python
from moya.tools import MemoryTool

# Set up memory components
memory_tool = MemoryTool(memory_repository=memory_repo)
tool_registry.register_tool(memory_tool)

# Store messages
agent.call_tool(
    tool_name="MemoryTool",
    method_name="store_message",
    thread_id="chat_1",
    sender="user",
    content="Hello!"
)

# Get conversation history
messages = agent.get_last_n_messages("chat_1", n=5)
```

## Advanced Topics

### Building a Multi-Agent System

1. Create specialized agents:
```python
tech_agent = OpenAIAgent(
    agent_name="tech_support",
    description="Technical support specialist",
    system_prompt="You are a technical support specialist..."
)

docs_agent = OpenAIAgent(
    agent_name="documentation",
    description="Documentation expert",
    system_prompt="You are a documentation specialist..."
)
```

2. Set up orchestration:
```python
from moya.orchestrators import MultiAgentOrchestrator
from moya.registry import AgentRegistry
from moya.classifiers import LLMClassifier

# Register agents
registry = AgentRegistry()
registry.register_agent(tech_agent)
registry.register_agent(docs_agent)

# Create classifier
classifier = LLMClassifier(
    llm_agent=OpenAIAgent(
        agent_name="classifier",
        description="Message router"
    )
)

# Set up orchestrator
orchestrator = MultiAgentOrchestrator(
    agent_registry=registry,
    classifier=classifier
)
```

3. Use the system:
```python
response = orchestrator.orchestrate(
    thread_id="chat_1",
    user_message="How do I create a custom agent?"
)
```

### Implementing Custom Tools

1. Define your tool:
```python
from moya.tools import BaseTool

class DataAnalysisTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="DataAnalysisTool",
            description="Performs data analysis tasks"
        )
    
    def analyze_data(self, data: list) -> dict:
        # Implement analysis logic
        return {"result": "analysis_output"}
```

2. Register and use:
```python
tool = DataAnalysisTool()
tool_registry.register_tool(tool)

result = agent.call_tool(
    tool_name="DataAnalysisTool",
    method_name="analyze_data",
    data=[1, 2, 3]
)
```

### Working with Remote Agents

1. Set up server:
```python
from fastapi import FastAPI, HTTPException
from moya.agents import RemoteAgent

app = FastAPI()
agent = RemoteAgent(...)

@app.post("/chat")
async def chat(message: dict):
    try:
        response = agent.handle_message(message["content"])
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, str(e))
```

2. Client usage:
```python
from moya.agents import RemoteAgent

agent = RemoteAgent(
    agent_name="remote_assistant",
    api_url="http://localhost:8000/chat",
    api_key="your-key"
)

response = agent.handle_message("Hello!")
```

## CloudOps Integration

### AWS Resource Management
```python
from moya.tools import CloudOpsTool
from moya.agents import BedrockAgent

# Set up cloud tool
cloud_tool = CloudOpsTool(aws_profile="prod")
tool_registry.register_tool(cloud_tool)

# Create cloud-aware agent
agent = BedrockAgent(
    agent_name="cloud_ops",
    description="AWS resource manager",
    tool_registry=tool_registry
)

# Manage resources
response = agent.handle_message("Check EC2 instance health in us-east-1")
```

### Multi-Cloud Orchestration
```python
# Create cloud-specific agents
aws_agent = BedrockAgent(name="aws_ops")
azure_agent = OpenAIAgent(name="azure_ops")

# Set up orchestration
registry = AgentRegistry()
registry.register_agent(aws_agent)
registry.register_agent(azure_agent)

orchestrator = MultiAgentOrchestrator(
    agent_registry=registry,
    classifier=classifier
)

# Handle multi-cloud operations
response = orchestrator.orchestrate(
    thread_id="cloud_ops",
    user_message="Compare resource usage across AWS and Azure"
)
```