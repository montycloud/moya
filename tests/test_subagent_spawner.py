"""
SubAgentSpawner tests.

Covers:
- REQ-SUBAG-01: spawn_from_spec, spawn_from_template
- REQ-SUBAG-02: context inheritance (system_prompt, tool_registry, skills)
- REQ-SUBAG-05: lifecycle observability events
- REQ-SUBAG-08: auto-register with AgentRegistry
"""

import os
import pytest
from unittest.mock import MagicMock

from moya.delegation.spawner import SubAgentSpawner, SubAgentSpec
from moya.registry.agent_registry import AgentRegistry
from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
from moya.tools.tool_registry import ToolRegistry
from moya.observability.event_bus import EventBus


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_parent(name="parent", system_prompt="I am the parent."):
    os.environ.setdefault("OPENAI_API_KEY", "sk-test")
    config = OpenAIAgentConfig(
        agent_name=name,
        agent_type="openai",
        description="Parent agent",
        api_key="sk-test",
        system_prompt=system_prompt,
        tool_registry=ToolRegistry(),
    )
    agent = OpenAIAgent(config)
    agent.client = MagicMock()
    return agent


def openai_spec(name="child", **kwargs) -> SubAgentSpec:
    return SubAgentSpec(
        agent_type="openai",
        agent_name=name,
        description=f"Child agent {name}",
        extra_kwargs={"api_key": "sk-test"},
        **kwargs,
    )


@pytest.fixture
def registry():
    return AgentRegistry()


@pytest.fixture
def bus():
    return EventBus()


@pytest.fixture
def spawner(registry):
    return SubAgentSpawner(registry)


@pytest.fixture
def observed_spawner(registry, bus):
    return SubAgentSpawner(registry, event_bus=bus)


# ── REQ-SUBAG-01: basic spawn ─────────────────────────────────────────────────

def test_spawn_from_spec_returns_agent(spawner):
    agent = spawner.spawn_from_spec(openai_spec())
    assert isinstance(agent, OpenAIAgent)
    assert agent.agent_name == "child"


def test_spawn_from_spec_unknown_type_raises(spawner):
    bad = SubAgentSpec(
        agent_type="unknown_llm",
        agent_name="x",
        description="test",
    )
    with pytest.raises(ValueError, match="No builder registered"):
        spawner.spawn_from_spec(bad)


def test_register_custom_builder(spawner):
    mock_agent = MagicMock()
    mock_agent.agent_name = "custom_child"
    spawner.register_builder("mock", lambda spec, cfg: mock_agent)

    spec = SubAgentSpec(agent_type="mock", agent_name="custom_child", description="d")
    spawner.registry = spawner._registry  # sanity alias
    agent = spawner.spawn_from_spec(spec)
    assert agent is mock_agent


# ── REQ-SUBAG-01: template spawn ─────────────────────────────────────────────

def test_spawn_from_template(spawner):
    tmpl = openai_spec("tmpl_child")
    spawner.register_template("my_template", tmpl)
    agent = spawner.spawn_from_template("my_template")
    assert agent.agent_name == "tmpl_child"


def test_spawn_from_template_with_overrides(spawner):
    tmpl = openai_spec("original")
    spawner.register_template("t", tmpl)
    agent = spawner.spawn_from_template("t", overrides={"agent_name": "overridden"})
    assert agent.agent_name == "overridden"


def test_spawn_from_unknown_template_raises(spawner):
    with pytest.raises(KeyError):
        spawner.spawn_from_template("not_there")


# ── REQ-SUBAG-02: context inheritance ────────────────────────────────────────

def test_inherits_tool_registry(spawner):
    parent = make_parent()
    agent = spawner.spawn_from_spec(openai_spec(), parent_agent=parent)
    assert agent.tool_registry is parent.tool_registry


def test_no_inherit_tool_registry_when_disabled(spawner):
    parent = make_parent()
    spec = openai_spec(inherit_tools=False)
    agent = spawner.spawn_from_spec(spec, parent_agent=parent)
    assert agent.tool_registry is None


def test_inherits_system_prompt_prefix(spawner):
    parent = make_parent(system_prompt="ParentPrefix.")
    spec = openai_spec(system_prompt="ChildSpecific.")
    agent = spawner.spawn_from_spec(spec, parent_agent=parent)
    assert agent.system_prompt.startswith("ParentPrefix.")
    assert "ChildSpecific." in agent.system_prompt


def test_no_inherit_system_prompt_when_disabled(spawner):
    parent = make_parent(system_prompt="ParentPrefix.")
    spec = openai_spec(system_prompt="ChildOnly.", inherit_system_prompt_prefix=False)
    agent = spawner.spawn_from_spec(spec, parent_agent=parent)
    assert agent.system_prompt == "ChildOnly."
    assert "ParentPrefix." not in agent.system_prompt


def test_no_parent_uses_spec_system_prompt(spawner):
    spec = openai_spec(system_prompt="Standalone.")
    agent = spawner.spawn_from_spec(spec)
    assert agent.system_prompt == "Standalone."


def test_no_parent_no_spec_prompt_uses_default(spawner):
    agent = spawner.spawn_from_spec(openai_spec())
    assert agent.system_prompt == "You are a helpful AI assistant."


# ── REQ-SUBAG-08: auto-register ──────────────────────────────────────────────

def test_spawned_agent_auto_registered(spawner, registry):
    spawner.spawn_from_spec(openai_spec("reg_child"))
    assert registry.get_agent("reg_child") is not None


def test_multiple_spawns_all_registered(spawner, registry):
    spawner.spawn_from_spec(openai_spec("child_a"))
    spawner.spawn_from_spec(openai_spec("child_b"))
    assert registry.get_agent("child_a") is not None
    assert registry.get_agent("child_b") is not None


# ── REQ-SUBAG-05: lifecycle observability ────────────────────────────────────

def test_spawn_emits_spawned_event(observed_spawner, bus):
    received = []
    bus.subscribe("agent.spawned", lambda e: received.append(e))
    observed_spawner.spawn_from_spec(openai_spec("ev_child"))
    assert len(received) == 1
    assert received[0].agent_name == "ev_child"
    assert received[0].event_type == "agent.spawned"


def test_spawn_event_includes_parent_name(observed_spawner, bus):
    received = []
    bus.subscribe("agent.spawned", lambda e: received.append(e))
    parent = make_parent("my_parent")
    observed_spawner.spawn_from_spec(openai_spec("my_child"), parent_agent=parent)
    assert received[0].parent_agent == "my_parent"


def test_spawn_event_inherited_tools_flag(observed_spawner, bus):
    received = []
    bus.subscribe("agent.spawned", lambda e: received.append(e))
    parent = make_parent()
    observed_spawner.spawn_from_spec(openai_spec(), parent_agent=parent)
    assert received[0].inherited_tools is True


def test_spawn_error_emits_error_event(observed_spawner, bus):
    received = []
    bus.subscribe("agent.spawn_error", lambda e: received.append(e))

    bad = SubAgentSpec(agent_type="bad_type", agent_name="fail", description="d")
    with pytest.raises(ValueError):
        observed_spawner.spawn_from_spec(bad)

    assert len(received) == 1
    assert "bad_type" in received[0].error or received[0].agent_name == "fail"


def test_no_event_bus_no_error(spawner):
    """Spawner without event_bus should not raise."""
    agent = spawner.spawn_from_spec(openai_spec("quiet_child"))
    assert agent is not None
