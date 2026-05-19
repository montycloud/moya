# Explanations

This section provides in-depth explanations of key concepts and components in the Moya framework.

## Agent Architecture

Moya's agents are modular and designed to interface with various AI services. Each agent has a specific role and can be customized to suit different use cases.

### Key Components:
- **Base Agent**: The foundation for all agents.
- **Specialized Agents**: Implementations for specific services like OpenAI, Azure, and AWS Bedrock.

## How Agents Work

Agents process user inputs, perform tasks, and return outputs. They can also collaborate with other agents to handle complex workflows.

### Example Workflow:
1. User sends a query.
2. Agent processes the query and generates a response.
3. Response is returned to the user.

## Agent Types

Moya supports multiple agent types, including:
- **OpenAI Agent**: Integrates with OpenAI's GPT models.
- **Azure OpenAI Agent**: Uses Azure's OpenAI service.
- **Bedrock Agent**: Connects to AWS Bedrock.
- **Ollama Agent**: Interfaces with Ollama's AI services.

## Memory Management

Memory in Moya is used to store and retrieve information during interactions. It supports conversation history, persistent storage, and more.

### Example:
```python
from moya.memory.conversation_memory import ConversationMemory

memory = ConversationMemory()
memory.add_message("user", "What is Moya?")
memory.add_message("agent", "Moya is an AI framework.")
print(memory.get_history())
```

## Multi-Agent Systems

Moya allows you to build systems with multiple agents that collaborate to solve tasks. Orchestrators manage the interactions between agents.

### Example:
```python
from moya.orchestrators.sequential_orchestrator import SequentialOrchestrator

orchestrator = SequentialOrchestrator()
orchestrator.add_agent("Agent1")
orchestrator.add_agent("Agent2")
result = orchestrator.execute_workflow({"tasks": ["task1", "task2"]})
print(result)
```

## Orchestrators

Orchestrators coordinate the actions of multiple agents. They can execute tasks sequentially or in parallel.

### Example:
```python
from moya.orchestrators.parallel_orchestrator import ParallelOrchestrator

orchestrator = ParallelOrchestrator()
orchestrator.add_agent("Agent1")
orchestrator.add_agent("Agent2")
result = orchestrator.execute_workflow({"tasks": ["task1", "task2"]})
print(result)
```

## Tool Registry and Tool Calling

Moya includes a tool registry that allows agents to call tools dynamically. This extends the capabilities of agents and enables integration with external services.

### Example:
```python
from moya.tools.api_client import APIClient

client = APIClient()
response = client.get("https://api.example.com/data")
print(response)
```