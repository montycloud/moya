# ADR-006: Replace always-visible Properties Panel with slide-in Inspector

## Status
Accepted

## Date
2026-05-19

## Context

The current layout has a **permanently visible Properties Panel** on the right side of the screen. It occupies roughly 280px of horizontal space at all times, even when no node is selected (in which case it shows a placeholder "Select a node").

Problems with the current approach:
1. **Wastes space** — the panel is empty most of the time
2. **Shrinks the canvas** — the single most important area (the flow canvas) loses 25–30% of its width permanently
3. **Visual clutter** — an empty right panel draws the eye and adds noise
4. **Not scalable** — as more node types are added (MCP, Delegation), the panel grows longer and harder to scroll

Options evaluated:

| Option | Description | Rejected because |
|---|---|---|
| Always-visible panel (current) | Right sidebar always shown | Wastes canvas space |
| **Slide-in drawer on node click** | Panel animates in from right when a node is selected | ✓ Chosen |
| Floating popover on node | Properties appear in a floating card near the node | Overlaps the canvas; awkward for long forms |
| Bottom panel for properties | Properties panel at the bottom | Conflicts with the existing Trace/Code panel |
| Modal dialog | Click node → modal opens | Breaks the flow of visual editing; too disruptive |

## Decision

The Properties Panel is replaced by a **slide-in Inspector drawer** that:

- Is **hidden by default** — no panel occupies the right edge when nothing is selected
- **Slides in** (200ms ease transition) from the right when any node is clicked
- **Collapses** when the user clicks the canvas background or presses Escape
- Has a **close button (✕)** in the top-right corner of the drawer
- Overlays the canvas slightly (semi-transparent backdrop is NOT used — the drawer sits beside the canvas, not over it)
- Width: fixed 320px — enough for all current field types without scrolling for most nodes

The canvas itself expands to fill the full width when the Inspector is closed, giving more working space.

### Implementation note

React Flow's `onNodeClick` callback triggers the Inspector open state. `onPaneClick` (clicking blank canvas) triggers close. This requires no changes to the node components themselves — state is managed in `App.tsx`.

## Consequences

### Positive
- Canvas gets ~30% more horizontal space in the common case (no node selected)
- Clean, uncluttered layout at rest
- Familiar pattern (used in Figma, Framer, Retool, VS Code Extensions panel)
- Smooth animation makes the interaction feel intentional and polished

### Negative / Trade-offs
- Users cannot see both the canvas and the Inspector simultaneously at full fidelity on small screens — the Inspector partially overlaps on viewports narrower than 1200px. Acceptable; a responsive mobile layout is out of scope for v1
- The transition adds ~200ms latency to editing after clicking a node — negligible, but different from the current zero-latency permanent panel
- Users who want to edit node properties and watch the canvas simultaneously (e.g. drag a connected node while the panel is open) may find it slightly awkward — the canvas is still interactive behind the Inspector
