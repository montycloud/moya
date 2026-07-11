# MOYA Framework — Extension Requirements

**Status:** Approved  
**Date:** 2026-05-03  
**Scope:** Six capability areas to extend the MOYA multi-agent framework

---

## 1. Background & Current State

MOYA is a Python-based multi-agent framework with the following existing capabilities:

| Capability | Current State |
|---|---|
| Agent types | OpenAI, Bedrock, Azure, Ollama, CrewAI, Remote (HTTP) |
| Orchestration | Simple (single-agent), MultiAgent (classifier-based), ReAct (thought-action-observation loop) |
| Tool integration | Function-wrapped tools, per-agent ToolRegistry, OpenAI/Bedrock/Ollama format conversion |
| Agent registry | In-memory registry with name/type/description lookup |
| Memory | In-memory and file-system conversation repositories |
| Agent communication | All messages routed through orchestrator; no direct peer-to-peer |
| Classifier | LLM-based agent selection from agent descriptions |

**Gaps addressed by this initiative:**
- No standardized agent-to-agent (A2A) communication protocol
- No MCP (Model Context Protocol) support for tool discovery and invocation
- Tool registry has no persistent catalog, no schema beyond single-agent scope
- Agent registry has no dynamic registration, health-check, or capability advertisement
- No pipeline / workflow primitives for sequenced or parallel agent flows
- No concept of Skills (reusable agent behaviors) or Sub-agents (agents delegating to child agents)

---

## 2. Capability Areas

### 2.1 Agent Flow (Workflow / Pipeline Primitives)

#### 2.1.1 Problem Statement
Currently, agent coordination is hard-coded inside orchestrator classes. There is no way for users to declaratively define multi-step workflows (sequential pipelines, parallel fan-outs, conditional branches, loops) without writing a custom orchestrator. Complex agentic pipelines require clear data contracts between steps, retry semantics, and the ability to compose smaller flows into larger ones.

#### 2.1.2 Requirements

**REQ-FLOW-01 — Sequential Step Execution**  
The framework MUST provide a `Pipeline` primitive that chains agents (or other pipelines) in a defined order. The output of step N is passed as input to step N+1. Each step MUST be independently configurable.

**REQ-FLOW-02 — Parallel Fan-Out / Fan-In**  
The framework MUST support running multiple agents concurrently and merging their outputs. Users MUST be able to choose the merge strategy (e.g., concatenate, select-best, aggregate with reducer function).

**REQ-FLOW-03 — Conditional Branching**  
The framework MUST support conditional routing: given an input, a user-defined condition (function or LLM-based classifier) selects which branch to execute.

**REQ-FLOW-04 — Loop / Iterative Refinement**  
The framework MUST support loops where the output of an agent is fed back as input until a termination condition is met (e.g., quality check passes, max iterations reached). This generalizes the existing ReAct pattern.

**REQ-FLOW-05 — Typed Data Contracts**  
Each step in a flow MUST be able to declare input and output schemas (Pydantic models or TypedDicts). The framework MUST validate data at step boundaries in strict mode and emit warnings in permissive mode.

**REQ-FLOW-06 — Composability**  
A `Pipeline` MUST be usable as a step inside another `Pipeline`, enabling hierarchical workflow composition.

**REQ-FLOW-07 — Streaming Through Pipelines**  
Pipelines MUST support end-to-end streaming: as a step produces output tokens, they MUST be passable to the downstream step and to an optional caller-provided stream callback.

**REQ-FLOW-08 — Flow Observability**  
Each step execution MUST emit structured events (start, complete, error, retry) that can be consumed by pluggable listeners (logging, tracing, metrics).

**REQ-FLOW-09 — Backward Compatibility**  
Existing `Orchestrator` subclasses MUST continue to work unchanged. A pipeline is an additive construct, not a replacement for orchestrators.

---

### 2.2 MCP (Model Context Protocol) Support

#### 2.2.1 Problem Statement
MCP is an open protocol for connecting LLM agents to external tools, data sources, and services. Currently MOYA tools are plain Python functions registered per-agent. MCP enables tool catalogs to be served over HTTP/stdio, discovered at runtime, versioned, and shared across agents and across processes without coupling the tool implementation to the agent code.

#### 2.2.2 Requirements

**REQ-MCP-01 — MCP Client Integration**  
MOYA MUST include an `MCPClient` that can connect to any MCP-compliant server (stdio, HTTP/SSE transport). Agents MUST be able to use MCP clients as a tool source transparently alongside existing local ToolRegistry tools.

**REQ-MCP-02 — Tool Discovery via MCP**  
When an `MCPClient` is attached to an agent, the agent MUST be able to call `discover_tools()` and receive the full list of tools advertised by that MCP server, alongside locally registered tools.

**REQ-MCP-03 — Tool Invocation via MCP**  
When an LLM selects an MCP-backed tool, the framework MUST serialize the invocation request in MCP format, call the server, deserialize the result, and return it to the LLM in the same format as local tool results.

**REQ-MCP-04 — MCP Server Hosting**  
MOYA MUST provide an `MCPServer` wrapper so that any `ToolRegistry` can be exposed as an MCP-compliant server. This allows MOYA agents to serve their tools to other MCP clients.

**REQ-MCP-05 — Multi-Server Support**  
An agent MUST be able to connect to multiple MCP servers simultaneously. Tool names MUST be namespaced to avoid collisions (e.g., `server_name/tool_name`).

**REQ-MCP-06 — Transport Agnosticism**  
The `MCPClient` MUST abstract over transport protocols. Initial support: stdio (subprocess) and HTTP/SSE. The interface MUST allow adding new transports without changing agent code.

**REQ-MCP-07 — Authentication**  
MCP client connections MUST support configurable authentication (API keys, OAuth bearer tokens) passed as connection-level config, not embedded in tool call arguments.

**REQ-MCP-08 — Schema Passthrough**  
Tool schemas returned by MCP servers MUST be passed through to the LLM without manual re-registration. The framework MUST convert MCP schema format to provider-specific formats (OpenAI, Bedrock, Ollama) automatically.

---

### 2.3 A2A (Agent-to-Agent) Protocol Support

#### 2.3.1 Problem Statement
Agents in MOYA currently cannot communicate directly. All coordination passes through an orchestrator, which limits horizontal scalability and prevents agents from delegating subtasks dynamically. The A2A protocol (Google's open standard) defines a wire format and discovery mechanism for agents to call each other as first-class services, including task delegation, streaming, and capability advertisement.

#### 2.3.2 Requirements

**REQ-A2A-01 — A2A Server**  
MOYA MUST provide an `A2AServer` that wraps any MOYA `Agent` and exposes it as an A2A-compliant HTTP endpoint. The server MUST implement A2A's `tasks/send`, `tasks/get`, `tasks/cancel`, and streaming endpoints.

**REQ-A2A-02 — Agent Card**  
Each `A2AServer` MUST publish a well-known Agent Card (`/.well-known/agent.json`) describing the agent's name, description, supported capabilities, input/output schemas, and authentication requirements.

**REQ-A2A-03 — A2A Client**  
MOYA MUST provide an `A2AClient` that can call any A2A-compliant server (including non-MOYA agents). The client MUST support synchronous task submission, polling, and streaming.

**REQ-A2A-04 — A2A Agent Type**  
MOYA MUST include an `A2AAgent` implementation (extending the existing `Agent` base class) that wraps an `A2AClient`. This allows an external A2A agent to be registered in MOYA's `AgentRegistry` and used anywhere a regular agent is used.

**REQ-A2A-05 — Task Lifecycle Management**  
The A2A layer MUST track task state (submitted, working, completed, failed, cancelled). Tasks MUST be addressable by a stable task ID. Users MUST be able to poll task status or subscribe to streaming updates.

**REQ-A2A-06 — Streaming over A2A**  
The A2A server MUST support Server-Sent Events (SSE) for streaming responses. The A2A client MUST expose a streaming interface compatible with MOYA's existing `stream_callback` pattern.

**REQ-A2A-07 — Authentication**  
A2A server endpoints MUST support configurable authentication (API key, OAuth). A2A client connections MUST support passing credentials per connection configuration.

**REQ-A2A-08 — A2A Discovery Integration**  
The A2A client MUST be able to fetch and parse an Agent Card from a URL to auto-configure itself, enabling zero-configuration peer agent discovery.

**REQ-A2A-09 — Backward Compatibility**  
Existing agents and orchestrators MUST continue to work unchanged. An `A2AAgent` is just another `Agent` from the framework's perspective.

---

### 2.4 Enhanced Tool Registry

#### 2.4.1 Problem Statement
The current `ToolRegistry` is per-agent, in-memory only, and has no rich metadata beyond name/description/parameters. There is no global catalog, no versioning, no access control, and no way to search tools semantically. As the number of tools grows, discovery and governance become critical.

#### 2.4.2 Requirements

**REQ-TOOL-01 — Global Tool Catalog**  
The framework MUST support a `GlobalToolRegistry` that aggregates tools across all agents and MCP servers. Agents may still have local registries that delegate to the global catalog.

**REQ-TOOL-02 — Rich Tool Metadata**  
Each tool registration MUST support extended metadata: version, author, tags, category, examples, input/output JSON schema (not just docstring-parsed parameters), deprecation status.

**REQ-TOOL-03 — Semantic Tool Search**  
The tool registry MUST support searching by keyword (substring match against name, description, tags) and, optionally, by semantic similarity (vector search, pluggable embedding provider).

**REQ-TOOL-04 — Persistent Tool Catalog**  
The tool registry MUST support persistence backends (file, SQLite, remote API) so that the catalog survives process restarts and can be shared across multiple MOYA instances.

**REQ-TOOL-05 — Tool Versioning**  
The registry MUST support multiple versions of the same tool name. Agents MAY pin to a specific version or request the latest. Version conflicts MUST be reported as errors, not silently overwritten.

**REQ-TOOL-06 — MCP Tool Integration**  
Tools discovered via MCP clients MUST be registerable in the global tool catalog with their MCP server as the execution backend. The registry MUST route invocations to the correct backend transparently.

**REQ-TOOL-07 — Tool Access Control**  
Tool registrations MUST support an optional access policy (allowed_agents list or role tags). The registry MUST enforce access at invocation time and return a clear authorization error when violated.

**REQ-TOOL-08 — Tool Health & Observability**  
The registry MUST track per-tool call counts, error rates, and average latency. An admin query MUST return this telemetry. Unhealthy tools (high error rate) MUST be flaggable.

---

### 2.5 Enhanced Agent Registry with Dynamic Discovery

#### 2.5.1 Problem Statement
The current `AgentRegistry` is in-memory and only supports exact-match or substring search. There is no way to discover agents at runtime from remote sources, no health check, no capability advertisement beyond a plain text description, and no way to register agents that live in other processes or machines.

#### 2.5.2 Requirements

**REQ-AREG-01 — Structured Capability Advertisement**  
`AgentInfo` MUST be extended to include: supported input/output modalities, supported skills (REQ-SKILL), tags, endpoint URL (for remote agents), health status, and a human-readable capability schema.

**REQ-AREG-02 — Remote Agent Registration**  
The registry MUST support registering agents by URL (A2A Agent Card endpoint). The registry MUST fetch and parse the Agent Card and store it as an `AgentInfo` entry, with the backing agent being an `A2AAgent`.

**REQ-AREG-03 — Dynamic Discovery**  
The registry MUST support a discovery mechanism where it can query one or more discovery endpoints (a simple REST API or DNS-SD) to find and register agents at runtime without user-written registration code.

**REQ-AREG-04 — Health Monitoring**  
The registry MUST periodically health-check registered agents (configurable interval). Unhealthy agents MUST be marked as unavailable and excluded from classifier selection until health is restored.

**REQ-AREG-05 — Semantic Agent Search**  
The registry MUST support semantic search over agent descriptions and capabilities using vector similarity (pluggable embedding provider). This supplements the existing keyword search.

**REQ-AREG-06 — Persistent Registry Backend**  
The registry MUST support persistence backends (file, SQLite, remote API). The `InMemoryAgentRepository` MUST remain the default for backward compatibility.

**REQ-AREG-07 — Agent Deregistration & TTL**  
Agents MUST be deregistrable. Remote agents SHOULD support a TTL so they are automatically removed if not re-registered within the TTL window, preventing stale entries.

**REQ-AREG-08 — Events**  
The registry MUST emit structured events (agent registered, agent deregistered, agent became unhealthy, agent recovered) that can be consumed by listeners.

---

### 2.6 Skills

#### 2.6.1 Problem Statement
Skills are reusable, named, parameterized behaviors that can be attached to one or more agents. Currently, behavior customization is done entirely through system prompts (free-text) or by registering tools. There is no way to package, version, compose, or share a behavior across agents or to describe to other agents what a given agent *knows how to do* in a structured way.

#### 2.6.2 Requirements

**REQ-SKILL-01 — Skill Definition**  
The framework MUST provide a `Skill` abstraction with: name, version, description, input schema, output schema, and an execution handler. The handler can be a prompt template, a tool call chain, or a sub-pipeline.

**REQ-SKILL-02 — Skill Registry**  
The framework MUST provide a `SkillRegistry` where skills can be registered, versioned, and looked up by name, tag, or semantic similarity.

**REQ-SKILL-03 — Skill Attachment to Agents**  
Agents MUST be able to declare which skills they support via a `skills` field in `AgentConfig`. When a skill is attached, its prompt template (if any) is appended to the agent's system prompt and its tools (if any) are registered in the agent's ToolRegistry.

**REQ-SKILL-04 — Skill Discovery by Other Agents**  
An agent MUST be able to query the registry (or another agent's Agent Card) to discover what skills a target agent supports before delegating a task.

**REQ-SKILL-05 — Skill-Based Routing**  
The classifier / orchestrator MUST support routing by required skill: given a user message that requires skill X, the classifier MUST find and select an agent that has skill X.

**REQ-SKILL-06 — Skill Composability**  
A skill MUST be able to reference other skills as dependencies. The framework MUST resolve skill dependency graphs and attach all required skills when a compound skill is attached to an agent.

**REQ-SKILL-07 — Built-in Skills**  
The framework MUST ship with a library of built-in reusable skills: `WebSearch`, `CodeExecution`, `DataSummarization`, `TranslationToLanguage(lang)`, `DocumentRetrieval`. These serve as reference implementations.

**REQ-SKILL-08 — Skill Versioning**  
Skills MUST be versioned using semantic versioning. Agents MAY pin to a skill version. Breaking changes to a skill MUST increment the major version.

---

### 2.7 Sub-Agents

#### 2.7.1 Problem Statement
There is no first-class mechanism for an agent to spawn, coordinate, and aggregate results from child agents. The ReAct orchestrator approximates this but is hard-coded logic rather than a composable primitive. Sub-agents are needed to model hierarchical delegation: a manager agent breaks a task into sub-tasks, assigns them to sub-agents, and synthesizes the results.

#### 2.7.2 Requirements

**REQ-SUBAG-01 — Sub-Agent Delegation API**  
The framework MUST provide a `delegate(task: str, agent_name_or_skill: str) -> str` call that any agent can make during its execution. The framework routes the task to the named agent or to an agent that has the required skill.

**REQ-SUBAG-02 — Dynamic Sub-Agent Spawning**  
A parent agent MUST be able to request the framework to create a new agent instance (from a template in the registry) to handle a sub-task. The spawned agent MUST be tracked and cleaned up after the task completes.

**REQ-SUBAG-03 — Parallel Sub-Agent Execution**  
A parent agent MUST be able to dispatch multiple sub-tasks to sub-agents concurrently and await all results before continuing (fan-out/fan-in at the agent level).

**REQ-SUBAG-04 — Context Inheritance**  
Sub-agents MUST inherit a scoped view of the parent's conversation context (configurable: full history, last N messages, or summary only) so they have necessary context without receiving unrelated history.

**REQ-SUBAG-05 — Result Aggregation**  
The framework MUST provide configurable aggregation strategies for combining sub-agent results: concatenation, LLM-based synthesis, structured merge (if outputs conform to a schema).

**REQ-SUBAG-06 — Recursion Guard**  
The framework MUST detect and prevent infinite delegation loops. A configurable max delegation depth MUST be enforced. Exceeding the depth MUST raise a clear error, not silently fail.

**REQ-SUBAG-07 — Observability**  
The delegation tree MUST be recorded as structured events (parent task ID, sub-task ID, delegated-to agent, depth) that can be consumed by tracing/logging listeners defined in REQ-FLOW-08.

**REQ-SUBAG-08 — Streaming Through Delegation**  
A parent agent MUST be able to stream sub-agent output tokens back to the end user as they are produced, without waiting for the sub-task to complete.

---

## 3. Cross-Cutting Concerns

### 3.1 Backward Compatibility
All new capabilities MUST be additive. No existing public API in `moya/agents`, `moya/orchestrators`, `moya/tools`, `moya/registry`, `moya/memory`, or `moya/classifiers` MUST break. Where a new feature requires changes to existing classes, the changes MUST be backward-compatible (new optional fields, new subclasses, not modifications to existing method signatures).

### 3.2 Configuration
All new components MUST follow the existing `*Config` dataclass pattern for initialization. No component MUST require environment variables beyond those already used by the agent backends.

### 3.3 Observability & Tracing
A unified event bus (or callback hook interface) MUST be available so that all framework events (tool calls, agent delegations, flow steps, registry changes) can be consumed by a single listener without modifying framework internals. OpenTelemetry span emission SHOULD be supported as an optional plugin.

### 3.4 Testing
All new modules MUST include unit tests with mocked external dependencies (LLMs, MCP servers, A2A endpoints). Integration tests using local MCP servers and loopback A2A agents SHOULD be provided. Test coverage MUST not drop below the existing coverage level.

### 3.5 Documentation
Each new capability MUST include at least one example file in `examples/` demonstrating end-to-end usage, following the existing example conventions (standalone script, minimal dependencies).

### 3.6 Python Version & Dependencies
The framework MUST remain compatible with Python 3.10+. New dependencies MUST be optional extras in `pyproject.toml` (e.g., `pip install moya[mcp]`, `pip install moya[a2a]`) so users who do not need a capability do not install its dependencies.

---

## 4. Out of Scope (for this initiative)

- Persistent LLM fine-tuning or model training
- Built-in vector database hosting (embedding providers are pluggable, not bundled)
- GUI / visual workflow editor
- Kubernetes operator or deployment infrastructure
- Agent marketplace or remote registry hosting service
- Multi-tenancy or user-level isolation primitives

---

## 5. Resolved Design Decisions

| # | Question | Decision | Rationale |
|---|---|---|---|
| OQ-1 | MCP SDK choice | **`fastmcp`** | Higher-level API, less boilerplate for both client and server creation |
| OQ-2 | A2A implementation approach | **Official `google-a2a` Python library** | Maintains protocol compliance as the spec evolves without us re-implementing it |
| OQ-3 | Semantic search embeddings | **`sentence-transformers` as default; pluggable `EmbeddingProvider` interface** | Local execution with no API cost by default; users can swap in OpenAI embeddings or others |
| OQ-4 | Tool registry scope | **Global persistent registry; per-agent `ToolRegistry` becomes a scoped view** | Centralises governance while remaining API-compatible via an adapter |
| OQ-5 | Built-in skills location | **Separate `moya-skills` PyPI distribution** | Keeps core MOYA lean; skills version independently and can evolve faster |
| OQ-6 | Persistence backend | **Local JSON files by default; abstract `StorageBackend` interface targeting SQLite next** | Zero extra dependencies; easy to inspect; clear migration path to SQLite for concurrent access |

---

## 6. Prioritization (Risk-First)

Capabilities are phased by external-dependency risk so the pure-Python infrastructure lands first and is battle-tested before protocol-heavy layers are built on top.

| Phase | Capability | Risk Level | Rationale |
|---|---|---|---|
| **Phase 1** | **2.4 Global Tool Registry** | Low | Pure Python; no external deps; foundational for everything else |
| **Phase 1** | **2.5 Enhanced Agent Registry** | Low | Pure Python; additive changes to existing registry |
| **Phase 1** | **2.1 Agent Flow / Pipelines** | Low | Pure Python; no external deps; unlocks composable workflows |
| **Phase 1** | **2.6 Skills** | Low | Builds only on Phase 1 registries; `moya-skills` ships separately |
| **Phase 2** | **2.2 MCP Support** | Medium | One new dependency (`fastmcp`); well-defined protocol |
| **Phase 2** | **2.7 Sub-Agents** | Medium | Builds on Phase 1; contained scope; no external protocol |
| **Phase 3** | **2.3 A2A Protocol** | Higher | External protocol compliance + `google-a2a` dependency; most complex integration |

---

*End of Requirements Document — Approved*
