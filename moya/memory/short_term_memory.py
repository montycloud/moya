"""
ShortTermMemory — recent, windowed conversation memory for Moya agents.

A :class:`~moya.memory.repository.Repository` that keeps only the most recent
``window_size`` messages per thread in RAM. This models an agent's *working*
memory: enough recent context to stay coherent, without the footprint (or
distraction) of the full history.

Usage::

    from moya import create_agent
    from moya.memory import ShortTermMemory

    agent = create_agent(
        "openai", name="chat", description="Windowed chat agent",
        memory=ShortTermMemory(window_size=10),
    )
"""

from typing import Dict, List, Optional

from moya.conversation.message import Message
from moya.conversation.thread import Thread
from moya.memory.repository import Repository


class ShortTermMemory(Repository):
    """
    In-memory repository that retains only the last ``window_size`` messages
    per thread. Appending beyond the window silently drops the oldest messages.
    """

    def __init__(self, window_size: int = 10):
        """
        :param window_size: Maximum number of messages retained per thread.
                            Must be >= 1.
        """
        if window_size < 1:
            raise ValueError("window_size must be >= 1")
        self.window_size = window_size
        self._threads: Dict[str, Thread] = {}

    def create_thread(self, thread: Thread) -> None:
        if thread.thread_id in self._threads:
            raise ValueError(f"Thread {thread.thread_id} already exists.")
        self._threads[thread.thread_id] = thread
        self._trim(thread.thread_id)

    def get_thread(self, thread_id: str) -> Optional[Thread]:
        return self._threads.get(thread_id, None)

    def append_message(self, thread_id: str, message: Message) -> None:
        if thread_id not in self._threads:
            raise ValueError(f"Thread {thread_id} does not exist.")
        self._threads[thread_id].add_message(message)
        self._trim(thread_id)

    def list_threads(self) -> List[str]:
        return list(self._threads.keys())

    def delete_thread(self, thread_id: str) -> None:
        self._threads.pop(thread_id, None)

    # ── Convenience / role-specific API ─────────────────────────────────────

    def recent(self, thread_id: str, n: Optional[int] = None) -> List[Message]:
        """
        Return the most recent ``n`` messages (defaults to the full window).
        """
        thread = self._threads.get(thread_id)
        if not thread:
            return []
        return thread.get_last_n_messages(n or self.window_size)

    def get_conversation_summary(self, thread_id: str) -> str:
        """Plain-text summary of the retained (windowed) messages."""
        thread = self._threads.get(thread_id)
        if not thread:
            return ""
        return "\n".join(f"{m.sender}: {m.content}" for m in thread.messages)

    # ── Internal ────────────────────────────────────────────────────────────

    def _trim(self, thread_id: str) -> None:
        """Drop oldest messages so the thread holds at most ``window_size``."""
        thread = self._threads.get(thread_id)
        if thread and len(thread.messages) > self.window_size:
            thread.messages = thread.messages[-self.window_size:]
