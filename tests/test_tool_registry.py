"""Tests for ToolRegistry CRUD and catalog."""

import pytest
from moya.tools.tool import Tool
from moya.tools.tool_registry import ToolRegistry


def greet(name: str) -> str:
    """Greet someone.

    Parameters:
    - name: The name to greet.
    """
    return f"Hello {name}"


def farewell(name: str) -> str:
    """Say goodbye.

    Parameters:
    - name: The name to address.
    """
    return f"Goodbye {name}"


@pytest.fixture
def registry():
    r = ToolRegistry()
    r.register_tool(Tool(name="greet", function=greet))
    r.register_tool(Tool(name="farewell", function=farewell))
    return r


def test_get_tool(registry):
    assert registry.get_tool("greet") is not None
    assert registry.get_tool("missing") is None


def test_list_tools(registry):
    names = registry.list_tools()
    assert "greet" in names
    assert "farewell" in names


def test_get_tools_returns_all(registry):
    assert len(registry.get_tools()) == 2


def test_catalog_structure(registry):
    catalog = registry.get_catalog()
    names = {t["name"] for t in catalog}
    assert names == {"greet", "farewell"}
    for entry in catalog:
        assert "name" in entry
        assert "description" in entry
        assert "parameters" in entry


def test_overwrite_existing(registry):
    def new_greet(name: str) -> str:
        """New greeting.

        Parameters:
        - name: The name.
        """
        return f"Hi {name}"

    registry.register_tool(Tool(name="greet", function=new_greet))
    assert registry.get_tool("greet").function("World") == "Hi World"


def test_call_via_tool_function(registry):
    tool = registry.get_tool("greet")
    assert tool.function(name="Alice") == "Hello Alice"
