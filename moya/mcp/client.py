"""
MCPClient — connect MOYA agents to any MCP-compliant tool server.

Tools discovered from an MCP server are returned as regular MOYA Tool objects,
so agents use them exactly like any locally registered tool — no API changes needed.

Supported transports
--------------------
- **stdio** (subprocess): server runs as a child process; communication over stdin/stdout.
- **HTTP/SSE**: server runs as an HTTP service; communication via Server-Sent Events.

Usage::

    from moya.mcp import MCPClient, MCPAuthConfig
    from moya.tools.tool_registry import ToolRegistry

    # --- stdio (subprocess) ---
    client = MCPClient.from_subprocess(
        command="python3",
        args=["my_mcp_server.py"],
        name="my_server",
    )

    # --- HTTP/SSE with auth ---
    auth = MCPAuthConfig(bearer_token="my-token")
    client = MCPClient.from_url("http://localhost:8000/sse", name="remote_server", auth=auth)

    # Discover tools and add them to a shared ToolRegistry
    tool_registry = ToolRegistry()
    for tool in client.get_tools():
        tool_registry.register_tool(tool)

    # Tools are now available to any agent that uses this registry.
    client.close()

    # Or use as a context manager:
    with MCPClient.from_subprocess("python3", ["server.py"], name="srv") as client:
        for tool in client.get_tools():
            tool_registry.register_tool(tool)
"""

import asyncio
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from moya.tools.tool import Tool


# ── Auth config ───────────────────────────────────────────────────────────────

@dataclass
class MCPAuthConfig:
    """
    Authentication configuration for MCPClient HTTP/SSE connections.

    Exactly one of ``bearer_token`` or ``api_key`` is typically set.
    Both can be set simultaneously if the server needs them.
    ``extra_headers`` accepts any additional headers needed.

    Usage::

        # Bearer token (OAuth / JWT)
        auth = MCPAuthConfig(bearer_token="eyJ...")

        # API key in a custom header
        auth = MCPAuthConfig(api_key="sk-...", api_key_header="X-API-Key")

        # Raw headers (escape hatch)
        auth = MCPAuthConfig(extra_headers={"X-Tenant": "acme"})
    """

    bearer_token: Optional[str] = None
    api_key: Optional[str] = None
    api_key_header: str = "X-API-Key"
    extra_headers: Dict[str, str] = field(default_factory=dict)

    def to_headers(self) -> Dict[str, str]:
        """Return the headers dict to pass to the HTTP transport."""
        headers: Dict[str, str] = dict(self.extra_headers)
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"
        if self.api_key:
            headers[self.api_key_header] = self.api_key
        return headers


# ── Schema conversion helpers ─────────────────────────────────────────────────

_JSON_TYPE_MAP = {
    "string": "string",
    "integer": "integer",
    "number": "number",
    "boolean": "boolean",
    "object": "object",
    "array": "array",
}

# Schema fields preserved verbatim so LLM providers receive full constraints
_PASSTHROUGH_KEYS = (
    "enum",
    "items",
    "properties",
    "additionalProperties",
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "minLength",
    "maxLength",
    "minItems",
    "maxItems",
    "pattern",
    "default",
    "examples",
)


def _resolve_type(pinfo: Dict[str, Any]) -> str:
    """
    Extract a single JSON-Schema type string from a property schema.

    Handles:
    - Plain ``{"type": "string"}``
    - List types ``{"type": ["string", "null"]}`` → picks first non-null
    - ``{"anyOf": [...]}`` / ``{"oneOf": [...]}`` nullable union → non-null branch
    - Falls back to ``"string"`` for unrecognised shapes.
    """
    # anyOf / oneOf nullable pattern
    for key in ("anyOf", "oneOf"):
        if key in pinfo:
            variants = pinfo[key]
            non_null = [v for v in variants if isinstance(v, dict) and v.get("type") != "null"]
            if non_null:
                return _resolve_type(non_null[0])
            return "string"

    raw = pinfo.get("type", "string")

    # JSON Schema allows type to be a list: ["string", "null"]
    if isinstance(raw, list):
        raw = next((t for t in raw if t != "null"), "string")

    return _JSON_TYPE_MAP.get(str(raw), "string")


def _convert_prop(pname: str, pinfo: Dict[str, Any], required_list: List[str]) -> Dict[str, Any]:
    """
    Convert a single MCP JSON-Schema property to MOYA parameter format.

    Always produces ``type`` and ``description``.
    Preserves ``enum``, ``items``, ``properties``, and other schema
    constraints so they can be forwarded to LLM providers.
    """
    # Unwrap anyOf / oneOf to get the base schema for type resolution
    base = pinfo
    for key in ("anyOf", "oneOf"):
        if key in pinfo:
            variants = pinfo[key]
            non_null = [v for v in variants if isinstance(v, dict) and v.get("type") != "null"]
            if non_null:
                base = {**non_null[0], "description": pinfo.get("description", pname)}
            break

    result: Dict[str, Any] = {
        "type": _resolve_type(pinfo),
        "description": pinfo.get("description") or base.get("description") or pname,
        "required": pname in required_list,
    }

    # Preserve rich schema constraints from the resolved base
    for key in _PASSTHROUGH_KEYS:
        val = base.get(key) if base is not pinfo else pinfo.get(key)
        if val is not None:
            result[key] = val

    return result


# ── MCPClient ─────────────────────────────────────────────────────────────────

class MCPConnectionError(Exception):
    """Raised when the connection to the MCP server fails."""


class MCPClient:
    """
    Synchronous MCP client that wraps an async MCP connection in a background thread.

    Do not instantiate directly — use the class-method constructors:
    ``MCPClient.from_subprocess()`` or ``MCPClient.from_url()``.
    """

    def __init__(self, name: str = "mcp_server") -> None:
        self.name = name
        self._session = None
        self._connected = threading.Event()
        self._connection_error: Optional[Exception] = None
        self._shutdown_event: Optional[asyncio.Event] = None

        # Dedicated event loop running in a daemon background thread.
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._loop_thread.start()

    # ── Constructors ──────────────────────────────────────────────────────────

    @classmethod
    def from_subprocess(
        cls,
        command: str,
        args: Optional[List[str]] = None,
        name: str = "mcp_server",
        env: Optional[Dict[str, str]] = None,
        timeout: float = 15.0,
    ) -> "MCPClient":
        """
        Connect to an MCP server running as a child subprocess (stdio transport).

        Args:
            command:  Executable to run (e.g. ``"python3"``).
            args:     Command-line arguments (e.g. ``["server.py"]``).
            name:     Logical name used to namespace tool names (``name__tool``).
            env:      Optional environment variables for the subprocess.
            timeout:  Seconds to wait for the server to be ready.
        """
        client = cls(name=name)
        client._start_stdio_connection(command, args or [], env, timeout)
        return client

    @classmethod
    def from_url(
        cls,
        url: str,
        name: str = "mcp_server",
        auth: Optional[MCPAuthConfig] = None,
        headers: Optional[Dict[str, Any]] = None,
        timeout: float = 15.0,
    ) -> "MCPClient":
        """
        Connect to an MCP server over HTTP/SSE.

        Args:
            url:      Full URL of the SSE endpoint (e.g. ``"http://host:8000/sse"``).
            name:     Logical name used to namespace tool names.
            auth:     Structured authentication config (API key / Bearer token).
            headers:  Raw headers dict — merged with ``auth.to_headers()`` when both
                      are provided.  Prefer ``auth`` for authentication headers.
            timeout:  Seconds to wait for the server to be ready.
        """
        merged_headers: Dict[str, str] = {}
        if auth:
            merged_headers.update(auth.to_headers())
        if headers:
            merged_headers.update(headers)
        client = cls(name=name)
        client._start_http_connection(url, merged_headers or None, timeout)
        return client

    # ── Public API ────────────────────────────────────────────────────────────

    def get_tools(self) -> List[Tool]:
        """
        Discover all tools advertised by the MCP server.

        Returns MOYA Tool objects with namespaced names (``server_name__tool_name``).
        These can be registered directly in a ToolRegistry.
        """
        self._require_session()
        future = asyncio.run_coroutine_threadsafe(
            self._session.list_tools(), self._loop
        )
        result = future.result(timeout=10)
        return [self._convert_tool(t) for t in result.tools]

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Call a tool on the MCP server directly (without going through a ToolRegistry).

        Args:
            tool_name:  The bare tool name (without server namespace prefix).
            arguments:  Dict of argument name → value.
        Returns:
            The tool's text output as a string.
        """
        self._require_session()
        future = asyncio.run_coroutine_threadsafe(
            self._session.call_tool(tool_name, arguments), self._loop
        )
        result = future.result(timeout=30)
        if not result.content:
            return ""
        return "\n".join(
            c.text for c in result.content if hasattr(c, "text") and c.text
        )

    def ping(self) -> bool:
        """Return True if the MCP server is still reachable."""
        try:
            future = asyncio.run_coroutine_threadsafe(
                self._session.send_ping(), self._loop
            )
            future.result(timeout=5)
            return True
        except Exception:
            return False

    def close(self) -> None:
        """Shut down the connection and stop the background thread."""
        if self._shutdown_event and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._shutdown_event.set)
            time.sleep(0.5)
        if self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

    def __enter__(self) -> "MCPClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # ── Internal — event loop ─────────────────────────────────────────────────

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _submit(self, coro, timeout: float = 30):
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=timeout)

    def _require_session(self) -> None:
        if not self._session:
            raise MCPConnectionError(
                "MCPClient is not connected. "
                "Use MCPClient.from_subprocess() or MCPClient.from_url()."
            )

    # ── Internal — stdio connection ───────────────────────────────────────────

    def _start_stdio_connection(
        self, command: str, args: List[str], env: Optional[dict], timeout: float
    ) -> None:
        resolved_env = self._resolve_env(env)
        asyncio.run_coroutine_threadsafe(
            self._keep_alive_stdio(command, args, resolved_env), self._loop
        )
        connected = self._connected.wait(timeout=timeout)
        # The event is also set when the connection *fails* — so check the
        # recorded error regardless of whether the wait timed out.
        if self._connection_error is not None:
            raise MCPConnectionError(
                f"Failed to connect to MCP server. Error: {self._connection_error}"
            )
        if not connected:
            raise MCPConnectionError(
                f"Failed to connect to MCP server within {timeout}s."
            )

    async def _keep_alive_stdio(
        self, command: str, args: List[str], env: Optional[dict]
    ) -> None:
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client

            self._shutdown_event = asyncio.Event()
            params = StdioServerParameters(command=command, args=args, env=env)

            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    self._session = session
                    self._connected.set()
                    await self._shutdown_event.wait()
        except Exception as exc:
            self._connection_error = exc
            self._connected.set()

    # ── Internal — HTTP/SSE connection ────────────────────────────────────────

    def _start_http_connection(
        self, url: str, headers: Optional[dict], timeout: float
    ) -> None:
        asyncio.run_coroutine_threadsafe(
            self._keep_alive_http(url, headers), self._loop
        )
        connected = self._connected.wait(timeout=timeout)
        # The event is also set when the connection *fails* — so check the
        # recorded error regardless of whether the wait timed out.
        if self._connection_error is not None:
            raise MCPConnectionError(
                f"Failed to connect to MCP server at {url}. Error: {self._connection_error}"
            )
        if not connected:
            raise MCPConnectionError(
                f"Failed to connect to MCP server at {url} within {timeout}s."
            )

    async def _keep_alive_http(self, url: str, headers: Optional[dict]) -> None:
        try:
            from mcp import ClientSession
            from mcp.client.sse import sse_client

            self._shutdown_event = asyncio.Event()
            async with sse_client(url, headers=headers or {}) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    self._session = session
                    self._connected.set()
                    await self._shutdown_event.wait()
        except Exception as exc:
            self._connection_error = exc
            self._connected.set()

    # ── Internal — environment helpers ────────────────────────────────────────

    @staticmethod
    def _resolve_env(env: Optional[dict]) -> dict:
        base = dict(os.environ) if env is None else dict(env)
        extra_paths = [p for p in sys.path if p and os.path.isdir(p)]
        if extra_paths:
            existing = base.get("PYTHONPATH", "")
            merged = os.pathsep.join(extra_paths + ([existing] if existing else []))
            base["PYTHONPATH"] = merged
        return base

    # ── Internal — tool conversion ────────────────────────────────────────────

    def _convert_tool(self, mcp_tool: Any) -> Tool:
        """Convert an MCP Tool descriptor into a MOYA Tool."""
        bare_name = mcp_tool.name
        namespaced_name = f"{self.name}__{bare_name}"
        client_ref = self

        def tool_fn(**kwargs) -> str:
            return client_ref.call_tool(bare_name, kwargs)

        tool_fn.__name__ = bare_name

        input_schema = mcp_tool.inputSchema or {}
        props = input_schema.get("properties", {})
        required_list: List[str] = input_schema.get("required", [])

        moya_params: Dict[str, Dict[str, Any]] = {
            pname: _convert_prop(pname, pinfo, required_list)
            for pname, pinfo in props.items()
        }

        return Tool(
            name=namespaced_name,
            description=mcp_tool.description or f"MCP tool: {bare_name}",
            function=tool_fn,
            parameters=moya_params if moya_params else {},
            required=required_list,
        )
