"""
GlobalToolRegistry — process-wide tool catalog for Moya.

Usage::

    from moya.tools.global_tool_registry import get_global_tool_registry
    registry = get_global_tool_registry()
    registry.register_tool(my_tool)

    # Get a scoped view for a specific agent (respects allowed_agents whitelist)
    scoped = registry.scoped("researcher_agent")
"""

import threading
from typing import Dict, List, Optional, TYPE_CHECKING

from moya.tools.tool import Tool

if TYPE_CHECKING:
    from moya.observability.event_bus import EventBus

_registry_lock = threading.Lock()
_global_registry: Optional["GlobalToolRegistry"] = None


class GlobalToolRegistry:
    """
    Process-wide catalog of all registered tools.

    Thread-safe.  Optionally wired to an EventBus to emit
    ToolRegisteredEvent on each registration.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._tools: Dict[str, Tool] = {}
        self._event_bus: Optional["EventBus"] = None

    def set_event_bus(self, bus: "EventBus") -> None:
        self._event_bus = bus

    def register_tool(self, tool: Tool) -> None:
        with self._lock:
            self._tools[tool.name] = tool
        self._emit_registered(tool)

    def get_tool(self, name: str) -> Optional[Tool]:
        with self._lock:
            return self._tools.get(name)

    def get_tools(self) -> List[Tool]:
        with self._lock:
            return list(self._tools.values())

    def list_tools(self) -> List[str]:
        with self._lock:
            return list(self._tools.keys())

    def remove_tool(self, name: str) -> None:
        with self._lock:
            self._tools.pop(name, None)

    def find_by_category(self, category: str) -> List[Tool]:
        with self._lock:
            return [t for t in self._tools.values() if t.category == category]

    def find_by_tag(self, tag: str) -> List[Tool]:
        with self._lock:
            return [t for t in self._tools.values() if tag in (t.tags or [])]

    def search(self, query: str) -> List[Tool]:
        """Keyword search over tool name and description."""
        q = query.lower()
        with self._lock:
            return [
                t for t in self._tools.values()
                if q in t.name.lower() or q in (t.description or "").lower()
            ]

    def get_catalog(self) -> List[dict]:
        with self._lock:
            return [
                {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters or {},
                    "required": t.required or [],
                    "version": t.version,
                    "category": t.category,
                    "tags": t.tags or [],
                    "deprecated": t.deprecated,
                }
                for t in self._tools.values()
            ]

    def scoped(self, agent_name: str) -> "ScopedToolRegistry":
        """Return a ScopedToolRegistry view for *agent_name*."""
        return ScopedToolRegistry(self, agent_name)

    def _emit_registered(self, tool: Tool) -> None:
        if self._event_bus is None:
            return
        try:
            from moya.observability.events import ToolRegisteredEvent
            self._event_bus.publish(ToolRegisteredEvent(
                source="GlobalToolRegistry",
                tool_name=tool.name,
            ))
        except Exception:
            pass


class ScopedToolRegistry:
    """
    A filtered view of GlobalToolRegistry for a specific agent.

    Agent-local tools registered here are invisible to other agents.
    Tools in the global registry are visible only if ``allowed_agents``
    is ``None`` (open) or contains this agent's name.
    """

    def __init__(self, global_registry: GlobalToolRegistry, agent_name: str) -> None:
        self._global = global_registry
        self._agent_name = agent_name
        self._local: Dict[str, Tool] = {}

    def register_tool(self, tool: Tool) -> None:
        """Register a tool locally (agent-scope only, not global)."""
        self._local[tool.name] = tool

    def get_tool(self, name: str) -> Optional[Tool]:
        if name in self._local:
            return self._local[name]
        tool = self._global.get_tool(name)
        return tool if tool and self._is_allowed(tool) else None

    def get_tools(self) -> List[Tool]:
        result: Dict[str, Tool] = dict(self._local)
        for t in self._global.get_tools():
            if t.name not in result and self._is_allowed(t):
                result[t.name] = t
        return list(result.values())

    def list_tools(self) -> List[str]:
        return [t.name for t in self.get_tools()]

    def get_catalog(self) -> List[dict]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters or {},
                "required": t.required or [],
            }
            for t in self.get_tools()
        ]

    def _is_allowed(self, tool: Tool) -> bool:
        if tool.deprecated:
            return False
        return tool.allowed_agents is None or self._agent_name in tool.allowed_agents


def get_global_tool_registry() -> GlobalToolRegistry:
    """Return (and lazily create) the process-wide GlobalToolRegistry."""
    global _global_registry
    with _registry_lock:
        if _global_registry is None:
            _global_registry = GlobalToolRegistry()
        return _global_registry


def set_global_tool_registry(registry: GlobalToolRegistry) -> None:
    """Replace the process-wide GlobalToolRegistry (useful for testing)."""
    global _global_registry
    with _registry_lock:
        _global_registry = registry
