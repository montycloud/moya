# ADR-003: Retain existing React + TypeScript + React Flow + Tailwind stack

## Status
Accepted

## Date
2026-05-19

## Context

The current frontend is built with:
- **React 18** + **TypeScript 5** — component model and type safety
- **@xyflow/react v12** (React Flow) — graph canvas with drag-drop, custom nodes, edge rendering
- **Tailwind CSS v3** — utility-first styling
- **Vite 4.5** — build tool (pinned to v4 due to Node 16 environment constraint)
- **Lucide React** — icon library

At the point of redesign, alternatives were evaluated:

| Alternative | Reason not chosen |
|---|---|
| Vue 3 + Vueflow | Rewrite cost is high; no meaningful gain over current stack |
| Next.js | SSR not needed; adds complexity; Vite is sufficient |
| Svelte + Svelteflow | Ecosystem smaller; team unfamiliar; migration cost not justified |
| shadcn/ui component library | Worth adding on top of Tailwind — evaluated separately |
| Framer Motion for animations | Could be added incrementally; not a stack decision |

The existing stack is well-suited to the use case. React Flow is specifically designed for node-graph UIs and has no viable competitor in the React ecosystem. The TypeScript foundation provides safety for a moderately complex state model.

**One addition is proposed:** [shadcn/ui](https://ui.shadcn.com/) — a collection of accessible, unstyled React components built on Radix UI primitives, styled with Tailwind. This would give us:
- Consistent, accessible UI for Dialog, Dropdown, Tooltip, Badge, Input, Textarea, Select
- No new styling system — it is pure Tailwind under the hood
- Replaces ad-hoc custom components with well-tested primitives

## Decision

**Retain the existing stack** with one addition:

- React 18 + TypeScript 5 ✓ (unchanged)
- @xyflow/react v12 ✓ (unchanged)
- Tailwind CSS v3 ✓ (unchanged)
- Vite 4.5 ✓ (unchanged, Node 16 constraint)
- Lucide React ✓ (unchanged)
- **shadcn/ui** — added for Dialog, Dropdown, Tooltip, Badge, Input, Textarea, Select, Tabs components

shadcn/ui components are copied into `src/components/ui/` (not installed as a package), keeping the dependency footprint small.

## Consequences

### Positive
- Zero rewrite cost — all existing nodes, types, and utilities are retained
- shadcn/ui gives consistent, accessible primitives without a new CSS system
- Team already familiar with the stack
- React Flow is the right tool for the graph canvas — no reason to change it

### Negative / Trade-offs
- Node 16 constraint pins us to Vite 4 — this limits some newer Vite plugin options. Acceptable until the environment is upgraded.
- shadcn/ui adds some Radix UI peer dependencies (`@radix-ui/*`) — small but non-zero bundle size increase
- As the app grows, the lack of a router (see ADR-002) may become a constraint; the stack itself does not prevent adding React Router later
