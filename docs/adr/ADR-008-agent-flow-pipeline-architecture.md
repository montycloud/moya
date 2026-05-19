# ADR-008: Agent Flow / Pipeline Architecture

**Status:** Accepted  
**Date:** 2026-05-04  
**Deciders:** Karthik Vaidhyanathan

---

## Context

MOYA has no declarative way to compose multi-step agent workflows. Orchestrators (Simple, MultiAgent, ReAct) are hard-coded routing strategies — not general composable primitives. Users who need a sequential pipeline (pre-process → agent A → post-process → agent B → synthesise) must write a custom orchestrator or build an external loop.

Requirements (§2.1) call for: sequential steps, parallel fan-out, conditional branching, loops, typed data contracts, composability (pipeline as a step), streaming, and observability events — all without breaking existing orchestrators.

---

## Decision

**Introduce a `moya/flows/` package built around three core concepts: `Step` (protocol), `Pipeline` (composable step container), and `FlowContext` (data carrier with events). Existing orchestrators are unaffected; they can be wrapped as steps if needed.**

---

## Core Abstractions

### Step Protocol

A `Step` is anything that conforms to:

```python
class Step(Protocol):
    name: str
    input_schema: Optional[Type]   # Pydantic model or None
    output_schema: Optional[Type]  # Pydantic model or None

    async def run(self, ctx: FlowContext) -> FlowContext:
        """Consume ctx.current_output, produce new ctx.current_output."""
```

Because `Step` is a `Protocol` (structural typing), any callable class with a `run` method and a `name` attribute is automatically a valid step. MOYA agents, pipelines, and user functions all qualify.

### FlowContext

```python
@dataclass
class FlowContext:
    thread_id: str
    current_output: Any            # carries data between steps
    metadata: Dict[str, Any]       # arbitrary step-to-step annotations
    events: List[FlowEvent]        # append-only event log
    stream_callback: Optional[Callable[[str], None]]
```

Steps read from and write to `current_output`. The event log accumulates `FlowEvent` records for observability.

### FlowEvent

```python
@dataclass
class FlowEvent:
    step_name: str
    event_type: str   # "start" | "complete" | "error" | "retry"
    timestamp: float
    data: Optional[Any]
```

### Pipeline

```python
class Pipeline:
    def __init__(self, steps: List[Step], name: str = "pipeline"):
        ...

    async def run(self, ctx: FlowContext) -> FlowContext:
        for step in self._steps:
            ctx = await step.run(ctx)
        return ctx
```

`Pipeline` implements the `Step` protocol — it has `name`, `input_schema`, `output_schema`, and `run()`. Therefore a `Pipeline` is composable inside another `Pipeline`.

---

## Built-in Step Types

### AgentStep

Wraps a MOYA agent as a step. Calls `agent.handle_message(ctx.current_output)` and writes the response back to `ctx.current_output`.

### ParallelStep

```python
class ParallelStep:
    def __init__(self, steps: List[Step], merge: MergeStrategy):
        ...

    async def run(self, ctx: FlowContext) -> FlowContext:
        results = await asyncio.gather(*[step.run(copy(ctx)) for step in self._steps])
        ctx.current_output = self._merge(results)
        return ctx
```

`MergeStrategy` is a callable `(List[FlowContext]) -> Any`. Built-in strategies: `ConcatenateMerge`, `FirstMerge`, `DictMerge` (for structured outputs).

### BranchStep

```python
class BranchStep:
    def __init__(self, selector: Callable[[FlowContext], str],
                 branches: Dict[str, Step]):
        ...

    async def run(self, ctx: FlowContext) -> FlowContext:
        branch_key = self._selector(ctx)
        return await self._branches[branch_key].run(ctx)
```

The `selector` can be a pure function or an LLM-backed classifier.

### LoopStep

```python
class LoopStep:
    def __init__(self, step: Step, until: Callable[[FlowContext], bool],
                 max_iterations: int = 10):
        ...

    async def run(self, ctx: FlowContext) -> FlowContext:
        for _ in range(self._max_iterations):
            ctx = await self._step.run(ctx)
            if self._until(ctx):
                break
        return ctx
```

### FunctionStep

Wraps a plain `async def f(ctx: FlowContext) -> FlowContext` for lightweight transforms without creating a full class.

---

## Data Validation

When a step declares non-None `input_schema` / `output_schema`, the pipeline validates `ctx.current_output` against that schema before/after the step using Pydantic's `model_validate`. Validation mode is configurable per-pipeline: `strict` (raises `StepValidationError`) or `permissive` (emits a warning event and continues).

---

## Fluent Builder API

```python
from moya.flows import FlowBuilder

flow = (
    FlowBuilder("research_pipeline")
    .then(AgentStep(retrieval_agent))
    .parallel([AgentStep(analyst_a), AgentStep(analyst_b)], merge=ConcatenateMerge())
    .branch(lambda ctx: "en" if "english" in ctx.metadata else "es",
            branches={"en": AgentStep(english_writer), "es": AgentStep(spanish_writer)})
    .then(AgentStep(editor_agent))
    .build()
)
result_ctx = await flow.run(FlowContext(thread_id="t1", current_output=user_input))
```

---

## Streaming

Each `AgentStep` checks for `ctx.stream_callback`. If set, it calls `agent.handle_message_stream()` and invokes the callback for each chunk. Streamed chunks are also accumulated into `current_output` so downstream steps receive the full text.

---

## Relationship to Existing Orchestrators

Existing `Orchestrator` subclasses are not changed. For users who want to embed an orchestrator in a pipeline, a `OrchestratorStep` adapter is provided:

```python
class OrchestratorStep:
    def __init__(self, orchestrator: Orchestrator):
        self.name = orchestrator.__class__.__name__
    async def run(self, ctx):
        ctx.current_output = orchestrator.orchestrate(ctx.thread_id, ctx.current_output)
        return ctx
```

---

## Alternatives Considered

**Extend existing `Orchestrator` base class with pipeline methods:** Mixes routing logic with flow logic in one class hierarchy. Harder to test and reason about. Rejected.

**Use an external workflow library (Prefect, Airflow, Temporal):** Overkill for in-process agent pipelines; adds infrastructure dependencies. These are deployment-level schedulers, not in-process composables. Rejected.

**LangChain-style chain pattern:** Similar concept but LangChain's chains are tightly coupled to its LCEL evaluation model. MOYA's `Step` protocol is simpler and framework-agnostic. Rejected for dependency reasons.

---

## Consequences

- New `moya/flows/` package with no external dependencies.
- All existing orchestrators continue to work unchanged.
- Async-first design (`async def run`) means pipelines must be run inside an event loop. Sync wrappers (`Pipeline.run_sync()`) will be provided for REPL and script usage.
- The `FlowEvent` log provides built-in observability without requiring external tracing setup.
