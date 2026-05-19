"""Tests for ToolRegistry enhancements: event_bus telemetry and Tool metadata."""

import pytest

from moya.tools.tool import Tool
from moya.tools.tool_registry import ToolRegistry
from moya.observability.event_bus import EventBus


def add(a: int, b: int) -> int:
    """Add two numbers.
    - a: first operand
    - b: second operand
    """
    return a + b


def explode(**kwargs):
    """Always raises."""
    raise ValueError("boom")


# ── Tool metadata fields ──────────────────────────────────────────────────────

def test_tool_default_metadata():
    t = Tool(name="t", function=add)
    assert t.version == "1.0.0"
    assert t.author is None
    assert t.tags == []
    assert t.category is None
    assert t.deprecated is False
    assert t.deprecation_message is None
    assert t.allowed_agents is None


def test_tool_custom_metadata():
    t = Tool(
        name="t",
        function=add,
        version="2.0.0",
        author="alice",
        tags=["math", "arithmetic"],
        category="utilities",
        deprecated=True,
        deprecation_message="Use calc instead",
        allowed_agents=["agent_a"],
    )
    assert t.version == "2.0.0"
    assert t.author == "alice"
    assert "math" in t.tags
    assert t.category == "utilities"
    assert t.deprecated is True
    assert t.deprecation_message == "Use calc instead"
    assert t.allowed_agents == ["agent_a"]


# ── ToolRegistry with event_bus ───────────────────────────────────────────────

@pytest.fixture()
def bus():
    return EventBus()


def _make_openai_response(tool_name, args):
    """Build a minimal OpenAI-style tool-call response object."""
    func = type("F", (), {"name": tool_name, "arguments": str(args).replace("'", '"')})()
    call = type("C", (), {"id": "c1", "function": func})()
    msg = type("M", (), {"tool_calls": [call]})()
    choice = type("Ch", (), {"message": msg})()
    return type("R", (), {"choices": [choice]})()


def test_tool_called_event_on_success(bus):
    tr = ToolRegistry(event_bus=bus)
    tr.register_tool(Tool(name="add", function=add))
    events = []
    bus.subscribe("tool.called", lambda e: events.append(e))

    response = _make_openai_response("add", {"a": 1, "b": 2})
    tr.handle_tool_call(response, "openai")

    assert len(events) == 1
    assert events[0].tool_name == "add"
    assert events[0].success is True
    assert events[0].duration_ms >= 0
    assert events[0].error is None


def test_tool_called_event_on_failure(bus):
    tr = ToolRegistry(event_bus=bus)
    tr.register_tool(Tool(name="explode", function=explode))
    events = []
    bus.subscribe("tool.called", lambda e: events.append(e))

    response = _make_openai_response("explode", {})
    tr.handle_tool_call(response, "openai")

    assert len(events) == 1
    assert events[0].success is False
    assert "boom" in events[0].error


def test_no_event_without_bus():
    tr = ToolRegistry()
    tr.register_tool(Tool(name="add", function=add))
    response = _make_openai_response("add", {"a": 1, "b": 2})
    result = tr.handle_tool_call(response, "openai")
    assert result[0]["result"] == 3


def test_no_event_for_no_tool_calls(bus):
    tr = ToolRegistry(event_bus=bus)
    events = []
    bus.subscribe("tool.called", lambda e: events.append(e))

    # OpenAI response with no tool_calls
    msg = type("M", (), {"tool_calls": None})()
    choice = type("Ch", (), {"message": msg})()
    response = type("R", (), {"choices": [choice]})()
    result = tr.handle_tool_call(response, "openai")
    assert result is None
    assert events == []


def test_event_duration_recorded(bus):
    import time

    def slow(**kwargs):
        time.sleep(0.01)
        return "done"

    tr = ToolRegistry(event_bus=bus)
    tr.register_tool(Tool(name="slow", function=slow))
    events = []
    bus.subscribe("tool.called", lambda e: events.append(e))

    response = _make_openai_response("slow", {})
    tr.handle_tool_call(response, "openai")

    assert events[0].duration_ms >= 10
