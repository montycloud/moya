"""
EphemeralMemory — lightweight in-process conversation memory.

Provides store / retrieve / summarise operations over a Repository.

Two usage styles:

1. **Instance** (recommended — each agent or orchestrator gets its own memory)::

       from moya.tools.ephemeral_memory import EphemeralMemory
       from moya.memory.in_memory_repository import InMemoryRepository

       mem = EphemeralMemory(InMemoryRepository())
       mem.store_message("thread1", "user", "Hello")
       print(mem.get_last_n_messages("thread1"))

2. **Static / legacy** (shared global store — kept for backward compatibility)::

       EphemeralMemory.store_message("thread1", "user", "Hello")
"""

import json
from typing import Optional

from moya.conversation.message import Message
from moya.conversation.thread import Thread
from moya.memory.in_memory_repository import InMemoryRepository
from moya.tools.tool import Tool
from moya.tools.tool_registry import ToolRegistry


class EphemeralMemory:
    """
    Lightweight memory wrapper that exposes store / retrieve / summarise
    as both instance methods and (for backward compatibility) static methods.
    """

    # Shared repository used only by the static API
    _global_repository: Optional[InMemoryRepository] = None

    def __init__(self, repository=None):
        """
        Create an EphemeralMemory backed by the given repository.

        :param repository: Any Repository implementation. Defaults to a new
                           InMemoryRepository private to this instance.
        """
        self._repository = repository or InMemoryRepository()

    # ------------------------------------------------------------------
    # Instance API
    # ------------------------------------------------------------------

    def store_message(
        self,
        thread_id: str,
        sender: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> str:
        """Store a message, creating the thread on first use."""
        return _store(self._repository, thread_id, sender, content, metadata)

    def get_last_n_messages(self, thread_id: str, n: int = 5) -> str:
        """Return the last *n* messages as a JSON string."""
        return _get_last_n(self._repository, thread_id, n)

    def get_thread_summary(self, thread_id: str) -> str:
        """Return a naive bullet-point summary of the thread."""
        return _summarise(self._repository, thread_id)

    def configure_memory_tools(self, tool_registry: ToolRegistry) -> None:
        """Register store / retrieve / summarise as callable tools."""
        mem = self
        tool_registry.register_tool(Tool(name="store_message",    function=mem.store_message))
        tool_registry.register_tool(Tool(name="get_last_n",       function=mem.get_last_n_messages))
        tool_registry.register_tool(Tool(name="get_summary",      function=mem.get_thread_summary))

    # ------------------------------------------------------------------
    # Static / legacy API (shared global repository)
    # ------------------------------------------------------------------

    @classmethod
    def _global_repo(cls) -> InMemoryRepository:
        if cls._global_repository is None:
            cls._global_repository = InMemoryRepository()
        return cls._global_repository

    @staticmethod
    def store_message_static(
        thread_id: str,
        sender: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> str:
        return _store(EphemeralMemory._global_repo(), thread_id, sender, content, metadata)

    @staticmethod
    def get_last_n_messages_static(thread_id: str, n: int = 5) -> str:
        return _get_last_n(EphemeralMemory._global_repo(), thread_id, n)

    @staticmethod
    def get_thread_summary_static(thread_id: str) -> str:
        return _summarise(EphemeralMemory._global_repo(), thread_id)

    @staticmethod
    def configure_memory_tools(tool_registry: ToolRegistry) -> None:  # type: ignore[override]
        """Register global-memory tools into the given registry (legacy helper)."""
        tool_registry.register_tool(
            Tool(name="store_message", function=EphemeralMemory.store_message_static)
        )
        tool_registry.register_tool(
            Tool(name="get_last_n", function=EphemeralMemory.get_last_n_messages_static)
        )
        tool_registry.register_tool(
            Tool(name="get_summary", function=EphemeralMemory.get_thread_summary_static)
        )


# ------------------------------------------------------------------
# Private helpers shared by both APIs
# ------------------------------------------------------------------

def _store(
    repo: InMemoryRepository,
    thread_id: str,
    sender: str,
    content: str,
    metadata: Optional[dict],
) -> str:
    if repo.get_thread(thread_id) is None:
        repo.create_thread(Thread(thread_id=thread_id))
    repo.append_message(
        thread_id,
        Message(thread_id=thread_id, sender=sender, content=content, metadata=metadata),
    )
    return f"Message stored in thread '{thread_id}'."


def _get_last_n(repo: InMemoryRepository, thread_id: str, n: int) -> str:
    thread = repo.get_thread(thread_id)
    messages = thread.get_last_n_messages(n) if thread else []
    return json.dumps([m.to_dict() for m in messages])


def _summarise(repo: InMemoryRepository, thread_id: str) -> str:
    thread = repo.get_thread(thread_id)
    if not thread:
        return ""
    lines = [f"{m.sender}: {m.content}" for m in thread.messages]
    return f"Summary of thread '{thread_id}':\n" + "\n".join(lines)
