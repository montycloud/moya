# ADR-001: Risk-Based Implementation Phasing

**Status:** Accepted  
**Date:** 2026-05-04  
**Deciders:** Karthik Vaidhyanathan

---

## Context

Seven capability areas have been approved for the MOYA extension initiative (see `REQUIREMENTS.md`). They vary significantly in external-dependency risk:

- **Pure-Python capabilities** (Flow, enhanced registries, Skills) require no new third-party protocol libraries and can be implemented, tested, and iterated on without worrying about upstream API stability.
- **Single-dependency capabilities** (MCP via `fastmcp`, Sub-Agents) introduce one new library but remain largely within MOYA's control.
- **Protocol-compliance capabilities** (A2A via `google-a2a`) require conformance to an external spec, are subject to Google's release cadence, and carry integration risk if the spec changes.

An alternative phasing — value-first or dependency-size-first — would land A2A or MCP earlier but risks building agent registries and flow primitives on unstable ground.

---

## Decision

**Implement in three risk-ordered phases:**

### Phase 1 — Pure-Python Infrastructure (no new external deps)

| Capability | Key Output |
|---|---|
| Global Tool Registry (§2.4) | `moya/tools/global_registry.py`, JSON persistence backend |
| Enhanced Agent Registry (§2.5) | Extended `AgentInfo`, health checks, semantic search interface |
| Agent Flow / Pipelines (§2.1) | `moya/flows/` package — `Step`, `Pipeline`, `ParallelStep`, `BranchStep`, `LoopStep` |
| Skills (§2.6) | `moya/skills/` in core; `moya-skills` distribution for built-in skill library |

### Phase 2 — Single-Dependency Extensions

| Capability | Key Output |
|---|---|
| MCP Support (§2.2) | `moya/mcp/` — `MCPClient`, `MCPServer`; optional `moya[mcp]` extra |
| Sub-Agents (§2.7) | `moya/delegation/` — `DelegationManager`, `delegate()` mixin |

### Phase 3 — Protocol-Heavy Integration

| Capability | Key Output |
|---|---|
| A2A Protocol (§2.3) | `moya/a2a/` — `A2AServer`, `A2AClient`, `A2AAgent`; optional `moya[a2a]` extra |

---

## Alternatives Considered

**Value-first phasing (A2A and MCP first):** Users would get external interoperability sooner, but the internal flow and registry primitives that A2A and MCP build on would not be ready, forcing shortcuts or rework.

**Dependency-size-first (smallest dependencies first):** Similar to risk-first but optimises for install size, not architectural stability. Risk-first is a strict superset of this and also accounts for protocol compliance risk.

**Big-bang (all at once):** Maximises parallelism but makes code review, testing, and rollback very difficult. Not appropriate for a framework where backward compatibility is a hard requirement.

---

## Consequences

- Phase 1 deliverables can be released independently as minor version bumps to `moya`.
- Phase 2 introduces optional extras (`moya[mcp]`) — the core package stays lean.
- Phase 3 introduces a second optional extra (`moya[a2a]`).
- Each phase's output MUST be stable and fully tested before the next phase begins.
- The implementation order within a phase is flexible; phases are the hard ordering constraint.
