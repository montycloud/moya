"""
SubAgentSpawner — dynamically create and register sub-agents from specs.

REQ-SUBAG-01: spawn agents from a spec or named template.
REQ-SUBAG-02: inherit parent's system prompt prefix, tool registry, and skills.
REQ-SUBAG-05: publish lifecycle events via event_bus.
REQ-SUBAG-08: auto-register spawned agents with AgentRegistry.

Usage::

    from moya.delegation.spawner import SubAgentSpawner, SubAgentSpec

    spawner = SubAgentSpawner(registry, event_bus=bus)

    spec = SubAgentSpec(
        agent_type="openai",
        agent_name="helper",
        description="Helps with research tasks",
        extra_kwargs={"api_key": "sk-...", "model_name": "gpt-4o-mini"},
    )

    child = spawner.spawn_from_spec(spec, parent_agent=parent)
    # child is registered in registry and inherits parent context
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from moya.agents.agent import Agent, AgentConfig


@dataclass
class SubAgentSpec:
    """
    Declarative description of a sub-agent to spawn.

    Fields
    ------
    agent_type:
        Registered builder key (e.g. ``"openai"``, ``"ollama"``).
    agent_name:
        Unique name for the new agent.
    description:
        Human-readable description of the agent's capabilities.
    system_prompt:
        Agent-specific system prompt (appended after the parent prefix
        when ``inherit_system_prompt_prefix=True``).
    llm_config:
        Extra LLM parameters (temperature, max_tokens, …).
    inherit_tools:
        Copy the parent's ``tool_registry`` reference to the child.
    inherit_skills:
        Copy the parent's ``skills`` list to the child.
    inherit_system_prompt_prefix:
        Prepend the parent's ``system_prompt`` to the child's prompt.
    extra_kwargs:
        Agent-type-specific keyword args forwarded to the config dataclass
        (e.g. ``api_key`` for OpenAI, ``base_url`` for Ollama).
    """

    agent_type: str
    agent_name: str
    description: str
    system_prompt: Optional[str] = None
    llm_config: Optional[Dict[str, Any]] = None
    inherit_tools: bool = True
    inherit_skills: bool = True
    inherit_system_prompt_prefix: bool = True
    extra_kwargs: Dict[str, Any] = field(default_factory=dict)


class SubAgentSpawner:
    """
    Creates Agent instances from :class:`SubAgentSpec` objects or named
    templates, with optional context inheritance from a parent agent.
    """

    def __init__(
        self,
        registry: Any,
        event_bus: Optional[Any] = None,
    ) -> None:
        self._registry = registry
        self._event_bus = event_bus
        self._templates: Dict[str, SubAgentSpec] = {}
        self._builders: Dict[str, Callable[[SubAgentSpec, AgentConfig], Agent]] = {}
        self._register_default_builders()

    # ── Template management ───────────────────────────────────────────────────

    def register_template(self, name: str, spec: SubAgentSpec) -> None:
        """Register a named template for later use with :meth:`spawn_from_template`."""
        self._templates[name] = spec

    def get_template(self, name: str) -> SubAgentSpec:
        if name not in self._templates:
            raise KeyError(f"No template registered under '{name}'.")
        return self._templates[name]

    # ── Builder registration ──────────────────────────────────────────────────

    def register_builder(
        self,
        agent_type: str,
        builder: Callable[[SubAgentSpec, AgentConfig], Agent],
    ) -> None:
        """Register a factory function for a custom agent type."""
        self._builders[agent_type] = builder

    # ── Spawning ──────────────────────────────────────────────────────────────

    def spawn_from_spec(
        self,
        spec: SubAgentSpec,
        parent_agent: Optional[Agent] = None,
    ) -> Agent:
        """
        Instantiate an agent from *spec*, optionally inheriting context from
        *parent_agent*, then auto-register it with the AgentRegistry.

        Raises:
            ValueError: if no builder is registered for *spec.agent_type*.
            KeyError: (re-raised) if the builder itself raises.
        """
        tool_registry = None
        skills: List[Any] = []
        system_prompt = spec.system_prompt or "You are a helpful AI assistant."

        if parent_agent is not None:
            if spec.inherit_tools and getattr(parent_agent, "tool_registry", None):
                tool_registry = parent_agent.tool_registry
            if spec.inherit_skills and getattr(parent_agent, "skills", None):
                skills = list(parent_agent.skills)
            if spec.inherit_system_prompt_prefix:
                parent_prefix = getattr(parent_agent, "system_prompt", "")
                if parent_prefix and parent_prefix != system_prompt:
                    system_prompt = f"{parent_prefix}\n\n{system_prompt}"

        config = AgentConfig(
            agent_name=spec.agent_name,
            agent_type=spec.agent_type,
            description=spec.description,
            system_prompt=system_prompt,
            llm_config=spec.llm_config,
            tool_registry=tool_registry,
            skills=skills,
        )

        try:
            agent = self._build(spec, config)
        except Exception as exc:
            self._emit_spawn_error(spec, parent_agent, exc)
            raise

        # REQ-SUBAG-08: auto-register with AgentRegistry
        self._registry.register_agent(agent)

        # REQ-SUBAG-05: publish spawn lifecycle event
        self._emit_spawned(
            spec,
            parent_agent,
            inherited_tools=tool_registry is not None,
            inherited_skills=bool(skills),
        )

        return agent

    def spawn_from_template(
        self,
        template_name: str,
        overrides: Optional[Dict[str, Any]] = None,
        parent_agent: Optional[Agent] = None,
    ) -> Agent:
        """
        Spawn from a named template, applying optional field *overrides*.

        Raises:
            KeyError: if *template_name* is not registered.
        """
        base = self.get_template(template_name)
        spec = dataclasses.replace(base, **(overrides or {}))
        return self.spawn_from_spec(spec, parent_agent=parent_agent)

    # ── Internals ─────────────────────────────────────────────────────────────

    def _build(self, spec: SubAgentSpec, config: AgentConfig) -> Agent:
        builder = self._builders.get(spec.agent_type)
        if builder is None:
            raise ValueError(
                f"No builder registered for agent_type '{spec.agent_type}'. "
                f"Call spawner.register_builder('{spec.agent_type}', fn) first."
            )
        return builder(spec, config)

    def _register_default_builders(self) -> None:
        try:
            from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig

            def _openai(spec: SubAgentSpec, config: AgentConfig) -> Agent:
                oc = OpenAIAgentConfig(
                    agent_name=config.agent_name,
                    agent_type=config.agent_type,
                    description=config.description,
                    system_prompt=config.system_prompt,
                    llm_config=config.llm_config,
                    tool_registry=config.tool_registry,
                    skills=config.skills,
                    **spec.extra_kwargs,
                )
                return OpenAIAgent(oc)

            self._builders["openai"] = _openai
        except ImportError:
            pass

        try:
            from moya.agents.ollama_agent import OllamaAgent, OllamaAgentConfig

            def _ollama(spec: SubAgentSpec, config: AgentConfig) -> Agent:
                oc = OllamaAgentConfig(
                    agent_name=config.agent_name,
                    agent_type=config.agent_type,
                    description=config.description,
                    system_prompt=config.system_prompt,
                    llm_config=config.llm_config,
                    tool_registry=config.tool_registry,
                    skills=config.skills,
                    **spec.extra_kwargs,
                )
                return OllamaAgent(oc)

            self._builders["ollama"] = _ollama
        except ImportError:
            pass

    def _emit_spawned(
        self,
        spec: SubAgentSpec,
        parent_agent: Optional[Agent],
        inherited_tools: bool,
        inherited_skills: bool,
    ) -> None:
        if not self._event_bus:
            return
        from moya.observability.events import AgentSpawnedEvent
        self._event_bus.publish(
            AgentSpawnedEvent(
                source="SubAgentSpawner",
                agent_name=spec.agent_name,
                agent_type=spec.agent_type,
                parent_agent=parent_agent.agent_name if parent_agent else "",
                inherited_tools=inherited_tools,
                inherited_skills=inherited_skills,
            )
        )

    def _emit_spawn_error(
        self,
        spec: SubAgentSpec,
        parent_agent: Optional[Agent],
        exc: Exception,
    ) -> None:
        if not self._event_bus:
            return
        from moya.observability.events import AgentSpawnErrorEvent
        self._event_bus.publish(
            AgentSpawnErrorEvent(
                source="SubAgentSpawner",
                agent_name=spec.agent_name,
                agent_type=spec.agent_type,
                parent_agent=parent_agent.agent_name if parent_agent else "",
                error=str(exc),
            )
        )
