# MOYA Work Log

## Session 1 — Test fixes, Documentation, and UI Builder

---

### 1. Test Suite Fixes

**All 85 tests pass, 0 warnings.**

Fixed `datetime.utcnow()` deprecation (Python 3.12+) in two files:
- `moya/conversation/thread.py:31` — added `timezone` import, replaced `.utcnow()` with `.now(timezone.utc)`
- `moya/conversation/message.py:40` — same fix

```bash
python3 -m pytest tests/ -v  # → 85 passed, 0 warnings
```

---

### 2. Documentation Overhaul

All docs rewritten to use the **correct current API** (`create_agent()` factory, `handle_message()`, `handle_message_stream()`). Previous docs had stale examples.

**Files updated / created:**

| File | What changed |
|---|---|
| `README.md` | Full rewrite: Mermaid system diagram, quick-start examples, key concepts table, updated directory structure |
| `docs/architecture.md` | NEW — 11 Mermaid diagrams: system overview, class hierarchy, tool calling sequence, memory ER, MCP integration, pipeline flowchart, orchestration sequences |
| `docs/quickstart.md` | Rewritten with correct API |
| `docs/agents.md` | Rewritten with correct API |
| `docs/tools.md` | Rewritten with correct API |
| `docs/orchestrators.md` | Rewritten with correct API |
| `docs/memory.md` | Rewritten with correct API |
| `docs/index.md` | Navigation table updated |
| `mkdocs.yml` | Added `architecture.md`, Mermaid rendering via `pymdownx.superfences`, Material theme features |

**`pyproject.toml` fix:** 5 subpackages were missing from the registered packages list — added `moya.delegation`, `moya.flows`, `moya.mcp`, `moya.skills`, `moya.utils` so they're included in the built wheel.

---

### 3. MOYA Flow Builder UI (`moya-ui/`)

A visual low-code interface for composing MOYA multi-agent pipelines. Runs fully in browser in simulation mode (no API key needed).

**Stack:** React 18 + TypeScript + React Flow v12 (`@xyflow/react`) + Tailwind CSS v3 + Vite 4

**Structure:**
```
moya-ui/
├── frontend/
│   └── src/
│       ├── App.tsx                  # Root: canvas + state + drag-and-drop
│       ├── types.ts                 # All data interfaces (extend Record<string,unknown>)
│       ├── constants.ts             # PROVIDER_MODELS, NODE_COLORS, NODE_DEFAULTS, 4 templates
│       ├── components/
│       │   ├── nodes/               # 8 custom node components
│       │   │   ├── NodeWrapper.tsx  # Shared styled wrapper
│       │   │   ├── InputNode.tsx
│       │   │   ├── AgentNode.tsx
│       │   │   ├── ToolNode.tsx
│       │   │   ├── SkillNode.tsx
│       │   │   ├── OutputNode.tsx
│       │   │   ├── ParallelNode.tsx
│       │   │   ├── LoopNode.tsx
│       │   │   └── BranchNode.tsx
│       │   ├── NodePalette.tsx      # Draggable palette (left sidebar)
│       │   ├── PropertiesPanel.tsx  # Per-node config (right sidebar)
│       │   ├── Toolbar.tsx          # Run, Templates, Clear, Settings buttons
│       │   └── BottomPanel.tsx      # Python Code tab + Execution Trace tab
│       └── utils/
│           ├── codeGenerator.ts     # Topological sort → live Python code string
│           └── simulator.ts         # Client-side flow execution (no LLM)
└── backend/
    ├── main.py                      # FastAPI SSE endpoint: POST /api/run
    ├── flow_builder.py              # Rebuilds live MOYA pipeline from JSON graph
    └── requirements.txt
```

**Node types:**

| Node | Color | MOYA equivalent |
|---|---|---|
| Input | Violet | Starting message |
| Agent | Purple | `create_agent("openai", ...)` + `AgentStep` |
| Tool | Orange | `Tool(...)` attached via `ToolRegistry` |
| Skill | Pink | `Skill(...)` injected into system prompt |
| Output | Green | Terminal node |
| Parallel | Cyan | `ParallelStep([...])` |
| Loop | Red | `LoopStep(agent, stop_keyword=..., max_iter=...)` |
| Branch | Amber | `BranchStep(condition_fn, true_step, false_step)` |

**Key features:**
- Drag nodes from palette → drop on canvas
- Click node → configure in right Properties Panel
- Python code panel updates **live** as you edit
- 4 built-in templates: Simple Chat, Research→Write, Parallel Analysis, Loop Refinement
- **Simulate** button: runs the whole flow client-side with animated trace events, no API key needed
- Optional real execution: start `backend/main.py` + enter OpenAI key in Settings

**Build status:** ✅ `npm run build` passes (1754 modules, 0 errors). Dev server runs at `http://localhost:5173`.

```bash
cd moya-ui/frontend
npm install
npm run dev       # → http://localhost:5173
```

---

### 4. Key Technical Gotchas (React Flow v12)

These bit us during the build — important for future changes:

1. **`nodeTypes` must be defined at module scope** (never inside the component function). Inlining it causes all nodes to remount on every render.
2. **All node data interfaces must extend `Record<string, unknown>`** — required by v12's generic constraint `NodeProps<Node<DataType>>`.
3. **`node.type` is `string | undefined`** in v12 — always use `node.type ?? ''` when passing to functions that expect `string`.
4. **`screenToFlowPosition()`** replaces `project()` from v11.
5. **`updateNodeData(id, partialData)`** replaces manual node-spreading for updates.
6. **`ReactFlowProvider` must wrap `App`** in `main.tsx` so `useReactFlow()` works inside `App`.
7. **Vite v6 requires Node.js 18+** — current env is Node 16, so we use Vite v4.5.3.

---

### 5. Feature Status

- [x] **Settings modal** — API key input for OpenAI/Ollama/Bedrock (`SettingsModal.tsx`)
- [x] **Save / Load flows** — named saves, export/import JSON, auto-save to localStorage
- [x] **More MOYA node types** — `MCPNode` (amber), `A2ANode` (rose); MCP + A2A templates
- [x] **Real streaming execution** — FastAPI SSE backend; Real / Simulation mode toggle
- [x] **Edge animation** — edges glow amber (node running) → indigo (node completed)
- [x] **Validation** — warns on missing Output node or isolated agents (yellow trace rows)
- [x] **Agent Marketplace** — Phases 1–5 complete; flat-file + SQLite backends; Try-it chat

---

## Session 2 — Phase 4 Framework Completion

### 1. pyproject.toml Fixes

- **Bug fix**: Added `moya.observability` to the `[tool.setuptools] packages` list (was missing — observability module would not ship in wheel)
- **New extra `mcp`**: `pip install moya-ai[mcp]` now installs `mcp>=1.0.0` (the MCP Python SDK)
- **New extra `observability`**: marker extra (pure stdlib, no deps) for discoverability
- **Updated `all`**: includes `mcp>=1.0.0`, `a2a-sdk>=1.0.3`, `httpx`, `starlette`, `sse-starlette`

### 2. CI Config

Created `.github/workflows/ci.yml`:
- Triggers on push to `main` / `moya-v2-karthik` and PRs to `main`
- Matrix: Python 3.11 and 3.12
- Installs `.[all,a2a,mcp]` and runs `pytest tests/ -v`

### 3. UI — Edge Animation (data flow visualisation)

`App.tsx`: `displayEdges` memo derived from `traceEvents`:
- Edge source **started** → amber stroke + 3px width + animated
- Edge source **completed** → indigo stroke + animated
- Resets automatically when a new run begins

### 4. UI — Flow Validation Warnings

`handleRun` in `App.tsx` now emits soft warning trace events (amber rows in Output panel):
- **No Output node** — warns, does not block the run
- **Isolated agents** — lists agents with no connections; they will be skipped

`types.ts`: Added `'warning'` to `TraceEvent.status`.
`BottomPanel.tsx`: `TraceRow` renders warning events with amber badge + amber background.

---

*Last updated: 2026-07-04*
