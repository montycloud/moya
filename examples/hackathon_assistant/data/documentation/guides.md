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

class CustomIntegrationTool(BaseTool):
    def __init__(self, config: dict):
        super().__init__(
            name="CustomIntegrationTool",
            description="Integrates with external services"
        )
        self.config = config
    
    def execute_operation(self, operation: str, **kwargs) -> dict:
        # Implement your custom integration logic
        return {"status": "success", "result": "operation_output"}
```

2. Register and use:
```python
tool = CustomIntegrationTool(config={
    "endpoint": "your_service_endpoint",
    "auth_token": "your_auth_token"
})
tool_registry.register_tool(tool)

result = agent.call_tool(
    tool_name="CustomIntegrationTool",
    method_name="execute_operation",
    operation="custom_action",
    **kwargs
)
```

### Integration Patterns

#### Service Integration Example
```python
from moya.agents import OpenAIAgent
from moya.tools import BaseIntegrationTool

# Create a service-specific tool
class ServiceTool(BaseIntegrationTool):
    def __init__(self, service_config: dict):
        super().__init__(
            name="ServiceTool",
            description="Integrates with external service"
        )
        self.config = service_config
        
    def connect(self):
        # Implement service connection
        pass
        
    def execute(self, action: str, params: dict):
        # Implement service interaction
        pass

# Use with any agent
agent = OpenAIAgent(
    agent_name="service_agent",
    description="Service integration agent",
    tool_registry=tool_registry
)
```

#### Distributed System Pattern
```python
from moya.orchestrators import MultiAgentOrchestrator
from moya.registry import AgentRegistry

# Set up distributed components
registry = AgentRegistry()
for service in services:
    agent = OpenAIAgent(
        agent_name=f"{service}_agent",
        description=f"Handles {service} operations"
    )
    registry.register_agent(agent)

# Orchestrate distributed operations
orchestrator = MultiAgentOrchestrator(
    agent_registry=registry,
    classifier=classifier
)
```