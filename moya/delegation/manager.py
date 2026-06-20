"""
DelegationManager — route tasks from a parent agent to sub-agents.

Two ways to use delegation:

1. **Programmatic** (from orchestrators or Pipelines): call ``delegate()`` or
   ``delegate_parallel()`` directly from your Python code.

2. **LLM-driven** (from tool-calling agents): call ``setup_tools()`` once to
   register ``list_agents`` and ``delegate_task`` tools into the parent agent's
   ToolRegistry. The LLM then decides *when* and *to whom* to delegate.

Both modes respect a configurable ``max_depth`` to prevent infinite loops.

Usage::

    from moya.delegation import DelegationManager

    manager = DelegationManager(agent_registry, max_depth=3)

    # --- Programmatic ---
    summary = manager.delegate(
        task="Summarise the Q3 earnings report",
        agent_name="summariser_agent",
    )

    # --- Parallel programmatic ---
    results = manager.delegate_parallel([
        ("Analyse the market data",   "market_analyst"),
        ("Analyse the risk exposure", "risk_analyst"),
    ])
    combined = "\\n\\n".join(results)

    # --- LLM-driven ---
    manager.setup_tools(parent_agent_tool_registry)
    # Parent agent can now call list_agents() and delegate_task(task, agent_name)
    # as ordinary tool calls.
"""

import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from typing import Callable, List, Optional, Tuple

from moya.tools.tool import Tool
from moya.tools.tool_registry import ToolRegistry
from moya.delegation.aggregation import aggregate as _aggregate


class MaxDelegationDepthError(Exception):
    """Raised when the delegation chain exceeds ``max_depth``."""


class AgentNotFoundError(Exception):
    """Raised when no matching agent can be found for a delegation request."""


class DelegationManager:
    """
    Routes tasks to sub-agents with depth tracking and parallel dispatch.

    Args:
        agent_registry:  The AgentRegistry to look up agents from.
        max_depth:       Maximum delegation depth (default 5). Prevents runaway
                         recursive delegation.

    Thread safety:
        Depth tracking uses ``threading.local()`` so sequential and parallel
        delegations in different threads each have independent counters.
    """

    def __init__(
        self,
        agent_registry: any,
        max_depth: int = 5,
        event_bus: Optional[any] = None,
    ) -> None:
        self._registry = agent_registry
        self.max_depth = max_depth
        self._local = threading.local()
        self._event_bus = event_bus

    # ------------------------------------------------------------------
    # Programmatic delegation
    # ------------------------------------------------------------------

    def delegate(
        self,
        task: str,
        agent_name: Optional[str] = None,
        skill: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> str:
        """
        Delegate a task to a single agent and return its response.

        Args:
            task:        The task or question to send to the sub-agent.
            agent_name:  Name of the agent to call. Takes priority over ``skill``.
            skill:       If ``agent_name`` is not given, route to any agent that
                         has this skill attached.
            thread_id:   Conversation thread ID passed to the sub-agent.

        Raises:
            MaxDelegationDepthError: if the call chain is deeper than ``max_depth``.
            AgentNotFoundError: if no matching agent is found.
        """
        depth = self._get_depth()
        if depth >= self.max_depth:
            raise MaxDelegationDepthError(
                f"Delegation depth limit ({self.max_depth}) reached. "
                "Possible infinite delegation loop detected."
            )

        agent = self._resolve(agent_name=agent_name, skill=skill)
        if not agent:
            ref = agent_name or f"skill:{skill}"
            raise AgentNotFoundError(f"No agent found for '{ref}'.")

        self._set_depth(depth + 1)
        self._emit_delegation_started(task, agent_name or f"skill:{skill}", depth + 1)
        t0 = time.monotonic()
        try:
            result = agent.handle_message(task, thread_id=thread_id or "delegation")
            self._emit_delegation_completed(task, agent_name or f"skill:{skill}", depth + 1, t0)
            return result
        except Exception as exc:
            self._emit_delegation_error(task, agent_name or f"skill:{skill}", depth + 1, exc)
            raise
        finally:
            self._set_depth(depth)

    def delegate_async(
        self,
        task: str,
        agent_name: Optional[str] = None,
        skill: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> Future:
        """
        Delegate a task non-blocking and return a :class:`concurrent.futures.Future`.

        The caller can call ``future.result()`` to block until the response
        arrives, or attach a callback via ``future.add_done_callback(fn)``.

        Args:
            task:       Task or question to delegate.
            agent_name: Name of the target agent.
            skill:      Route to an agent with this skill (when *agent_name* omitted).
            thread_id:  Conversation thread ID for the sub-agent.

        Returns:
            A :class:`~concurrent.futures.Future` that resolves to the agent's
            response string.
        """
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(
            self.delegate, task, agent_name, skill, thread_id
        )
        executor.shutdown(wait=False)
        return future

    def delegate_parallel(
        self,
        tasks: List[Tuple[str, str]],
        thread_id: Optional[str] = None,
        merge: Optional[Callable[[List[str]], str]] = None,
        aggregation: Optional[str] = None,
    ) -> List[str]:
        """
        Delegate multiple tasks concurrently and return a list of responses.

        Args:
            tasks:      List of ``(task, agent_ref)`` pairs where ``agent_ref``
                        is either an agent name or ``"skill:<skill_name>"``.
            thread_id:  Thread ID passed to every sub-agent call.
            merge:      Optional ``(List[str]) -> str`` to combine results into
                        a single string. When provided, returns a one-element list.

        Returns:
            List of response strings, one per task (in submission order).

        Example::

            results = manager.delegate_parallel([
                ("Summarise topic A",  "agent_a"),
                ("Summarise topic B",  "skill:summarisation"),
            ])
        """
        parent_depth = self._get_depth()
        if parent_depth >= self.max_depth:
            raise MaxDelegationDepthError(
                f"Delegation depth limit ({self.max_depth}) reached."
            )

        def run_task(item: Tuple[str, str]) -> str:
            task, agent_ref = item
            depth = parent_depth + 1
            self._set_depth(depth)
            self._emit_delegation_started(task, agent_ref, depth)
            t0 = time.monotonic()
            try:
                if isinstance(agent_ref, str) and agent_ref.startswith("skill:"):
                    skill_name = agent_ref[len("skill:"):]
                    agent = self._resolve(skill=skill_name)
                else:
                    agent = self._resolve(agent_name=agent_ref)
                if not agent:
                    raise AgentNotFoundError(f"No agent found for '{agent_ref}'.")
                result = agent.handle_message(task, thread_id=thread_id or "delegation")
                self._emit_delegation_completed(task, agent_ref, depth, t0)
                return result
            except Exception as exc:
                self._emit_delegation_error(task, agent_ref, depth, exc)
                raise
            finally:
                self._set_depth(parent_depth)

        results: List[str] = [""] * len(tasks)
        with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
            future_to_idx = {executor.submit(run_task, t): i for i, t in enumerate(tasks)}
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                results[idx] = future.result()

        if aggregation:
            return [_aggregate(results, strategy=aggregation, custom_fn=merge)]
        if merge:
            return [merge(results)]
        return results

    # ------------------------------------------------------------------
    # LLM-driven delegation via tools
    # ------------------------------------------------------------------

    def setup_tools(self, tool_registry: ToolRegistry) -> None:
        """
        Register delegation tools into a ToolRegistry so that a tool-calling
        agent can discover available agents and delegate tasks to them.

        Registers two tools:

        - **list_agents**: Returns the names and descriptions of all registered
          agents. Call this first so the LLM knows what options are available.

        - **delegate_task**: Delegates a task to a named agent and returns its
          response.

        Args:
            tool_registry:  The ToolRegistry attached to the parent agent.

        Example::

            manager = DelegationManager(registry)
            manager.setup_tools(parent_tool_registry)
            # Now add the tool_registry to an is_tool_caller=True agent.
            # The LLM will call list_agents() and delegate_task() as needed.
        """
        manager = self

        def list_agents() -> str:
            """List all available agents and their descriptions.

            Returns a summary of every agent registered in the system,
            including their names and what they are capable of.
            Use this before calling delegate_task to find the right agent.
            """
            infos = manager._registry.list_agents()
            if not infos:
                return "No agents are currently registered."
            lines = [f"- {a.name}: {a.description}" for a in infos]
            return "Available agents:\n" + "\n".join(lines)

        def delegate_task(task: str, agent_name: str) -> str:
            """Delegate a subtask to a specialized agent and return its response.

            Parameters:
            - task: The specific task, question, or instruction to send to the agent.
            - agent_name: The exact name of the agent to delegate to (from list_agents).
            """
            return manager.delegate(task=task, agent_name=agent_name)

        tool_registry.register_tool(Tool(name="list_agents", function=list_agents))
        tool_registry.register_tool(Tool(name="delegate_task", function=delegate_task))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_depth(self) -> int:
        return getattr(self._local, "depth", 0)

    def _set_depth(self, value: int) -> None:
        self._local.depth = value

    def _resolve(self, agent_name: Optional[str] = None, skill: Optional[str] = None):
        """Return the first matching agent, or None."""
        if agent_name:
            return self._registry.get_agent(agent_name)
        if skill:
            agents = self._registry.find_agents_with_skill(skill)
            return agents[0] if agents else None
        return None

    def _emit_delegation_started(self, task: str, target: str, depth: int) -> None:
        if not self._event_bus:
            return
        from moya.observability.events import DelegationStartedEvent
        self._event_bus.publish(
            DelegationStartedEvent(
                source="DelegationManager",
                delegating_to=target,
                task_preview=task[:200],
                depth=depth,
            )
        )

    def _emit_delegation_completed(
        self, task: str, target: str, depth: int, t0: float
    ) -> None:
        if not self._event_bus:
            return
        from moya.observability.events import DelegationCompletedEvent
        self._event_bus.publish(
            DelegationCompletedEvent(
                source="DelegationManager",
                delegating_to=target,
                task_preview=task[:200],
                depth=depth,
                duration_ms=(time.monotonic() - t0) * 1000,
            )
        )

    def _emit_delegation_error(
        self, task: str, target: str, depth: int, exc: Exception
    ) -> None:
        if not self._event_bus:
            return
        from moya.observability.events import DelegationErrorEvent
        self._event_bus.publish(
            DelegationErrorEvent(
                source="DelegationManager",
                delegating_to=target,
                task_preview=task[:200],
                depth=depth,
                error=str(exc),
            )
        )
