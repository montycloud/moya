"""
moya.mcp — Model Context Protocol support for MOYA.

Connect agents to external MCP tool servers (MCPClient) or expose
MOYA tools to other MCP clients (MCPServer).

Quick start::

    from moya.mcp import MCPClient, MCPServer

    # Use tools from an external MCP server
    with MCPClient.from_subprocess("python3", ["my_server.py"], name="srv") as client:
        for tool in client.get_tools():
            tool_registry.register_tool(tool)

    # Expose your MOYA tools as an MCP server
    server = MCPServer(name="my_tools", tool_registry=tool_registry)
    server.run()   # blocks — run this as a standalone process
"""

from moya.mcp.client import MCPClient, MCPConnectionError, MCPAuthConfig
from moya.mcp.server import MCPServer

__all__ = ["MCPClient", "MCPConnectionError", "MCPAuthConfig", "MCPServer"]
