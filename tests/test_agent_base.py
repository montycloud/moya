"""Tests for Agent base-class behaviour: memory, call_tool, discover_tools."""

import os
import pytest
from unittest.mock import MagicMock

from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
from moya.memory.in_memory_repository import InMemoryRepository
from moya.tools.tool import Tool
from moya.tools.tool_registry import ToolRegistry


def make_agent(memory=None, tool_registry=None):
    os.environ.setdefault("OPENAI_API_KEY", "sk-test")
    config = OpenAIAgentConfig(
        agent_name="tester",
        agent_type="openai",
        description="test",
        api_key="sk-test",
        memory=memory,
        tool_registry=tool_registry or ToolRegistry(),
    )
    agent = OpenAIAgent(config)
    agent.client = MagicMock()
    return agent


# ---- _remember() -------------------------------------------------------

def test_remember_creates_thread_on_first_call():
    repo = InMemoryRepository()
    agent = make_agent(memory=repo)
    agent._remember("t1", "hello", "hi there")
    assert repo.get_thread("t1") is not None


def test_remember_appends_two_messages():
    repo = InMemoryRepository()
    agent = make_agent(memory=repo)
    agent._remember("t1", "hello", "hi there")
    thread = repo.get_thread("t1")
    msgs = thread.get_messages()
    assert len(msgs) == 2
    assert msgs[0].sender == "user"
    assert msgs[1].sender == "tester"


def test_remember_multiple_turns():
    repo = InMemoryRepository()
    agent = make_agent(memory=repo)
    agent._remember("t1", "turn1", "resp1")
    agent._remember("t1", "turn2", "resp2")
    thread = repo.get_thread("t1")
    assert len(thread.get_messages()) == 4


def test_remember_no_memory_is_noop():
    agent = make_agent(memory=None)
    agent._remember("t1", "hello", "world")  # should not raise


# ---- call_tool() -------------------------------------------------------

def test_call_tool_invokes_function():
    def add(a: int, b: int) -> int:
        """Add two numbers.

        Parameters:
        - a: First number.
        - b: Second number.
        """
        return a + b

    registry = ToolRegistry()
    registry.register_tool(Tool(name="add", function=add))
    agent = make_agent(tool_registry=registry)
    result = agent.call_tool("add", a=3, b=4)
    assert result == 7


def test_call_tool_missing_name_raises():
    agent = make_agent()
    with pytest.raises(ValueError, match="No tool named"):
        agent.call_tool("nonexistent")


def test_call_tool_no_registry_raises():
    config = OpenAIAgentConfig(
        agent_name="no_reg",
        agent_type="openai",
        description="d",
        api_key="sk-test",
        tool_registry=None,
    )
    agent = OpenAIAgent(config)
    agent.client = MagicMock()
    with pytest.raises(RuntimeError, match="no tool registry"):
        agent.call_tool("anything")


# ---- discover_tools() --------------------------------------------------

def test_discover_tools_returns_names():
    registry = ToolRegistry()

    def noop() -> str:
        """Noop."""
        return ""

    registry.register_tool(Tool(name="t1", function=noop))
    registry.register_tool(Tool(name="t2", function=noop))
    agent = make_agent(tool_registry=registry)
    names = agent.discover_tools()
    assert set(names) == {"t1", "t2"}


def test_discover_tools_no_registry_returns_empty():
    config = OpenAIAgentConfig(
        agent_name="no_reg",
        agent_type="openai",
        description="d",
        api_key="sk-test",
        tool_registry=None,
    )
    agent = OpenAIAgent(config)
    agent.client = MagicMock()
    assert agent.discover_tools() == []


# ---- create_agent factory ----------------------------------------------

def test_create_agent_openai():
    from moya import create_agent
    agent = create_agent("openai", name="a", description="d", api_key="sk-test")
    assert agent.agent_name == "a"
    assert isinstance(agent, OpenAIAgent)


def test_create_agent_sets_tags():
    from moya import create_agent
    agent = create_agent("openai", name="a", description="d",
                         api_key="sk-test", tags=["specialist"])
    assert agent.tags == ["specialist"]


def test_create_agent_auto_tool_caller():
    from moya import create_agent
    registry = ToolRegistry()
    agent = create_agent("openai", name="a", description="d",
                         api_key="sk-test", tool_registry=registry)
    assert agent.is_tool_caller is True


def test_create_agent_unknown_provider_raises():
    from moya import create_agent
    with pytest.raises(ValueError, match="Unknown provider"):
        create_agent("fakeai", name="a", description="d")


def test_create_agent_ollama_no_network():
    from moya import create_agent
    # Should not raise even if Ollama isn't running (network check removed from __init__)
    agent = create_agent("ollama", name="local", description="d")
    assert agent.agent_name == "local"
