# ADR-008: "Try it" — full multi-turn streaming chat interface

## Status
Accepted

## Date
2026-05-19

## Context

The Marketplace needs a way for users to interact with a published agent before deciding to clone or use it. Options considered ranged from a simple one-shot input to a full conversational interface.

The primary goal is giving a potential user enough signal to decide whether an agent is worth cloning. Secondary goal: demonstrate the agent's streaming, multi-agent routing, and conversational coherence — core differentiating features of Moya-built agents.

Options evaluated:

| Option | Description | Rejected because |
|---|---|---|
| No Try it | User must clone to test | Defeats the Marketplace purpose — too high friction |
| Single one-shot input | One text box, one response, no history | Does not demonstrate multi-turn; too shallow |
| **Full multi-turn streaming chat** | Persistent thread, streaming output, agent badge on each response | ✓ Chosen |
| Iframe embed | Agent UI embedded in a card | Requires each agent to have its own hosted UI; not feasible for v1 |
| API playground (curl-style) | Raw request/response JSON | Developer-only; alienates non-technical users |

The full chat interface is the right choice because:
1. Moya's key differentiator is multi-agent routing — a one-shot test cannot demonstrate which specialist handled the query
2. Streaming output is a first-class UX feature; users should see it before committing to clone
3. It matches the mental model users have from tools like ChatGPT and Claude — low learning curve

## Decision

Each Marketplace agent listing has a **"Try it"** button that opens a **full-screen chat overlay** with:

### Chat interface features
- **Streaming responses** — output appears token by token via SSE (same FastAPI `/run` endpoint as the Builder)
- **Multi-turn thread** — conversation history is maintained for the session; messages accumulate in a scrollable thread
- **Agent badge** — each assistant message shows a small badge with the agent name that handled the response (e.g. `itinerary_agent`), making multi-agent routing visible
- **User messages** right-aligned; **assistant messages** left-aligned — standard chat layout
- **Loading indicator** — animated dots while awaiting first token
- **Stop button** — cancels an in-flight stream (future enhancement; not required for v1)

### Layout
- Opens as a full-screen overlay (z-index above the Marketplace grid)
- Header: agent name + description + close (✕) button
- Body: scrollable message thread
- Footer: text input + Send button (Enter to send, Shift+Enter for newline)

### Session scope
- Thread state is local to the overlay; closing and reopening starts a fresh session
- No persistence between sessions — v1 is stateless for Try it
- A new `thread_id` is generated per session (UUID)

### Backend
- Reuses the existing `/api/run` SSE endpoint — no new backend routes needed for v1
- The agent flow definition from the Marketplace listing is passed as the flow payload
- The endpoint already handles multi-turn via `thread_id` + `ConversationManager`

## Consequences

### Positive
- Users experience the agent as-built before cloning — most authentic preview possible
- Multi-agent routing becomes visible via agent badges, turning a UX feature into a marketing feature
- No new backend work — fully reuses existing SSE streaming infrastructure
- Familiar chat UI reduces learning curve to near zero

### Negative / Trade-offs
- Running the agent consumes Ollama compute — if many users Try it simultaneously, local Ollama will be the bottleneck. Acceptable for v1 (single-user or small-team deployments)
- Session is ephemeral — users who want to continue a conversation must clone and run the agent themselves. This is intentional; it creates a conversion funnel toward cloning
- Full-screen overlay means the user loses context of the Marketplace listing while chatting — a split-pane layout would be better but is out of scope for v1
