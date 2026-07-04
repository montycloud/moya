# Moya Agent Studio

A visual builder for multi-agent pipelines. Drag, connect, and configure nodes on a canvas to compose MOYA flows — watch the generated Python code update live, simulate execution in the browser, or run it for real against a local Ollama or OpenAI backend.

---

## What you can do

- **Build** multi-agent pipelines visually — no code required to get started
- **Understand** how MOYA's Pipeline, AgentStep, ParallelStep, LoopStep, and BranchStep work through live code generation
- **Simulate** any flow instantly in the browser without an API key
- **Run for real** against Ollama (local) or OpenAI with a single click
- **Publish** flows to a local Marketplace so others can discover and clone them
- **Try** any Marketplace agent interactively before cloning it

---

## Quick start

### Option 1 — startup script (recommended)

Requires Python 3.9+ and Node 18+.

```bash
cd moya-ui
./start.sh
```

That's it. The script:
1. Checks that Python and Node are installed
2. Installs all Python and npm dependencies (first run only)
3. Starts the FastAPI backend on **http://localhost:8000**
4. Starts the Vite frontend on **http://localhost:5173**
5. Ctrl+C cleanly stops both

On subsequent runs you can skip the install step for a faster start:

```bash
./start.sh --no-install
```

---

### Option 2 — run manually in two terminals

**Terminal 1 — backend**

```bash
cd moya-ui/backend
pip install -r requirements.txt
python3 main.py
# → http://localhost:8000
```

**Terminal 2 — frontend**

```bash
cd moya-ui/frontend
npm install
npm run dev
# → http://localhost:5173
```

---

### Option 3 — Docker (OpenAI / deployment use case)

Requires Docker and Docker Compose.

```bash
cd moya-ui
cp .env.example .env        # add your OPENAI_API_KEY
docker compose up --build
# → frontend on http://localhost:3000
# → backend  on http://localhost:8000
```

> **Ollama + Docker:** Ollama needs GPU access and must run on the host, not inside a container. If you use Ollama, stick with Option 1 or 2 and point the Studio at `http://localhost:11434` in Settings.

---

## The interface

```
┌─ Top nav ──────────────────────────────────────────────────────── ⚙ ─┐
│  Moya Agent Studio    Builder  |  Marketplace                         │
├─ Toolbar ──────────────────────────────────────────────────────────────┤
│  Templates  Skills  Publish  ·····  Clear  [Code] [Trace]  Mode  Run  │
├─ Palette ─┬─ Canvas ─────────────────────────────────────────────────┤
│  Input    │                                                            │
│  Agent    │   [Input] ──► [Researcher] ──► [Writer] ──► [Output]      │
│  Output   │                                                            │
│  ─────    │   Click a node → Properties panel slides in from right     │
│  Tool     │   Code / Trace panels slide up from bottom on demand       │
│  Skill    │                                                            │
│  Parallel │                                                            │
│  Loop     │                                                            │
│  Branch   │                                                            │
└───────────┴────────────────────────────────────────────────────────────┘
```

---

## Building a flow

### 1 — Add nodes

Drag any node from the left palette onto the canvas. A node's properties panel opens automatically when you drop it.

### 2 — Connect nodes

Drag from the **right handle** of one node to the **left handle** of another. Edges show direction of data flow.

**Special connection rules:**
- Drag a **Tool → Agent** to give that agent access to the tool function
- Drag a **Skill → Agent** to attach a reusable prompt snippet to the agent

### 3 — Configure properties

Click any node to open its property panel (slides in from the right). Press **Escape** to close it.

### 4 — Run

Click **Run** in the toolbar. The **Trace** panel opens automatically and shows each step as it executes.

### 5 — See the code

Click **Code** in the toolbar to open the Python code panel. It updates live as you edit the canvas — this is the generated MOYA code you would run outside the Studio.

---

## Node types

| Node | Purpose | MOYA equivalent |
|---|---|---|
| **Input** | Starting message for the pipeline | `pipeline.run(message=...)` |
| **Agent** | An LLM agent with a provider, model, and system prompt | `create_agent(provider, ...)` |
| **Tool** | A callable function the agent can invoke | `Tool(name, function)` + `ToolRegistry` |
| **Skill** | A reusable prompt snippet bundled as a capability | `Skill(name, prompt_snippet)` |
| **Output** | Terminal node — displays the final result | — |
| **Parallel** | Runs multiple agents concurrently and merges results | `ParallelStep` |
| **Loop** | Repeats an agent until a stop keyword appears in the output | `LoopStep` |
| **Branch** | Routes to one of two paths based on a keyword condition | `BranchStep` |

---

## Agent providers

Each Agent node lets you pick a provider. In Real mode the backend creates the corresponding MOYA agent:

| Provider | What you need |
|---|---|
| **Ollama** | Ollama running locally (`http://localhost:11434`). Free, offline, GPU optional. |
| **OpenAI** | `OPENAI_API_KEY` entered in Settings |
| **AWS Bedrock** | AWS credentials + region configured in Settings |
| **Azure OpenAI** | Azure endpoint + key (Bedrock/Azure need additional MOYA config) |

---

## Run modes

Switch modes using the dropdown in the toolbar (right side, next to the Run button).

### Simulation (default — no API key needed)

Runs entirely in the browser. Each agent returns a descriptive placeholder response. All node types (Parallel, Loop, Branch) execute their logic so you can verify the flow structure before spending API credits.

### Real

POSTs the flow to the FastAPI backend and streams live trace events back via SSE. The actual LLM is called for each Agent node.

**First-time setup for Real mode:**
1. Make sure the backend is running (`./start.sh` does this automatically)
2. Click the **⚙** gear icon in the top-right corner
3. Verify the Backend URL shows green — *Backend reachable*
4. Enter your OpenAI API key if using OpenAI agents
5. Adjust the Ollama URL if Ollama is not on the default port

Settings are saved in the browser (localStorage) so you only need to do this once.

---

## Skills Library

Skills let you define reusable prompt snippets and attach them to any agent.

1. Click **Skills** in the toolbar
2. Click **New Skill** and fill in:
   - **Name** — e.g. `Travel Safety Advisor`
   - **Description** — one line summary
   - **Prompt Snippet** — appended to the agent's system prompt at runtime
   - **Bundled Tools** — optional comma-separated function names
3. Click **Save Skill**

To use a skill: drag a **Skill** node onto the canvas, click it, and pick from the *Load from Skills Library* dropdown — or type the snippet directly.

Skills are saved in the browser across sessions.

---

## Templates

The **Templates** dropdown (toolbar, left side) loads a ready-made flow instantly, replacing the current canvas.

| Template | What it demonstrates |
|---|---|
| Simple Chat | Single agent — the most basic MOYA pipeline |
| Research → Write | Sequential two-agent pipeline |
| Parallel Analysis | Benefits + risks agents running concurrently |
| Loop Refinement | Agent iterates until a stop keyword appears in its output |

---

## Marketplace

The **Marketplace** tab is a gallery of agent flows you can clone and try.

### Clone to Builder
Loads the flow into the Builder so you can edit it, run it, or use it as a starting point.

### Try it
Opens a simulation modal — type any message and watch the flow execute step by step. No API key needed.

### Publish your own agent
1. Build a flow in the Builder
2. Click **Publish** in the toolbar
3. Give it a name, description, category, and tags
4. It appears in the Marketplace under **My Agents**

Published agents are stored in the browser (localStorage). The **My Agents** filter tab shows only yours, and you can delete them with the trash icon on the card.

---

## Settings

Click **⚙** in the top-right corner of the nav bar.

| Setting | Default | Description |
|---|---|---|
| Backend URL | `http://localhost:8000` | Address of the running FastAPI server |
| OpenAI API Key | — | Required for `openai` provider agents in Real mode |
| Ollama URL | `http://localhost:11434` | Ollama server address |
| AWS Region | `us-east-1` | Region used for AWS Bedrock calls |

Click **Test** next to the Backend URL to verify the connection before switching to Real mode.

---

## Architecture

```
moya-ui/
├── start.sh                  # One-command startup script (recommended)
├── docker-compose.yml        # Docker option (OpenAI / deployment)
├── Dockerfile.backend        # FastAPI image (built from repo root)
├── Dockerfile.frontend       # nginx image serving the Vite build
├── .env.example              # Copy to .env for Docker usage
│
├── frontend/                 # React 18 + TypeScript + Vite + Tailwind
│   └── src/
│       ├── App.tsx                    # Root component — all state lives here
│       ├── types.ts                   # Shared TypeScript interfaces
│       ├── constants.ts               # NODE_COLORS, TEMPLATES, NODE_DEFAULTS
│       ├── components/
│       │   ├── nodes/                 # 8 React Flow custom node components
│       │   │   ├── NodeWrapper.tsx    # Shared header + handle layout
│       │   │   ├── AgentNode.tsx
│       │   │   ├── InputNode.tsx
│       │   │   ├── OutputNode.tsx
│       │   │   ├── ToolNode.tsx
│       │   │   ├── SkillNode.tsx
│       │   │   ├── ParallelNode.tsx
│       │   │   ├── LoopNode.tsx
│       │   │   └── BranchNode.tsx
│       │   ├── TopNav.tsx             # Navigation bar + Settings trigger
│       │   ├── Toolbar.tsx            # Run, Templates, Skills, Publish, mode
│       │   ├── NodePalette.tsx        # Draggable node palette (left sidebar)
│       │   ├── Inspector.tsx          # Per-node property panel (right overlay)
│       │   ├── BottomPanel.tsx        # Code + Trace slide-up panels
│       │   ├── SkillsLibrary.tsx      # Skills CRUD overlay (left)
│       │   ├── Marketplace.tsx        # Gallery + Try it modal
│       │   └── SettingsModal.tsx      # API keys + backend URL config
│       └── utils/
│           ├── codeGenerator.ts       # Graph → Python code string
│           ├── simulator.ts           # Client-side flow execution (no LLM)
│           └── runner.ts              # Real-mode SSE runner (calls backend)
│
└── backend/                  # FastAPI + MOYA
    ├── main.py                # POST /api/run → SSE stream of trace events
    ├── flow_builder.py        # Builds live MOYA pipeline from flow JSON
    └── requirements.txt
```

### How the backend works

`POST /api/run` accepts the flow graph (nodes + edges + api_config) and:
1. Builds real MOYA `Agent`, `Tool`, `Skill` objects from the node data
2. Assembles a `Pipeline` using `AgentStep`, `ParallelStep`, `LoopStep`, `BranchStep`
3. Runs the pipeline in a background thread
4. Streams `trace` events (started / completed per node) and a final `result` event back via Server-Sent Events

The frontend's `runner.ts` reads the SSE stream and feeds each event into the Trace panel in real time.

---

## Requirements

| | Minimum version |
|---|---|
| Python | 3.9 |
| Node.js | 18 |
| npm | 8 |
| Docker (optional) | 24 |

Python packages: `fastapi`, `uvicorn`, `sse-starlette`, `moya-ai[openai,ollama]`

Frontend packages: React 18, @xyflow/react 12, Tailwind CSS 3, Vite 4, TypeScript 5

---

## Common issues

**Backend URL shows red in Settings**

The FastAPI server is not running or not reachable. Start it with `./start.sh` or manually:
```bash
cd moya-ui/backend && python3 main.py
```

**Ollama agents return errors in Real mode**

Make sure Ollama is running and the model is pulled:
```bash
ollama serve
ollama pull llama3.1
```

**Port already in use**

`start.sh` automatically frees ports 8000 and 5173 before starting. If you run manually, stop any existing process on those ports first.

**Docker: can't reach Ollama from the container**

Ollama must run on the host. Set the Ollama URL in Settings to:
- Mac / Windows: `http://host.docker.internal:11434`
- Linux: `http://172.17.0.1:11434`
