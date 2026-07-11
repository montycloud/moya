"""
Tests for moya.mcp — MCPAuthConfig, schema conversion, and round-trip integration.

Unit tests mock the MCP session; the integration test spins up a real MCPServer
subprocess and connects with MCPClient.from_subprocess().
"""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch

from moya.mcp.client import (
    MCPAuthConfig,
    MCPClient,
    MCPConnectionError,
    _convert_prop,
    _resolve_type,
)


# ── MCPAuthConfig ─────────────────────────────────────────────────────────────

class TestMCPAuthConfig:
    def test_bearer_token(self):
        auth = MCPAuthConfig(bearer_token="my-jwt")
        h = auth.to_headers()
        assert h["Authorization"] == "Bearer my-jwt"

    def test_api_key_default_header(self):
        auth = MCPAuthConfig(api_key="sk-123")
        h = auth.to_headers()
        assert h["X-API-Key"] == "sk-123"

    def test_api_key_custom_header(self):
        auth = MCPAuthConfig(api_key="token", api_key_header="Authorization")
        h = auth.to_headers()
        assert h["Authorization"] == "token"

    def test_extra_headers(self):
        auth = MCPAuthConfig(extra_headers={"X-Tenant": "acme", "X-Version": "2"})
        h = auth.to_headers()
        assert h["X-Tenant"] == "acme"
        assert h["X-Version"] == "2"

    def test_bearer_and_extra_headers_merged(self):
        auth = MCPAuthConfig(bearer_token="tok", extra_headers={"X-Custom": "val"})
        h = auth.to_headers()
        assert h["Authorization"] == "Bearer tok"
        assert h["X-Custom"] == "val"

    def test_both_bearer_and_api_key(self):
        auth = MCPAuthConfig(bearer_token="jwt", api_key="key")
        h = auth.to_headers()
        assert h["Authorization"] == "Bearer jwt"
        assert h["X-API-Key"] == "key"

    def test_empty_config_returns_empty_dict(self):
        assert MCPAuthConfig().to_headers() == {}

    def test_from_url_accepts_auth(self):
        """MCPClient.from_url forwards auth headers — verify no TypeError."""
        auth = MCPAuthConfig(bearer_token="tok")
        # We just verify the constructor path doesn't raise before connection attempt
        with pytest.raises(MCPConnectionError):
            MCPClient.from_url("http://localhost:9999/sse", auth=auth, timeout=0.1)


# ── Schema type resolution ────────────────────────────────────────────────────

class TestResolveType:
    def test_plain_string(self):
        assert _resolve_type({"type": "string"}) == "string"

    def test_plain_integer(self):
        assert _resolve_type({"type": "integer"}) == "integer"

    def test_plain_boolean(self):
        assert _resolve_type({"type": "boolean"}) == "boolean"

    def test_plain_object(self):
        assert _resolve_type({"type": "object"}) == "object"

    def test_plain_array(self):
        assert _resolve_type({"type": "array"}) == "array"

    def test_missing_type_defaults_to_string(self):
        assert _resolve_type({}) == "string"

    def test_unknown_type_defaults_to_string(self):
        assert _resolve_type({"type": "custom"}) == "string"

    def test_list_type_picks_non_null(self):
        assert _resolve_type({"type": ["string", "null"]}) == "string"

    def test_list_type_null_first(self):
        assert _resolve_type({"type": ["null", "integer"]}) == "integer"

    def test_anyof_nullable(self):
        schema = {"anyOf": [{"type": "string"}, {"type": "null"}]}
        assert _resolve_type(schema) == "string"

    def test_anyof_nullable_null_first(self):
        schema = {"anyOf": [{"type": "null"}, {"type": "number"}]}
        assert _resolve_type(schema) == "number"

    def test_oneof_nullable(self):
        schema = {"oneOf": [{"type": "boolean"}, {"type": "null"}]}
        assert _resolve_type(schema) == "boolean"

    def test_anyof_all_null_fallback(self):
        schema = {"anyOf": [{"type": "null"}]}
        assert _resolve_type(schema) == "string"


# ── Property conversion ───────────────────────────────────────────────────────

class TestConvertProp:
    def test_simple_string(self):
        p = _convert_prop("name", {"type": "string", "description": "A name"}, [])
        assert p["type"] == "string"
        assert p["description"] == "A name"
        assert p["required"] is False

    def test_required_flag(self):
        p = _convert_prop("q", {"type": "string", "description": "Query"}, ["q"])
        assert p["required"] is True

    def test_enum_preserved(self):
        p = _convert_prop("mode", {
            "type": "string",
            "description": "Mode",
            "enum": ["fast", "slow"],
        }, [])
        assert p["enum"] == ["fast", "slow"]

    def test_array_items_preserved(self):
        p = _convert_prop("tags", {
            "type": "array",
            "description": "Tags",
            "items": {"type": "string"},
        }, [])
        assert p["type"] == "array"
        assert p["items"] == {"type": "string"}

    def test_nested_object_properties_preserved(self):
        p = _convert_prop("config", {
            "type": "object",
            "description": "Config",
            "properties": {
                "key": {"type": "string"},
                "value": {"type": "integer"},
            },
        }, [])
        assert p["type"] == "object"
        assert "properties" in p
        assert p["properties"]["key"] == {"type": "string"}

    def test_nullable_anyof_extracts_type(self):
        p = _convert_prop("opt", {
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "description": "Optional text",
        }, [])
        assert p["type"] == "string"
        assert p["description"] == "Optional text"

    def test_nullable_anyof_preserves_enum(self):
        p = _convert_prop("status", {
            "anyOf": [
                {"type": "string", "enum": ["active", "inactive"]},
                {"type": "null"},
            ],
            "description": "Status",
        }, [])
        assert p["type"] == "string"
        assert p["enum"] == ["active", "inactive"]

    def test_number_constraints_preserved(self):
        p = _convert_prop("count", {
            "type": "integer",
            "description": "Count",
            "minimum": 0,
            "maximum": 100,
        }, [])
        assert p["minimum"] == 0
        assert p["maximum"] == 100

    def test_string_constraints_preserved(self):
        p = _convert_prop("name", {
            "type": "string",
            "description": "Name",
            "minLength": 1,
            "maxLength": 50,
            "pattern": "^[a-z]+$",
        }, [])
        assert p["minLength"] == 1
        assert p["maxLength"] == 50
        assert p["pattern"] == "^[a-z]+$"

    def test_missing_description_uses_param_name(self):
        p = _convert_prop("my_param", {"type": "string"}, [])
        assert p["description"] == "my_param"

    def test_no_extra_keys_when_none_present(self):
        p = _convert_prop("x", {"type": "string", "description": "X"}, [])
        assert "enum" not in p
        assert "items" not in p
        assert "properties" not in p


# ── _convert_tool (via mocked MCP tool object) ────────────────────────────────

def _make_mcp_tool(name, description, input_schema):
    t = MagicMock()
    t.name = name
    t.description = description
    t.inputSchema = input_schema
    return t


class TestConvertTool:
    def setup_method(self):
        self.client = MCPClient.__new__(MCPClient)
        self.client.name = "test_server"
        self.client._session = MagicMock()
        self.client._loop = MagicMock()

    def test_namespaced_tool_name(self):
        mcp_tool = _make_mcp_tool("search", "Search", {
            "type": "object",
            "properties": {"q": {"type": "string", "description": "Query"}},
            "required": ["q"],
        })
        tool = self.client._convert_tool(mcp_tool)
        assert tool.name == "test_server__search"

    def test_description_passed_through(self):
        mcp_tool = _make_mcp_tool("calc", "A calculator", {"type": "object", "properties": {}})
        tool = self.client._convert_tool(mcp_tool)
        assert tool.description == "A calculator"

    def test_empty_description_uses_fallback(self):
        mcp_tool = _make_mcp_tool("x", "", {"type": "object", "properties": {}})
        tool = self.client._convert_tool(mcp_tool)
        assert "MCP tool" in tool.description

    def test_simple_parameters_converted(self):
        mcp_tool = _make_mcp_tool("greet", "Greet", {
            "type": "object",
            "properties": {"name": {"type": "string", "description": "Name"}},
            "required": ["name"],
        })
        tool = self.client._convert_tool(mcp_tool)
        assert "name" in tool.parameters
        assert tool.parameters["name"]["type"] == "string"
        assert tool.parameters["name"]["required"] is True

    def test_enum_parameter_preserved(self):
        mcp_tool = _make_mcp_tool("set_mode", "Set mode", {
            "type": "object",
            "properties": {
                "mode": {"type": "string", "description": "Mode",
                         "enum": ["fast", "slow", "auto"]}
            },
            "required": [],
        })
        tool = self.client._convert_tool(mcp_tool)
        assert tool.parameters["mode"]["enum"] == ["fast", "slow", "auto"]

    def test_array_items_preserved(self):
        mcp_tool = _make_mcp_tool("filter", "Filter items", {
            "type": "object",
            "properties": {
                "ids": {"type": "array", "description": "IDs",
                        "items": {"type": "integer"}}
            },
            "required": [],
        })
        tool = self.client._convert_tool(mcp_tool)
        assert tool.parameters["ids"]["type"] == "array"
        assert tool.parameters["ids"]["items"] == {"type": "integer"}

    def test_nullable_param_resolved(self):
        mcp_tool = _make_mcp_tool("search", "Search", {
            "type": "object",
            "properties": {
                "filter": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "description": "Optional filter",
                }
            },
            "required": [],
        })
        tool = self.client._convert_tool(mcp_tool)
        assert tool.parameters["filter"]["type"] == "string"

    def test_no_parameters_gives_empty_dict(self):
        mcp_tool = _make_mcp_tool("ping", "Ping", {"type": "object", "properties": {}})
        tool = self.client._convert_tool(mcp_tool)
        assert tool.parameters == {}

    def test_required_list_passed_to_tool(self):
        mcp_tool = _make_mcp_tool("create", "Create", {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name"},
                "desc": {"type": "string", "description": "Desc"},
            },
            "required": ["name"],
        })
        tool = self.client._convert_tool(mcp_tool)
        assert tool.required == ["name"]

    def test_tool_function_calls_server(self):
        """The generated tool_fn calls back to the MCP session."""
        mcp_tool = _make_mcp_tool("add", "Add", {
            "type": "object",
            "properties": {
                "a": {"type": "integer", "description": "a"},
                "b": {"type": "integer", "description": "b"},
            },
            "required": ["a", "b"],
        })
        tool = self.client._convert_tool(mcp_tool)

        # Patch call_tool to verify it's invoked
        self.client.call_tool = MagicMock(return_value="42")
        result = tool.function(a=1, b=2)
        self.client.call_tool.assert_called_once_with("add", {"a": 1, "b": 2})
        assert result == "42"


# ── OpenAI get_tool_definitions schema passthrough ────────────────────────────

class TestOpenAISchemaPassthrough:
    def _make_agent_with_tool(self, parameters):
        from moya.tools.tool import Tool
        from moya.tools.tool_registry import ToolRegistry
        from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig

        def fn(**kwargs): return "ok"
        fn.__doc__ = "Test tool."

        registry = ToolRegistry()
        registry.register_tool(Tool(name="test_tool", function=fn,
                                    parameters=parameters))
        os.environ.setdefault("OPENAI_API_KEY", "sk-test")
        config = OpenAIAgentConfig(
            agent_name="a", agent_type="openai", description="Test",
            api_key="sk-test", tool_registry=registry, is_tool_caller=True,
        )
        agent = OpenAIAgent(config)
        agent.client = MagicMock()
        return agent

    def test_simple_type_passed_through(self):
        agent = self._make_agent_with_tool({
            "q": {"type": "string", "description": "Query"}
        })
        defs = agent.get_tool_definitions()
        prop = defs[0]["function"]["parameters"]["properties"]["q"]
        assert prop["type"] == "string"
        assert prop["description"] == "Query"

    def test_enum_passed_through(self):
        agent = self._make_agent_with_tool({
            "mode": {"type": "string", "description": "Mode",
                     "enum": ["fast", "slow"]}
        })
        defs = agent.get_tool_definitions()
        prop = defs[0]["function"]["parameters"]["properties"]["mode"]
        assert prop["enum"] == ["fast", "slow"]

    def test_array_items_passed_through(self):
        agent = self._make_agent_with_tool({
            "ids": {"type": "array", "description": "IDs",
                    "items": {"type": "integer"}}
        })
        defs = agent.get_tool_definitions()
        prop = defs[0]["function"]["parameters"]["properties"]["ids"]
        assert prop["items"] == {"type": "integer"}

    def test_nested_properties_passed_through(self):
        agent = self._make_agent_with_tool({
            "cfg": {"type": "object", "description": "Config",
                    "properties": {"key": {"type": "string"}}}
        })
        defs = agent.get_tool_definitions()
        prop = defs[0]["function"]["parameters"]["properties"]["cfg"]
        assert "properties" in prop
        assert prop["properties"]["key"] == {"type": "string"}


# ── Integration test — real MCPServer subprocess ──────────────────────────────

MINI_SERVER = """\
from moya.mcp import MCPServer
from moya.tools.tool import Tool
from moya.tools.tool_registry import ToolRegistry

def echo(message: str) -> str:
    \"\"\"Echo the message back.
    Parameters:
    - message: Text to echo.
    \"\"\"
    return f"echo: {message}"

def add(a: int, b: int) -> int:
    \"\"\"Add two integers.
    Parameters:
    - a: First operand.
    - b: Second operand.
    \"\"\"
    return a + b

registry = ToolRegistry()
registry.register_tool(Tool(name="echo", function=echo))
registry.register_tool(Tool(name="add", function=add))
server = MCPServer(name="test_srv", tool_registry=registry)
server.run()
"""


@pytest.fixture(scope="module")
def mcp_client(tmp_path_factory):
    """Start a real MCPServer subprocess and connect MCPClient to it."""
    tmp = tmp_path_factory.mktemp("mcp")
    script = tmp / "mini_server.py"
    script.write_text(MINI_SERVER)

    try:
        client = MCPClient.from_subprocess(
            command=sys.executable,
            args=[str(script)],
            name="test_srv",
            timeout=15.0,
        )
        yield client
        client.close()
    except MCPConnectionError as exc:
        pytest.skip(f"MCP subprocess could not start: {exc}")


class TestMCPIntegration:
    def test_tool_discovery(self, mcp_client):
        tools = mcp_client.get_tools()
        names = {t.name for t in tools}
        assert "test_srv__echo" in names
        assert "test_srv__add" in names

    def test_echo_tool_call(self, mcp_client):
        result = mcp_client.call_tool("echo", {"message": "hello"})
        assert "hello" in result

    def test_add_tool_call(self, mcp_client):
        result = mcp_client.call_tool("add", {"a": 3, "b": 4})
        assert "7" in result

    def test_tool_function_callable(self, mcp_client):
        tools = {t.name: t for t in mcp_client.get_tools()}
        result = tools["test_srv__echo"].function(message="world")
        assert "world" in result

    def test_tool_parameters_present(self, mcp_client):
        tools = {t.name: t for t in mcp_client.get_tools()}
        echo_tool = tools["test_srv__echo"]
        assert echo_tool.parameters is not None

    def test_ping(self, mcp_client):
        assert mcp_client.ping() is True
