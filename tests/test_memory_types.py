"""Tests for the memory subsystem: ShortTermMemory, LongTermMemory, CompositeMemory."""

import os
from unittest.mock import MagicMock

import pytest

from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
from moya.conversation.message import Message
from moya.conversation.thread import Thread
from moya.memory import (
    ShortTermMemory,
    LongTermMemory,
    CompositeMemory,
    InMemoryRepository,
)


def _msg(thread_id, sender, content):
    return Message(thread_id=thread_id, sender=sender, content=content)


# ── ShortTermMemory ─────────────────────────────────────────────────────────

def test_short_term_keeps_only_window():
    mem = ShortTermMemory(window_size=3)
    mem.create_thread(Thread(thread_id="t1"))
    for i in range(6):
        mem.append_message("t1", _msg("t1", "user", str(i)))
    thread = mem.get_thread("t1")
    contents = [m.content for m in thread.messages]
    assert contents == ["3", "4", "5"]


def test_short_term_recent_defaults_to_window():
    mem = ShortTermMemory(window_size=5)
    mem.create_thread(Thread(thread_id="t1"))
    for i in range(10):
        mem.append_message("t1", _msg("t1", "user", str(i)))
    assert [m.content for m in mem.recent("t1")] == ["5", "6", "7", "8", "9"]
    assert [m.content for m in mem.recent("t1", 2)] == ["8", "9"]


def test_short_term_rejects_bad_window():
    with pytest.raises(ValueError):
        ShortTermMemory(window_size=0)


def test_short_term_summary():
    mem = ShortTermMemory(window_size=10)
    mem.create_thread(Thread(thread_id="t1"))
    mem.append_message("t1", _msg("t1", "user", "hi"))
    mem.append_message("t1", _msg("t1", "bot", "hello"))
    summary = mem.get_conversation_summary("t1")
    assert "user: hi" in summary
    assert "bot: hello" in summary


# ── LongTermMemory ──────────────────────────────────────────────────────────

def test_long_term_persists_across_instances(tmp_path):
    path = str(tmp_path / "mem")
    mem1 = LongTermMemory(base_path=path)
    mem1.create_thread(Thread(thread_id="t1"))
    mem1.append_message("t1", _msg("t1", "user", "remember the blue whale"))

    # New instance, same path — data survives.
    mem2 = LongTermMemory(base_path=path)
    thread = mem2.get_thread("t1")
    assert thread is not None
    assert any("blue whale" in m.content for m in thread.messages)


def test_long_term_recall_ranks_by_overlap(tmp_path):
    mem = LongTermMemory(base_path=str(tmp_path / "mem"))
    mem.create_thread(Thread(thread_id="t1"))
    mem.append_message("t1", _msg("t1", "user", "I love hiking in the mountains"))
    mem.append_message("t1", _msg("t1", "user", "the weather is sunny today"))
    mem.append_message("t1", _msg("t1", "user", "mountains are beautiful in winter"))

    hits = mem.recall("t1", "mountains winter", k=2)
    assert len(hits) == 2
    # The message mentioning both query words ranks first.
    assert "winter" in hits[0].content


def test_long_term_recall_empty_query_returns_recent(tmp_path):
    mem = LongTermMemory(base_path=str(tmp_path / "mem"))
    mem.create_thread(Thread(thread_id="t1"))
    for i in range(4):
        mem.append_message("t1", _msg("t1", "user", f"message {i}"))
    hits = mem.recall("t1", "", k=2)
    assert [m.content for m in hits] == ["message 2", "message 3"]


def test_long_term_recall_no_overlap_returns_empty(tmp_path):
    mem = LongTermMemory(base_path=str(tmp_path / "mem"))
    mem.create_thread(Thread(thread_id="t1"))
    mem.append_message("t1", _msg("t1", "user", "apples and oranges"))
    assert mem.recall("t1", "quantum physics", k=5) == []


# ── CompositeMemory ─────────────────────────────────────────────────────────

def test_composite_requires_a_store():
    with pytest.raises(ValueError):
        CompositeMemory([])


def test_composite_fans_out_writes(tmp_path):
    short = ShortTermMemory(window_size=10)
    long = LongTermMemory(base_path=str(tmp_path / "mem"))
    comp = CompositeMemory([long, short])  # long-term primary

    comp.create_thread(Thread(thread_id="t1"))
    comp.append_message("t1", _msg("t1", "user", "hello world"))

    assert short.get_thread("t1") is not None
    assert long.get_thread("t1") is not None
    assert short.get_thread("t1").messages[0].content == "hello world"
    assert long.get_thread("t1").messages[0].content == "hello world"


def test_composite_reads_from_primary():
    a = InMemoryRepository()
    b = InMemoryRepository()
    comp = CompositeMemory([a, b])
    comp.create_thread(Thread(thread_id="t1"))
    comp.append_message("t1", _msg("t1", "user", "primary read"))
    # Reads come from the first store.
    assert comp.get_thread("t1").messages[0].content == "primary read"
    assert comp.list_threads() == ["t1"]


def test_composite_append_creates_missing_thread_in_secondary(tmp_path):
    """Long-term has a thread from a prior session; fresh short-term does not."""
    path = str(tmp_path / "mem")
    long_prev = LongTermMemory(base_path=path)
    long_prev.create_thread(Thread(thread_id="t1"))
    long_prev.append_message("t1", _msg("t1", "user", "old message"))

    # New session: long-term reloads, short-term is empty.
    comp = CompositeMemory([LongTermMemory(base_path=path), ShortTermMemory()])
    # Should NOT raise even though short-term never saw "t1".
    comp.append_message("t1", _msg("t1", "user", "new message"))
    assert comp.get_thread("t1") is not None


def test_composite_recall_delegates_to_long_term(tmp_path):
    short = ShortTermMemory(window_size=10)
    long = LongTermMemory(base_path=str(tmp_path / "mem"))
    comp = CompositeMemory([short, long])  # short-term primary, but it has no recall
    comp.create_thread(Thread(thread_id="t1"))
    comp.append_message("t1", _msg("t1", "user", "the eiffel tower is in paris"))
    hits = comp.recall("t1", "paris", k=1)
    assert len(hits) == 1
    assert "paris" in hits[0].content


# ── End-to-end with a real agent ────────────────────────────────────────────

def _make_agent(memory):
    os.environ.setdefault("OPENAI_API_KEY", "sk-test")
    config = OpenAIAgentConfig(
        agent_name="tester",
        agent_type="openai",
        description="test",
        api_key="sk-test",
        memory=memory,
    )
    agent = OpenAIAgent(config)
    agent.client = MagicMock()
    return agent


def test_agent_with_composite_memory_remembers_across_turns(tmp_path):
    memory = CompositeMemory([
        LongTermMemory(base_path=str(tmp_path / "mem")),
        ShortTermMemory(window_size=10),
    ])
    agent = _make_agent(memory)
    agent._remember("t1", "my name is Ada", "nice to meet you Ada")
    agent._remember("t1", "what is my name?", "your name is Ada")

    recent = agent.get_last_n_messages("t1", n=4)
    assert len(recent) == 4
    assert any("Ada" in m.content for m in recent)


def test_agent_short_term_window_bounds_history(tmp_path):
    agent = _make_agent(ShortTermMemory(window_size=2))
    agent._remember("t1", "turn1", "resp1")   # 2 messages
    agent._remember("t1", "turn2", "resp2")   # +2 → trimmed to last 2
    thread = agent.memory.get_thread("t1")
    assert len(thread.messages) == 2
    assert thread.messages[-1].content == "resp2"
