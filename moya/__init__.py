"""
MOYA — Multi-agent framework for building LLM-powered applications.

Quick start::

    from moya import create_agent, Pipeline, AgentStep, Tool, ToolRegistry

    agent = create_agent("openai", name="assistant", description="Helpful assistant")

    pipeline = Pipeline([AgentStep(agent)])
    result = pipeline.run(thread_id="t1", message="Hello!")

Provider values for create_agent(): "openai", "ollama", "remote", "bedrock", "azure", "crewai"
"""

import os
from typing import Any, List, Optional

# Core building blocks — always available
from moya.tools.tool import Tool
from moya.tools.tool_registry import ToolRegistry
from moya.tools.global_tool_registry import (
    GlobalToolRegistry,
    ScopedToolRegistry,
    get_global_tool_registry,
    set_global_tool_registry,
)
from moya.registry.agent_registry import AgentRegistry, AgentRegistryConfig
from moya.registry.json_agent_repository import JsonAgentRepository
from moya.flows.pipeline import FlowContext, Pipeline
from moya.observability import (
    EventBus,
    get_event_bus,
    set_event_bus,
    LoggingListener,
    CallbackListener,
    FilteredListener,
)
from moya.flows.steps import AgentStep, BranchStep, FunctionStep, LoopStep, ParallelStep
from moya.skills.skill import Skill
from moya.skills.registry import SkillRegistry, SkillVersionConflictError, SkillNotFoundError
from moya.skills.attachment import attach_skills
from moya.classifiers.skill_classifier import SkillClassifier
from moya.memory.in_memory_repository import InMemoryRepository
from moya.memory.file_system_repo import FileSystemRepository
from moya.mcp.client import MCPClient
from moya.mcp.server import MCPServer
from moya.delegation.manager import DelegationManager
from moya.orchestrators.simple_orchestrator import SimpleOrchestrator
from moya.orchestrators.multi_agent_orchestrator import MultiAgentOrchestrator

# Default agent — no optional deps
from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
from moya.agents.ollama_agent import OllamaAgent, OllamaAgentConfig
from moya.agents.remote_agent import RemoteAgent, RemoteAgentConfig


def create_agent(
    provider: str,
    *,
    name: str,
    description: str,
    system_prompt: str = "You are a helpful AI assistant.",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    tool_registry: Optional[ToolRegistry] = None,
    memory=None,
    is_tool_caller: Optional[bool] = None,
    skills: Optional[List[Any]] = None,
    tags: Optional[List[str]] = None,
    **kwargs,
):
    """
    Create a MOYA agent for the given provider with minimal boilerplate.

    Args:
        provider:       LLM backend — "openai", "ollama", "remote",
                        "bedrock", "azure", or "crewai".
        name:           Unique agent name (used as the agent identifier).
        description:    Short description of what this agent does.
        system_prompt:  System prompt / persona for the agent.
        model:          Model name or ID (provider-specific default used if omitted).
        api_key:        API key. Falls back to the standard environment variable
                        for the provider (e.g. OPENAI_API_KEY) when omitted.
        tool_registry:  ToolRegistry to attach. ``is_tool_caller`` is auto-set
                        to True when a registry is provided unless explicitly set.
        memory:         Repository instance for conversation memory.
        is_tool_caller: Override the tool-caller flag. Defaults to True when
                        ``tool_registry`` is supplied, False otherwise.
        skills:         List of Skill objects to attach.
        tags:           Free-form string tags for agent discovery.
        **kwargs:       Provider-specific options (e.g. ``base_url`` for Ollama,
                        ``region`` for Bedrock, ``api_base`` / ``api_version``
                        for Azure).

    Returns:
        A configured agent instance, ready to call handle_message().

    Examples::

        # OpenAI
        agent = create_agent("openai", name="writer", description="Creative writer")

        # Ollama (local)
        agent = create_agent("ollama", name="local", description="Local model",
                             model="llama3.1", base_url="http://localhost:11434")

        # With tools
        registry = ToolRegistry()
        registry.register_tool(Tool(name="search", function=my_search))
        agent = create_agent("openai", name="researcher", description="Research agent",
                             tool_registry=registry)
    """
    provider = provider.lower()

    # Auto-set is_tool_caller when a registry is supplied
    if is_tool_caller is None:
        is_tool_caller = tool_registry is not None

    _common = dict(
        agent_name=name,
        agent_type=provider,
        description=description,
        system_prompt=system_prompt,
        tool_registry=tool_registry,
        memory=memory,
        is_tool_caller=is_tool_caller,
        skills=skills or [],
    )

    if provider == "openai":
        from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
        config = OpenAIAgentConfig(
            **_common,
            model_name=model or "gpt-4o",
            api_key=api_key or os.environ.get("OPENAI_API_KEY", ""),
            **{k: v for k, v in kwargs.items()
               if k in ("tool_choice", "max_iterations")},
        )
        agent = OpenAIAgent(config)

    elif provider == "ollama":
        from moya.agents.ollama_agent import OllamaAgent, OllamaAgentConfig
        config = OllamaAgentConfig(
            **_common,
            model_name=model or "llama3.1",
            base_url=kwargs.pop("base_url",
                                os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")),
            **{k: v for k, v in kwargs.items() if k in ("max_iterations",)},
        )
        agent = OllamaAgent(config)

    elif provider == "remote":
        from moya.agents.remote_agent import RemoteAgent, RemoteAgentConfig
        if "base_url" not in kwargs:
            raise ValueError("create_agent('remote', ...) requires base_url=<url>")
        config = RemoteAgentConfig(
            **_common,
            base_url=kwargs.pop("base_url"),
            auth_token=kwargs.pop("auth_token", None),
            verify_ssl=kwargs.pop("verify_ssl", True),
        )
        agent = RemoteAgent(config)

    elif provider == "bedrock":
        from moya.agents.bedrock_agent import BedrockAgent, BedrockAgentConfig
        config = BedrockAgentConfig(
            **_common,
            model_id=model or "anthropic.claude-3-haiku-20240307-v1:0",
            region=kwargs.pop("region", os.environ.get("AWS_DEFAULT_REGION", "us-east-1")),
            **{k: v for k, v in kwargs.items() if k in ("max_iterations",)},
        )
        agent = BedrockAgent(config)

    elif provider == "azure":
        from moya.agents.azure_openai_agent import AzureOpenAIAgent, AzureOpenAIAgentConfig
        config = AzureOpenAIAgentConfig(
            **_common,
            model_name=model or "gpt-4o",
            api_key=api_key or os.environ.get("AZURE_OPENAI_API_KEY", ""),
            api_base=kwargs.pop("api_base", os.environ.get("AZURE_OPENAI_ENDPOINT", "")),
            api_version=kwargs.pop("api_version", os.environ.get("AZURE_OPENAI_API_VERSION", "")),
        )
        agent = AzureOpenAIAgent(config)

    elif provider == "crewai":
        from moya.agents.crewai_agent import CrewAIAgent, CrewAIAgentConfig
        config = CrewAIAgentConfig(
            **_common,
            model_name=model or "gpt-4o",
            api_key=api_key or os.environ.get("OPENAI_API_KEY"),
        )
        agent = CrewAIAgent(config)

    else:
        supported = ("openai", "ollama", "remote", "bedrock", "azure", "crewai")
        raise ValueError(
            f"Unknown provider '{provider}'. Supported providers: {', '.join(supported)}"
        )

    if tags:
        agent.tags = tags

    return agent


__all__ = [
    # Factory
    "create_agent",
    # Tools
    "Tool",
    "ToolRegistry",
    "GlobalToolRegistry",
    "ScopedToolRegistry",
    "get_global_tool_registry",
    "set_global_tool_registry",
    # Registry
    "AgentRegistry",
    "AgentRegistryConfig",
    "JsonAgentRepository",
    # Flows
    "FlowContext",
    "Pipeline",
    "AgentStep",
    "FunctionStep",
    "ParallelStep",
    "BranchStep",
    "LoopStep",
    # Skills
    "Skill",
    "SkillRegistry",
    "SkillVersionConflictError",
    "SkillNotFoundError",
    "attach_skills",
    "SkillClassifier",
    # Memory
    "InMemoryRepository",
    "FileSystemRepository",
    # MCP
    "MCPClient",
    "MCPServer",
    # Delegation
    "DelegationManager",
    # Orchestrators
    "SimpleOrchestrator",
    "MultiAgentOrchestrator",
    # Agents
    "OpenAIAgent",
    "OpenAIAgentConfig",
    "OllamaAgent",
    "OllamaAgentConfig",
    "RemoteAgent",
    "RemoteAgentConfig",
    # Observability
    "EventBus",
    "get_event_bus",
    "set_event_bus",
    "LoggingListener",
    "CallbackListener",
    "FilteredListener",
]
