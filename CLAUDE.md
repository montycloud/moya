# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install (pick the extras you need)
pip install -e ".[all]"          # everything
pip install -e ".[openai]"       # OpenAI only
pip install -e ".[ollama]"       # Ollama only

# Run all tests
python3 -m pytest tests/

# Run a single test file
python3 -m pytest tests/test_skills_enhanced.py

# Run a single test
python3 -m pytest tests/test_skills_enhanced.py::test_skill_version_conflict

# Run tests matching a keyword
python3 -m pytest tests/ -k "delegation"

# Run an example
python3 examples/quick_start_subagents.py
python3 examples/trip_planner/run.py
```

There is no lint or type-check command configured — pytest is the only automated check.

## Architecture

### Layers (top → bottom)

```
Entry points → Orchestrators → AgentRegistry → Agents → ToolRegistry → Tools / Skills / MCP
```

**Entry points** (`examples/`, user code): build registries, attach skills, create a `DelegationManager` or `Pipeline`, then call `orchestrate()` or `delegate()`.

**Orchestrators** (`moya/orchestrators/`): `SimpleOrchestrator` (name-based routing), `MultiAgentOrchestrator` (LLM classifier picks the agent), `ReActOrchestrator` (Thought→Action→Observation loop). All read from an `AgentRegistry`.

**AgentRegistry** (`moya/registry/`): runtime catalog of agents. Stores each agent alongside an `AgentInfo` (health status, TTL, skills list, tags). `find_agents_with_skill()` and `search_agents()` enable capability-based discovery. Backed by a pluggable `AgentRepository`; default is `InMemoryAgentRepository`.

**Agents** (`moya/agents/`): all share the `Agent` / `AgentConfig` base. Concrete implementations: `OpenAIAgent`, `BedrockAgent`, `OllamaAgent`, `AzureOpenAIAgent`, `RemoteAgent`, `CrewAIAgent`. Each calls `attach_skills()` during `__init__` if `AgentConfig.skills` is non-empty. The agent holds a reference to its `ToolRegistry` and `memory` repository; tool calls go through `call_tool()` which delegates to `ToolRegistry.get_tool(name).function()`.

**Skills** (`moya/skills/`): a `Skill` dataclass bundles a `prompt_snippet` (str) and a `tools_factory` (callable returning `List[Tool]`). `attach_skills()` resolves transitive dependencies via `SkillRegistry`, deduplicates by name, appends each snippet to `agent.system_prompt`, and registers the tools. `SkillRegistry` stores skills by name+version (semver ordering) and detects dependency cycles.

**DelegationManager** (`moya/delegation/`): routes tasks between agents with depth limiting, parallel dispatch, and named aggregation strategies. Key methods:
- `delegate(task, agent_name=, skill=)` — synchronous, single agent
- `delegate_async(task, agent_name=)` → `Future`
- `delegate_parallel(tasks, aggregation="concat"|"first"|"vote"|"custom")` — concurrent, returns list
- `setup_tools(tool_registry)` — registers `list_agents` + `delegate_task` so an LLM agent can self-delegate

**SubAgentSpawner** (`moya/delegation/spawner.py`): creates new agents at runtime from a `SubAgentSpec` or a named template, optionally inheriting the parent's `tool_registry`, `skills`, and `system_prompt` prefix. Spawned agents are auto-registered in `AgentRegistry`. Publishes `AgentSpawnedEvent` / `AgentSpawnErrorEvent`.

**ToolRegistry** (`moya/tools/`): maps tool names to `Tool` objects (name + function). `GlobalToolRegistry` is a module-level singleton; `ScopedToolRegistry` inherits from it and falls back to the global on lookup miss. Tool schemas are auto-generated from Python type hints and docstrings by each agent backend.

**MCP** (`moya/mcp/`): `MCPClient` connects to an MCP server via subprocess or HTTP, discovers tools, and wraps them as `Tool` objects with auto-converted schemas. `MCPAuthConfig` handles bearer tokens and API keys. Tool names are namespaced as `server_name__tool_name`.

**Observability** (`moya/observability/`): `EventBus` is a thread-safe pub/sub bus. Use `get_event_bus()` for the process-wide singleton or create a fresh `EventBus()` instance. Subscribe with `bus.subscribe("event.type", handler)` or `"*"` for all events. Events are defined in `events.py` — `AgentEvent`, `ToolEvent`, `PipelineEvent`, `DelegationEvent`, `AgentSpawnedEvent`, etc. All agents, tools, pipelines, and the `DelegationManager` publish events automatically when an `event_bus` is wired in.

**Pipelines** (`moya/flows/`): `Pipeline` chains `AgentStep`, `FunctionStep`, `ParallelStep`, `BranchStep`, `LoopStep`. Steps communicate via `FlowContext` (output string + metadata dict). Each step publishes `StepStartedEvent` / `StepCompletedEvent`.

### Key design invariants

- `AgentInfo` (health, TTL, skills) is stored separately from the `Agent` object in `InMemoryAgentRepository._infos`. Mutations to health/TTL go through `AgentInfo`, not the agent.
- `attach_skills()` is idempotent on skill name — already-attached skills are skipped.
- `SkillVersionConflictError` is raised when the same name+version is registered with a different object; pass `overwrite=True` to replace.
- Depth tracking in `DelegationManager` uses `threading.local()` so parallel delegations in different threads have independent counters.
- MCP tool naming uses double-underscore: `server_name__tool_name`.

### Examples layout

`examples/` contains standalone runnable scripts per feature (`quick_start_skills.py`, `quick_start_subagents.py`, etc.). `examples/trip_planner/` is a full multi-agent demo using Ollama. New feature demos go in `examples/<feature_name>/` or as a top-level `examples/quick_start_<feature>.py`.

## Commit style

Footer: `Authors: Karthik powered by Claude` (no `Co-Authored-By` trailer).
