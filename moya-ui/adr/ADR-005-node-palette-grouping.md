# ADR-005: Node palette grouped into Core and Advanced tiers

## Status
Accepted

## Date
2026-05-19

## Context

The current node palette shows all 8 node types in a flat list:

```
Input | Output | Agent | Tool | Skill | Parallel | Loop | Branch
```

User research and usage patterns indicate:
- **Input, Agent, Output** — used in every flow; every user needs these immediately
- **Tool, Skill** — used once users understand agent capabilities; intermediate
- **Parallel, Loop, Branch** — control-flow constructs; used by more experienced builders only

Showing all 8 types at once creates visual noise for new users and implies false equivalence between "create an agent" and "configure a loop step".

Options evaluated:

| Option | Description | Rejected because |
|---|---|---|
| Flat list (current) | All 8 types always visible | Overwhelming for new users |
| Searchable palette | Type to filter nodes | Adds interaction cost for basic tasks |
| Tabbed palette | "Basic" tab / "Advanced" tab | Tabs within a sidebar feel nested and cramped |
| **Collapsible sections** | Core always expanded; Advanced collapsed by default | ✓ Progressive disclosure without hiding anything |
| Wizard / guided mode | Step-by-step first flow | Too much for v1 scope |

## Decision

The palette is split into **two collapsible sections**:

**Core** (always expanded by default):
- Input
- Agent
- Output

**Advanced** (collapsed by default, expands on click):
- Tool
- Skill
- Parallel
- Loop
- Branch

Each item shows: icon + name. Description is shown only as a tooltip on hover — not inline.

The section header (`Advanced ▾`) toggles visibility. Once a user expands Advanced, the preference is stored in `localStorage` so it remains open on return visits.

No nodes are removed — this is a presentational grouping only. All 8 types remain fully accessible.

## Consequences

### Positive
- New users see three nodes — far less intimidating
- Advanced users can expand once and the state persists
- No functionality is hidden; experienced users lose nothing
- Tooltips still expose full descriptions on demand

### Negative / Trade-offs
- "Tool" and "Skill" placement in the Advanced tier could slow down users who regularly use them — they must expand the section. Acceptable given the target audience for v1
- If a fourth core concept is added (e.g. a Memory node), the Core/Advanced boundary will need revisiting
