"""Tests for AgentRegistry discovery methods."""

import os
import pytest
from unittest.mock import MagicMock

from moya.registry.agent_registry import AgentRegistry
from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
from moya.skills.skill import Skill
from moya.tools.tool_registry import ToolRegistry


def make_agent(name, description="desc", skills=None, tags=None):
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


@pytest.fixture
def registry():
    r = AgentRegistry()
    safety_skill = Skill(name="safety", description="Safety skill")
    eco_skill = Skill(name="eco", description="Eco skill")

    r.register_agent(make_agent("researcher", "Does research",
                                skills=[safety_skill, eco_skill], tags=["specialist"]))
    r.register_agent(make_agent("writer", "Writes content",
                                skills=[safety_skill], tags=["specialist"]))
    r.register_agent(make_agent("coordinator", "Coordinates",
                                tags=["coordinator"]))
    return r


def test_list_agents(registry):
    assert len(registry.list_agents()) == 3


def test_get_agent(registry):
    a = registry.get_agent("researcher")
    assert a is not None
    assert a.agent_name == "researcher"


def test_get_missing_agent(registry):
    assert registry.get_agent("nobody") is None


def test_find_agents_with_skill(registry):
    agents = registry.find_agents_with_skill("safety")
    names = {a.agent_name for a in agents}
    assert names == {"researcher", "writer"}


def test_find_agents_missing_skill(registry):
    assert registry.find_agents_with_skill("nonexistent") == []


def test_find_agents_by_tag(registry):
    specialists = registry.find_agents_by_tag("specialist")
    assert len(specialists) == 2
    coordinators = registry.find_agents_by_tag("coordinator")
    assert len(coordinators) == 1
    assert coordinators[0].agent_name == "coordinator"


def test_find_agents_missing_tag(registry):
    assert registry.find_agents_by_tag("no_such_tag") == []


def test_register_and_remove(registry):
    registry.register_agent(make_agent("temp"))
    assert registry.get_agent("temp") is not None
    registry.remove_agent("temp")
    assert registry.get_agent("temp") is None


def test_agent_info_has_skills_and_tags(registry):
    infos = {i.name: i for i in registry.list_agents()}
    assert "safety" in infos["researcher"].skills
    assert "eco" in infos["researcher"].skills
    assert "specialist" in infos["researcher"].tags
