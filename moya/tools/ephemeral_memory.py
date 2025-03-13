"""
MemoryTool for Moya.

A tool that interacts with a BaseMemoryRepository to store and retrieve
conversation data (threads, messages).
"""

from typing import Optional, List
from moya.tools.tool_registry import ToolRegistry
from moya.tools.base_tool import BaseTool
from moya.memory.in_memory_repository import InMemoryRepository
from moya.conversation.thread import Thread
from moya.conversation.message import Message


class EphemeralMemory:
    """
    Provides conversation memory operations, including:
      - Storing messages to a thread,
      - Retrieving the last N messages,
      - Generating a naive thread summary.

    In a production environment, you could augment summarization with an LLM or
    custom logic for concise conversation overviews.
    """

    memory_repository = InMemoryRepository()

    @staticmethod
    def store_message(
        thread_id: str,
        sender: str,
        content: str,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Store a message in the specified thread. If the thread doesn't exist,
        we create it. 

        Parameters:
            - thread_id: Unique identifier for the conversation thread.
            - sender: Sender of the message (e.g., 'user', 'agent').
            - content: The message content.
            - metadata: Optional metadata dictionary.
        """
        existing_thread = EphemeralMemory.memory_repository.get_thread(thread_id)
        if not existing_thread:
            # Create the thread on the fly if it doesn't exist
            new_thread = Thread(thread_id=thread_id)
            EphemeralMemory.memory_repository.create_thread(new_thread)

        message = Message(
            thread_id=thread_id,
            sender=sender,
            content=content,
            metadata=metadata
        )
        EphemeralMemory.memory_repository.append_message(thread_id, message)
        return f"Message stored in thread {thread_id}."

    @staticmethod
    def get_last_n_messages(thread_id: str, n: int = 5) -> List[Message]:
        """
        Retrieve the last N messages from the specified thread.

        Parameters:
            - thread_id: Unique identifier for the conversation thread.
            - n: Number of messages to retrieve (default: 5).
        """
        thread = EphemeralMemory.memory_repository.get_thread(thread_id)
        if not thread:
            return []
        return thread.get_last_n_messages(n=n)

    @staticmethod
    def get_thread_summary(thread_id: str) -> str:
        """
        A naive summary of the conversation so far. In this simplistic implementation,
        we simply concatenate the messages in the thread. 

        Parameters:
            - thread_id: Unique identifier for the conversation thread.
        """
        thread = EphemeralMemory.memory_repository.get_thread(thread_id)
        if not thread:
            return ""

        # For demonstration, we'll just build a naive bullet-point summary
        lines = []
        for msg in thread.messages:
            lines.append(f"{msg.sender} said: {msg.content}")

        summary = "\n".join(lines)
        return f"Summary of thread {thread_id}:\n{summary}"

    @staticmethod
    def configure_memory_tools(tool_registry: ToolRegistry) -> None:
        """
        Register the MemoryTool with the tool registry.

        Parameters:
            - tool_registry: The tool registry to register the MemoryTool with.
        """
        tool_registry.register_tool(BaseTool(name="Store", function = EphemeralMemory.store_message))
        tool_registry.register_tool(BaseTool(name="get_last_n", function=EphemeralMemory.get_last_n_messages))
        tool_registry.register_tool(BaseTool(name="get_summary", function=EphemeralMemory.get_thread_summary))
