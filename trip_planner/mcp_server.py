"""
MCP Server for the MOYA Trip Planner demo.

Run this script directly to start an MCP-compliant tool server on stdio.
The server exposes the four trip-data tools from tools.py so that any
MCP client (including MOYA's MCPClient) can discover and call them.

Usage (standalone)::

    python3 trip_planner/mcp_server.py

Typical usage — launched as a subprocess by agents.py::

    client = MCPClient.from_subprocess(
        command=sys.executable,
        args=["trip_planner/mcp_server.py"],
        name="trip_tools",
    )
"""

import sys
import os

# Allow running from repo root or from this directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from moya.mcp import MCPServer
from moya.tools.tool import Tool
from moya.tools.tool_registry import ToolRegistry
from trip_planner.tools import (
    get_destination_facts,
    estimate_trip_cost,
    get_weather_summary,
    get_visa_requirements,
)

if __name__ == "__main__":
    registry = ToolRegistry()
    registry.register_tool(Tool(name="get_destination_facts", function=get_destination_facts))
    registry.register_tool(Tool(name="estimate_trip_cost",    function=estimate_trip_cost))
    registry.register_tool(Tool(name="get_weather_summary",   function=get_weather_summary))
    registry.register_tool(Tool(name="get_visa_requirements", function=get_visa_requirements))

    server = MCPServer(name="trip_tools", tool_registry=registry)
    server.run()   # blocks — serves MCP requests over stdio
