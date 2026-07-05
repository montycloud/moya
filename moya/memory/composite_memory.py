"""
CompositeMemory — combine several memory types into one agent memory.

A :class:`~moya.memory.repository.Repository` that wraps an ordered list of
other repositories. This lets a single agent hold, say, a short-term working
window *and* a persistent long-term store at the same time:

    from moya import create_agent
    from moya.memory import ShortTermMemory, LongTermMemory, CompositeMemory

    memory = CompositeMemory([
        LongTermMemory(base_path="./moya_memory"),  # primary — full history
        ShortTermMemory(window_size=10),            # working window
    ])
    agent = create_agent("openai", name="a", description="d", memory=memory)

Semantics:
- **Writes** (``create_thread`` / ``append_message`` / ``delete_thread``) fan
  out to *every* backing store.
- **Reads** (``get_thread`` / ``list_threads`` / ``get_conversation_summary``)
  come from the **primary** store — the first one in the list. Order long-term
  first so reads see the complete history while short-term still caps its own
  footprint.

Because every store receives identical appends, reads need no de-duplication.
Writes are defensive: if a store is missing the thread (e.g. a long-term store
that persisted it in a previous session, paired with a fresh short-term store),
the thread is created there before appending.
"""

from typing import List, Optional

from moya.conversation.message import Message
from moya.conversation.thread import Thread
from moya.memory.repository import Repository


class CompositeMemory(Repository):
    """Fan-out writes to all backing repositories; read from the primary."""

    def __init__(self, memories: List[Repository]):
        """
        :param memories: Ordered, non-empty list of repositories. The first is
                        the *primary* used for reads.
        """
        if not memories:
            raise ValueError("CompositeMemory requires at least one repository.")
        self.memories = memories

    @property
    def primary(self) -> Repository:
        return self.memories[0]

    # ── Writes: fan out to every store ──────────────────────────────────────

    def create_thread(self, thread: Thread) -> None:
        for mem in self.memories:
            self._ensure_thread(mem, thread.thread_id, thread)

    def append_message(self, thread_id: str, message: Message) -> None:
        for mem in self.memories:
            self._ensure_thread(mem, thread_id)
            mem.append_message(thread_id, message)

    def delete_thread(self, thread_id: str) -> None:
        for mem in self.memories:
            mem.delete_thread(thread_id)

    # ── Reads: from the primary store ───────────────────────────────────────

    def get_thread(self, thread_id: str) -> Optional[Thread]:
        return self.primary.get_thread(thread_id)

    def list_threads(self) -> List[str]:
        return self.primary.list_threads()

    def get_conversation_summary(self, thread_id: str) -> str:
        summariser = getattr(self.primary, "get_conversation_summary", None)
        if callable(summariser):
            return summariser(thread_id)
        thread = self.primary.get_thread(thread_id)
        if not thread:
            return ""
        return "\n".join(f"{m.sender}: {m.content}" for m in thread.messages)

    def recall(self, thread_id: str, query: str, k: int = 5) -> List[Message]:
        """
        Delegate to the first backing store that supports ``recall`` (typically
        a :class:`~moya.memory.long_term_memory.LongTermMemory`). Returns an
        empty list if none do.
        """
        for mem in self.memories:
            recaller = getattr(mem, "recall", None)
            if callable(recaller):
                return recaller(thread_id, query, k)
        return []

    # ── Internal ────────────────────────────────────────────────────────────

    @staticmethod
    def _ensure_thread(
        mem: Repository, thread_id: str, thread: Optional[Thread] = None
    ) -> None:
        """Create the thread in ``mem`` if it isn't already there."""
        if mem.get_thread(thread_id) is not None:
            return
        try:
            mem.create_thread(thread or Thread(thread_id=thread_id))
        except ValueError:
            # Raced with another create / already exists — safe to ignore.
            pass
