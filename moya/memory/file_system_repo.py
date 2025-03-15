"""
FileSystemRepository for conversation memory in Moya.

An implementation of BaseMemoryRepository that stores threads
as JSON files and messages as JSON lines within those files.
"""

import os
import json
from datetime import datetime
from typing import Dict, Optional, List, Any, Union
from moya.conversation.thread import Thread
from moya.conversation.message import Message
from moya.memory.base_repository import BaseMemoryRepository


class FileSystemRepository(BaseMemoryRepository):
    """
    Maintains threads as JSON files on disk.
    Each thread is stored as a separate file with thread metadata at the top
    and messages as JSON lines in the file.
    """

    def __init__(self, base_path: str):
        """Initialize the repository with a base directory path."""
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
    
    def _thread_file_path(self, thread_id: str) -> str:
        """Get the file path for a thread"""
        return os.path.join(self.base_path, f"{thread_id}.json")
    
    def create_thread(self, thread: Thread) -> None:
        """
        Store a new thread. If the thread already exists, silently succeeds
        without overwriting the existing thread.
        """
        file_path = self._thread_file_path(thread.thread_id)
        if os.path.exists(file_path):
            # Thread already exists, just return without error
            return
        
        # Create the thread file with initial metadata
        thread_data = {
            "thread_id": thread.thread_id,
            "metadata": thread.metadata
        }
        
        # Write thread metadata and initial messages if any
        with open(file_path, 'w') as f:
            json.dump(thread_data, f)
            if thread.messages:
                f.write("\n")
                for msg in thread.messages:
                    # Use raw message data for storage to preserve original format
                    raw_data = {
                        "message_id": msg.message_id,
                        "thread_id": msg.thread_id,
                        "sender": msg.sender,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat() if hasattr(msg, 'timestamp') else datetime.utcnow().isoformat(),
                        "metadata": msg.metadata or {}
                    }
                    f.write(json.dumps(raw_data) + "\n")

    def get_thread(self, thread_id: str) -> Optional[Thread]:
        """
        Retrieve a thread by ID or return None if not found.
        """
        file_path = self._thread_file_path(thread_id)
        if not os.path.exists(file_path):
            return None
        
        try:
            # Read the thread file
            messages = []
            with open(file_path, 'r') as f:
                lines = f.readlines()
                
                if not lines:
                    return Thread(thread_id=thread_id, metadata={})
                
                # First line contains thread metadata
                try:
                    thread_data = json.loads(lines[0])
                except (json.JSONDecodeError, IndexError):
                    thread_data = {"thread_id": thread_id, "metadata": {}}
                
                # Remaining lines are messages
                for line in lines[1:]:
                    if not line.strip():  # Skip empty lines
                        continue
                    
                    try:
                        msg_data = json.loads(line)
                        if "sender" in msg_data and "content" in msg_data:
                            # Keep the content in its original format - don't convert to string
                            content = msg_data["content"]
                            
                            # Reconstruct the message with original content
                            messages.append(Message(
                                thread_id=thread_id,
                                message_id=msg_data.get("message_id"),
                                sender=msg_data["sender"],
                                content=content,
                                metadata=msg_data.get("metadata", {})
                            ))
                    except Exception as e:
                        # Skip invalid message lines
                        print(f"Error loading message: {e}")
                        continue
            
            # Recreate the thread
            thread = Thread(thread_id=thread_id, metadata=thread_data.get("metadata", {}))
            for msg in messages:
                thread.add_message(msg)
                
            return thread
            
        except Exception as e:
            # Return an empty thread as fallback
            print(f"Error loading thread {thread_id}: {e}")
            return Thread(thread_id=thread_id, metadata={})

    def append_message(self, thread_id: str, message: Message) -> None:
        """
        Append a message to an existing thread. Creates the thread if it doesn't exist.
        """
        file_path = self._thread_file_path(thread_id)
        
        # Create thread file if it doesn't exist
        if not os.path.exists(file_path):
            thread = Thread(thread_id=thread_id)
            self.create_thread(thread)
        
        try:
            # Store raw message data format
            raw_data = {
                "message_id": message.message_id,
                "thread_id": message.thread_id,
                "sender": message.sender,
                "content": message.content,  # Keep content in its original format
                "timestamp": message.timestamp.isoformat() if hasattr(message, 'timestamp') else datetime.utcnow().isoformat(),
                "metadata": message.metadata or {}
            }
            
            with open(file_path, 'a') as f:
                f.write(json.dumps(raw_data) + "\n")
        except Exception as e:
            raise ValueError(f"Failed to append message to thread {thread_id}: {str(e)}")

    def list_threads(self) -> List[str]:
        """Return a list of all thread IDs"""
        thread_ids = []
        try:
            for filename in os.listdir(self.base_path):
                if filename.endswith(".json"):
                    thread_ids.append(filename[:-5])  # Remove .json extension
        except OSError:
            # Handle directory access errors
            pass
        return thread_ids

    def delete_thread(self, thread_id: str) -> None:
        """Delete a thread file if it exists"""
        file_path = self._thread_file_path(thread_id)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            # Silently handle file deletion errors
            pass
