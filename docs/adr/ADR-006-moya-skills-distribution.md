# ADR-006: moya-skills as a Separate PyPI Distribution

**Status:** Accepted  
**Date:** 2026-05-04  
**Deciders:** Karthik Vaidhyanathan

---

## Context

REQ-SKILL-07 calls for a library of built-in reusable skills: `WebSearch`, `CodeExecution`, `DataSummarization`, `TranslationToLanguage`, `DocumentRetrieval`. These built-in skills:

- Pull in third-party dependencies (e.g., `requests` or `httpx` for web search, a sandboxed executor for code, an embedding model for retrieval).
- Change more frequently than the core Skills abstraction.
- Are optional — many MOYA deployments will not need all of them.

Two packaging options exist:

| Option | Install | Versioning | Core package size |
|---|---|---|---|
| Bundle in `moya` core | `pip install moya` | Skills version with MOYA | Larger; installs unused deps |
| Separate `moya-skills` package | `pip install moya-skills` | Independent | Core stays lean |

---

## Decision

**Ship built-in skills in a separate `moya-skills` PyPI package that declares `moya>=X.Y` as its only required dependency.**

### Package Structure

```
moya-skills/
├── pyproject.toml          # depends on moya>=0.4
├── moya_skills/
│   ├── __init__.py
│   ├── web_search.py       # WebSearchSkill
│   ├── code_execution.py   # CodeExecutionSkill
│   ├── summarization.py    # DataSummarizationSkill
│   ├── translation.py      # TranslationSkill(target_lang)
│   └── retrieval.py        # DocumentRetrievalSkill
└── tests/
```

Each skill is a concrete implementation of `moya.skills.Skill` (defined in core).

### Division of Responsibility

| Package | Contains |
|---|---|
| `moya` (core) | `Skill` abstract class, `SkillRegistry`, `SkillConfig`, skill attachment logic |
| `moya-skills` | Concrete skill implementations, their tool functions, prompt snippets |

### Versioning

`moya-skills` uses independent semver. A breaking change to a built-in skill increments `moya-skills` major; a new skill is a minor bump. The core `moya` `Skill` interface is versioned separately and evolves more slowly.

---

## Alternatives Considered

**Bundle in `moya` as an optional extra (`pip install moya[skills]`):** Simpler distribution model but ties skill versioning to core releases. Every new skill requires a `moya` release. Rejected to keep release cadences independent.

**Single monorepo with multiple packages (moya, moya-skills, moya-mcp, moya-a2a):** Clean model but adds CI complexity for a small team. For now, only skills warrant a separate distribution because of dependency scope; MCP and A2A are optional extras of core `moya`.

---

## Consequences

- Users who want built-in skills: `pip install moya moya-skills`.
- Core `moya` install remains lightweight (no `requests`, no code sandbox, no retrieval deps).
- `moya-skills` can ship hotfixes independently of the core framework.
- Third parties can publish their own `moya-mycompany-skills` packages that follow the same `Skill` interface.
- The `moya-skills` README must clearly state the minimum `moya` version required.
