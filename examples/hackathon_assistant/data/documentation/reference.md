# API Reference

## Core Classes

### Agent Classes

#### BaseAgent
```python
class BaseAgent(abc.ABC):
    def __init__(
        self,
        agent_name: str,
        description: str,
        tool_registry: Optional[ToolRegistry] = None
    ):
        """
        Initialize a base agent.
        
        Args:
            agent_name: Unique identifier for the agent
            description: Human-readable description of agent's capabilities
            tool_registry: Optional registry for tool access
        """
        
    @abc.abstractmethod
    def handle_message(
        self, 
        message: str,
        **kwargs
    ) -> str:
        """Process a message and return response."""
        
    def call_tool(
        self,
        tool_name: str,
        method_name: str,
        **kwargs
    ) -> Any:
        """Call a registered tool method."""
```

#### OpenAIAgent
```python
class OpenAIAgent(BaseAgent):
    def __init__(
        self,
        agent_name: str,
        description: str,
        agent_config: Optional[OpenAIAgentConfig] = None,
        tool_registry: Optional[ToolRegistry] = None
    ):
        """
        Initialize OpenAI-based agent.
        
        Args:
            agent_name: Unique identifier
            description: Agent capabilities
            agent_config: OpenAI-specific configuration
            tool_registry: Optional tool registry
        """
```

#### BedrockAgent
```python
class BedrockAgent(BaseAgent):
    def __init__(
        self,
        agent_name: str,
        description: str,
        agent_config: Optional[BedrockAgentConfig] = None,
        tool_registry: Optional[ToolRegistry] = None
    ):
        """
        Initialize AWS Bedrock-based agent.
        
        Args:
            agent_name: Unique identifier
            description: Agent capabilities
            agent_config: Bedrock-specific configuration
            tool_registry: Optional tool registry
        """
```

### Tool Classes

#### BaseTool
```python
class BaseTool(abc.ABC):
    def __init__(
        self,
        name: str,
        description: str
    ):
        """
        Initialize a base tool.
        
        Args:
            name: Tool identifier
            description: Tool capabilities
        """
```

#### MemoryTool
```python
class MemoryTool(BaseTool):
    def __init__(
        self,
        memory_repository: BaseRepository
    ):
        """
        Initialize memory management tool.
        
        Args:
            memory_repository: Storage backend
        """
        
    def store_message(
        self,
        thread_id: str,
        sender: str,
        content: str
    ) -> None:
        """Store a message in memory."""
        
    def get_last_n_messages(
        self,
        thread_id: str,
        n: int = 5
    ) -> List[Message]:
        """Retrieve recent messages."""
```

### Orchestrator Classes

#### BaseOrchestrator
```python
class BaseOrchestrator(abc.ABC):
    def __init__(
        self,
        agent_registry: AgentRegistry
    ):
        """
        Initialize base orchestrator.
        
        Args:
            agent_registry: Registry of available agents
        """
        
    @abc.abstractmethod
    def orchestrate(
        self,
        thread_id: str,
        user_message: str,
        **kwargs
    ) -> str:
        """Route and process message."""
```

#### MultiAgentOrchestrator
```python
class MultiAgentOrchestrator(BaseOrchestrator):
    def __init__(
        self,
        agent_registry: AgentRegistry,
        classifier: Optional[BaseClassifier] = None
    ):
        """
        Initialize multi-agent orchestrator.
        
        Args:
            agent_registry: Available agents
            classifier: Optional message classifier
        """
```

### Registry Classes

#### AgentRegistry
```python
class AgentRegistry:
    def register_agent(
        self,
        agent: BaseAgent
    ) -> None:
        """Register a new agent."""
        
    def get_agent(
        self,
        agent_name: str
    ) -> BaseAgent:
        """Retrieve an agent by name."""
```

#### ToolRegistry
```python
class ToolRegistry:
    def register_tool(
        self,
        tool: BaseTool
    ) -> None:
        """Register a new tool."""
        
    def get_tool(
        self,
        tool_name: str
    ) -> BaseTool:
        """Retrieve a tool by name."""
```

## Data Classes

### Message
```python
@dataclass
class Message:
    thread_id: str
    sender: str
    content: str
    timestamp: datetime
```

### AgentConfig
```python
@dataclass
class AgentConfig:
    system_prompt: str
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 2000
```

## Exceptions

### AgentError
Base exception for agent-related errors.

### ToolError
Base exception for tool-related errors.

### OrchestratorError
Base exception for orchestration errors.

## Constants

### ModelNames
```python
class ModelNames:
    GPT4 = "gpt-4o"
    GPT35_TURBO = "gpt-3.5-turbo"
    CLAUDE = "anthropic.claude-v2"
    LLAMA2 = "llama2"
```

### AgentTypes
```python
class AgentTypes:
    OPENAI = "openai"
    BEDROCK = "bedrock"
    OLLAMA = "ollama"
    REMOTE = "remote"
```