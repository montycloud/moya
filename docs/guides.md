# Guides

Moya provides detailed guides to help you understand and utilize its features effectively. Below are some of the key guides available:

## Creating Agents

Learn how to create and configure agents in Moya. Agents are the core components that perform tasks and interact with users.

### Example:
```python
from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig

# Create a configuration for the agent
config = OpenAIAgentConfig(
    api_key="your-api-key",
    model_name="gpt-4o",
    system_prompt="You are a helpful assistant."
)

# Create the agent
agent = OpenAIAgent(config=config)

# Generate a response to a user message
response = agent.handle_message("Hello, Moya!")
print(response)
```

## Managing Memory

Understand how to use Moya's memory module to store and retrieve conversation threads and messages.

### Example:
```python
from moya.memory.in_memory_repository import InMemoryRepository
from moya.conversation.thread import Thread
from moya.conversation.message import Message

# Create an in-memory repository
repository = InMemoryRepository()

# Create a new conversation thread
thread = Thread(thread_id="conversation_1")
repository.create_thread(thread)

# Add messages to the thread
message1 = Message(thread_id="conversation_1", sender="user", content="What is Moya?")
repository.append_message("conversation_1", message1)

message2 = Message(thread_id="conversation_1", sender="agent", content="Moya is an AI framework.")
repository.append_message("conversation_1", message2)

# Retrieve the thread with its messages
retrieved_thread = repository.get_thread("conversation_1")
for message in retrieved_thread.messages:
    print(f"{message.sender}: {message.content}")
```

## Building Multi-Agent Systems

Learn how to create systems with multiple agents that collaborate to solve complex tasks.

### Example:
```python
from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
from moya.registry.agent_registry import AgentRegistry
from moya.orchestrators.simple_orchestrator import SimpleOrchestrator

# Create the agent registry
registry = AgentRegistry()

# Create and register agents
config1 = OpenAIAgentConfig(
    agent_name="researcher",
    api_key="your-api-key",
    system_prompt="You are a research assistant who finds information."
)
researcher = OpenAIAgent(config=config1)
registry.register_agent(researcher)

config2 = OpenAIAgentConfig(
    agent_name="writer",
    api_key="your-api-key",
    system_prompt="You are a writer who creates concise summaries."
)
writer = OpenAIAgent(config=config2)
registry.register_agent(writer)

# Create an orchestrator with the agent registry
orchestrator = SimpleOrchestrator(
    agent_registry=registry,
    default_agent_name="researcher"
)

# Process a user request
response = orchestrator.orchestrate(
    thread_id="task_123",
    user_message="Research climate change impacts",
    agent_name="researcher"
)
print(response)
```

## Streaming Responses

Explore how to implement streaming responses for real-time interactions.

### Example:
```python
from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig

def handle_stream_chunk(chunk):
    print(chunk, end="", flush=True)

# Create a configuration for the agent
config = OpenAIAgentConfig(
    api_key="your-api-key",
    model_name="gpt-4o"
)

# Create the agent
agent = OpenAIAgent(config=config)

# Using the orchestrator for streaming
from moya.registry.agent_registry import AgentRegistry
from moya.orchestrators.simple_orchestrator import SimpleOrchestrator

registry = AgentRegistry()
registry.register_agent(agent)

orchestrator = SimpleOrchestrator(agent_registry=registry)
orchestrator.orchestrate(
    thread_id="stream_demo",
    user_message="Tell me a short story about AI.",
    stream_callback=handle_stream_chunk
)
```