"""
Thread model for Moya.

Represents a conversation thread which consists of multiple messages.
"""

from typing import List, Optional
from datetime import datetime
from moya.conversation.message import Message


class Thread:
    """
    A conversation thread that holds a sequence of messages.

    Attributes:
        thread_id (str): The unique identifier for this conversation thread.
        created_at (datetime): When the thread was created.
        messages (List[Message]): The list of messages in this thread.
        participants (List[str]): Optionally, keep track of participants (e.g., user IDs, agent names).
        metadata (dict): Any additional info or context about this thread.
    """

    def __init__(
        self,
        thread_id: str,
        participants: Optional[List[str]] = None,
        metadata: Optional[dict] = None
    ):
        self.thread_id = thread_id
        self.created_at = datetime.utcnow()
        self.messages: List[Message] = []
        self.participants = participants or []
        self.metadata = metadata or {}

    def add_message(self, message: Message) -> None:
        """
        Append a new message to this thread. The message must
        have a matching thread_id.
        """
        if message.thread_id != self.thread_id:
            raise ValueError(
                f"Message thread_id {message.thread_id} does not match "
                f"this Thread's thread_id {self.thread_id}."
            )
        self.messages.append(message)

    def get_messages(self) -> List[Message]:
        """
        Return the list of messages in this thread.
        """
        return self.messages

    def get_last_n_messages(self, n: int = 5) -> List[Message]:
        """
        Return the last n messages from this thread.
        """
        return self.messages[-n:] if len(self.messages) >= n else self.messages

    def __repr__(self) -> str:
        return (
            f"Thread("
            f"thread_id={self.thread_id!r}, "
            f"created_at={self.created_at.isoformat()!r}, "
            f"messages={len(self.messages)}, "
            f"participants={self.participants!r}, "
            f"metadata={self.metadata!r}"
            f")"
        )
