"""Tests for moya.observability — EventBus, events, and listeners."""

import threading
import time
import pytest

from moya.observability.event_bus import EventBus, get_event_bus, set_event_bus
from moya.observability.events import (
    MoyaEvent,
    AgentRegisteredEvent,
    AgentRemovedEvent,
    AgentHealthChangedEvent,
    ToolRegisteredEvent,
    ToolCalledEvent,
    PipelineStartedEvent,
    PipelineCompletedEvent,
    PipelineErrorEvent,
    StepStartedEvent,
    StepCompletedEvent,
    StepErrorEvent,
)
from moya.observability.listeners import (
    LoggingListener,
    CallbackListener,
    FilteredListener,
)


@pytest.fixture(autouse=True)
def fresh_bus(monkeypatch):
    """Each test gets an isolated EventBus."""
    bus = EventBus()
    monkeypatch.setattr("moya.observability.event_bus._default_bus", bus)
    return bus


# ── EventBus basics ───────────────────────────────────────────────────────────

def test_subscribe_and_receive_typed(fresh_bus):
    received = []
    fresh_bus.subscribe("tool.called", lambda e: received.append(e))
    fresh_bus.publish(ToolCalledEvent(source="test", tool_name="t1"))
    assert len(received) == 1
    assert received[0].tool_name == "t1"


def test_wildcard_receives_all(fresh_bus):
    received = []
    fresh_bus.subscribe("*", lambda e: received.append(e.event_type))
    fresh_bus.publish(ToolCalledEvent(source="s"))
    fresh_bus.publish(AgentRegisteredEvent(source="s", agent_name="a"))
    assert "tool.called" in received
    assert "agent.registered" in received


def test_typed_listener_does_not_receive_other_types(fresh_bus):
    received = []
    fresh_bus.subscribe("tool.called", lambda e: received.append(e))
    fresh_bus.publish(AgentRegisteredEvent(source="s", agent_name="a"))
    assert received == []


def test_unsubscribe_typed(fresh_bus):
    received = []
    listener = lambda e: received.append(e)
    fresh_bus.subscribe("tool.called", listener)
    fresh_bus.unsubscribe("tool.called", listener)
    fresh_bus.publish(ToolCalledEvent(source="s"))
    assert received == []


def test_unsubscribe_wildcard(fresh_bus):
    received = []
    listener = lambda e: received.append(e)
    fresh_bus.subscribe("*", listener)
    fresh_bus.unsubscribe("*", listener)
    fresh_bus.publish(ToolCalledEvent(source="s"))
    assert received == []


def test_duplicate_subscribe_is_noop(fresh_bus):
    received = []
    listener = lambda e: received.append(e)
    fresh_bus.subscribe("tool.called", listener)
    fresh_bus.subscribe("tool.called", listener)
    fresh_bus.publish(ToolCalledEvent(source="s"))
    assert len(received) == 1


def test_bad_listener_does_not_break_others(fresh_bus):
    good = []

    def bad(e):
        raise RuntimeError("listener exploded")

    fresh_bus.subscribe("*", bad)
    fresh_bus.subscribe("*", lambda e: good.append(e))
    fresh_bus.publish(ToolCalledEvent(source="s"))
    assert len(good) == 1


def test_clear(fresh_bus):
    received = []
    fresh_bus.subscribe("*", lambda e: received.append(e))
    fresh_bus.clear()
    fresh_bus.publish(ToolCalledEvent(source="s"))
    assert received == []


def test_thread_safe_publish(fresh_bus):
    received = []
    lock = threading.Lock()
    fresh_bus.subscribe("*", lambda e: (lock.acquire(), received.append(e), lock.release()))

    def publish_many():
        for _ in range(50):
            fresh_bus.publish(ToolCalledEvent(source="thread"))

    threads = [threading.Thread(target=publish_many) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(received) == 200


# ── Event dataclasses ─────────────────────────────────────────────────────────

def test_event_has_timestamp():
    e = ToolCalledEvent(source="src", tool_name="t")
    assert e.timestamp is not None


def test_event_defaults():
    e = MoyaEvent()
    assert e.event_type == ""
    assert e.source == ""
    assert e.metadata == {}


def test_tool_called_event_fields():
    e = ToolCalledEvent(
        source="registry",
        tool_name="search",
        arguments={"q": "test"},
        duration_ms=12.5,
        success=True,
    )
    assert e.event_type == "tool.called"
    assert e.tool_name == "search"
    assert e.duration_ms == 12.5
    assert e.success is True


def test_agent_health_changed_event():
    e = AgentHealthChangedEvent(
        source="registry",
        agent_name="agent1",
        old_status="unknown",
        new_status="healthy",
    )
    assert e.event_type == "agent.health_changed"
    assert e.old_status == "unknown"
    assert e.new_status == "healthy"


def test_step_error_event():
    e = StepErrorEvent(
        source="pipeline",
        pipeline_id="p1",
        thread_id="t1",
        step_name="AgentStep",
        step_type="AgentStep",
        error="timeout",
    )
    assert e.event_type == "step.error"
    assert e.error == "timeout"


# ── Listeners ─────────────────────────────────────────────────────────────────

def test_logging_listener_does_not_raise(fresh_bus, caplog):
    import logging
    with caplog.at_level(logging.DEBUG, logger="moya.observability"):
        fresh_bus.subscribe("*", LoggingListener())
        fresh_bus.publish(ToolCalledEvent(source="s", tool_name="t"))
    assert "tool.called" in caplog.text


def test_callback_listener(fresh_bus):
    calls = []
    fresh_bus.subscribe("*", CallbackListener(lambda e: calls.append(e.event_type)))
    fresh_bus.publish(AgentRegisteredEvent(source="s", agent_name="a"))
    assert calls == ["agent.registered"]


def test_filtered_listener_passes_matching(fresh_bus):
    seen = []
    fresh_bus.subscribe("*", FilteredListener(
        predicate=lambda e: e.source == "trusted",
        listener=lambda e: seen.append(e),
    ))
    fresh_bus.publish(ToolCalledEvent(source="trusted", tool_name="t"))
    fresh_bus.publish(ToolCalledEvent(source="untrusted", tool_name="t"))
    assert len(seen) == 1
    assert seen[0].source == "trusted"


# ── get_event_bus singleton ───────────────────────────────────────────────────

def test_get_event_bus_returns_same_instance():
    b1 = get_event_bus()
    b2 = get_event_bus()
    assert b1 is b2


def test_set_event_bus_replaces_singleton():
    original = get_event_bus()
    new_bus = EventBus()
    set_event_bus(new_bus)
    assert get_event_bus() is new_bus
    set_event_bus(original)  # restore
