"""Tests for GlobalToolRegistry and ScopedToolRegistry."""

import pytest

from moya.tools.tool import Tool
from moya.tools.global_tool_registry import (
    GlobalToolRegistry,
    ScopedToolRegistry,
    get_global_tool_registry,
    set_global_tool_registry,
)
from moya.observability.event_bus import EventBus


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_tool(name, category=None, tags=None, allowed_agents=None, deprecated=False):
    def fn():
        """A tool function."""
        return name
    return Tool(
        name=name,
        function=fn,
        category=category,
        tags=tags or [],
        allowed_agents=allowed_agents,
        deprecated=deprecated,
    )


@pytest.fixture()
def reg():
    return GlobalToolRegistry()


# ── GlobalToolRegistry basics ─────────────────────────────────────────────────

def test_register_and_get(reg):
    t = make_tool("search")
    reg.register_tool(t)
    assert reg.get_tool("search") is t


def test_get_missing_returns_none(reg):
    assert reg.get_tool("no_such_tool") is None


def test_list_tools(reg):
    reg.register_tool(make_tool("a"))
    reg.register_tool(make_tool("b"))
    assert set(reg.list_tools()) == {"a", "b"}


def test_get_tools_returns_all(reg):
    reg.register_tool(make_tool("a"))
    reg.register_tool(make_tool("b"))
    assert len(reg.get_tools()) == 2


def test_remove_tool(reg):
    reg.register_tool(make_tool("a"))
    reg.remove_tool("a")
    assert reg.get_tool("a") is None


def test_remove_nonexistent_is_noop(reg):
    reg.remove_tool("phantom")  # should not raise


def test_find_by_category(reg):
    reg.register_tool(make_tool("search", category="web"))
    reg.register_tool(make_tool("calc", category="math"))
    reg.register_tool(make_tool("fetch", category="web"))
    web = reg.find_by_category("web")
    assert {t.name for t in web} == {"search", "fetch"}


def test_find_by_tag(reg):
    reg.register_tool(make_tool("a", tags=["alpha", "shared"]))
    reg.register_tool(make_tool("b", tags=["shared"]))
    reg.register_tool(make_tool("c", tags=["other"]))
    shared = reg.find_by_tag("shared")
    assert {t.name for t in shared} == {"a", "b"}


def test_search_by_name(reg):
    reg.register_tool(make_tool("weather_lookup"))
    reg.register_tool(make_tool("calc"))
    results = reg.search("weather")
    assert len(results) == 1
    assert results[0].name == "weather_lookup"


def test_search_by_description(reg):
    def fn():
        """Fetches current weather data."""
        return "weather"
    reg.register_tool(Tool(name="wx", function=fn))
    results = reg.search("weather data")
    assert any(t.name == "wx" for t in results)


def test_search_no_match(reg):
    reg.register_tool(make_tool("calc"))
    assert reg.search("zzznomatch") == []


def test_get_catalog_includes_metadata(reg):
    reg.register_tool(make_tool("t", category="cat", tags=["x"]))
    catalog = reg.get_catalog()
    entry = next(e for e in catalog if e["name"] == "t")
    assert entry["category"] == "cat"
    assert "x" in entry["tags"]
    assert "version" in entry
    assert "deprecated" in entry


# ── Event emission ────────────────────────────────────────────────────────────

def test_emits_tool_registered_event(reg):
    bus = EventBus()
    reg.set_event_bus(bus)
    events = []
    bus.subscribe("tool.registered", lambda e: events.append(e.tool_name))
    reg.register_tool(make_tool("search"))
    assert "search" in events


def test_no_event_without_bus(reg):
    reg.register_tool(make_tool("search"))  # should not raise


# ── ScopedToolRegistry ────────────────────────────────────────────────────────

def test_scoped_sees_global_tool(reg):
    reg.register_tool(make_tool("shared"))
    scoped = reg.scoped("agent_a")
    assert scoped.get_tool("shared") is not None


def test_scoped_local_tool_invisible_to_others(reg):
    scoped_a = reg.scoped("agent_a")
    scoped_b = reg.scoped("agent_b")
    local = make_tool("local_a")
    scoped_a.register_tool(local)
    assert scoped_a.get_tool("local_a") is local
    assert scoped_b.get_tool("local_a") is None
    assert reg.get_tool("local_a") is None


def test_scoped_local_overrides_global(reg):
    global_t = make_tool("t")
    reg.register_tool(global_t)
    local_t = make_tool("t")
    scoped = reg.scoped("agent_a")
    scoped.register_tool(local_t)
    assert scoped.get_tool("t") is local_t


def test_scoped_allowed_agents_whitelist(reg):
    reg.register_tool(make_tool("secret", allowed_agents=["agent_a"]))
    assert reg.scoped("agent_a").get_tool("secret") is not None
    assert reg.scoped("agent_b").get_tool("secret") is None


def test_scoped_open_tool_visible_to_all(reg):
    reg.register_tool(make_tool("open"))  # allowed_agents=None → open
    assert reg.scoped("anyone").get_tool("open") is not None


def test_scoped_deprecated_tool_hidden(reg):
    reg.register_tool(make_tool("old", deprecated=True))
    assert reg.scoped("agent_a").get_tool("old") is None


def test_scoped_list_tools(reg):
    reg.register_tool(make_tool("global_t"))
    scoped = reg.scoped("a")
    scoped.register_tool(make_tool("local_t"))
    names = set(scoped.list_tools())
    assert "global_t" in names
    assert "local_t" in names


def test_scoped_catalog(reg):
    reg.register_tool(make_tool("g"))
    scoped = reg.scoped("a")
    scoped.register_tool(make_tool("l"))
    catalog = scoped.get_catalog()
    names = {e["name"] for e in catalog}
    assert {"g", "l"} == names


# ── Singleton helpers ─────────────────────────────────────────────────────────

def test_get_global_tool_registry_same_instance():
    r1 = get_global_tool_registry()
    r2 = get_global_tool_registry()
    assert r1 is r2


def test_set_global_tool_registry():
    original = get_global_tool_registry()
    new_reg = GlobalToolRegistry()
    set_global_tool_registry(new_reg)
    assert get_global_tool_registry() is new_reg
    set_global_tool_registry(original)  # restore
