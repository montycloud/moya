"""
MoyaAgentExecutor — bridges the A2A AgentExecutor interface to a Moya Agent.

The A2A SDK calls ``execute()`` (async) when a task arrives. This class
runs the Moya agent's synchronous ``handle_message()`` in a thread-pool
executor so it does not block the asyncio event loop, then enqueues the
appropriate task-state events back to the caller.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.helpers.proto_helpers import new_text_status_update_event
from a2a.types import Task, TaskState, TaskStatus

if TYPE_CHECKING:
    from moya.agents.agent import Agent


class MoyaAgentExecutor(AgentExecutor):
    """
    Wraps a Moya ``Agent`` as an A2A ``AgentExecutor``.

    On each ``execute()`` call the executor:
    1. Emits ``TASK_STATE_WORKING`` to signal processing has started.
    2. Calls the Moya agent's ``handle_message()`` in a thread (non-blocking).
    3. Emits ``TASK_STATE_COMPLETED`` with the response text on success.
    4. Emits ``TASK_STATE_FAILED`` with the error message on exception.
    """

    def __init__(self, agent: "Agent") -> None:
        self._agent = agent

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task_id = context.task_id
        context_id = context.context_id or "a2a-session"
        user_text = context.get_user_input()

        # V2 SDK requires a Task object first, before any TaskStatusUpdateEvent
        await event_queue.enqueue_event(
            Task(
                id=task_id,
                context_id=context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_WORKING),
            )
        )

        loop = asyncio.get_event_loop()
        try:
            response: str = await loop.run_in_executor(
                None,
                lambda: self._agent.handle_message(user_text, thread_id=context_id),
            )
            await event_queue.enqueue_event(
                new_text_status_update_event(
                    task_id=task_id,
                    context_id=context_id,
                    state=TaskState.TASK_STATE_COMPLETED,
                    text=response,
                )
            )
        except Exception as exc:
            await event_queue.enqueue_event(
                new_text_status_update_event(
                    task_id=task_id,
                    context_id=context_id,
                    state=TaskState.TASK_STATE_FAILED,
                    text=str(exc),
                )
            )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await event_queue.enqueue_event(
            new_text_status_update_event(
                task_id=context.task_id,
                context_id=context.context_id or "a2a-session",
                state=TaskState.TASK_STATE_CANCELED,
                text="Task cancelled.",
            )
        )
