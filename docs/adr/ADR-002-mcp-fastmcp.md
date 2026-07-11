# ADR-002: MCP Integration via fastmcp

**Status:** Accepted  
**Date:** 2026-05-04  
**Deciders:** Karthik Vaidhyanathan

---

## Context

MCP (Model Context Protocol) defines a wire protocol for connecting LLM agents to external tool servers. Two Python libraries exist:

| Library | Maintainer | API Level | Notes |
|---|---|---|---|
| `mcp` | Anthropic (official) | Low-level; mirrors the raw protocol primitives | Verbose; requires manual session management |
| `fastmcp` | Community (Jeremy Howard / fastai lineage) | High-level; wraps `mcp` | Decorator-based server creation; client context manager; popular in practice |

MOYA needs both **client** (calling external MCP servers) and **server** (exposing MOYA tools as an MCP server) capabilities.

---

## Decision

**Use `fastmcp` as the primary MCP dependency.**

`fastmcp` is chosen because:

1. **Server creation is declarative.** Decorating a function with `@mcp.tool()` is all that is needed — no manual schema construction. This maps well to MOYA's existing `Tool` wrapper pattern.
2. **Client usage is a clean context manager.** `async with fastmcp.Client(server) as client: await client.call_tool(...)` is ergonomic and fits MOYA's async-first flow design.
3. **It wraps `mcp`, not replaces it.** Protocol-level compliance is inherited from the official `mcp` package underneath. If Anthropic breaks the low-level API, `fastmcp` absorbs the update.
4. **Active community and frequent releases.** The `moya[mcp]` optional extra pins `fastmcp>=2.0` and gets protocol updates via `fastmcp`'s own dependencies.

---

## Architecture

```
moya/mcp/
├── __init__.py
├── client.py          # MCPClient — wraps fastmcp.Client; handles multi-server namespacing
├── server.py          # MCPServer — wraps a ToolRegistry as a fastmcp server
├── tool_adapter.py    # Converts MCP tool schemas → MOYA Tool objects (and vice versa)
└── config.py          # MCPClientConfig, MCPServerConfig dataclasses
```

**MCPClient** connects to one MCP server. An agent may hold multiple `MCPClient` instances. Tool names are prefixed: `server_alias/tool_name` to avoid collisions.

**MCPServer** iterates over a `ToolRegistry`, registers each `Tool` with `fastmcp`, and starts serving (stdio or HTTP/SSE).

**Tool adapter** converts `fastmcp` JSON Schema tool definitions into MOYA `Tool` objects so the rest of the framework is unaware of the MCP transport layer.

---

## Alternatives Considered

**Use `mcp` (Anthropic official) directly:** More future-proof at the protocol level but significantly more verbose. Writing an MCP server requires constructing protocol primitives manually. Given MOYA prioritises developer experience, the ergonomic overhead is not justified.

**Hand-rolled MCP implementation:** Maximum control but high maintenance burden as the spec evolves. Rejected.

---

## Consequences

- `fastmcp` is an optional dependency: `pip install moya[mcp]` pulls it in.
- `fastmcp` currently requires Python 3.10+ — matches MOYA's minimum.
- If `fastmcp` diverges from the MCP spec in a breaking way, `tool_adapter.py` is the only file that needs updating.
- MOYA's existing `Tool` and `ToolRegistry` interfaces are unchanged; MCP tools appear as regular `Tool` objects to agents.
