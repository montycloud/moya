"""Tests for Pipeline observability event emission."""

import pytest

from moya.flows.pipeline import FlowContext, Pipeline
from moya.observability.event_bus import EventBus


class EchoStep:
    """Step that appends its name to the output."""
    def __init__(self, name="echo"):
        self.name = name

    def run(self, ctx: FlowContext) -> FlowContext:
        ctx.output = ctx.output + f"[{self.name}]"
        return ctx


class FailingStep:
    def __init__(self, name="failing"):
        self.name = name

    def run(self, ctx: FlowContext) -> FlowContext:
        raise RuntimeError("step failed")


@pytest.fixture()
def bus():
    return EventBus()


def test_pipeline_started_event(bus):
    events = []
    bus.subscribe("pipeline.started", lambda e: events.append(e))
    p = Pipeline([EchoStep()], event_bus=bus)
    p.run(thread_id="t1", message="hello")
    assert len(events) == 1
    assert events[0].thread_id == "t1"
    assert events[0].source == "pipeline"


def test_pipeline_completed_event(bus):
    events = []
    bus.subscribe("pipeline.completed", lambda e: events.append(e))
    p = Pipeline([EchoStep()], event_bus=bus)
    p.run(thread_id="t1", message="hello")
    assert len(events) == 1
    assert events[0].duration_ms >= 0


def test_step_started_event(bus):
    events = []
    bus.subscribe("step.started", lambda e: events.append(e))
    p = Pipeline([EchoStep("step_a"), EchoStep("step_b")], event_bus=bus)
    p.run(thread_id="t1", message="hi")
    names = [e.step_name for e in events]
    assert "step_a" in names
    assert "step_b" in names


def test_step_completed_event(bus):
    events = []
    bus.subscribe("step.completed", lambda e: events.append(e))
    p = Pipeline([EchoStep("s1"), EchoStep("s2")], event_bus=bus)
    p.run(thread_id="t1", message="hi")
    assert len(events) == 2
    for e in events:
        assert e.duration_ms >= 0


def test_step_error_event(bus):
    step_errors = []
    pipeline_errors = []
    bus.subscribe("step.error", lambda e: step_errors.append(e))
    bus.subscribe("pipeline.error", lambda e: pipeline_errors.append(e))

    p = Pipeline([EchoStep("ok"), FailingStep("bad")], event_bus=bus)
    with pytest.raises(RuntimeError):
        p.run(thread_id="t1", message="hi")

    assert len(step_errors) == 1
    assert step_errors[0].step_name == "bad"
    assert "step failed" in step_errors[0].error

    assert len(pipeline_errors) == 1
    assert "step failed" in pipeline_errors[0].error


def test_pipeline_no_events_without_bus():
    """Pipeline works normally with no event_bus (default behavior)."""
    p = Pipeline([EchoStep("a"), EchoStep("b")])
    result = p.run(thread_id="t1", message="start")
    assert "[a][b]" in result


def test_pipeline_result_unchanged_with_bus(bus):
    p = Pipeline([EchoStep("x"), EchoStep("y")], event_bus=bus)
    result = p.run(thread_id="t1", message="msg")
    assert "msg[x][y]" == result


def test_pipeline_id_in_metadata(bus):
    started = []
    bus.subscribe("pipeline.started", lambda e: started.append(e))
    p = Pipeline([EchoStep()], event_bus=bus)
    p.run(thread_id="t1", message="hi")
    assert started[0].pipeline_id != ""


def test_wildcard_receives_all_pipeline_events(bus):
    seen_types = []
    bus.subscribe("*", lambda e: seen_types.append(e.event_type))
    p = Pipeline([EchoStep("s")], event_bus=bus)
    p.run(thread_id="t1", message="hi")
    assert "pipeline.started" in seen_types
    assert "step.started" in seen_types
    assert "step.completed" in seen_types
    assert "pipeline.completed" in seen_types


def test_named_pipeline_uses_name_as_source(bus):
    events = []
    bus.subscribe("pipeline.started", lambda e: events.append(e))
    p = Pipeline([EchoStep()], name="my_flow", event_bus=bus)
    p.run(thread_id="t1", message="hi")
    assert events[0].source == "my_flow"
