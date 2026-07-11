"""
Built-in Step types for MOYA Pipelines.

All steps share the same contract::

    step.run(ctx: FlowContext) -> FlowContext

Steps read from ``ctx.output``, do their work, write their result back to
``ctx.output``, and return ``ctx``.  Steps should not modify ``ctx.message``
(the original user message) — only ``ctx.output`` and ``ctx.metadata``.

Available steps
---------------
AgentStep       — calls a MOYA agent with the current output as its message
FunctionStep    — wraps a plain Python function (ctx -> ctx)
ParallelStep    — runs multiple steps concurrently, merges their outputs
BranchStep      — routes to one of several steps based on a condition
LoopStep        — repeats a step until a condition is met or max iterations reached
"""

import copy
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional

from moya.flows.pipeline import FlowContext


class AgentStep:
    """
    Wraps a MOYA agent as a Pipeline step.

    The agent receives ``ctx.output`` as its message and ``ctx.thread_id``
    as the thread ID.  Its response becomes the new ``ctx.output``.

    Args:
        agent:  Any MOYA agent with a ``handle_message(message, thread_id=...)`` method.
        name:   Optional label; defaults to the agent's ``agent_name``.

    Example::

        step = AgentStep(my_openai_agent)
        step = AgentStep(my_openai_agent, name="researcher")
    """

    def __init__(self, agent: Any, name: Optional[str] = None) -> None:
        self.agent = agent
        self.name = name or getattr(agent, "agent_name", "agent_step")

    def run(self, ctx: FlowContext) -> FlowContext:
        ctx.output = self.agent.handle_message(ctx.output, thread_id=ctx.thread_id)
        return ctx


class FunctionStep:
    """
    Wraps a plain Python function as a Pipeline step.

    The function receives the FlowContext and must return it (modified or not).
    Useful for lightweight transforms between agent calls.

    Args:
        func:  A callable ``(ctx: FlowContext) -> FlowContext``.
        name:  Optional label; defaults to the function's ``__name__``.

    Example::

        def add_prefix(ctx):
            ctx.output = "Summary: " + ctx.output
            return ctx

        step = FunctionStep(add_prefix)
    """

    def __init__(self, func: Callable[[FlowContext], FlowContext], name: Optional[str] = None) -> None:
        self.func = func
        self.name = name or getattr(func, "__name__", "function_step")

    def run(self, ctx: FlowContext) -> FlowContext:
        return self.func(ctx)


class ParallelStep:
    """
    Runs multiple steps concurrently and merges their outputs.

    Each sub-step receives a *copy* of the incoming context (same input).
    After all sub-steps complete, their outputs are combined using the
    ``merge`` function (default: join with double newline).

    Args:
        steps:  List of steps to run in parallel.
        name:   Optional label.
        merge:  ``(outputs: List[str]) -> str`` — how to combine results.
                Default concatenates with ``"\\n\\n"``.

    Example::

        parallel = ParallelStep([
            AgentStep(analyst_a, name="analysis_a"),
            AgentStep(analyst_b, name="analysis_b"),
        ])

        # Custom merge: join with a separator line
        parallel = ParallelStep(
            [AgentStep(a), AgentStep(b)],
            merge=lambda outputs: "\\n---\\n".join(outputs),
        )
    """

    def __init__(
        self,
        steps: List[Any],
        name: str = "parallel",
        merge: Optional[Callable[[List[str]], str]] = None,
    ) -> None:
        self.steps = list(steps)
        self.name = name
        self.merge = merge or (lambda outputs: "\n\n".join(str(o) for o in outputs))

    def run(self, ctx: FlowContext) -> FlowContext:
        outputs: List[str] = []
        with ThreadPoolExecutor(max_workers=len(self.steps)) as executor:
            futures = {
                executor.submit(step.run, copy.copy(ctx)): step
                for step in self.steps
            }
            for future in as_completed(futures):
                result_ctx = future.result()
                outputs.append(result_ctx.output)
        ctx.output = self.merge(outputs)
        return ctx


class BranchStep:
    """
    Routes to one of several steps based on a condition function.

    The condition receives the current FlowContext and must return a string
    key that maps to one of the ``branches``.

    Args:
        condition:  ``(ctx: FlowContext) -> str`` — returns the branch key.
        branches:   Dict mapping branch keys to step objects.
        name:       Optional label.

    Raises:
        KeyError: if the condition returns a key not in ``branches``.

    Example::

        branch = BranchStep(
            condition=lambda ctx: "code" if "python" in ctx.output.lower() else "prose",
            branches={
                "code":  AgentStep(code_agent),
                "prose": AgentStep(writing_agent),
            },
        )
    """

    def __init__(
        self,
        condition: Callable[[FlowContext], str],
        branches: Dict[str, Any],
        name: str = "branch",
    ) -> None:
        self.condition = condition
        self.branches = branches
        self.name = name

    def run(self, ctx: FlowContext) -> FlowContext:
        key = self.condition(ctx)
        step = self.branches.get(key)
        if step is None:
            available = list(self.branches.keys())
            raise KeyError(
                f"BranchStep '{self.name}': condition returned '{key}', "
                f"but no branch for that key. Available keys: {available}"
            )
        return step.run(ctx)


class LoopStep:
    """
    Repeats a step until a termination condition is met.

    Useful for iterative refinement workflows where an agent keeps improving
    its output until it reaches a quality threshold.

    Args:
        step:           The step to repeat.
        until:          ``(ctx: FlowContext) -> bool`` — return True to stop.
        max_iterations: Hard cap to prevent infinite loops. Default: 10.
        name:           Optional label.

    Example::

        loop = LoopStep(
            step=AgentStep(refiner_agent),
            until=lambda ctx: "APPROVED" in ctx.output,
            max_iterations=5,
        )
    """

    def __init__(
        self,
        step: Any,
        until: Callable[[FlowContext], bool],
        max_iterations: int = 10,
        name: str = "loop",
    ) -> None:
        self.step = step
        self.until = until
        self.max_iterations = max_iterations
        self.name = name

    def run(self, ctx: FlowContext) -> FlowContext:
        for _ in range(self.max_iterations):
            ctx = self.step.run(ctx)
            if self.until(ctx):
                break
        return ctx
