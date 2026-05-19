# ADR-003: A2A Integration via Official google-a2a Library

**Status:** Accepted  
**Date:** 2026-05-04  
**Deciders:** Karthik Vaidhyanathan

---

## Context

The Agent-to-Agent (A2A) protocol is an open standard published by Google that defines how LLM agents discover each other, delegate tasks, and exchange structured results over HTTP. MOYA needs:

- An **A2A Server** to expose any MOYA agent as an A2A endpoint.
- An **A2A Client** to call any external A2A-compliant agent.
- An **A2A Agent wrapper** so remote A2A agents appear as first-class MOYA agents.

Three implementation paths exist:

| Approach | Pros | Cons |
|---|---|---|
| Official `google-a2a` Python SDK | Protocol compliance guaranteed; spec updates absorbed | Tied to Google's release cadence |
| Hand-rolled from spec | Full control; no dependency | High maintenance; risk of spec drift |
| Third-party community library | May have ergonomic improvements | Uncertain maintenance; compliance risk |

---

## Decision

**Use the official `google-a2a` Python library (`a2a-sdk` on PyPI).**

Rationale:

1. **Spec compliance is non-negotiable.** The A2A spec defines exact JSON structures for `tasks/send`, `tasks/get`, streaming, and Agent Cards. Hand-rolling these correctly — and keeping them correct as the spec evolves — is a maintenance burden MOYA should not own.
2. **Interoperability is the whole point.** If MOYA's A2A implementation diverges from the spec, it cannot communicate with other A2A agents (e.g., Google ADK agents, LangGraph agents). Using the official library makes compliance automatic.
3. **The SDK provides request/response models.** Using the SDK's Pydantic models for `Task`, `TaskStatus`, `AgentCard`, etc. means MOYA gets type safety and validation for free.

---

## Architecture

```
moya/a2a/
├── __init__.py
├── server.py          # A2AServer — wraps a MOYA Agent; handles HTTP routing via google-a2a
├── client.py          # A2AClient — wraps google-a2a client; maps to MOYA streaming pattern
├── agent.py           # A2AAgent — Agent subclass backed by A2AClient
├── card.py            # AgentCard builder — generates /.well-known/agent.json from AgentInfo
└── config.py          # A2AServerConfig, A2AClientConfig dataclasses
```

**A2AServer** wraps a single MOYA `Agent`, creates an ASGI app (via `google-a2a`'s server utilities), and mounts the standard endpoints. It also generates and serves the Agent Card from the agent's `AgentInfo`.

**A2AClient** uses `google-a2a`'s async client to submit tasks and poll/stream results. It surfaces a `handle_message()` / `handle_message_stream()` interface so the rest of MOYA doesn't know about A2A.

**A2AAgent** extends MOYA's `Agent` base class and delegates all `handle_message` calls to an `A2AClient`. This makes a remote A2A agent register-able in `AgentRegistry` and usable in any orchestrator.

---

## Alternatives Considered

**Hand-rolled HTTP endpoints (FastAPI/Starlette):** Gives full control over request/response format but requires us to re-implement and maintain spec-compliant JSON schemas, streaming logic, and Agent Card format. Rejected for maintenance reasons.

**Community `a2a-protocol` package:** Less traction, unclear maintenance status. The official SDK is the safer long-term bet.

---

## Consequences

- `google-a2a` (`a2a-sdk`) is an optional dependency: `pip install moya[a2a]`.
- MOYA requires an ASGI-capable web server (e.g., `uvicorn`) to host an `A2AServer` — this is documented, not bundled.
- If Google publishes breaking spec changes before releasing the updated SDK, MOYA's A2A layer may lag until the SDK catches up. This is accepted as preferable to maintaining our own compliance.
- `A2AAgent` is transparent to orchestrators — no orchestrator code changes are required to use remote A2A agents.
