"""
MemoryTool for Moya.

A tool that interacts with a BaseMemoryRepository to store and retrieve
conversation data (threads, messages).
"""

from typing import Optional, List
from moya.tools.base_tool import BaseTool
from moya.memory.base_repository import BaseMemoryRepository
from moya.conversation.thread import Thread
from moya.conversation.message import Message


class MemoryTool(BaseTool):
    """
    Provides conversation memory operations, including:
      - Storing messages to a thread,
      - Retrieving the last N messages,
      - Generating a naive thread summary.

    In a production environment, you could augment summarization with an LLM or
    custom logic for concise conversation overviews.
    """

    def __init__(
        self,
        memory_repository: BaseMemoryRepository,
        name: str = "MemoryTool",
        description: str = "Tool to store and retrieve conversation messages."
    ):
        super().__init__(name=name, description=description)
        self.memory_repository = memory_repository

    def store_message(
        self,
        thread_id: str,
        sender: str,
        content: str,
        metadata: Optional[dict] = None
    ) -> None:
        """
        Store a message in the specified thread. If the thread doesn't exist,
        we create it. This approach ensures ad-hoc threads can be formed dynamically.
        """
        existing_thread = self.memory_repository.get_thread(thread_id)
        if not existing_thread:
            # Create the thread on the fly if it doesn't exist
            new_thread = Thread(thread_id=thread_id)
            self.memory_repository.create_thread(new_thread)

        message = Message(
            thread_id=thread_id,
            sender=sender,
            content=content,
            metadata=metadata
        )
        self.memory_repository.append_message(thread_id, message)

    def get_last_n_messages(self, thread_id: str, n: int = 5) -> List[Message]:
        """
        Retrieve the last N messages from the specified thread.
        """
        thread = self.memory_repository.get_thread(thread_id)
        if not thread:
            return []
        return thread.get_last_n_messages(n=n)

    def get_thread_summary(self, thread_id: str) -> str:
        """
        A naive summary of the conversation so far. In this simplistic implementation,
        we concatenate the messages. You could:
          - Summarize with an LLM,
          - Keep track of running conversation state,
          - Use custom logic or heuristics.
        """
        thread = self.memory_repository.get_thread(thread_id)
        if not thread:
            return ""

        # For demonstration, we'll just build a naive bullet-point summary
        lines = []
        for msg in thread.messages:
            lines.append(f"{msg.sender} said: {msg.content}")

        summary = "\n".join(lines)
        return f"Summary of thread {thread_id}:\n{summary}"
