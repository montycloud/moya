# ADR-002: Two-area navigation — Builder and Marketplace

## Status
Accepted

## Date
2026-05-19

## Context

The original application had a single screen: the flow canvas. Adding a Marketplace requires a clear top-level navigation structure.

Options considered:

| Option | Description | Rejected because |
|---|---|---|
| Single page with sidebar toggle | Marketplace slides in from the side | Clutters the canvas; feels like an afterthought |
| Separate routes (`/builder`, `/marketplace`) | Each area is its own page | Requires a router; adds complexity; page refreshes lose canvas state |
| Modal for Marketplace | Marketplace opens as a full-screen modal | Modals are not appropriate for a primary navigation destination |
| **Two tabs in a top nav bar** | Builder and Marketplace are siblings at the top level | ✓ Chosen |

The top-nav tab approach is standard in creative tools (Figma, VS Code, Retool) and clearly separates the two concerns without requiring routing or nested navigation.

## Decision

The application will have a **persistent top navigation bar** with exactly two primary destinations:

1. **Builder** — the visual flow canvas (the current application, redesigned)
2. **Marketplace** — the catalogue of published agents

Navigation state is managed in React component state (not URL-based routing) for v1. This avoids adding React Router as a dependency and keeps the codebase minimal.

The top bar also contains:
- App name / logo (left)
- Tab switcher: Builder | Marketplace (centre-left)
- Settings gear icon (right)

## Consequences

### Positive
- Clear mental model: you either build or you browse
- No routing library needed in v1 — lower complexity
- Tab UI is universally understood by users
- Canvas state is preserved when switching to Marketplace and back (same React component, just hidden)

### Negative / Trade-offs
- No deep-linking (e.g. `/marketplace/agent-123`) in v1 — users cannot share direct links to a Marketplace listing
- If navigation complexity grows (e.g. a third "Chat" area), a proper router will need to be introduced; this ADR should be revisited at that point
- The Builder canvas is mounted even when Marketplace is active (hidden via CSS) — minimal memory cost but worth monitoring for large flows
