"""
ToolRegistry for Moya.

A centralized place where tools (e.g., MemoryTool) can be registered
and discovered by agents.
"""

from typing import Dict, Optional, List
from moya.tools.base_tool import BaseTool


class ToolRegistry:
    """
    Holds references to various tools and allows dynamic discovery
    by name. Agents can call 'get_tool("MemoryTool")' to retrieve
    and invoke the tool's methods.
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register_tool(self, tool: BaseTool) -> None:
        """
        Register a tool. If a tool with the same name exists, it gets overwritten.
        """
        self._tools[tool.name] = tool

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        Retrieve a registered tool by name.
        """
        return self._tools.get(tool_name)

    def list_tools(self) -> List[str]:
        """
        Return a list of all registered tool names.
        """
        return list(self._tools.keys())
