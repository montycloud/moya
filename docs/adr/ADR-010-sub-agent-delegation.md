# ADR-010: Sub-Agent Delegation Architecture

**Status:** Accepted  
**Date:** 2026-05-04  
**Deciders:** Karthik Vaidhyanathan

---

## Context

MOYA has no first-class mechanism for one agent to delegate a sub-task to another agent and receive its result. The existing ReAct orchestrator approximates this, but it is a hard-coded iteration loop rather than a composable primitive.

The Sub-Agents capability needs to support:
- **Synchronous delegation**: parent agent blocks until sub-agent completes.
- **Parallel delegation**: parent dispatches multiple sub-tasks concurrently.
- **Dynamic spawning**: sub-agent instances created on-demand from a template.
- **Context inheritance**: sub-agent receives scoped parent context.
- **Recursion guard**: bounded delegation depth.
- **Streaming**: sub-agent tokens forwarded to end user in real time.

The mechanism must be transparent to orchestrators and must not require agents to import each other directly (avoids tight coupling).

---

## Decision

**Implement sub-agent delegation via three components: `DelegationContext` (data object injected into agents), a `Delegatable` mixin (adds `delegate()` method to agents), and `DelegationManager` (singleton that handles routing, depth tracking, context scoping, and spawning).**

---

## Core Abstractions

### DelegationContext

Passed into `handle_message()` as a keyword argument. Agents that want to delegate must accept it; agents that don't can ignore it (backward compatible).

```python
@dataclass
class DelegationContext:
    parent_task_id: str
    depth: int                              # current delegation depth
    max_depth: int                          # configurable; default 5
    thread_id: str
    inherited_context: List[Message]        # scoped parent history
    stream_callback: Optional[Callable]
    manager: "DelegationManager"            # back-reference for delegate() call
```

### DelegationManager

```python
class DelegationManager:
    def __init__(self, agent_registry: AgentRegistry,
                 max_depth: int = 5,
                 context_scope: ContextScopeStrategy = LastNMessages(n=10)):
        ...

    async def delegate(
        self,
        task: str,
        agent_name: Optional[str] = None,
        skill: Optional[str] = None,
        parent_ctx: DelegationContext
    ) -> str:
        if parent_ctx.depth >= parent_ctx.max_depth:
            raise MaxDelegationDepthExceeded(parent_ctx.depth)

        target_agent = self._resolve_target(agent_name, skill)
        child_ctx = self._create_child_context(parent_ctx, task)

        self._emit_event(DelegationEvent(
            event_type="delegated",
            parent_task_id=parent_ctx.parent_task_id,
            child_task_id=child_ctx.parent_task_id,
            target_agent=target_agent.agent_name,
            depth=child_ctx.depth
        ))

        return await target_agent.handle_message_async(task, delegation_ctx=child_ctx)

    async def delegate_parallel(
        self,
        tasks: List[Tuple[str, str]],   # [(task, agent_name_or_skill), ...]
        parent_ctx: DelegationContext,
        aggregation: AggregationStrategy = ConcatenateAggregation()
    ) -> str:
        results = await asyncio.gather(*[
            self.delegate(task, agent_name_or_skill, parent_ctx=parent_ctx)
            for task, agent_name_or_skill in tasks
        ])
        return aggregation.aggregate(results)
```

### Delegatable Mixin

```python
class Delegatable:
    """Mixin that adds delegate() to any Agent subclass."""

    def delegate(self, task: str, agent_name: Optional[str] = None,
                 skill: Optional[str] = None) -> str:
        if not hasattr(self, "_delegation_ctx") or self._delegation_ctx is None:
            raise DelegationNotAvailableError(
                "delegate() called outside a DelegationContext. "
                "Ensure this agent is invoked via DelegationManager."
            )
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self._delegation_ctx.manager.delegate(
                task, agent_name=agent_name, skill=skill,
                parent_ctx=self._delegation_ctx
            )
        )

    def delegate_parallel(self, tasks: List[Tuple[str, str]]) -> str:
        ...  # similar pattern
```

Agents that want delegation capability: `class MyAgent(OpenAIAgent, Delegatable)`.

---

## Context Inheritance

`DelegationManager` uses a `ContextScopeStrategy` to determine what history a sub-agent receives from the parent:

```python
class ContextScopeStrategy(ABC):
    @abstractmethod
    def scope(self, parent_history: List[Message]) -> List[Message]: ...

class LastNMessages(ContextScopeStrategy):
    def __init__(self, n: int): self._n = n
    def scope(self, history): return history[-self._n:]

class FullHistory(ContextScopeStrategy):
    def scope(self, history): return history

class SummaryOnly(ContextScopeStrategy):
    def __init__(self, summarizer_agent): ...
    def scope(self, history): return [summarizer_agent.summarize(history)]
```

---

## Dynamic Agent Spawning

When an agent name or skill is requested but no registered agent matches, `DelegationManager` can spawn a new agent from a registered template:

```python
class AgentTemplate:
    template_name: str
    agent_class: Type[Agent]
    base_config: AgentConfig
```

Templates are registered in `AgentRegistry`. The manager instantiates, uses, and optionally caches or discards the spawned agent based on a TTL policy.

---

## Aggregation Strategies

```python
class AggregationStrategy(ABC):
    @abstractmethod
    def aggregate(self, results: List[str]) -> str: ...

class ConcatenateAggregation(AggregationStrategy):
    def aggregate(self, results): return "\n\n".join(results)

class LLMSynthesisAggregation(AggregationStrategy):
    def __init__(self, synthesizer_agent: Agent): ...
    def aggregate(self, results): ...  # calls synthesizer LLM

class StructuredMergeAggregation(AggregationStrategy):
    def __init__(self, output_schema: Type): ...
    def aggregate(self, results): ...  # validates + merges Pydantic models
```

---

## Recursion Guard

`DelegationManager` raises `MaxDelegationDepthExceeded` when `depth >= max_depth`. The default `max_depth=5` is configurable at `DelegationManager` construction. The error carries the full delegation trace (list of agent names and task summaries) for debugging.

---

## Observability

`DelegationManager` emits `DelegationEvent` records into the `FlowContext.events` list (if a `FlowContext` is available) and also calls any registered `EventListener`. Events include:

- `delegated`: task handed off to sub-agent
- `sub_task_completed`: sub-agent returned result
- `sub_task_failed`: sub-agent raised an exception
- `depth_exceeded`: recursion guard triggered

---

## Streaming Through Delegation

When `parent_ctx.stream_callback` is set, `DelegationManager` passes it into the child `DelegationContext`. The sub-agent's `handle_message_stream()` is called instead of `handle_message()`, and chunks are forwarded to the end user via the callback as they are produced.

---

## Backward Compatibility

- Existing agents do not need to change — they simply never receive a `DelegationContext` argument.
- Existing orchestrators work unchanged.
- Adding `Delegatable` to an existing agent is an opt-in change.
- `DelegationManager` is not a singleton in the strict sense — it is instantiated and passed to the orchestrator or pipeline that needs it. Tests can create independent instances.

---

## Alternatives Considered

**Delegation as a tool registered in the ToolRegistry:** The LLM calls `delegate(task, agent)` like any other tool. Simpler wiring but the LLM must know agent names ahead of time, and the delegation path goes through the tool-calling loop rather than MOYA's routing logic. Rejected — too much LLM control over infrastructure concerns.

**Event-driven delegation (message bus):** Agents emit delegation events; a bus routes them. Decoupled but adds significant complexity (ordering, back-pressure, error propagation across async boundaries). Rejected for Phase 2 scope.

**Extend ReActOrchestrator to be the delegation layer:** ReAct is already an approximation. Formalising it as the delegation primitive would conflate thought/action reasoning with sub-task delegation. Rejected — keep them separate.

---

## Consequences

- New `moya/delegation/` package: `DelegationManager`, `DelegationContext`, `Delegatable`, aggregation strategies, context scope strategies.
- No changes to `Agent` base class — `Delegatable` is an opt-in mixin.
- `AgentRegistry` gains `AgentTemplate` registration (small additive change).
- The async design means delegation-heavy code runs best in async contexts. The sync `delegate()` wrapper on `Delegatable` is a convenience for blocking contexts.
- Circular delegation (agent A delegates to B which delegates back to A) is caught by the depth guard — it does not detect true cycles without full call-graph tracking. This is an accepted limitation for Phase 2.
