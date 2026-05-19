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

### 5. Potential Next Features (Not Yet Built)

- [ ] **Settings modal** — API key input for OpenAI/Ollama/Bedrock (Toolbar has `onOpenSettings` stub)
- [ ] **Save / Load flows** — export/import flow JSON to localStorage or file
- [ ] **More MOYA node types** — `MCPClientNode`, `DelegationNode`, `AgentRegistryNode`
- [ ] **Real streaming execution** — connect Simulate to backend SSE when API key is set
- [ ] **Edge labels** — show data flowing along connections in simulation
- [ ] **Validation** — warn when flow has no Input/Output node, disconnected agents, etc.
- [ ] **MOYA framework additions** — streaming improvements, new providers, CLI, more orchestrator patterns

---

*Last updated: 2026-05-13*
