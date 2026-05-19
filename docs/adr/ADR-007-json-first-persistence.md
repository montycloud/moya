# ADR-007: JSON-First Persistence with Abstract StorageBackend

**Status:** Accepted  
**Date:** 2026-05-04  
**Deciders:** Karthik Vaidhyanathan

---

## Context

The Global Tool Registry (ADR-004) and Enhanced Agent Registry need persistence so that registered tools and agents survive process restarts. A `SkillRegistry` will need the same.

Three persistence candidates were considered:

| Backend | Dependencies | Concurrent writes | Queryable | Inspect-friendly |
|---|---|---|---|---|
| Local JSON files | None (stdlib) | No (file lock needed) | No (load all) | Yes (human-readable) |
| SQLite | None (stdlib `sqlite3`) | Yes (WAL mode) | Yes (SQL) | Moderate |
| Redis / Postgres | Heavy external dep | Yes | Yes | No |

The framework must remain usable with zero infrastructure beyond Python. Most MOYA deployments are single-process at first, so concurrent-write safety is not critical at launch.

---

## Decision

**Default to local JSON file persistence. Define an abstract `StorageBackend` interface now so that SQLite and other backends can be added without changing registry code. SQLite backend ships in a future minor release.**

### StorageBackend Interface

```python
class StorageBackend(ABC):
    @abstractmethod
    def load(self) -> Dict[str, Any]:
        """Load the full registry as a dict."""

    @abstractmethod
    def save(self, data: Dict[str, Any]) -> None:
        """Persist the full registry dict atomically."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Load a single entry by key (optional optimisation)."""

    @abstractmethod
    def put(self, key: str, value: Any) -> None:
        """Persist a single entry (optional optimisation)."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove an entry."""

    @abstractmethod
    def list_keys(self) -> List[str]:
        """Return all keys."""
```

### JsonStorageBackend

```python
class JsonStorageBackend(StorageBackend):
    def __init__(self, path: Path):
        self._path = path

    def save(self, data):
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(self._path)   # atomic rename on POSIX
```

Atomic rename (`os.replace`) prevents partial writes from corrupting the catalog file.

### File Layout

```
~/.moya/                          # default data directory (configurable)
├── tool_registry.json
├── agent_registry.json
└── skill_registry.json
```

Each file is a flat JSON object: `{ "entries": [...], "schema_version": "1" }`.

### Migration to SQLite

When a `SqliteStorageBackend` is added (future minor release), users opt in by passing `backend=SqliteStorageBackend(path)` to the registry constructor. Existing JSON files can be migrated with a one-time `moya registry migrate --to sqlite` CLI command (not in scope for Phase 1 implementation, but the interface design accommodates it).

---

## Alternatives Considered

**Start with SQLite directly:** `sqlite3` is in the stdlib so there are no extra dependencies. However, JSON files are trivially inspectable with any text editor, easier to include in bug reports, and simpler to reset during development. SQLite adds WAL-mode setup and schema management without delivering meaningful benefit for single-process use. Rejected for Phase 1.

**Use `shelve` (stdlib):** Binary format, not human-readable, platform-specific quirks. Rejected.

**Use `tinydb`:** Third-party, JSON-backed, but adds a dependency with no benefit over stdlib `json`. Rejected.

---

## Consequences

- Zero new dependencies for persistence.
- JSON files are easy to inspect, copy, and version-control during development.
- Concurrent multi-process access is **not** safe with JSON backend — documented limitation. SQLite backend resolves this.
- `StorageBackend` is the only interface that registry implementations interact with; switching backends is a one-line config change.
- All three registries (Tool, Agent, Skill) share the same `StorageBackend` interface — consistent, no per-registry persistence logic.
