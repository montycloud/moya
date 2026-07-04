# ADR-009: "Clone to Builder" replaces canvas without confirmation dialog

## Status
Accepted

## Date
2026-05-19

## Context

When a user finds a Marketplace agent they want to modify, they need a way to bring it into the Builder canvas. The question is what happens to any existing canvas content when they do.

Options evaluated:

| Option | Description | Rejected because |
|---|---|---|
| Open in new browser tab | Clone opens Builder in a new tab | State management across tabs is complex; out of scope for v1 |
| Merge into existing canvas | Add cloned nodes alongside current nodes | Position conflicts; merged graph is likely confusing |
| **Replace canvas, no confirmation** | Cloned flow replaces any existing canvas; user is warned via tooltip only | ✓ Chosen — see rationale below |
| Replace with confirmation dialog | "You have unsaved changes. Replace?" modal | Adds friction for the common case (empty canvas); save/load not yet in v1 scope |
| Replace with auto-save | Auto-save existing flow, then replace | Requires save/load infrastructure; deferred to Phase 2 |

### Rationale for no-confirmation replace

In v1, the Builder has **no save/load functionality** (that is Phase 2 scope). This means:
- The canvas is always ephemeral — there is no "saved state" to protect
- A confirmation dialog asking "are you sure you want to replace?" is misleading when the user cannot save their work anyway
- The honest UX is: the canvas is temporary; clone overwrites it; users who want to preserve work should not clone until Phase 2 save/load is available

A **tooltip on the Clone button** reads: *"This will replace your current canvas. Save your flow first if you want to keep it."* In v1, "save your flow first" is aspirational — the tooltip is forward-looking and sets expectations for Phase 2.

Once Phase 2 (Save/Load) ships, the behavior is revisited: if there are unsaved changes, a confirmation dialog is added. This ADR should be updated at that point.

## Decision

**"Clone to Builder"** works as follows:

1. User clicks **Clone to Builder** on a Marketplace listing card or on the Try it overlay header
2. The app switches the active tab to **Builder**
3. The current canvas nodes and edges are replaced entirely with the cloned flow's nodes and edges
4. React Flow's `fitView()` is called to zoom/pan to fit the newly loaded graph
5. The Inspector is closed (no node selected)
6. A transient toast notification appears: *"Cloned: [Agent Name] — canvas replaced"* (auto-dismisses after 3 seconds)

No confirmation dialog is shown in v1. The Clone button has a tooltip warning that the canvas will be replaced.

### State management
- The clone operation dispatches a `setNodes` + `setEdges` update in `App.tsx` state
- No routing, no new components — this is a state mutation triggered by a button click in the Marketplace component
- The Marketplace component receives a callback prop `onCloneToBuilder(flow: FlowDefinition)` from `App.tsx`

## Consequences

### Positive
- Frictionless path from Marketplace to Builder — one click, you're editing
- No false safety net (no confirmation for a canvas that can't be saved anyway)
- Simple implementation: state mutation + tab switch

### Negative / Trade-offs
- Users who had manually built a flow on the canvas and clicked Clone by accident will lose their work — no undo. Acceptable in v1 because save/load doesn't exist yet; the loss ceiling is "work I did in this browser session"
- The tooltip warning is easy to miss. When Phase 2 save/load ships, this must be upgraded to a confirmation dialog
- `fitView()` may produce an odd zoom level for flows with very few or very many nodes — minor cosmetic issue
