"""Tests for DelegationManager — depth tracking, parallel dispatch, tool wiring."""

import os
import pytest
from unittest.mock import MagicMock

from moya.delegation.manager import (
    AgentNotFoundError,
    DelegationManager,
    MaxDelegationDepthError,
)
from moya.registry.agent_registry import AgentRegistry
from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
from moya.tools.tool_registry import ToolRegistry


def make_echo_agent(name, response=None):
    os.environ.setdefault("OPENAI_API_KEY", "sk-test")
    config = OpenAIAgentConfig(
        agent_name=name,
        agent_type="openai",
        description=f"Echo agent {name}",
        api_key="sk-test",
        tool_registry=ToolRegistry(),
    )
    agent = OpenAIAgent(config)
    agent.client = MagicMock()
    # Stub handle_message to return a predictable value
    agent.handle_message = MagicMock(return_value=response or f"ECHO:{name}")
    return agent


@pytest.fixture
def registry():
    r = AgentRegistry()
    r.register_agent(make_echo_agent("alpha"))
    r.register_agent(make_echo_agent("beta"))
    return r


@pytest.fixture
def manager(registry):
    return DelegationManager(registry, max_depth=3)


# ---- delegate() --------------------------------------------------------

def test_delegate_by_name(manager):
    result = manager.delegate("task", agent_name="alpha")
    assert result == "ECHO:alpha"


def test_delegate_missing_agent_raises(manager):
    with pytest.raises(AgentNotFoundError):
        manager.delegate("task", agent_name="nobody")


def test_delegate_no_ref_raises(manager):
    with pytest.raises(AgentNotFoundError):
        manager.delegate("task")


# ---- depth guard -------------------------------------------------------

def test_max_depth_guard(registry):
    dm = DelegationManager(registry, max_depth=1)
    # Set depth to max before calling
    dm._set_depth(1)
    with pytest.raises(MaxDelegationDepthError):
        dm.delegate("task", agent_name="alpha")


# ---- delegate_parallel() -----------------------------------------------

def test_delegate_parallel_order(manager):
    results = manager.delegate_parallel([
        ("task1", "alpha"),
        ("task2", "beta"),
    ])
    assert results[0] == "ECHO:alpha"
    assert results[1] == "ECHO:beta"


def test_delegate_parallel_all_run(registry):
    dm = DelegationManager(registry, max_depth=5)
    called = []

    def track(name):
        agent = registry.get_agent(name)
        original = agent.handle_message.side_effect

        def _side_effect(msg, **kw):
            called.append(name)
            return f"ECHO:{name}"

        agent.handle_message.side_effect = _side_effect

    track("alpha")
    track("beta")
    dm.delegate_parallel([("t", "alpha"), ("t", "beta")])
    assert set(called) == {"alpha", "beta"}


# ---- setup_tools() -----------------------------------------------------

def test_setup_tools_registers_list_and_delegate(manager):
    tr = ToolRegistry()
    manager.setup_tools(tr)
    assert tr.get_tool("list_agents") is not None
    assert tr.get_tool("delegate_task") is not None


def test_list_agents_tool_output(manager, registry):
    tr = ToolRegistry()
    manager.setup_tools(tr)
    output = tr.get_tool("list_agents").function()
    assert "alpha" in output
    assert "beta" in output


def test_delegate_task_tool(manager):
    tr = ToolRegistry()
    manager.setup_tools(tr)
    result = tr.get_tool("delegate_task").function(task="ping", agent_name="alpha")
    assert result == "ECHO:alpha"
