# ADR-009: Skills Architecture

**Status:** Accepted  
**Date:** 2026-05-04  
**Deciders:** Karthik Vaidhyanathan

---

## Context

MOYA currently has no concept of a reusable, named agent behavior. Capabilities are embedded in system prompts (free text) or as tools in a `ToolRegistry`. Neither is shareable, discoverable, or composable across agents without copy-pasting configuration.

A **Skill** should represent a named, versioned, self-contained capability that:
- Adds a specific prompt snippet to an agent's system prompt.
- Optionally registers tools needed by that capability.
- Optionally references a sub-pipeline (from ADR-008) that implements the capability.
- Can depend on other skills, forming a dependency graph.
- Can be discovered by other agents or orchestrators to enable skill-based routing.

---

## Decision

**Introduce `moya/skills/` in core MOYA with a `Skill` dataclass, `SkillRegistry`, and skill attachment logic. Concrete built-in skill implementations live in the separate `moya-skills` package (ADR-006).**

---

## Core Abstractions

### Skill

```python
@dataclass
class Skill:
    name: str
    version: str                               # semver e.g. "1.0.0"
    description: str
    tags: List[str] = field(default_factory=list)
    prompt_snippet: Optional[str] = None       # appended to agent system prompt
    tools_factory: Optional[Callable[[], List[Tool]]] = None  # returns tools to register
    pipeline_factory: Optional[Callable[[], "Pipeline"]] = None  # returns a sub-pipeline
    dependencies: List[str] = field(default_factory=list)  # other skill names
```

A skill is a **descriptor**, not an active object. Attaching it to an agent produces side effects (prompt mutation, tool registration) but the `Skill` object itself is stateless and reusable.

### SkillRegistry

```python
class SkillRegistry:
    def register(self, skill: Skill) -> None: ...
    def get(self, name: str, version: Optional[str] = None) -> Skill: ...
    def list_skills(self) -> List[Skill]: ...
    def find_by_tag(self, tag: str) -> List[Skill]: ...
    def find_by_semantic_similarity(self, query: str, top_k: int = 5) -> List[Skill]: ...
    def resolve_dependencies(self, skill_name: str) -> List[Skill]:
        """Return skills in dependency-resolved order (topological sort)."""
```

The `SkillRegistry` uses the same `StorageBackend` interface (ADR-007) and the same `EmbeddingProvider` interface (ADR-005) as the tool and agent registries.

---

## Skill Attachment to Agents

Skills are attached at **agent creation time**, not runtime, for predictability. The `AgentConfig` dataclass gains an optional `skills` field:

```python
@dataclass
class AgentConfig:
    ...
    skills: List[str] = field(default_factory=list)  # skill names to attach
```

During `Agent.__init__()`, a new `SkillAttacher` utility:

1. Resolves the dependency graph for each named skill (topological order).
2. For each resolved skill:
   a. Appends `skill.prompt_snippet` to the agent's `system_prompt` (if non-None).
   b. Calls `skill.tools_factory()` and registers returned tools in the agent's tool registry (if non-None).
3. Stores the resolved skill names in `agent.attached_skills: List[str]` for discovery.

```python
class SkillAttacher:
    def __init__(self, skill_registry: SkillRegistry):
        self._registry = skill_registry

    def attach(self, config: AgentConfig) -> AgentConfig:
        all_skills = []
        for skill_name in config.skills:
            all_skills.extend(self._registry.resolve_dependencies(skill_name))
        seen = set()
        for skill in all_skills:
            if skill.name in seen:
                continue
            seen.add(skill.name)
            if skill.prompt_snippet:
                config.system_prompt += f"\n\n# Skill: {skill.name}\n{skill.prompt_snippet}"
            if skill.tools_factory:
                for tool in skill.tools_factory():
                    config.tool_registry.register_tool(tool)
        return config
```

---

## Skill Discovery by Other Agents

`AgentInfo` (in the enhanced agent registry) gains a `skills: List[str]` field. When an agent is registered, `agent.attached_skills` is read and stored in `AgentInfo`.

```python
@dataclass
class AgentInfo:
    name: str
    description: str
    type: str
    skills: List[str] = field(default_factory=list)   # NEW
    endpoint: Optional[str] = None                    # for remote agents
    health_status: str = "unknown"
```

The agent registry's `find_agents_with_skill(skill_name)` method filters on this field.

---

## Skill-Based Routing

`LLMClassifier` and the new `SkillBasedRouter` can route by required skill:

```python
class SkillBasedRouter:
    def route(self, required_skill: str, message: str) -> str:
        candidates = self._agent_registry.find_agents_with_skill(required_skill)
        if not candidates:
            raise NoAgentForSkillError(required_skill)
        if len(candidates) == 1:
            return candidates[0].name
        # Break tie with LLM classifier over the candidates
        return self._classifier.classify(message, available_agents=candidates)
```

---

## Dependency Resolution

Circular skill dependencies raise `CircularSkillDependencyError` at resolution time (not silently skipped). Resolution uses Kahn's algorithm (topological sort) so skills are attached in dependency order.

---

## Example: Defining and Using a Skill

```python
# In moya-skills package
from moya.skills import Skill

web_search_skill = Skill(
    name="web_search",
    version="1.0.0",
    description="Gives the agent the ability to search the web for current information.",
    tags=["search", "web", "realtime"],
    prompt_snippet="You have access to a web search tool. Use it when you need current information.",
    tools_factory=lambda: [WebSearchTool()],
)

# In user code
from moya_skills import web_search_skill

skill_registry.register(web_search_skill)

config = OpenAIAgentConfig(
    agent_name="research_agent",
    skills=["web_search"],
    ...
)
agent = OpenAIAgent(config)  # web search prompt + tool auto-attached
```

---

## Alternatives Considered

**Runtime skill attachment (hot-swap):** More flexible but makes the agent's effective system prompt a moving target — harder to debug and test. Rejected for simplicity; skills are a config-time concern.

**Skills as orchestrators:** Treats each skill as a mini-orchestrator. Too heavy; skills should be lightweight decorations on an agent, not coordination layers. Rejected.

**Skills as tools only (no prompt snippets):** Tools alone cannot encode behavioral guidance. A `WebSearch` skill without a prompt snippet doesn't tell the agent *when* to search. Rejected.

---

## Consequences

- `moya/skills/` package: `Skill`, `SkillRegistry`, `SkillAttacher`, `SkillBasedRouter` — no external dependencies.
- `AgentConfig` gets an optional `skills: List[str]` field — fully backward compatible.
- `AgentInfo` gets a `skills: List[str]` field — backward compatible (defaults to empty list).
- Skills are immutable once attached — recreate the agent to change skills. This is documented.
- `moya-skills` ships concrete skills; users can ship their own skill packages following the same pattern.
