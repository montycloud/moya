"""
Message model for Moya.

Represents a single message within a conversation thread.
"""

from datetime import datetime
from typing import Optional
from typing import Dict, Any
from uuid import uuid4


class Message:
    """
    A single message in a conversation thread.
    
    Attributes:
        message_id (str): A unique identifier for this message (optional).
        thread_id (str): The ID of the thread this message belongs to.
        sender (str): The name/identifier of whoever sent the message
                      (e.g., "user", "system", "agent_name").
        content (str): The text content of the message.
        timestamp (datetime): When the message was created.
        metadata (dict): Any additional structured data for this message 
                         (e.g., role info, model parameters, etc.).
    """

    def __init__(
        self,
        thread_id: str,
        sender: str,
        content: str,
        message_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[dict] = None
    ):
        self.message_id = message_id
        if not message_id:
            # Generate a GUID for message ID if not provided
            self.message_id = str(uuid4())
        self.thread_id = thread_id
        self.sender = sender
        self.content = content
        self.timestamp = timestamp or datetime.utcnow()
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        return (
            f"Message("
            f"thread_id={self.thread_id!r}, "
            f"sender={self.sender!r}, "
            f"content={self.content!r}, "
            f"timestamp={self.timestamp.isoformat()!r}, "
            f"message_id={self.message_id!r}, "
            f"metadata={self.metadata!r}"
            f")"
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Message object into a JSON-serializable dictionary.
        """
        return {
            "role": self.sender.lower(),  # Ensure role is lowercase
            "content": [{"type": "text", "text": self.content}],  # Structured content
            "timestamp": self.timestamp.isoformat(),  # Convert datetime to string
            "metadata": self.metadata  # Keep metadata as-is
        }