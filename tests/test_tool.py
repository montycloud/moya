"""Tests for Tool auto-introspection and validation."""

import pytest
from moya.tools.tool import Tool


def simple(x: int, y: str) -> str:
    """Add a number to a string.

    Parameters:
    - x: The integer value.
    - y: The string value.
    """
    return f"{x}{y}"


def no_params() -> str:
    """A tool with no parameters."""
    return "ok"


def test_auto_description():
    t = Tool(name="simple", function=simple)
    assert "Add a number" in t.description


def test_auto_parameters_types():
    t = Tool(name="simple", function=simple)
    assert t.parameters["x"]["type"] == "integer"
    assert t.parameters["y"]["type"] == "string"


def test_auto_parameters_descriptions():
    t = Tool(name="simple", function=simple)
    assert "integer" in t.parameters["x"]["description"].lower() or len(t.parameters["x"]["description"]) > 0
    assert t.parameters["y"]["description"] != ""


def test_no_params_tool():
    t = Tool(name="noop", function=no_params)
    assert t.parameters == {}


def test_explicit_parameters_accepted():
    t = Tool(
        name="manual",
        function=simple,
        parameters={"x": {"type": "integer", "description": "num"}},
    )
    assert t.parameters["x"]["type"] == "integer"


def test_invalid_type_raises():
    with pytest.raises(ValueError, match="invalid type"):
        Tool(
            name="bad",
            function=simple,
            parameters={"x": {"type": "badtype", "description": "d"}},
        )


def test_missing_description_key_raises():
    with pytest.raises(ValueError, match="missing required key"):
        Tool(
            name="bad",
            function=simple,
            parameters={"x": {"type": "string"}},
        )


def test_function_required():
    with pytest.raises((ValueError, TypeError)):
        Tool(name="nofunc")


def test_no_provider_methods():
    t = Tool(name="t", function=simple)
    assert not hasattr(t, "get_openai_definition")
    assert not hasattr(t, "get_bedrock_definition")
    assert not hasattr(t, "get_ollama_definition")
