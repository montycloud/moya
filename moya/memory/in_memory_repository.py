"""
InMemoryRepository for conversation memory in Moya.

A simple implementation of BaseMemoryRepository that stores threads
and messages in a Python dictionary (RAM only).
"""

from typing import Dict, Optional, List
from moya.conversation.thread import Thread
from moya.conversation.message import Message
from moya.memory.base_repository import BaseMemoryRepository


class InMemoryRepository(BaseMemoryRepository):
    """
    Maintains an in-memory dictionary of Thread objects.
    Dictionary Key: thread_id, Value: Thread
    """

    def __init__(self):
        self._threads: Dict[str, Thread] = {}

    def create_thread(self, thread: Thread) -> None:
        """
        Store a new thread. Raises ValueError if a thread with
        the same ID already exists.
        """
        if thread.thread_id in self._threads:
            raise ValueError(f"Thread {thread.thread_id} already exists.")
        self._threads[thread.thread_id] = thread

    def get_thread(self, thread_id: str) -> Optional[Thread]:
        return self._threads.get(thread_id, None)

    def append_message(self, thread_id: str, message: Message) -> None:
        """
        Append a message to an existing thread. Raises ValueError
        if the thread does not exist.
        """
        if thread_id not in self._threads:
            raise ValueError(f"Thread {thread_id} does not exist.")
        self._threads[thread_id].add_message(message)

    def list_threads(self) -> List[str]:
        return list(self._threads.keys())

    def delete_thread(self, thread_id: str) -> None:
        if thread_id in self._threads:
            del self._threads[thread_id]
