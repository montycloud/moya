# ADR-004: Marketplace storage — flat-file JSON with abstracted MarketplaceStore

## Status
Accepted

## Date
2026-05-19

## Context

The Marketplace needs to persist published agents across page refreshes and browser sessions, and eventually across users. Options evaluated:

| Option | Pros | Cons |
|---|---|---|
| **localStorage only** | Zero backend changes | Browser-scoped; agents invisible to other users; easily wiped |
| **Flat-file JSON on disk** | Simple; persistent; shareable across sessions | Not horizontally scalable; file contention under concurrent writes |
| **SQLite** | Proper DB; queries; no server needed | More setup; overkill for v1 |
| **PostgreSQL / hosted DB** | Production-grade; multi-user | Requires infra; too heavy for v1 |
| **Firebase / Supabase** | Hosted; real-time | Vendor dependency; auth complexity |

localStorage was ruled out immediately because agents published on one browser are invisible on another — defeating the sharing purpose of a Marketplace.

SQLite or a hosted DB are the right long-term answer but are disproportionate for v1 where the primary goal is establishing the UX and data model.

A **flat-file JSON approach** is the simplest option that satisfies the v1 constraints:
- Agents persist across sessions (stored server-side)
- No DB setup required
- The data model is defined and locked in v1
- The storage layer can be swapped without changing the API

## Decision

Marketplace data is stored in a single JSON file: **`backend/marketplace.json`**.

The backend exposes:
```
GET  /api/marketplace                  → list all published agents
POST /api/marketplace/publish          → add a new agent listing
GET  /api/marketplace/{id}             → get a single listing
```

All file I/O is handled through a **`MarketplaceStore` abstract interface**:

```python
class MarketplaceStore(ABC):
    @abstractmethod
    def list_agents(self) -> list[AgentListing]: ...

    @abstractmethod
    def get_agent(self, agent_id: str) -> AgentListing | None: ...

    @abstractmethod
    def publish_agent(self, listing: AgentListing) -> AgentListing: ...
```

v1 ships with `JsonFileMarketplaceStore` as the concrete implementation.
v2 can introduce `SqlAlchemyMarketplaceStore` or `SqliteMarketplaceStore` by implementing the same interface — the FastAPI routes and frontend are untouched.

### AgentListing schema (v1)

```json
{
  "id": "uuid-v4",
  "name": "Trip Planner",
  "description": "Plans trips using 4 specialist agents.",
  "tags": ["travel", "multi-agent", "ollama"],
  "category": "General",
  "provider": "ollama",
  "node_count": { "agents": 4, "tools": 3, "skills": 2 },
  "flow": { "nodes": [...], "edges": [...] },
  "published_at": "2026-05-19T10:00:00Z"
}
```

## Consequences

### Positive
- Zero infrastructure requirement for v1 — just a JSON file
- Full API and data model established in v1; DB migration is a pure backend change
- `MarketplaceStore` abstraction ensures no API or frontend changes needed when upgrading storage
- Agents are shared across browser sessions and users on the same server

### Negative / Trade-offs
- Not safe under concurrent writes (two users publishing simultaneously could corrupt the file). Acceptable for v1 (low traffic); v2 DB eliminates this
- No querying / filtering on the backend — all filtering happens client-side in v1. Fine for small catalogues; v2 DB adds proper queries
- `marketplace.json` must be included in `.gitignore` if this is a shared repo, or seeded with example data for demos
- File path must be configurable via environment variable to support different deployment layouts
