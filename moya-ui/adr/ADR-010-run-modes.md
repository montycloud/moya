# ADR-010: Two run modes — Simulation and Real execution

## Status
Accepted

## Date
2026-05-19

## Context

The Builder needs a way to execute flows. There are two fundamentally different execution scenarios:

1. **Real execution** — the flow is sent to the FastAPI backend, which instantiates actual Moya agents, calls Ollama, and streams real LLM responses back via SSE
2. **Simulation** — the flow is "run" without a live backend; nodes animate in sequence and placeholder text is shown, allowing users to verify flow structure without needing Ollama running

The question is whether both modes are needed, and if so, how to expose them.

### Why Simulation matters

- Many users will build flows on laptops or in environments where Ollama is not running
- Testing the flow graph structure (connections, ordering, node types) does not require a live LLM
- Simulation mode makes the Builder useful as a design/planning tool, not just an execution tool
- It reduces the barrier to entry: a user can design a multi-agent flow before setting up their Ollama environment

### Why Real execution matters

- Simulation responses are fake — they do not reflect actual agent behavior, routing decisions, or LLM output quality
- The streaming trace view is only meaningful with real data
- Eventually all flows must be run in Real mode to be published to the Marketplace

Options evaluated:

| Option | Description | Rejected because |
|---|---|---|
| Real only | No simulation; run button always calls backend | Blocks users without Ollama; poor first-run experience |
| Simulation only | Never calls real backend | Not useful for actual agent development |
| Auto-detect | Try backend; fall back to simulation | Ambiguous UX; user doesn't know which mode they're in |
| **Explicit toggle with indicator** | Mode switcher in the toolbar; current mode always visible | ✓ Chosen |

## Decision

The Builder toolbar contains a **mode indicator** showing the current run mode:

```
[▶ Run]   [● Simulation ▾]
```

The mode switcher is a small dropdown with two options:
- **Simulation** (default) — animated execution, placeholder responses, no backend required
- **Real** — live execution via FastAPI + Ollama SSE

### Simulation mode behavior

- When ▶ Run is clicked in Simulation mode:
  - Nodes animate sequentially (pulse highlight, ~500ms per node) following edge connections
  - The Trace/Code panel opens and shows placeholder output:
    ```
    [Simulated] destination_agent → "This is a simulated response for destination_agent..."
    [Simulated] itinerary_agent → "This is a simulated response for itinerary_agent..."
    ```
  - No network request is made
  - Input node prompts the user to enter a message (or uses a default placeholder)
  - Total simulation runs in ~2–3 seconds regardless of flow complexity

### Real mode behavior

- When ▶ Run is clicked in Real mode:
  - The flow definition is serialized and POSTed to `POST /api/run`
  - The Trace/Code panel opens and streams real SSE output
  - The Run button changes to a Stop button for the duration
  - If the backend is unreachable, an error toast is shown: *"Cannot connect to backend. Switch to Simulation mode or start the backend."*

### Mode persistence
- The selected mode is stored in `localStorage` so it persists across sessions
- Default is **Simulation** on first launch — ensures a working out-of-box experience

### Visual indicator
- A small colored dot in the toolbar indicates mode:
  - Gray dot = Simulation
  - Green dot = Real (connected)
  - Red dot = Real (backend unreachable — shown after a failed run attempt)

## Consequences

### Positive
- Users can design and validate flow structure without Ollama — dramatically lower barrier to entry
- The mode is always explicit — no ambiguity about whether a run was real or simulated
- Real mode leverages the existing SSE infrastructure with no changes
- Default Simulation mode means a new user's first run always succeeds

### Negative / Trade-offs
- Simulation responses are obviously fake — they do not help users test prompt quality or agent routing. Users must mentally track "this was simulated, real behavior may differ"
- The mode switcher adds a UI element to the toolbar; small but non-zero visual complexity
- Simulation mode could give a false sense of confidence about a flow that fails in Real mode due to LLM behavior. Mitigated by making clear in the UI and tooltip that Simulation does not test LLM responses
- Two code paths to maintain (simulation animation + real SSE streaming)
