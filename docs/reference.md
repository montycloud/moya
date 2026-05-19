# API Reference

This section provides a detailed reference for all public modules, classes, and methods in Moya.

## Agents

### Agent (Base Class)

```python
class Agent(abc.ABC):
    """
    Abstract base class for all Moya agents.
    """

    def __init__(self, config: AgentConfig):
        """
        Initialize the agent with its configuration.

        :param config: Configuration for the agent including name, type, description, etc.
        """

    @abc.abstractmethod
    def handle_message(self, message: str, **kwargs) -> str:
        """
        Process a message and return a response.

        :param message: The message to process.
        :param kwargs: Additional context or parameters the agent might need.
        :return: The agent's response as a string.
        """
    
    @abc.abstractmethod
    def handle_message_stream(self, message: str, **kwargs):
        """
        Process a message and return a response in streaming fashion.

        :param message: The message to process.
        :param kwargs: Additional context or parameters the agent might need.
        :yield: Chunks of the agent's response as strings.
        """
    
    def call_tool(self, tool_name: str, method_name: str, *args, **kwargs) -> Any:
        """
        Call a method on a registered tool by name.

        :param tool_name: The unique name or identifier of the tool.
        :param method_name: The name of the method to call on the tool.
        :param args: Positional arguments to pass to the tool method.
        :param kwargs: Keyword arguments to pass to the tool method.
        :return: The result of the tool method call.
        """
    
    def discover_tools(self) -> List[str]:
        """
        Return a list of available tool names from the registry.

        :return: A list of tool names (strings).
        """
```

### AgentConfig

```python
@dataclass
class AgentConfig:
    """
    Configuration data for an agent.
    """
    agent_name: str
    agent_type: str
    description: str
    system_prompt: str = "You are a helpful AI assistant."
    llm_config: Optional[Dict[str, Any]] = None
    tool_registry: Optional[ToolRegistry] = None
    memory: Optional[Repository] = None
    is_tool_caller: bool = False
    is_streaming: bool = False
```

### OpenAIAgent

```python
class OpenAIAgent(Agent):
    """
    A simple OpenAI-based agent that uses the ChatCompletion API.
    """

    def __init__(self, config: OpenAIAgentConfig):
        """
        Initialize the OpenAIAgent.

        :param config: Configuration for the agent including API key, model name, etc.
        """

    def handle_message(self, message: str, **kwargs) -> str:
        """
        Process a message and return a response using OpenAI's API.

        :param message: The message to process.
        :param kwargs: Additional context or parameters.
        :return: The agent's response as a string.
        """

    def handle_message_stream(self, message: str, **kwargs):
        """
        Process a message and return a streaming response using OpenAI's API.

        :param message: The message to process.
        :param kwargs: Additional context or parameters.
        :yield: Chunks of the agent's response as strings.
        """
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Generate tool definitions for OpenAI ChatCompletion.

        :return: A list of tool definitions in OpenAI format.
        """
```

### OpenAIAgentConfig

```python
@dataclass
class OpenAIAgentConfig(AgentConfig):
    """
    Configuration data for an OpenAIAgent.
    """
    model_name: str = "gpt-4o"
    api_key: str = None
    tool_choice: Optional[str] = None
```

## Tools

### Tool

```python
@dataclass
class Tool:
    """
    A generic interface for a "tool" that an agent can discover and call.
    """
    name: str
    description: Optional[str] = None
    function: Optional[Callable] = None
    parameters: Optional[Dict[str, Dict[str, Any]]] = None
    required: Optional[List[str]] = None

    def get_openai_definition(self) -> Dict[str, Any]:
        """
        Returns the tool definition in a format compatible with OpenAI.

        :return: Tool definition formatted for OpenAI.
        """
    
    def get_bedrock_definition(self) -> Dict[str, Any]:
        """
        Returns the tool definition in a format compatible with AWS Bedrock.

        :return: Tool definition formatted for AWS Bedrock.
        """
    
    def get_ollama_definition(self) -> Dict[str, Any]:
        """
        Returns the tool definition in a format compatible with Ollama.

        :return: Tool definition formatted for Ollama.
        """
```

### ToolRegistry

```python
class ToolRegistry:
    """
    Registry for managing tools that can be used by agents.
    """

    def __init__(self):
        """
        Initialize an empty tool registry.
        """
    
    def register_tool(self, tool: Tool) -> None:
        """
        Register a tool with the registry.

        :param tool: The Tool instance to register.
        """

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """
        Retrieve a tool by name.

        :param tool_name: The name of the tool to retrieve.
        :return: The Tool instance if found, else None.
        """

    def list_tools(self) -> List[str]:
        """
        List all registered tool names.

        :return: A list of tool names.
        """

    def get_tools(self) -> List[Tool]:
        """
        Get all registered tools.

        :return: A list of Tool instances.
        """
```

## Orchestrators

### Orchestrator (Base Class)

```python
class Orchestrator(abc.ABC):
    """
    Abstract base class for orchestrating conversations between users and agents.
    """

    def __init__(self, agent_registry: AgentRegistry, config: Optional[Any] = None, **kwargs):
        """
        Initialize the orchestrator.

        :param agent_registry: The AgentRegistry to retrieve agents from.
        :param config: Optional configuration for the orchestrator.
        :param kwargs: Additional orchestrator-specific parameters.
        """

    @abc.abstractmethod
    def orchestrate(self, thread_id: str, user_message: str, stream_callback=None, **kwargs) -> str:
        """
        Orchestrate conversation flow given a user message.

        :param thread_id: The identifier of the conversation thread.
        :param user_message: The message from the user.
        :param stream_callback: Optional callback function for streaming responses.
        :param kwargs: Additional context that may be relevant.
        :return: A string response.
        """
```

### SimpleOrchestrator

```python
class SimpleOrchestrator(Orchestrator):
    """
    A basic orchestrator that routes messages to a single agent.
    """

    def __init__(self, agent_registry: AgentRegistry, default_agent_name: Optional[str] = None, config: Optional[dict] = None):
        """
        Initialize the SimpleOrchestrator.

        :param agent_registry: The AgentRegistry to retrieve agents from.
        :param default_agent_name: The default agent to fall back on if no specialized match is found.
        :param config: Optional dictionary for orchestrator configuration.
        """

    def orchestrate(self, thread_id: str, user_message: str, stream_callback=None, **kwargs) -> str:
        """
        Orchestrate a conversation by routing the message to an appropriate agent.

        :param thread_id: The conversation thread ID.
        :param user_message: The message from the user.
        :param stream_callback: Optional callback function for streaming responses.
        :param kwargs: Additional context (e.g., 'agent_name' to override which agent to call).
        :return: The response from the chosen agent.
        """
```

## Registry

### AgentRegistry

```python
class AgentRegistry:
    """
    Registry for managing and discovering agents.
    """

    def __init__(self, repository: Optional[AgentRepository] = None):
        """
        Initialize the AgentRegistry.

        :param repository: An AgentRepository instance for storage. If not provided,
                          defaults to an InMemoryAgentRepository.
        """

    def register_agent(self, agent: Agent) -> None:
        """
        Register an Agent in this registry.
        
        :param agent: The Agent instance to register.
        """

    def remove_agent(self, agent_name: str) -> None:
        """
        Remove an Agent from the registry by its name.

        :param agent_name: The unique identifier (agent_name) of the Agent to remove.
        """

    def get_agent(self, agent_name: str) -> Optional[Agent]:
        """
        Retrieve an Agent by its agent_name.

        :param agent_name: The name of the Agent to retrieve.
        :return: The Agent instance if found, else None.
        """

    def list_agents(self) -> List[AgentInfo]:
        """
        List the information of all currently registered Agents.

        :return: A list of AgentInfo.
        """
```

## Memory

### Repository (Base Class)

```python
class Repository(abc.ABC):
    """
    Abstract interface for storing and retrieving conversation threads.
    """

    @abc.abstractmethod
    def create_thread(self, thread: Thread) -> None:
        """
        Store a new thread in the repository.

        :param thread: The Thread instance to store.
        """

    @abc.abstractmethod
    def get_thread(self, thread_id: str) -> Optional[Thread]:
        """
        Retrieve a thread by its ID.

        :param thread_id: The unique ID of the thread to fetch.
        :return: The Thread object if found, else None.
        """

    @abc.abstractmethod
    def append_message(self, thread_id: str, message: Message) -> None:
        """
        Add a new message to an existing thread.

        :param thread_id: The ID of the thread to which we add a message.
        :param message: The message to append.
        """

    @abc.abstractmethod
    def list_threads(self) -> List[str]:
        """
        List the IDs of all threads currently stored.

        :return: A list of thread_id strings.
        """

    @abc.abstractmethod
    def delete_thread(self, thread_id: str) -> None:
        """
        Remove a thread (and its messages) from the repository.

        :param thread_id: The ID of the thread to remove.
        """
```

### InMemoryRepository

```python
class InMemoryRepository(Repository):
    """
    In-memory implementation of the Repository interface.
    """

    def __init__(self):
        """
        Initialize an empty in-memory repository.
        """
```

### FileSystemRepository

```python
class FileSystemRepository(Repository):
    """
    File-based implementation of the Repository interface.
    """

    def __init__(self, base_path: str):
        """
        Initialize the repository with a base directory path.

        :param base_path: The directory path where thread files will be stored.
        """
```

## Conversation

### Thread

```python
class Thread:
    """
    Represents a conversation thread containing messages.
    """

    def __init__(self, thread_id: str, metadata: Optional[Dict] = None):
        """
        Initialize a new thread.

        :param thread_id: Unique identifier for this thread.
        :param metadata: Optional metadata associated with the thread.
        """

    def add_message(self, message: Message) -> None:
        """
        Add a message to this thread.

        :param message: The Message instance to add.
        """
```

### Message

```python
class Message:
    """
    Represents a message within a conversation thread.
    """

    def __init__(self, thread_id: str, sender: str, content: Any, message_id: Optional[str] = None, metadata: Optional[Dict] = None):
        """
        Initialize a new message.

        :param thread_id: The ID of the thread this message belongs to.
        :param sender: The identifier of the sender (e.g., "user", "agent").
        :param content: The content of the message.
        :param message_id: Optional unique identifier for this message.
        :param metadata: Optional metadata associated with the message.
        """
```