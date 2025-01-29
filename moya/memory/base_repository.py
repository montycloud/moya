"""
Base repository for conversation memory in Moya.

Defines an abstract class describing how to store and retrieve conversation
Threads (and their Messages).
"""

import abc
from typing import Optional, List
from moya.conversation.thread import Thread
from moya.conversation.message import Message


class BaseMemoryRepository(abc.ABC):
    """
    Abstract interface for storing and retrieving conversation threads
    (and messages within those threads).
    """

    @abc.abstractmethod
    def create_thread(self, thread: Thread) -> None:
        """
        Store a new thread in the repository. If a thread with the same
        thread_id already exists, this should raise an error (or overwrite,
        depending on your policy).
        """
        pass

    @abc.abstractmethod
    def get_thread(self, thread_id: str) -> Optional[Thread]:
        """
        Retrieve a thread by its ID.

        :param thread_id: The unique ID of the thread to fetch.
        :return: The Thread object if found, else None.
        """
        pass

    @abc.abstractmethod
    def append_message(self, thread_id: str, message: Message) -> None:
        """
        Add a new message to an existing thread.

        :param thread_id: The ID of the thread to which we add a message.
        :param message: The message to append.
        """
        pass

    @abc.abstractmethod
    def list_threads(self) -> List[str]:
        """
        List the IDs of all threads currently stored.

        :return: A list of thread_id strings.
        """
        pass

    @abc.abstractmethod
    def delete_thread(self, thread_id: str) -> None:
        """
        Remove a thread (and its messages) from the repository.

        :param thread_id: The ID of the thread to remove.
        """
        pass
