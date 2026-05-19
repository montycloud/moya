"""
Base Agent interface for Moya.

This module defines the abstract Agent class, which describes
the behavior and interface that all agents in Moya must follow.

Agents can:
- Provide a textual 'description' of their capabilities,
- Expose an 'agent_type' to facilitate registry logic,
- Initialize themselves with 'setup()',
- Handle incoming messages via 'handle_message()',
- Dynamically call external tools via 'call_tool()',
- Discover available tools via 'discover_tools()',
- Optionally retrieve conversation memory (summary, last n messages)
  through a MemoryTool if registered in the Tool registry.
"""


import abc
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from moya.tools.tool import Tool
from moya.tools.tool_registry import ToolRegistry
from moya.memory.repository import Repository
from moya.conversation.thread import Thread
from moya.conversation.message import Message

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
    # List of Skill objects to attach to this agent at creation time.
    # Each skill may contribute a prompt snippet and/or a set of tools.
    skills: List[Any] = field(default_factory=list)
    # Optional SkillRegistry used to resolve skill dependencies at attach time.
    skill_registry: Optional[Any] = None

    def __post_init__(self):
        if not self.agent_name:
            raise ValueError("Agent name must be provided.")
        if not self.description:
            raise ValueError("Agent description must be provided.")
        default_llm_config = {
                'model_name': "default",
                'temperature': 0.7,
                'max_tokens':  2000,
                'top_p': 1.0,
                'frequency_penalty': 0.0,
                'presence_penalty': 0.0,
                'stop_sequences':  [],
        }
        self.llm_config = {**default_llm_config, **(self.llm_config or {})}



class Agent(abc.ABC):
    """
    Abstract base class for all Moya agents.

    Agents are responsible for:
    - A textual description of their capabilities (description property),
    - A type descriptor (agent_type) that helps the registry handle them,
    - Any necessary setup or initialization (setup()),
    - Receiving messages or prompts (handle_message()),
    - Generating responses (usually via an LLM or other logic),
    - Optionally discovering & calling tools (call_tool, discover_tools).

    Concrete implementations (e.g., OpenAIAgent, AnthropicAgent, RemoteAgent)
    should override the abstract methods with vendor or application-specific logic.
    """

    def __init__(
        self,
        config: AgentConfig
    ):
        """
        Initialize the agent with:
          - a name (agent_name),
          - an agent type (agent_type) for registry usage,
          - a brief description of its capabilities/role,
          - an optional config dictionary (API keys, model parameters, etc.),
          - an optional reference to a tool registry.

        :param agent_name: A unique name or identifier for the agent.
        :param agent_type: A short string representing the type of the agent
                           (e.g., "BaseAgent", "RemoteAgent", "OpenAIAgent").
        :param description: A brief explanation of the agent's capabilities and role.
        :param config: Optional configuration dict (e.g., API keys, parameters).
        :param agent_config: Optional AgentConfig object with model parameters.
        :param tool_registry: A reference to a centralized ToolRegistry (if any).
        """
        self.agent_name = config.agent_name
        self.agent_type = config.agent_type
        self.description = config.description
        self.llm_config = config.llm_config or {}
        self.tool_registry = config.tool_registry
        self.system_prompt = config.system_prompt or "You are a helpful AI assistant."
        self.memory = config.memory
        self.is_tool_caller = config.is_tool_caller
        self.is_streaming = config.is_streaming
        self.skills: List[Any] = []

        # Attach skills with optional dependency resolution.
        if config.skills:
            from moya.skills.attachment import attach_skills
            attach_skills(
                self,
                list(config.skills),
                registry=getattr(config, "skill_registry", None),
            )
        

    @abc.abstractmethod
    def handle_message(self, message: str, **kwargs) -> str:
        """
        Receive a message (prompt) and generate a response.

        :param message: The user or system prompt to be handled.
        :param kwargs: Additional context or parameters the agent might need,
                       such as conversation ID, user metadata, etc.
        :return: The agent's response as a string.
        """
        raise NotImplementedError("Subclasses must implement handle_message().")

    @abc.abstractmethod
    def handle_message_stream(self, message: str, **kwargs):
        """
        Receive a message (prompt) and generate a response in a streaming fashion.

        :param message: The user or system prompt to be handled.
        :param kwargs: Additional context or parameters the agent might need,
                       such as conversation ID, user metadata, etc.
        :yield: Chunks of the agent's response as strings.
        """
        raise NotImplementedError("Subclasses must implement handle_message_stream().")

    def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Call a registered tool by name, passing keyword arguments to its function.

        :param tool_name: The name of the tool to call.
        :param kwargs:    Arguments forwarded to the tool's underlying function.
        :return:          The return value of the tool function.
        """
        if not self.tool_registry:
            raise RuntimeError(
                f"Agent '{self.agent_name}' has no tool registry. "
                "Pass a ToolRegistry via AgentConfig.tool_registry."
            )
        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            available = self.tool_registry.list_tools()
            raise ValueError(
                f"No tool named '{tool_name}' in the registry. "
                f"Available tools: {available}"
            )
        try:
            return tool.function(**kwargs)
        except Exception as e:
            raise RuntimeError(f"Error executing tool '{tool_name}': {e}") from e

    def discover_tools(self) -> List[str]:
        """
        Return a list of available tool names from the registry.

        :return: A list of tool names (strings).
        """
        if not self.tool_registry:
            return []
        return self.tool_registry.list_tools()

    def get_conversation_summary(self, thread_id: str) -> str:
        """
        Retrieve a summary of the conversation so far using the MemoryTool, if available.

        :param thread_id: The identifier of the conversation thread.
        :return: A textual summary of the conversation so far. If no MemoryTool
                 or no registry is found, returns an empty string or raises an error.
        """        
        if not self.memory:
            return ""
        return self.memory.get_conversation_summary(thread_id)

    def get_last_n_messages(self, thread_id: str, n: int = 5) -> List[Any]:
        """
        Retrieve the last n messages of the conversation using the MemoryTool, if available.

        :param thread_id: The identifier of the conversation thread.
        :param n: The number of recent messages to retrieve.
        :return: A list of message objects or dictionaries.
        """
        if not self.memory:
            return []
        thread = self.memory.get_thread(thread_id)
        if not thread:
            return []
        return thread.get_last_n_messages(n)

    def _remember(self, thread_id: str, user_msg: str, assistant_response: str) -> None:
        """
        Persist the user message and the agent's response to memory.

        Creates the thread automatically on first call. No-op when no memory
        repository is configured.

        :param thread_id:           Conversation thread identifier.
        :param user_msg:            The user's input message.
        :param assistant_response:  The agent's response to store.
        """
        if not self.memory:
            return
        if self.memory.get_thread(thread_id) is None:
            self.memory.create_thread(Thread(thread_id=thread_id))
        self.memory.append_message(
            thread_id, Message(thread_id=thread_id, sender="user", content=user_msg)
        )
        self.memory.append_message(
            thread_id, Message(thread_id=thread_id, sender=self.agent_name, content=assistant_response)
        )