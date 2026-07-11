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

## Session 3 — Agent capabilities: Tools, Memory & MCP per agent

Agents are now richly configurable from the inspector. Config is additive and
backward-compatible (existing flows still load).

### 1. Framework — real memory subsystem (`moya/memory/`)

Three new `Repository` implementations, composable per agent:
- `short_term_memory.py` — `ShortTermMemory(window_size=N)`: in-RAM, trims each
  thread to the last N messages (working context).
- `long_term_memory.py` — `LongTermMemory(base_path=…)`: disk-backed (wraps
  `FileSystemRepository`); adds `recall(thread_id, query, k)` ranking messages by
  keyword overlap + recency.
- `composite_memory.py` — `CompositeMemory([...])`: fan-out writes to every store,
  reads from the primary (first); `recall` delegates to the first store that supports it.
- `__init__.py` exports all three.

**Bug fix (`file_system_repo.py`):** `create_thread` wrote the metadata line without
a trailing newline, so the first `append_message` concatenated onto it and the first
message was lost on read. Now always newline-terminated.

**Bug fix (`moya/mcp/client.py`):** `from_url`/`from_subprocess` returned a broken
client instead of raising when a connection failed fast (the failure sets the same
`_connected` event success uses, so the `if not wait()` guard was skipped). Now the
recorded `_connection_error` is checked after the wait. This also de-flakes
`test_mcp.py::test_from_url_accepts_auth` (was failing ~2/3 full-suite runs).

Tests: `tests/test_memory_types.py` (15). Full suite **354 passed**, stable across 4 runs.

### 2. UI — Tool Registry library + per-agent inspector config

- `components/ToolRegistryLibrary.tsx` — reusable shared tool library (localStorage
  `moya_tool_registry`), modeled on `SkillsLibrary`. Opened via a new **Tools** button
  in the toolbar.
- `Inspector.tsx` `AgentForm` gains three collapsible sections:
  - **Tools** — checklist of registry tools + inline one-off tools
  - **Memory** — short-term (window size) and/or long-term (path) toggles
  - **MCP Servers** — add/remove per-agent MCP connections (transport/url/command/args/apiKey)
- `AgentNode.tsx` shows capability chips (`N tools · memory · N mcp`) on the canvas.
- `types.ts` — `RegistryTool`, `InlineTool`, `AgentMemoryConfig`, `AgentMCP`; extended
  `AgentNodeData` with `toolIds` / `inlineTools` / `memory` / `mcpServers`.

### 3. Code generation + live backend

- `codeGenerator.ts` — now takes `registryTools`; emits a **per-agent** `<agent>_registry`
  (registry tools + inline tools + edge tools + per-agent `MCPClient`s), plus
  `ShortTermMemory` / `LongTermMemory` / `CompositeMemory` wired into `create_agent(memory=…)`.
  Verified: generated Python parses and all imports resolve against the framework.
- `flow_builder.py` (real mode) — mirrors codegen: builds each agent's `ToolRegistry`,
  composite memory, and MCP connections; MCP failures degrade to an amber trace warning
  instead of killing the run. Registry tools arrive via a new `registry_tools` payload
  field (`main.py`, `runner.ts`).
- `simulator.ts` — agents surface their tools/memory/MCP in the simulated trace output.

---

## Session 4 — Executable tools, A2A-as-provider, memory clarity

Follow-up on feedback: tools weren't runnable, memory was unclear, and MCP/A2A nodes were
redundant now that MCP is per-agent.

### 1. Executable tools (API endpoint or Python function)

Tools now carry a `kind: 'python' | 'api'` plus `code` / `method` / `url` / `headers`
(alongside `mockReturnValue` for simulation). Applies to registry tools, inline agent tools,
and the standalone Tool node.
- `components/ToolExecEditor.tsx` (new, shared) — params editor + Python|API toggle +
  code box / URL+headers + simulated-return. Used by `ToolRegistryLibrary`, the inline-tool
  editor, and `ToolForm`.
- `codeGenerator.ts` — Python tools emit a real function body; API tools emit a `requests`
  call with `{param}` URL substitution + parsed headers.
- `flow_builder.py` — `_build_tool_callable()` execs the Python body (real signature) or
  builds an HTTP closure; `requests` added to `backend/requirements.txt`.
- Verified: generated Python parses, imports resolve, and both a Python tool (`add(2,3)=5`)
  and the backend builder execute.

### 2. A2A folded into the agent; MCP/A2A nodes removed

- `AgentNodeData.provider` gains `'a2a'`; agent gets `endpointUrl` / `timeoutSeconds`. When
  provider is A2A the inspector shows endpoint + timeout and hides model/prompt/tools/memory;
  the node shows an `A2A · <endpoint>` subtitle + `remote` chip.
- codegen + `flow_builder.py` emit `A2AAgent(A2AAgentConfig(...))` for A2A agents.
- Removed the palette **Integrations** section, `mcp`/`a2a` node types, `MCPNode`/`A2ANode`
  components, their inspector forms, the MCP/A2A templates, and the `MCPNodeData`/`A2ANodeData`
  types. Per-agent MCP (inspector) stays.

### 3. Memory clarity

Inspector Memory section now explains the model (per-thread store→recall each turn) with
distinct short-term vs long-term descriptions; the simulator emits a clear
"recalled earlier context / storing this exchange" trace line.

**Verification:** frontend `tsc` + `npm run build` clean; `pytest` 354 passed; codegen harness
produces valid runnable Python for python/api tools + an A2A agent; screenshot confirms chips
(`2 tools · memory · 1 mcp`) and the A2A `remote` agent; Integrations palette section gone.

### 4. Node deletion with confirmation

- `Delete` **or** `Backspace` (Mac) on a selected node now prompts a confirmation modal, then
  removes the node + its edges. `App.tsx`: `onBeforeDelete` returns a Promise resolved by the
  modal; `deleteKeyCode={['Delete','Backspace']}`; `onNodesDelete` clears the selection.
- Inspector header gains a trash button (routes through `deleteElements` → same confirm).
- Edge-only deletions skip the prompt.

### 5. API tool request body

- Tools gained a `body` field — a JSON request-body template shown for POST/PUT/PATCH in
  `ToolExecEditor`. `{param}` placeholders are substituted via per-parameter `.replace()`
  (not `str.format`, which would choke on literal JSON braces), so `{"item": "{item}"}` stays
  valid JSON. Empty body = send all params as JSON. `Content-Type: application/json` is added
  automatically when a body is present and none is set.
- Wired through `types.ts`, `ToolExecEditor`, `codeGenerator.ts`, `flow_builder.py`,
  `constants.ts`. Verified: generated POST tool substitutes params, keeps braces, parses as
  JSON, and sets the header.

---

## Session 6 — Starter examples + flow templates

Functional templates so people have something to learn from, in both the framework and the UI.
Each showcases **memory + tools + multiple agents**.

### Framework examples (`examples/`)

- **`research_assistant/`** — a 2-agent `Pipeline` (`researcher` → `writer`). The researcher
  calls real Python tools (`search_knowledge`, `list_related_topics`); both agents share a
  `CompositeMemory` (long-term on disk + short-term window). Prior turns are recalled and
  injected, so a follow-up ("how is it *different*?") remembers turn 1.
- **`support_desk/`** — `AgentRegistry` + `DelegationManager` route to a `billing_agent` or
  `shipping_agent` (deterministic keyword router). Specialists share tools (`lookup_order`,
  `refund_policy`) and a `CompositeMemory` that remembers the order id across turns — even
  across a hand-off to a different agent.
- Both pick OpenAI when `OPENAI_API_KEY` is set, else local Ollama, and ship a
  `--check` mode that exercises tools + memory + build with no LLM call. READMEs included.
- Key detail: agents auto-store to memory via `_remember`, but `_build_conversation` does
  **not** auto-recall — so the examples recall + inject explicitly (the reliable pattern).

### UI flow templates (`constants.ts`)

- **"Research Assistant (tools + memory)"** and **"Support Desk (routing + tools + memory)"**
  added to the Templates menu, mirroring the framework examples with inline Python tools and
  per-agent memory. Support Desk uses a `branch` to route Triage → Shipping / Billing.

**Verification:** both examples' `--check` pass; `pytest` 354 passed; frontend `tsc` + build
clean; codegen for both templates produces Python that parses; screenshot confirms the Support
Desk template renders with branch + tool/memory chips. Demo memory output is gitignored
(`moya_memory/`).

---

*Last updated: 2026-07-05*
