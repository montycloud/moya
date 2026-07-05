"""
LongTermMemory — persistent, recallable memory for Moya agents.

A :class:`~moya.memory.repository.Repository` that persists conversation
threads to disk (across process restarts and sessions) and adds a lightweight
:meth:`recall` that ranks past messages by keyword overlap and recency. This
models an agent's *long-term* memory: durable history you can search, rather
than just the most recent turns.

Persistence is delegated to :class:`~moya.memory.file_system_repo.FileSystemRepository`
so we don't duplicate the JSON-on-disk logic.

Usage::

    from moya import create_agent
    from moya.memory import LongTermMemory

    memory = LongTermMemory(base_path="./moya_memory")
    agent = create_agent(
        "openai", name="assistant", description="Agent with recall",
        memory=memory,
    )

    # Later — search everything the agent has stored on a thread:
    hits = memory.recall("thread-1", "billing refund", k=3)
"""

import re
from typing import List, Optional, Tuple

from moya.conversation.message import Message
from moya.conversation.thread import Thread
from moya.memory.file_system_repo import FileSystemRepository
from moya.memory.repository import Repository

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> List[str]:
    return _WORD_RE.findall(text.lower())


class LongTermMemory(Repository):
    """
    Disk-backed repository with keyword+recency recall.

    Reads/writes go through an internal FileSystemRepository, so all threads
    survive restarts. :meth:`recall` provides relevance-ranked retrieval over a
    thread's stored messages.
    """

    def __init__(self, base_path: str = "./moya_memory"):
        """
        :param base_path: Directory where thread files are stored. Created if
                          it does not exist.
        """
        self.base_path = base_path
        self._store = FileSystemRepository(base_path)

    # ── Repository interface (delegated to file store) ──────────────────────

    def create_thread(self, thread: Thread) -> None:
        self._store.create_thread(thread)

    def get_thread(self, thread_id: str) -> Optional[Thread]:
        return self._store.get_thread(thread_id)

    def append_message(self, thread_id: str, message: Message) -> None:
        self._store.append_message(thread_id, message)

    def list_threads(self) -> List[str]:
        return self._store.list_threads()

    def delete_thread(self, thread_id: str) -> None:
        self._store.delete_thread(thread_id)

    # ── Role-specific API ───────────────────────────────────────────────────

    def recall(self, thread_id: str, query: str, k: int = 5) -> List[Message]:
        """
        Return up to ``k`` past messages from ``thread_id`` most relevant to
        ``query``, ranked by keyword overlap with a small recency tie-breaker.

        Messages with no keyword overlap are excluded. When ``query`` is empty
        this falls back to the ``k`` most recent messages.
        """
        thread = self._store.get_thread(thread_id)
        if not thread or not thread.messages:
            return []

        messages = thread.messages
        q_tokens = set(_tokens(query))
        if not q_tokens:
            return thread.get_last_n_messages(k)

        n = len(messages)
        scored: List[Tuple[float, int, Message]] = []
        for idx, msg in enumerate(messages):
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            overlap = len(q_tokens & set(_tokens(content)))
            if overlap == 0:
                continue
            # Recency bonus in [0, 1): later messages score slightly higher.
            recency = (idx + 1) / (n + 1)
            scored.append((overlap + recency, idx, msg))

        scored.sort(key=lambda t: t[0], reverse=True)
        return [m for _, _, m in scored[:k]]

    def get_conversation_summary(self, thread_id: str) -> str:
        """Plain-text summary of the full persisted thread."""
        thread = self._store.get_thread(thread_id)
        if not thread:
            return ""
        return "\n".join(f"{m.sender}: {m.content}" for m in thread.messages)
