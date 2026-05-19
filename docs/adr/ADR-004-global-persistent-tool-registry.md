# ADR-004: Global Persistent Tool Registry

**Status:** Accepted  
**Date:** 2026-05-04  
**Deciders:** Karthik Vaidhyanathan

---

## Context

The current `ToolRegistry` is:
- **Per-agent**: each agent holds its own registry instance; tools are not shared.
- **In-memory only**: tools are re-registered on every process start.
- **Flat**: no versioning, no rich metadata, no access control.
- **Opaque**: no catalog view, no semantic search.

As MOYA scales to many agents and many tools (including MCP-backed tools), a per-agent ephemeral registry becomes impractical. Governance (who can use which tool), discovery (which tool does X), and observability (how often is tool Y failing) require a centralised, persistent catalog.

---

## Decision

**Replace the per-agent ephemeral model with a global persistent `ToolRegistry` that serves as the single source of truth. The existing per-agent `ToolRegistry` API is preserved as a scoped proxy/view over the global registry.**

### Architectural Model

```
GlobalToolRegistry  (persistent; one per MOYA deployment)
    │
    ├── StorageBackend (pluggable)
    │   ├── JsonStorageBackend   ← default
    │   └── SqliteStorageBackend ← future
    │
    └── AgentToolView(agent_name)  ← what agents receive as "their" ToolRegistry
            - filters to tools accessible by that agent
            - presents the same API as the old ToolRegistry (full backward compat)
```

### ToolRecord (replaces Tool for storage)

```python
@dataclass
class ToolRecord:
    name: str
    version: str                         # semver, e.g. "1.0.0"
    description: str
    parameters: Dict[str, Any]           # JSON Schema object
    required: List[str]
    tags: List[str]
    author: str
    backend: str                         # "local" | "mcp:<server_alias>"
    allowed_agents: Optional[List[str]]  # None = all agents
    deprecated: bool
    # Telemetry (runtime-updated, not persisted to JSON)
    call_count: int
    error_count: int
    avg_latency_ms: float
```

The existing `Tool` dataclass is unchanged — it remains the runtime object that agents receive. `ToolRecord` is the catalog entry that is persisted.

### Migration Path

Existing code that creates a `ToolRegistry` and registers tools continues to work. On first use, tools are automatically promoted to the global registry with `version="1.0.0"` and `allowed_agents=None`.

```python
# Existing code — still works
tool_registry = ToolRegistry()
tool_registry.register_tool(my_tool)

# New code — explicit global registration
from moya.tools import GlobalToolRegistry
GlobalToolRegistry.register(ToolRecord(...))
```

### Tool Versioning

Multiple versions of a tool can coexist under the same name. The latest non-deprecated version is returned by default. Agents may pin: `GlobalToolRegistry.get("my_tool", version="1.2.0")`.

---

## Alternatives Considered

**Keep per-agent registries, add a voluntary global catalog alongside them:** This avoids any migration but creates two sources of truth. Tool governance would require checking both. Rejected for complexity.

**Global registry with no backward-compatible proxy:** Cleaner architecture but breaks every existing example and user code. Rejected because backward compatibility is a hard requirement.

---

## Consequences

- **Breaking risk is low**: the `AgentToolView` proxy means `agent.tool_registry.register_tool(...)` still works.
- The `GlobalToolRegistry` is a process-level singleton by default; tests can reset it.
- JSON persistence means the tool catalog survives restarts — tools do not need to be re-registered in setup scripts.
- MCP-discovered tools (ADR-002) are registered with `backend="mcp:<alias>"` and their invocations are routed to the right `MCPClient` at call time.
- Semantic search over tools (tag/description similarity) is enabled by the rich `ToolRecord` metadata and the `EmbeddingProvider` interface (ADR-005).
