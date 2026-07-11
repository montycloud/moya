"""
MCPServer — expose a MOYA ToolRegistry as an MCP-compliant server.

Any MCP client (another MOYA agent, a Claude client, an IDE extension, etc.)
can discover and call your MOYA tools through this server.

Usage::

    from moya.mcp import MCPServer
    from moya.tools.tool_registry import ToolRegistry
    from moya.tools.tool import Tool

    def add(a: int, b: int) -> int:
        \"\"\"Add two integers.\"\"\"
        return a + b

    registry = ToolRegistry()
    registry.register_tool(Tool(name="add", function=add))

    server = MCPServer(name="my_tools", tool_registry=registry)
    server.run()        # stdio (default) — run as subprocess
    # server.run("sse") # HTTP/SSE — run as HTTP service on port 8000

When used as a standalone script the server blocks and serves MCP requests
until the process is killed. Clients connect via ``MCPClient.from_subprocess()``.
"""

from typing import Optional

from moya.tools.tool import Tool
from moya.tools.tool_registry import ToolRegistry


class MCPServer:
    """
    Wraps a MOYA ToolRegistry as an MCP-compliant server using FastMCP.

    Args:
        name:           Server name announced in the MCP handshake.
        tool_registry:  ToolRegistry whose tools will be exposed. Additional
                        registries or individual tools can be added later.

    Example::

        server = MCPServer(name="research_tools", tool_registry=registry)
        server.run()
    """

    def __init__(
        self,
        name: str = "moya",
        tool_registry: Optional[ToolRegistry] = None,
    ) -> None:
        try:
            from mcp.server.fastmcp import FastMCP
        except ImportError as exc:
            raise ImportError(
                "The 'mcp' package is required for MCPServer. "
                "Install it with: pip install mcp"
            ) from exc

        self._mcp = FastMCP(name)
        self.name = name

        if tool_registry:
            self.add_tool_registry(tool_registry)

    # ------------------------------------------------------------------
    # Tool registration
    # ------------------------------------------------------------------

    def add_tool_registry(self, registry: ToolRegistry) -> None:
        """
        Register all tools from a ToolRegistry with this server.

        Can be called multiple times to add tools from different registries.
        """
        for tool in registry.get_tools():
            self.add_tool(tool)

    def add_tool(self, tool: Tool) -> None:
        """
        Register a single MOYA Tool with this server.

        The tool's Python function is registered directly — FastMCP uses its
        type hints to build the MCP JSON schema. Tools without type hints are
        still registered but will have a permissive schema.
        """
        if not tool.function:
            return
        self._mcp.add_tool(
            tool.function,
            name=tool.name,
            description=tool.description,
        )

    # ------------------------------------------------------------------
    # Running the server
    # ------------------------------------------------------------------

    def run(self, transport: str = "stdio") -> None:
        """
        Start the MCP server (blocking call).

        Args:
            transport:  ``"stdio"`` (default) for subprocess mode — the server
                        communicates over stdin/stdout. Clients use
                        ``MCPClient.from_subprocess()`` to connect.

                        ``"sse"`` for HTTP/Server-Sent Events mode — the server
                        listens on a port and clients connect via
                        ``MCPClient.from_url()``.

        Note:
            This method blocks until the process is killed. It is intended to
            be the sole entry point when the script is run as a subprocess.
        """
        self._mcp.run(transport=transport)
