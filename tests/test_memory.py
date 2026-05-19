"""Tests for InMemoryRepository, FileSystemRepository, and EphemeralMemory."""

import json
import os
import tempfile
import pytest

from moya.memory.in_memory_repository import InMemoryRepository
from moya.conversation.thread import Thread
from moya.conversation.message import Message
from moya.tools.ephemeral_memory import EphemeralMemory


# ---- InMemoryRepository ------------------------------------------------

def make_repo():
    return InMemoryRepository()


def test_create_and_get_thread():
    repo = make_repo()
    repo.create_thread(Thread(thread_id="t1"))
    assert repo.get_thread("t1") is not None


def test_get_missing_thread_returns_none():
    repo = make_repo()
    assert repo.get_thread("nope") is None


def test_duplicate_thread_raises():
    repo = make_repo()
    repo.create_thread(Thread(thread_id="t1"))
    with pytest.raises(ValueError):
        repo.create_thread(Thread(thread_id="t1"))


def test_append_and_retrieve_messages():
    repo = make_repo()
    repo.create_thread(Thread(thread_id="t1"))
    repo.append_message("t1", Message(thread_id="t1", sender="user", content="hi"))
    repo.append_message("t1", Message(thread_id="t1", sender="agent", content="hello"))
    thread = repo.get_thread("t1")
    assert len(thread.get_messages()) == 2


def test_get_last_n_messages():
    repo = make_repo()
    repo.create_thread(Thread(thread_id="t1"))
    for i in range(5):
        repo.append_message("t1", Message(thread_id="t1", sender="user", content=str(i)))
    thread = repo.get_thread("t1")
    assert len(thread.get_last_n_messages(3)) == 3
    assert thread.get_last_n_messages(3)[-1].content == "4"


def test_list_and_delete_threads():
    repo = make_repo()
    repo.create_thread(Thread(thread_id="t1"))
    repo.create_thread(Thread(thread_id="t2"))
    assert set(repo.list_threads()) == {"t1", "t2"}
    repo.delete_thread("t1")
    assert repo.get_thread("t1") is None
    assert "t2" in repo.list_threads()


# ---- EphemeralMemory (instance) ----------------------------------------

def test_ephemeral_store_and_retrieve():
    mem = EphemeralMemory()
    mem.store_message("t1", "user", "hello")
    mem.store_message("t1", "agent", "world")
    result = json.loads(mem.get_last_n_messages("t1", n=5))
    assert len(result) == 2
    assert result[0]["role"] == "user"


def test_ephemeral_creates_thread_on_first_store():
    mem = EphemeralMemory()
    mem.store_message("new_thread", "user", "first message")
    result = json.loads(mem.get_last_n_messages("new_thread"))
    assert len(result) == 1


def test_ephemeral_summary():
    mem = EphemeralMemory()
    mem.store_message("t1", "user", "What time is it?")
    mem.store_message("t1", "agent", "It is noon.")
    summary = mem.get_thread_summary("t1")
    assert "What time is it?" in summary
    assert "It is noon." in summary


def test_ephemeral_instances_are_isolated():
    mem1 = EphemeralMemory()
    mem2 = EphemeralMemory()
    mem1.store_message("t1", "user", "hello")
    result = json.loads(mem2.get_last_n_messages("t1"))
    assert result == []


def test_ephemeral_custom_repository():
    repo = InMemoryRepository()
    mem = EphemeralMemory(repository=repo)
    mem.store_message("t1", "user", "hi")
    assert repo.get_thread("t1") is not None
