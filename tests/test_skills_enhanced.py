"""
Tests for enhanced Skills — REQ-SKILL-01 through REQ-SKILL-08.

Covers:
  - Skill new fields (input_schema, output_schema, dependencies, handler)
  - SkillRegistry versioning and conflict detection
  - SkillRegistry dependency resolution (including cycles and missing deps)
  - attach_skills() with and without a registry
  - Agent skill attachment with dependency resolution
  - SkillClassifier routing
"""

import os
import pytest
from unittest.mock import MagicMock

from moya.skills.skill import Skill
from moya.skills.registry import SkillRegistry, SkillVersionConflictError, SkillNotFoundError
from moya.skills.attachment import attach_skills
from moya.classifiers.skill_classifier import SkillClassifier
from moya.agents.agent_info import AgentInfo
from moya.tools.tool import Tool
from moya.tools.tool_registry import ToolRegistry
from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_skill(name, version="1.0.0", deps=None, prompt=None, has_tool=False, handler=None):
    factory = None
    if has_tool:
        def fn(): return "ok"
        fn.__doc__ = f"Tool for {name}.\n- dummy: unused"
        factory = lambda: [Tool(name=f"tool_{name}", function=fn)]
    return Skill(
        name=name,
        description=f"Skill {name}",
        version=version,
        prompt_snippet=prompt or f"You have skill {name}.",
        tools_factory=factory,
        dependencies=deps or [],
        handler=handler,
        input_schema={"input": {"type": "string"}},
        output_schema={"output": {"type": "string"}},
    )


def make_agent(name="test_agent", skills=None, skill_registry=None):
    os.environ.setdefault("OPENAI_API_KEY", "sk-test")
    config = OpenAIAgentConfig(
        agent_name=name,
        agent_type="openai",
        description="Test agent",
        api_key="sk-test",
        skills=skills or [],
        tool_registry=ToolRegistry(),
        skill_registry=skill_registry,
    )
    agent = OpenAIAgent(config)
    agent.client = MagicMock()
    return agent


# ── REQ-SKILL-01: Skill fields ────────────────────────────────────────────────

def test_skill_new_fields_present():
    s = Skill(name="s", description="d")
    assert s.input_schema is None
    assert s.output_schema is None
    assert s.dependencies == []
    assert s.handler is None


def test_skill_with_schemas():
    s = Skill(
        name="calc",
        description="Calculator",
        input_schema={"a": {"type": "number"}, "b": {"type": "number"}},
        output_schema={"result": {"type": "number"}},
    )
    assert s.input_schema["a"]["type"] == "number"
    assert s.output_schema["result"]["type"] == "number"


def test_skill_handler_execute():
    s = Skill(
        name="adder",
        description="Add two numbers",
        handler=lambda inp: {"result": inp["a"] + inp["b"]},
    )
    assert s.execute({"a": 3, "b": 4}) == {"result": 7}


def test_skill_execute_no_handler_raises():
    s = Skill(name="s", description="d")
    with pytest.raises(NotImplementedError, match="no handler"):
        s.execute({})


def test_skill_backward_compat():
    """Original Skill construction must still work."""
    s = Skill(name="web", description="Search", version="1.0.0",
              tags=["search"], prompt_snippet="Use search.")
    assert s.name == "web"
    assert s.version == "1.0.0"
    assert "search" in s.tags
    assert s.prompt_snippet == "Use search."


# ── REQ-SKILL-02 + REQ-SKILL-08: SkillRegistry versioning ───────────────────

def test_register_and_get_latest():
    reg = SkillRegistry()
    s1 = make_skill("s", "1.0.0")
    s2 = make_skill("s", "2.0.0")
    reg.register(s1)
    reg.register(s2)
    assert reg.get("s") is s2


def test_get_pinned_version():
    reg = SkillRegistry()
    s1 = make_skill("s", "1.0.0")
    s2 = make_skill("s", "2.0.0")
    reg.register(s1)
    reg.register(s2)
    assert reg.get("s", version="1.0.0") is s1
    assert reg.get("s", version="2.0.0") is s2


def test_get_missing_returns_none():
    reg = SkillRegistry()
    assert reg.get("ghost") is None
    assert reg.get("ghost", version="1.0.0") is None


def test_list_versions_newest_first():
    reg = SkillRegistry()
    for v in ["1.0.0", "3.0.0", "2.0.0"]:
        reg.register(make_skill("s", v))
    assert reg.list_versions("s") == ["3.0.0", "2.0.0", "1.0.0"]


def test_list_versions_empty_for_unknown():
    assert SkillRegistry().list_versions("x") == []


def test_version_conflict_raises():
    reg = SkillRegistry()
    s = make_skill("s", "1.0.0")
    reg.register(s)
    different = make_skill("s", "1.0.0")  # same name+version, different object
    with pytest.raises(SkillVersionConflictError):
        reg.register(different)


def test_overwrite_same_version():
    reg = SkillRegistry()
    s = make_skill("s", "1.0.0")
    reg.register(s)
    s2 = make_skill("s", "1.0.0")
    reg.register(s2, overwrite=True)  # should not raise
    assert reg.get("s") is s2


def test_same_object_registered_twice_is_noop():
    reg = SkillRegistry()
    s = make_skill("s", "1.0.0")
    reg.register(s)
    reg.register(s)  # same object — no conflict


def test_list_skills_returns_latest_per_name():
    reg = SkillRegistry()
    reg.register(make_skill("a", "1.0.0"))
    reg.register(make_skill("a", "2.0.0"))
    reg.register(make_skill("b", "1.0.0"))
    skills = {s.name: s for s in reg.list_skills()}
    assert skills["a"].version == "2.0.0"
    assert "b" in skills


def test_find_by_tag():
    reg = SkillRegistry()
    s = Skill(name="s", description="d", tags=["alpha", "beta"])
    reg.register(s)
    assert s in reg.find_by_tag("alpha")
    assert s not in reg.find_by_tag("gamma")


def test_find_by_name_fragment():
    reg = SkillRegistry()
    reg.register(Skill(name="web_search", description="Search the web"))
    reg.register(Skill(name="calculator", description="Do math"))
    results = reg.find_by_name_fragment("web")
    assert any(s.name == "web_search" for s in results)
    assert all(s.name != "calculator" for s in results)


# ── REQ-SKILL-06: Dependency resolution ──────────────────────────────────────

def test_resolve_no_deps():
    reg = SkillRegistry()
    s = make_skill("s")
    reg.register(s)
    ordered = reg.resolve_dependencies("s")
    assert ordered == [s]


def test_resolve_single_dep():
    reg = SkillRegistry()
    base = make_skill("base")
    child = make_skill("child", deps=["base"])
    reg.register(base)
    reg.register(child)
    ordered = reg.resolve_dependencies("child")
    assert ordered[0].name == "base"
    assert ordered[1].name == "child"


def test_resolve_transitive_deps():
    reg = SkillRegistry()
    a = make_skill("a")
    b = make_skill("b", deps=["a"])
    c = make_skill("c", deps=["b"])
    reg.register(a)
    reg.register(b)
    reg.register(c)
    ordered = reg.resolve_dependencies("c")
    assert [s.name for s in ordered] == ["a", "b", "c"]


def test_resolve_diamond_deps_no_duplicates():
    """a ← b, a ← c, d depends on b and c."""
    reg = SkillRegistry()
    a = make_skill("a")
    b = make_skill("b", deps=["a"])
    c = make_skill("c", deps=["a"])
    d = make_skill("d", deps=["b", "c"])
    for s in [a, b, c, d]:
        reg.register(s)
    ordered = reg.resolve_dependencies("d")
    names = [s.name for s in ordered]
    assert names.index("a") < names.index("b")
    assert names.index("a") < names.index("c")
    assert names.index("b") < names.index("d")
    assert names.index("c") < names.index("d")
    assert names.count("a") == 1  # no duplicates


def test_resolve_missing_dep_raises():
    reg = SkillRegistry()
    s = make_skill("s", deps=["missing"])
    reg.register(s)
    with pytest.raises(SkillNotFoundError, match="missing"):
        reg.resolve_dependencies("s")


def test_resolve_missing_root_raises():
    reg = SkillRegistry()
    with pytest.raises(SkillNotFoundError):
        reg.resolve_dependencies("ghost")


def test_resolve_cycle_raises():
    reg = SkillRegistry()
    a = make_skill("a", deps=["b"])
    b = make_skill("b", deps=["a"])
    reg.register(a)
    reg.register(b)
    with pytest.raises(ValueError, match="Circular"):
        reg.resolve_dependencies("a")


def test_resolve_self_cycle_raises():
    reg = SkillRegistry()
    s = make_skill("s", deps=["s"])
    reg.register(s)
    with pytest.raises(ValueError, match="Circular"):
        reg.resolve_dependencies("s")


# ── attach_skills() ───────────────────────────────────────────────────────────

def test_attach_skills_no_registry():
    agent = make_agent()
    s = make_skill("s", has_tool=True)
    attached = attach_skills(agent, [s])
    assert len(attached) == 1
    assert agent.skills[0].name == "s"
    assert "tool_s" in agent.tool_registry.list_tools()
    assert "You have skill s" in agent.system_prompt


def test_attach_skills_with_registry_resolves_deps():
    reg = SkillRegistry()
    base = make_skill("base", has_tool=True)
    top = make_skill("top", deps=["base"])
    reg.register(base)
    reg.register(top)

    agent = make_agent()
    attach_skills(agent, [top], registry=reg)

    names = [s.name for s in agent.skills]
    assert "base" in names
    assert "top" in names
    assert names.index("base") < names.index("top")


def test_attach_skills_skips_already_attached():
    agent = make_agent()
    s = make_skill("s")
    attach_skills(agent, [s])
    attach_skills(agent, [s])  # second attach should be ignored
    assert sum(1 for x in agent.skills if x.name == "s") == 1


def test_attach_skills_returns_attached_list():
    agent = make_agent()
    a = make_skill("a")
    b = make_skill("b")
    result = attach_skills(agent, [a, b])
    assert len(result) == 2


def test_attach_skills_cycle_raises():
    reg = SkillRegistry()
    a = make_skill("a", deps=["b"])
    b = make_skill("b", deps=["a"])
    reg.register(a)
    reg.register(b)
    agent = make_agent()
    with pytest.raises(ValueError, match="Circular"):
        attach_skills(agent, [a], registry=reg)


# ── Agent skill attachment via config ─────────────────────────────────────────

def test_agent_attaches_skills_at_init():
    s = make_skill("s", has_tool=True)
    agent = make_agent(skills=[s])
    assert any(x.name == "s" for x in agent.skills)
    assert "tool_s" in agent.tool_registry.list_tools()
    assert "You have skill s" in agent.system_prompt


def test_agent_resolves_deps_via_registry():
    reg = SkillRegistry()
    base = make_skill("base")
    top = make_skill("top", deps=["base"])
    reg.register(base)
    reg.register(top)

    agent = make_agent(skills=[top], skill_registry=reg)
    names = [s.name for s in agent.skills]
    assert "base" in names
    assert "top" in names
    assert names.index("base") < names.index("top")


def test_agent_no_skills_by_default():
    agent = make_agent()
    assert agent.skills == []


# ── REQ-SKILL-05: SkillClassifier ────────────────────────────────────────────

def make_agent_info(name, skills=None):
    info = AgentInfo(name=name, description=f"Agent {name}", type="openai",
                     skills=skills or [])
    return info


def test_skill_classifier_returns_sole_match():
    clf = SkillClassifier(required_skill="web_search", default_agent="default")
    agents = [
        make_agent_info("searcher", skills=["web_search"]),
        make_agent_info("writer"),
    ]
    assert clf.classify("find something", available_agents=agents) == "searcher"


def test_skill_classifier_no_match_returns_default():
    clf = SkillClassifier(required_skill="coding", default_agent="fallback")
    agents = [make_agent_info("writer")]
    assert clf.classify("write code", available_agents=agents) == "fallback"


def test_skill_classifier_no_agents_returns_default():
    clf = SkillClassifier(required_skill="s", default_agent="d")
    assert clf.classify("hi", available_agents=[]) == "d"
    assert clf.classify("hi", available_agents=None) == "d"


def test_skill_classifier_multiple_candidates_deterministic():
    clf = SkillClassifier(required_skill="math", default_agent="d")
    agents = [
        make_agent_info("calc_b", skills=["math"]),
        make_agent_info("calc_a", skills=["math"]),
    ]
    # No fallback → alphabetically first
    assert clf.classify("compute", available_agents=agents) == "calc_a"


def test_skill_classifier_uses_fallback_for_multiple():
    fallback = MagicMock()
    fallback.classify.return_value = "calc_b"
    clf = SkillClassifier(required_skill="math", fallback_classifier=fallback)
    agents = [
        make_agent_info("calc_a", skills=["math"]),
        make_agent_info("calc_b", skills=["math"]),
    ]
    result = clf.classify("compute", available_agents=agents)
    assert result == "calc_b"
    fallback.classify.assert_called_once()
    # Fallback should only receive the 2 math candidates
    call_agents = fallback.classify.call_args[1]["available_agents"]
    assert len(call_agents) == 2


def test_skill_classifier_with_extractor():
    def extractor(msg):
        return "web_search" if "search" in msg else None

    clf = SkillClassifier(skill_extractor=extractor, default_agent="default")
    agents = [make_agent_info("searcher", skills=["web_search"])]

    assert clf.classify("please search for X", available_agents=agents) == "searcher"
    assert clf.classify("write me a poem", available_agents=agents) == "default"


def test_skill_classifier_requires_skill_or_extractor():
    with pytest.raises(ValueError):
        SkillClassifier(default_agent="d")


def test_skill_classifier_static_skill_overrides_extractor():
    clf = SkillClassifier(
        required_skill="math",
        skill_extractor=lambda m: "web_search",
        default_agent="d",
    )
    agents = [make_agent_info("calc", skills=["math"])]
    # Static required_skill wins over extractor
    assert clf.classify("compute", available_agents=agents) == "calc"
