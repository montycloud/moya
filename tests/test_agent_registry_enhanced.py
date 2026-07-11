"""Tests for enhanced AgentRegistry: events, TTL, search, health."""

import os
import time
import tempfile
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

from moya.registry.agent_registry import AgentRegistry, AgentRegistryConfig
from moya.registry.json_agent_repository import JsonAgentRepository
from moya.agents.agent_info import AgentInfo
from moya.observability.event_bus import EventBus
from moya.tools.tool_registry import ToolRegistry
from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
from moya.skills.skill import Skill


def make_agent(name, description="A helpful agent", tags=None, skills=None):
    os.environ.setdefault("OPENAI_API_KEY", "sk-test")
    config = OpenAIAgentConfig(
        agent_name=name,
        agent_type="openai",
        description=description,
        api_key="sk-test",
        skills=skills or [],
        tool_registry=ToolRegistry(),
    )
    agent = OpenAIAgent(config)
    agent.client = MagicMock()
    agent.tags = tags or []
    return agent


@pytest.fixture()
def bus():
    return EventBus()


@pytest.fixture()
def registry(bus):
    return AgentRegistry(event_bus=bus)


# ── Event emission ────────────────────────────────────────────────────────────

def test_register_emits_event(registry, bus):
    names = []
    bus.subscribe("agent.registered", lambda e: names.append(e.agent_name))
    registry.register_agent(make_agent("alice"))
    assert "alice" in names


def test_remove_emits_event(registry, bus):
    removed = []
    bus.subscribe("agent.removed", lambda e: removed.append(e.agent_name))
    registry.register_agent(make_agent("bob"))
    registry.remove_agent("bob")
    assert "bob" in removed


def test_no_event_without_bus():
    reg = AgentRegistry()
    reg.register_agent(make_agent("charlie"))
    reg.remove_agent("charlie")


# ── search_agents ─────────────────────────────────────────────────────────────

def test_search_agents_by_name(registry):
    registry.register_agent(make_agent("weather_bot", description="Provides forecasts"))
    registry.register_agent(make_agent("calc", description="Calculator"))
    results = registry.search_agents("weather")
    assert any(a.agent_name == "weather_bot" for a in results)


def test_search_agents_by_description(registry):
    registry.register_agent(make_agent("a", description="Writes blog posts"))
    registry.register_agent(make_agent("b", description="Answers questions"))
    results = registry.search_agents("blog")
    assert len(results) == 1
    assert results[0].agent_name == "a"


def test_search_agents_by_tag(registry):
    registry.register_agent(make_agent("a", tags=["nlp", "research"]))
    registry.register_agent(make_agent("b", tags=["vision"]))
    results = registry.search_agents("nlp")
    assert any(a.agent_name == "a" for a in results)
    assert all(a.agent_name != "b" for a in results)


def test_search_agents_no_match(registry):
    registry.register_agent(make_agent("a"))
    assert registry.search_agents("zzznomatch") == []


def test_search_agents_ranked_by_score(registry):
    # "research" in name scores higher than "research" only in description
    registry.register_agent(make_agent("researcher", description="General agent"))
    registry.register_agent(make_agent("writer", description="Does research and writing"))
    results = registry.search_agents("research")
    assert results[0].agent_name == "researcher"


# ── TTL pruning ───────────────────────────────────────────────────────────────

def test_expired_agent_pruned_from_list():
    reg = AgentRegistry(config=AgentRegistryConfig(prune_expired_on_list=True))
    agent = make_agent("temp")
    reg.register_agent(agent)
    # Manually set TTL to already-expired on the stored AgentInfo
    for info in reg.repository.list_agents():
        if info.name == "temp":
            info.ttl_seconds = 0
            info.registered_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    names = {i.name for i in reg.list_agents()}
    assert "temp" not in names


def test_non_expired_agent_visible(registry):
    registry.register_agent(make_agent("permanent"))
    names = {i.name for i in registry.list_agents()}
    assert "permanent" in names


# ── find_healthy_agents ───────────────────────────────────────────────────────

def test_find_healthy_agents(registry):
    registry.register_agent(make_agent("healthy_a"))
    registry.register_agent(make_agent("unhealthy_b"))
    # Mark healthy
    for info in registry.list_agents():
        if info.name == "healthy_a":
            info.health.mark_success()
    healthy = registry.find_healthy_agents()
    names = {a.agent_name for a in healthy}
    assert "healthy_a" in names
    assert "unhealthy_b" not in names


# ── JsonAgentRepository ───────────────────────────────────────────────────────

def test_json_repo_persists_and_loads(tmp_path):
    path = str(tmp_path / "catalog.json")
    repo1 = JsonAgentRepository(path=path)
    agent = make_agent("persistent")
    repo1.save_agent(agent)
    assert repo1.get_agent("persistent") is not None

    # New repo instance loads from disk
    repo2 = JsonAgentRepository(path=path)
    infos = {i.name for i in repo2.list_agents()}
    assert "persistent" in infos


def test_json_repo_remove(tmp_path):
    path = str(tmp_path / "catalog.json")
    repo = JsonAgentRepository(path=path)
    repo.save_agent(make_agent("a"))
    repo.remove_agent("a")
    assert repo.get_agent("a") is None
    infos = {i.name for i in repo.list_agents()}
    assert "a" not in infos


def test_json_repo_missing_file_loads_empty(tmp_path):
    path = str(tmp_path / "nonexistent.json")
    repo = JsonAgentRepository(path=path)
    assert repo.list_agents() == []


def test_json_repo_attaches_agent_info_to_agent(tmp_path):
    path = str(tmp_path / "catalog.json")
    repo = JsonAgentRepository(path=path)
    agent = make_agent("a")
    repo.save_agent(agent)
    assert hasattr(agent, "_agent_info")
    assert agent._agent_info.name == "a"


# ── Backward compatibility ────────────────────────────────────────────────────

def test_existing_registry_api_unchanged(registry):
    """All original AgentRegistry methods still work."""
    s = Skill(name="writing", description="Writing skill")
    registry.register_agent(make_agent("writer", description="Writes content", skills=[s], tags=["content"]))
    registry.register_agent(make_agent("coder", description="Writes code", tags=["tech"]))

    assert registry.get_agent("writer") is not None
    assert registry.get_agent("ghost") is None
    assert len(registry.list_agents()) == 2
    assert len(registry.find_agents_by_type("openai")) == 2
    assert len(registry.find_agents_by_description("Writes content")) == 1
    assert len(registry.find_agents_with_skill("writing")) == 1
    assert len(registry.find_agents_by_tag("content")) == 1
    registry.remove_agent("writer")
    assert len(registry.list_agents()) == 1
