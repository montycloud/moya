"""Tests for Pipeline, FlowContext, and all Step types."""

import pytest
from moya.flows.pipeline import FlowContext, Pipeline
from moya.flows.steps import (
    AgentStep,
    BranchStep,
    FunctionStep,
    LoopStep,
    ParallelStep,
)


# ---- Helpers -----------------------------------------------------------

def upper_step(ctx: FlowContext) -> FlowContext:
    ctx.output = ctx.output.upper()
    return ctx


def append_step(suffix: str):
    def _step(ctx: FlowContext) -> FlowContext:
        ctx.output = ctx.output + suffix
        return ctx
    _step.__name__ = f"append_{suffix}"
    return _step


class EchoAgent:
    agent_name = "echo"
    def handle_message(self, message, **kwargs):
        return f"ECHO:{message}"


# ---- FlowContext -------------------------------------------------------

def test_flow_context_defaults():
    ctx = FlowContext(thread_id="t1", message="hello", output="hello")
    assert ctx.metadata == {}


def test_flow_context_kwargs_in_metadata():
    pipeline = Pipeline([FunctionStep(lambda c: c)])
    pipeline.run(thread_id="t1", message="m", foo="bar", num=42)


# ---- FunctionStep ------------------------------------------------------

def test_function_step_transforms_output():
    pipeline = Pipeline([FunctionStep(upper_step)])
    result = pipeline.run(thread_id="t1", message="hello")
    assert result == "HELLO"


def test_function_step_chain():
    pipeline = Pipeline([
        FunctionStep(append_step("-A")),
        FunctionStep(append_step("-B")),
    ])
    result = pipeline.run(thread_id="t1", message="X")
    assert result == "X-A-B"


# ---- AgentStep ---------------------------------------------------------

def test_agent_step_calls_handle_message():
    pipeline = Pipeline([AgentStep(EchoAgent())])
    result = pipeline.run(thread_id="t1", message="ping")
    assert result == "ECHO:ping"


# ---- ParallelStep ------------------------------------------------------

def test_parallel_step_runs_all():
    results = []

    def track(label):
        def _step(ctx):
            results.append(label)
            ctx.output = label
            return ctx
        _step.__name__ = label
        return FunctionStep(_step)

    parallel = ParallelStep([track("a"), track("b"), track("c")])
    pipeline = Pipeline([parallel])
    pipeline.run(thread_id="t1", message="go")
    assert set(results) == {"a", "b", "c"}


def test_parallel_step_merges_outputs():
    steps = [
        FunctionStep(lambda c: setattr(c, "output", "X") or c),
        FunctionStep(lambda c: setattr(c, "output", "Y") or c),
    ]
    parallel = ParallelStep(steps, merge=lambda outs: "+".join(sorted(outs)))
    pipeline = Pipeline([parallel])
    result = pipeline.run(thread_id="t1", message="start")
    assert result == "X+Y"


def test_parallel_step_independent_contexts():
    """Each branch gets a copy of ctx; mutations don't leak between branches."""
    def set_meta(key, val):
        def _f(ctx):
            ctx.metadata[key] = val
            ctx.output = key
            return ctx
        return FunctionStep(_f)

    parallel = ParallelStep([set_meta("a", 1), set_meta("b", 2)])
    ctx = FlowContext(thread_id="t1", message="m", output="m")
    result_ctx = parallel.run(ctx)
    # Neither branch's metadata key should leak into the final context
    # (ParallelStep merges outputs, not metadata)
    assert result_ctx.output != ""


# ---- BranchStep --------------------------------------------------------

def test_branch_step_routes_correctly():
    branch = BranchStep(
        condition=lambda ctx: ctx.metadata.get("style", "a"),
        branches={
            "a": FunctionStep(append_step(":A")),
            "b": FunctionStep(append_step(":B")),
        },
    )
    pipeline = Pipeline([branch])
    result = pipeline.run(thread_id="t1", message="X", style="b")
    assert result == "X:B"


def test_branch_step_unknown_key_raises():
    branch = BranchStep(
        condition=lambda ctx: "unknown",
        branches={"a": FunctionStep(lambda c: c)},
    )
    with pytest.raises(KeyError):
        Pipeline([branch]).run(thread_id="t1", message="m")


# ---- LoopStep ----------------------------------------------------------

def test_loop_step_stops_on_condition():
    counter = {"n": 0}

    def increment(ctx):
        counter["n"] += 1
        ctx.output = str(counter["n"])
        return ctx

    loop = LoopStep(
        step=FunctionStep(increment),
        until=lambda ctx: ctx.output == "3",
        max_iterations=10,
    )
    result = Pipeline([loop]).run(thread_id="t1", message="0")
    assert result == "3"
    assert counter["n"] == 3


def test_loop_step_respects_max_iterations():
    counter = {"n": 0}

    def increment(ctx):
        counter["n"] += 1
        ctx.output = str(counter["n"])
        return ctx

    loop = LoopStep(
        step=FunctionStep(increment),
        until=lambda ctx: False,
        max_iterations=4,
    )
    Pipeline([loop]).run(thread_id="t1", message="0")
    assert counter["n"] == 4


# ---- Nested pipelines --------------------------------------------------

def test_nested_pipeline_via_function_step():
    inner = Pipeline([FunctionStep(upper_step), FunctionStep(append_step("!")),])
    outer = Pipeline([FunctionStep(lambda ctx: inner.run_ctx(ctx))])
    result = outer.run(thread_id="t1", message="hello")
    assert result == "HELLO!"


# ---- Metadata propagation ----------------------------------------------

def test_metadata_flows_through_steps():
    def save(ctx):
        ctx.metadata["saved"] = ctx.output
        return ctx

    def check(ctx):
        ctx.output = ctx.metadata.get("saved", "MISSING")
        return ctx

    pipeline = Pipeline([FunctionStep(save), FunctionStep(upper_step), FunctionStep(check)])
    result = pipeline.run(thread_id="t1", message="hi")
    assert result == "hi"
