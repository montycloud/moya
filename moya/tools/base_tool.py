"""
BaseTool for Moya.

Describes a generic interface for a "tool" that an agent can discover and call.
"""

import abc


class BaseTool(abc.ABC):
    """
    Abstract base class for all Moya tools.
    Tools are callable utilities that agents can invoke (e.g., MemoryTool, WebSearchTool).
    """

    def __init__(self, name: str, description: str):
        """
        :param name: Unique name for the tool (e.g., 'MemoryTool').
        :param description: Short explanation of the tool's functionality.
        """
        self._name = name
        self._description = description

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description
