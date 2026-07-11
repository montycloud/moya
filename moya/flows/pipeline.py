"""
Pipeline — the core building block for multi-step agent workflows.

A Pipeline chains Steps in order, passing the output of each step as the
input to the next. It keeps a FlowContext object that carries the current
value, the original message, the thread ID, and any step-to-step metadata.

Quick start::

    from moya.flows import Pipeline, AgentStep

    pipeline = Pipeline([
        AgentStep(researcher),
        AgentStep(writer),
        AgentStep(editor),
    ])

    result = pipeline.run(thread_id="t1", message="Write about climate change")
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from moya.observability.event_bus import EventBus


@dataclass
class FlowContext:
    """
    Carries state through a Pipeline run.

    Attributes:
        thread_id:  Conversation thread ID passed to agents.
        message:    The original user message (unchanged throughout the run).
        output:     The current value — each step reads this and writes back to it.
        metadata:   Free-form dict for steps to share annotations with each other.
    """

    thread_id: str
    message: str
    output: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class Pipeline:
    """
    Executes a sequence of Steps, piping the output of each into the next.

    A Pipeline is itself a valid Step, so pipelines can be nested::

        inner = Pipeline([step_a, step_b])
        outer = Pipeline([inner, step_c])

    Args:
        steps:  An ordered list of step objects. Each must have a
                ``run(ctx: FlowContext) -> FlowContext`` method.
        name:   Optional label used in error messages and logging.
    """

    def __init__(
        self,
        steps: List[Any],
        name: str = "pipeline",
        event_bus: Optional["EventBus"] = None,
    ) -> None:
        self.name = name
        self.steps = list(steps)
        self._event_bus = event_bus

    def run(self, thread_id: str, message: str, **kwargs) -> str:
        """
        Execute the pipeline and return the final output string.

        Args:
            thread_id:  Passed through to every AgentStep.
            message:    The starting input — also available as ``ctx.message``
                        in every step for reference.
            **kwargs:   Extra values merged into ``ctx.metadata``.

        Returns:
            The output string produced by the last step.
        """
        pipeline_id = str(uuid.uuid4())
        ctx = FlowContext(
            thread_id=thread_id,
            message=message,
            output=message,
            metadata=dict(kwargs),
        )
        ctx.metadata.setdefault("pipeline_id", pipeline_id)

        t0 = time.monotonic()
        self._emit_pipeline_started(pipeline_id, thread_id)
        try:
            for step in self.steps:
                step_name = getattr(step, "name", type(step).__name__)
                step_type = type(step).__name__
                t_step = time.monotonic()
                self._emit_step_started(pipeline_id, thread_id, step_name, step_type)
                try:
                    ctx = step.run(ctx)
                    self._emit_step_completed(
                        pipeline_id, thread_id, step_name, step_type,
                        (time.monotonic() - t_step) * 1000,
                    )
                except Exception as exc:
                    self._emit_step_error(
                        pipeline_id, thread_id, step_name, step_type, str(exc)
                    )
                    raise
            self._emit_pipeline_completed(pipeline_id, thread_id, (time.monotonic() - t0) * 1000)
        except Exception as exc:
            self._emit_pipeline_error(pipeline_id, thread_id, str(exc))
            raise
        return ctx.output

    # Allow Pipeline to be used as a step inside another Pipeline.
    def run_ctx(self, ctx: FlowContext) -> FlowContext:
        for step in self.steps:
            ctx = step.run(ctx)
        return ctx

    # ── Event helpers (all silently no-op when event_bus is None) ─────────────

    def _emit_pipeline_started(self, pipeline_id: str, thread_id: str) -> None:
        self._emit(lambda: __import__(
            "moya.observability.events", fromlist=["PipelineStartedEvent"]
        ).PipelineStartedEvent(
            source=self.name, pipeline_id=pipeline_id, thread_id=thread_id,
        ))

    def _emit_pipeline_completed(self, pipeline_id: str, thread_id: str, ms: float) -> None:
        self._emit(lambda: __import__(
            "moya.observability.events", fromlist=["PipelineCompletedEvent"]
        ).PipelineCompletedEvent(
            source=self.name, pipeline_id=pipeline_id, thread_id=thread_id, duration_ms=ms,
        ))

    def _emit_pipeline_error(self, pipeline_id: str, thread_id: str, error: str) -> None:
        self._emit(lambda: __import__(
            "moya.observability.events", fromlist=["PipelineErrorEvent"]
        ).PipelineErrorEvent(
            source=self.name, pipeline_id=pipeline_id, thread_id=thread_id, error=error,
        ))

    def _emit_step_started(
        self, pipeline_id: str, thread_id: str, step_name: str, step_type: str
    ) -> None:
        self._emit(lambda: __import__(
            "moya.observability.events", fromlist=["StepStartedEvent"]
        ).StepStartedEvent(
            source=self.name, pipeline_id=pipeline_id, thread_id=thread_id,
            step_name=step_name, step_type=step_type,
        ))

    def _emit_step_completed(
        self, pipeline_id: str, thread_id: str, step_name: str, step_type: str, ms: float
    ) -> None:
        self._emit(lambda: __import__(
            "moya.observability.events", fromlist=["StepCompletedEvent"]
        ).StepCompletedEvent(
            source=self.name, pipeline_id=pipeline_id, thread_id=thread_id,
            step_name=step_name, step_type=step_type, duration_ms=ms,
        ))

    def _emit_step_error(
        self, pipeline_id: str, thread_id: str, step_name: str, step_type: str, error: str
    ) -> None:
        self._emit(lambda: __import__(
            "moya.observability.events", fromlist=["StepErrorEvent"]
        ).StepErrorEvent(
            source=self.name, pipeline_id=pipeline_id, thread_id=thread_id,
            step_name=step_name, step_type=step_type, error=error,
        ))

    def _emit(self, event_factory) -> None:
        if self._event_bus is None:
            return
        try:
            self._event_bus.publish(event_factory())
        except Exception:
            pass
