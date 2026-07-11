# Moya Agent Studio — Requirements

> **Status:** Draft v1 — decisions locked, ready for implementation.

---

## 1. Vision

Rename and redesign `moya-ui` from "Flow Builder" into **Moya Agent Studio** — a clean, approachable interface where anyone (developer or non-developer) can:

1. **Build** agentic systems visually using a simplified flow canvas.
2. **Test** their agents with real or simulated LLMs.
3. **Publish** finished agents to a shared **Agent Marketplace**.
4. **Discover and run** agents published by others.

The portal is the primary human-facing surface for the Moya framework.

---

## 2. App Structure — Two Main Areas

```
┌─────────────────────────────────────────────────────────────┐
│  Moya Agent Development Portal                              │
│  ─────────────────────────────────────────────────────────  │
│  [ Builder ]   [ Marketplace ]                    [Nav]     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Builder  ←→  Marketplace                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

| Area | Purpose |
|---|---|
| **Builder** | Visual canvas to compose, configure, and test agent flows |
| **Marketplace** | Browse, search, and run published agents |

Navigation is a simple top bar with two tabs. No sidebars or modals for navigation.

---

## 3. Builder — Requirements

### 3.1 Layout (simplified)

Current layout has too many panels competing for space. New layout:

```
┌──────────┬──────────────────────────────────┬───────────────┐
│  Palette │         Canvas                   │  Inspector    │
│  (left,  │  (centre, ~60% width)            │  (right,      │
│  narrow) │                                  │  collapsible) │
│          │                                  │               │
│          ├──────────────────────────────────┤               │
│          │  Output / Trace (bottom, toggle) │               │
└──────────┴──────────────────────────────────┴───────────────┘
```

- **Left palette** — narrower, icon + label only (no long descriptions cluttering it)
- **Canvas** — more breathing room, cleaner grid background
- **Inspector (right)** — slides in when a node is selected; hidden otherwise
- **Bottom panel** — toggled by a single button; shows Output or Trace (not both at once)
- **Top bar** — app name, nav tabs, Run button, Settings icon, Publish button

### 3.2 Node Palette — Simplification

Group nodes into two clear tiers:

**Core nodes** (always visible):
| Node | What it does (one line) |
|---|---|
| Input | Where the user message enters |
| Agent | An LLM-powered agent |
| Output | Where the result comes out |

**Advanced nodes** (collapsed under "Advanced", expand on click):
| Node | What it does (one line) |
|---|---|
| Tool | A Python function the agent can call |
| Skill | Reusable prompt + tools bundle |
| Parallel | Run multiple agents at the same time |
| Loop | Repeat until a condition is met |
| Branch | Route based on a keyword condition |

Each palette item: icon + name + one-line tooltip on hover. No inline descriptions.

### 3.3 Node Cards — Visual Clean-up

Current node cards are dense. New design:

- **Smaller default size** — just enough for the label and type badge
- **Clean colour-coded header strip** (left border accent, not full header bar)
- **No text overflow** — truncate long labels with ellipsis
- **Selected state** — subtle glow/ring, no jarring outline
- **Handles** — small, only visible on hover or when connecting

### 3.4 Inspector Panel

Replaces the current always-visible Properties Panel. Opens as a slide-in panel on the right when a node is selected; closes (or collapses) when canvas is clicked.

Contents per node type:

| Node | Inspector Fields |
|---|---|
| Input | Message (textarea) |
| Agent | Name, Provider (dropdown), Model (dropdown), System Prompt (textarea), Description, Tags |
| Tool | Name, Description, Parameters (add/remove rows), Mock return value |
| Skill | Name, Description, Prompt snippet, Tags |
| Output | (read-only result display) |
| Parallel | Merge strategy (concat / summarise), Branch count |
| Loop | Stop keyword, Max iterations |
| Branch | Condition keyword |

All fields update the node in real-time (no Save button needed).

### 3.5 Canvas Toolbar (top of canvas)

Minimal set of actions:

| Button | Action |
|---|---|
| ▶ Run | Run the flow (simulation or real, depending on settings) |
| Templates ▾ | Dropdown: Simple Chat, Research→Write, Parallel Analysis, Loop Refinement |
| Clear | Reset canvas (with confirmation) |
| Save | Save flow to localStorage (with a name prompt on first save) |
| Load | Load a previously saved flow |
| Publish → | Publish this flow to the Marketplace (opens Publish modal) |

Remove: Settings button from toolbar (move to top-nav gear icon).

### 3.6 Live Code Panel

Keep but make it less prominent:

- Hidden by default; toggled via a `</>` button at the bottom right of the canvas
- Shows the generated Python code in a read-only code block with syntax highlighting
- Copy button in the top-right corner of the code block

### 3.7 Execution Trace

- Shown in the bottom panel, toggled by a separate "Trace" tab
- Each trace event is a row: timestamp | node name | type badge | message
- Animated spinner on the currently-running node
- Clear button to wipe the trace

### 3.8 Run Modes

| Mode | When active | Behaviour |
|---|---|---|
| **Simulation** | No API key set | Client-side mock; no LLM calls; shows plausible fake output |
| **Real** | API key configured in Settings | Calls backend `/api/run`; streams real LLM output via SSE |

A small status pill in the toolbar indicates the current mode: `● Simulation` or `● Live`.

### 3.9 Settings Modal (currently missing — stub only)

Triggered by the gear icon in the top nav. Fields:

- OpenAI API Key (masked input, stored in localStorage)
- Ollama Base URL (default `http://localhost:11434`)
- AWS Region / Bedrock credentials (optional, collapsible)
- Theme: Light / Dark

### 3.10 Save / Load Flows (currently missing)

- **Save**: serialises current nodes + edges to JSON, stores in `localStorage` under a user-chosen name
- **Load**: lists saved flows in a modal; click to restore
- **Export**: downloads the flow JSON as a `.moya-flow.json` file
- **Import**: drag-drop or file-picker to load a `.moya-flow.json` file

---

## 4. Agent Marketplace — Requirements

### 4.1 Purpose

A browsable catalogue of agent flows built and published by users. Each listing represents a complete, runnable Moya agent or multi-agent system.

### 4.2 Marketplace Page Layout

```
┌────────────────────────────────────────────────────────────┐
│  Agent Marketplace                    [ + Publish Agent ]  │
│  ──────────────────────────────────────────────────────    │
│  Search ___________________  Filter: [All ▾] [Tag ▾]       │
│                                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │  Agent   │ │  Agent   │ │  Agent   │ │  Agent   │      │
│  │  Card    │ │  Card    │ │  Card    │ │  Card    │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│                                                            │
│  ┌──────────┐ ┌──────────┐ ...                             │
└────────────────────────────────────────────────────────────┘
```

### 4.3 Agent Card

Each card shows:

- **Name** (bold, truncated at 2 lines)
- **Description** (2–3 lines, truncated)
- **Tags** (up to 3 pill badges, e.g. `research`, `ollama`, `multi-agent`)
- **Provider badge** (openai / ollama / bedrock)
- **Node count** (e.g. "3 agents · 2 tools")
- **Actions**: `▶ Try it` · `< > View Code` · `📋 Clone to Builder`

### 4.4 Agent Detail / Run View

Clicking `▶ Try it` opens a **full chat interface** (right-side drawer or full page):

- Agent name + description in the header
- **Multi-turn conversation** — full chat history preserved during the session
- Streaming responses, token by token
- Each assistant message shows a **agent badge** (which specialist agent / node responded)
- Input box at the bottom with Send button + Enter to submit
- A "Clone to Builder" button in the header — replaces current canvas with this flow (confirmation prompt if canvas has unsaved work)

### 4.5 Publishing a Flow (Publish Modal)

Triggered from the Builder toolbar's "Publish →" button. Steps:

1. **Name** — what to call this agent in the Marketplace
2. **Description** — what it does (textarea, 2–3 sentences)
3. **Tags** — comma-separated (e.g. `travel, research, multi-agent`)
4. **Category** — dropdown: General, Research, Writing, Data, Coding, Customer Support, Other
5. **Visibility** — Public / Unlisted *(v1 scope: all public)*
6. **Confirm** — "Publish to Marketplace"

On publish, the flow JSON + metadata is saved (localStorage for v1; API for v2).

### 4.6 Search and Filter

- **Search bar** — filters by name and description (client-side, instant)
- **Category filter** — dropdown: All, General, Research, Writing, etc.
- **Tag filter** — multi-select pills
- **Sort** — Most Recent (default), A–Z

### 4.7 Marketplace Data Storage

**v1 — Flat-file backend:**
- Published agents stored as a JSON file on disk (`backend/marketplace.json`)
- FastAPI exposes `GET /api/marketplace` and `POST /api/marketplace/publish`
- Storage abstracted behind a `MarketplaceStore` interface so the backend can be swapped to SQLite → PostgreSQL without touching the API layer
- Listings persist across page refreshes and browser sessions
- No auth in v1 — any user can publish and browse

**v2 (future) — DB integration:**
- Replace `MarketplaceStore` flat-file implementation with a SQLAlchemy-backed DB
- Add user identity, versioning, and visibility controls

---

## 5. Visual Design Principles

The current UI feels cluttered and developer-only. New principles:

| Principle | Guidance |
|---|---|
| **White space** | Generous padding; nodes should not feel cramped |
| **Neutral base** | Off-white / light grey background (`#F8F9FA`), not pure white |
| **Colour with purpose** | Node accent colours are kept but used as left-border strips or badges, not full backgrounds |
| **Typography** | One font family (Inter or system-ui); clear hierarchy: `xl` for titles, `sm` for labels |
| **Icons over text** | Use Lucide icons where action is obvious; add tooltip on hover |
| **Dark mode** | Supported via Tailwind `dark:` variants; toggled in Settings |

---

## 6. What Does NOT Change

- The underlying React + TypeScript + React Flow + Tailwind stack stays
- All 8 node types are kept (core vs advanced grouping is a UX change, not a deletion)
- The Python code generator (`codeGenerator.ts`) stays as-is
- The backend FastAPI + SSE architecture stays as-is
- The Vite + proxy setup stays

---

## 7. Out of Scope for v1

- User authentication / accounts
- Backend persistence for the Marketplace (v1 = localStorage)
- Agent versioning
- Comments or ratings on Marketplace listings
- Collaborative editing (multi-user canvas)
- CLI integration
- Mobile layout

---

## 8. Decisions (resolved)

| # | Question | Decision |
|---|---|---|
| 1 | App name | **Moya Agent Studio** |
| 2 | Marketplace v1 storage | **Minimal flat-file backend** (JSON file on disk). Architected for future DB swap-in — storage layer abstracted behind a simple interface. |
| 3 | "Try it" panel | **Full chat interface** — streaming, multi-turn conversation, agent badge per message |
| 4 | Clone to Builder | **Replace current canvas** with a confirmation prompt if the canvas has unsaved changes |
| 5 | Tool + Skill nodes | **Keep separate** — Tool (callable function) and Skill (prompt bundle) remain distinct node types |

---

## 9. Phased Delivery

| Phase | Scope | Goal |
|---|---|---|
| **Phase 1** | UI redesign + simplification of Builder | Cleaner, less cluttered canvas and panels |
| **Phase 2** | Save/Load + Settings modal + Run modes | Builder is fully functional end-to-end |
| **Phase 3** | Marketplace page + Publish flow + Agent cards + flat-file backend | Core Marketplace UX with persistent listings |
| **Phase 4** | "Try it" full chat panel + Clone to Builder + streaming | Marketplace agents are fully runnable |
| **Phase 5** | DB integration (SQLite → Postgres) via MarketplaceStore swap | Production-grade persistence |

---

*Created: 2026-05-19 — Iterate on this document before implementation begins.*
