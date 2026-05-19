"""Tests for Skill attachment and SkillRegistry discovery."""

import pytest
from moya.skills.skill import Skill
from moya.skills.registry import SkillRegistry
from moya.tools.tool import Tool
from moya.tools.tool_registry import ToolRegistry


# ---- Skill dataclass ---------------------------------------------------

def test_skill_defaults():
    s = Skill(name="test", description="A test skill")
    assert s.version == "1.0.0"
    assert s.tags == []
    assert s.prompt_snippet is None
    assert s.tools_factory is None


def test_skill_has_dependencies_field():
    s = Skill(name="test", description="desc")
    assert hasattr(s, "dependencies")
    assert s.dependencies == []


def test_skill_with_prompt_snippet():
    s = Skill(name="safety", description="Safety skill", prompt_snippet="Be safe.")
    assert s.prompt_snippet == "Be safe."


def test_skill_tools_factory():
    def my_tool() -> str:
        """A tool."""
        return "result"

    s = Skill(
        name="tooled",
        description="Has tools",
        tools_factory=lambda: [Tool(name="my_tool", function=my_tool)],
    )
    tools = s.tools_factory()
    assert len(tools) == 1
    assert tools[0].name == "my_tool"


# ---- Skill attachment to agent -----------------------------------------

def _make_agent(skills=None):
    """Create a minimal OpenAIAgent with the given skills (no real API call)."""
    import os
    from unittest.mock import MagicMock
    from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig

    os.environ.setdefault("OPENAI_API_KEY", "sk-test")
    registry = ToolRegistry()
    config = OpenAIAgentConfig(
        agent_name="tester",
        agent_type="openai",
        description="test agent",
        system_prompt="Base prompt.",
        api_key="sk-test",
        tool_registry=registry,
        skills=skills or [],
    )
    agent = OpenAIAgent(config)
    agent.client = MagicMock()
    return agent


def test_skill_appends_prompt_snippet():
    skill = Skill(name="s1", description="desc", prompt_snippet="## Extra\nBe careful.")
    agent = _make_agent(skills=[skill])
    assert "## Extra" in agent.system_prompt
    assert "Base prompt." in agent.system_prompt


def test_multiple_skills_all_appended():
    s1 = Skill(name="s1", description="d", prompt_snippet="SNIPPET_A")
    s2 = Skill(name="s2", description="d", prompt_snippet="SNIPPET_B")
    agent = _make_agent(skills=[s1, s2])
    assert "SNIPPET_A" in agent.system_prompt
    assert "SNIPPET_B" in agent.system_prompt


def test_skill_registers_tools():
    def eco(city: str) -> str:
        """Eco tips.

        Parameters:
        - city: The city name.
        """
        return f"Eco tips for {city}"

    skill = Skill(
        name="eco",
        description="eco skill",
        tools_factory=lambda: [Tool(name="eco_tips", function=eco)],
    )
    agent = _make_agent(skills=[skill])
    assert agent.tool_registry.get_tool("eco_tips") is not None


def test_prompt_only_skill_no_tools_registered():
    skill = Skill(name="safety", description="d", prompt_snippet="Stay safe.")
    agent = _make_agent(skills=[skill])
    # only the eco_tips tool from the tools_factory should be absent
    assert agent.tool_registry.get_tool("eco_tips") is None


# ---- SkillRegistry -----------------------------------------------------

@pytest.fixture
def sreg():
    r = SkillRegistry()
    r.register(Skill(name="web_search", description="Web search", tags=["web", "search"]))
    r.register(Skill(name="code_exec", description="Execute code", tags=["code", "execution"]))
    r.register(Skill(name="eco", description="Eco tips", tags=["eco", "travel"]))
    return r


def test_registry_get(sreg):
    assert sreg.get("web_search") is not None
    assert sreg.get("nope") is None


def test_registry_list(sreg):
    assert len(sreg.list_skills()) == 3


def test_registry_find_by_tag(sreg):
    results = sreg.find_by_tag("eco")
    assert len(results) == 1
    assert results[0].name == "eco"


def test_registry_find_by_name_fragment(sreg):
    results = sreg.find_by_name_fragment("search")
    assert any(s.name == "web_search" for s in results)


def test_registry_overwrite(sreg):
    updated = Skill(name="web_search", description="Updated", version="2.0.0")
    sreg.register(updated)
    assert sreg.get("web_search").description == "Updated"  # latest is now 2.0.0
