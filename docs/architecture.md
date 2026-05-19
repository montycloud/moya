# MOYA Architecture

This document covers the internal design of the MOYA framework: how its subsystems are organised, how data flows through them, and the reasoning behind key design decisions.

---

## 1. System Overview

MOYA is organised into eight subsystems that are deliberately loosely coupled. Each subsystem has a well-defined interface; nothing except the outermost `create_agent()` factory reaches across subsystem boundaries.

```mermaid
graph TB
    User(["User / Application"])

    subgraph Public["Public API  (moya/__init__.py)"]
        FA["create_agent(provider, ...)"]
    end

    subgraph A["Agents"]
        ABC["Agent (ABC)\n+ AgentConfig"]
        OA["OpenAIAgent"]
        BA["BedrockAgent"]
        OlA["OllamaAgent"]
        AZA["AzureOpenAIAgent"]
        RA["RemoteAgent"]
        CA["CrewAIAgent"]
    end

    subgraph R["Registries"]
        AR["AgentRegistry"]
        SR["SkillRegistry"]
        TR["ToolRegistry"]
    end

    subgraph C["Composition"]
        PL["Pipeline"]
        SO["SimpleOrchestrator"]
        MAO["MultiAgentOrchestrator"]
        RAO["ReActOrchestrator"]
        DM["DelegationManager"]
    end

    subgraph SK["Skills"]
        Skill["Skill\n(prompt_snippet + tools_factory)"]
    end

    subgraph T["Tooling"]
        Tool["Tool\n(auto-schema from docstring)"]
        MCP["MCPClient / MCPServer"]
        EM["EphemeralMemory"]
    end

    subgraph M["Memory"]
        Repo["Repository (ABC)"]
        IMR["InMemoryRepository"]
        FSR["FileSystemRepository"]
    end

    User --> FA
    FA --> OA & BA & OlA & AZA & RA & CA
    OA & BA & OlA & AZA & RA & CA -.->|"implements"| ABC

    AR --> OA & BA & OlA & AZA & RA & CA
    SO & MAO & RAO & DM --> AR

    ABC --> TR & Repo
    TR --> Tool & MCP & EM
    Repo --> IMR & FSR

    Skill --> TR & SR
    PL --> SO & MAO & RAO & DM
```

---

## 2. Agent Layer

### Class Hierarchy

Every agent inherits from the abstract `Agent` base class, which enforces a uniform interface regardless of the underlying LLM provider.

```mermaid
classDiagram
    class AgentConfig {
        +agent_name: str
        +agent_type: str
        +description: str
        +system_prompt: str
        +llm_config: dict
        +tool_registry: ToolRegistry
        +memory: Repository
        +is_tool_caller: bool
        +is_streaming: bool
        +skills: List[Skill]
    }

    class Agent {
        <<abstract>>
        +agent_name: str
        +system_prompt: str
        +tool_registry: ToolRegistry
        +memory: Repository
        +tags: List[str]
        +handle_message(message, **kwargs) str*
        +handle_message_stream(message, **kwargs) Iterator*
        +call_tool(tool_name, **kwargs) Any
        +discover_tools() List[str]
        +_remember(thread_id, user_msg, response)
        +get_last_n_messages(thread_id, n) List
        +get_conversation_summary(thread_id) str
    }

    class OpenAIAgent {
        +model_name: str
        +max_iterations: int
        +handle_message()
        +handle_message_stream()
        +get_tool_definitions() List[dict]
    }

    class BedrockAgent {
        +model_id: str
        +region: str
        +handle_message()
        +handle_message_stream()
    }

    class OllamaAgent {
        +model_name: str
        +base_url: str
        +setup()
        +handle_message()
        +handle_message_stream()
    }

    class AzureOpenAIAgent {
        +api_base: str
        +api_version: str
    }

    class RemoteAgent {
        +base_url: str
        +auth_token: str
        +setup()
        +handle_message()
        +handle_message_stream()
    }

    class CrewAIAgent {
        +setup()
        +handle_message()
        +handle_message_stream()
    }

    AgentConfig --> Agent : "passed to __init__"
    Agent <|-- OpenAIAgent
    Agent <|-- BedrockAgent
    Agent <|-- OllamaAgent
    OpenAIAgent <|-- AzureOpenAIAgent
    Agent <|-- RemoteAgent
    Agent <|-- CrewAIAgent
```

### Skill Attachment at Construction

When an agent is constructed with `skills=[...]`, the base class `__init__` iterates through each skill **before** the subclass finishes initialising:

1. If `skill.prompt_snippet` exists → append it to `config.system_prompt`.
2. If `skill.tools_factory` exists → call it and register each returned `Tool` into `config.tool_registry`.

This means the fully-assembled `system_prompt` (base + all snippets) is ready when the subclass first reads it, and the tool registry is fully populated before the first `handle_message()` call.

---

## 3. Tool Calling Flow

### Tool Definition

Tools are plain Python functions. MOYA auto-generates the JSON schema from type hints and the docstring:

```
get_weather(city: str) -> str
  docstring:
    "Return current weather.
     Parameters:
     - city: The city name."
```

Auto-generates:
```json
{
  "name": "get_weather",
  "description": "Return current weather.",
  "parameters": {
    "city": {"type": "string", "description": "The city name."}
  }
}
```

### Execution Flow

```mermaid
sequenceDiagram
    participant App
    participant Agent
    participant ToolRegistry
    participant LLM
    participant ToolFn as Tool Function

    App->>Agent: handle_message("What's the weather in Paris?")
    Agent->>Agent: build messages list (system + history + user)
    Agent->>ToolRegistry: get_tool_definitions() → format for provider
    Agent->>LLM: POST /chat/completions (messages + tools)
    LLM-->>Agent: response with tool_call: get_weather(city="Paris")

    loop Tool execution loop (max_iterations)
        Agent->>ToolRegistry: handle_tool_call(response, provider)
        ToolRegistry->>ToolRegistry: _extract_tool_calls(response, provider)
        ToolRegistry->>ToolFn: get_weather(city="Paris")
        ToolFn-->>ToolRegistry: "Sunny, 22°C in Paris"
        ToolRegistry-->>Agent: {call_id → result}
        Agent->>LLM: POST /chat with tool_result appended
        LLM-->>Agent: final text response (no more tool calls)
    end

    Agent->>Agent: _remember(thread_id, user_msg, response)
    Agent-->>App: "The weather in Paris is sunny at 22°C."
```

### Provider-Specific Schema Formatting

`ToolRegistry` stores tools in a provider-neutral format. Each agent's `get_tool_definitions()` converts to the provider's wire format:

| Provider | Schema format |
|---|---|
| OpenAI | `{"type": "function", "function": {"name": ..., "parameters": {"type": "object", "properties": {...}}}}` |
| Bedrock (Converse) | `{"toolSpec": {"name": ..., "inputSchema": {"json": {"type": "object", "properties": {...}}}}}` |
| Ollama | Same as OpenAI (Ollama uses OpenAI-compatible tool format) |

`ToolRegistry._extract_tool_calls()` handles the inverse — parsing the LLM's response back into `{id, name, arguments}` triples regardless of provider.

---

## 4. Memory Model

### Conversation Thread Structure

```mermaid
erDiagram
    Thread {
        string thread_id PK
        datetime created_at
        list participants
        dict metadata
    }
    Message {
        string message_id PK
        string thread_id FK
        string sender
        string content
        datetime timestamp
        dict metadata
    }
    Thread ||--o{ Message : "contains"
```

### Repository Pattern

`Repository` is an abstract base class. Swap implementations without changing any agent code:

```mermaid
classDiagram
    class Repository {
        <<abstract>>
        +create_thread(thread)
        +get_thread(thread_id) Thread
        +append_message(thread_id, message)
        +list_threads() List[str]
        +delete_thread(thread_id)
    }

    class InMemoryRepository {
        -_threads: Dict[str, Thread]
        +create_thread()
        +get_thread()
        +append_message()
        +list_threads()
        +delete_thread()
    }

    class FileSystemRepository {
        -base_path: str
        +create_thread()   stores as JSON file
        +get_thread()      loads from JSON file
        +append_message()
        +list_threads()
        +delete_thread()
    }

    Repository <|-- InMemoryRepository
    Repository <|-- FileSystemRepository
```

### EphemeralMemory

`EphemeralMemory` is a convenience wrapper that turns memory operations into **tools** the LLM can call directly. Each instance gets its own isolated `InMemoryRepository`:

```python
em = EphemeralMemory()              # private repository
em.configure_memory_tools(registry) # registers store_message, get_last_n_messages,
                                    # get_thread_summary into registry
```

This allows a tool-calling agent to manage its own memory without the calling code tracking thread IDs explicitly.

---

## 5. Pipeline Execution Model

A `Pipeline` is a list of steps that transform a `FlowContext`. The context carries:

- `thread_id` — conversation identity
- `message` — original user message (read-only by convention)
- `output` — mutable string passed between steps
- `metadata` — dict for step-to-step annotations

```mermaid
flowchart LR
    Input["FlowContext\n(message, output=message)"]

    subgraph P["Pipeline"]
        direction LR
        S1["AgentStep\ncall agent.handle_message(output)"]
        S2["FunctionStep\nctx.output = transform(ctx)"]
        S3["ParallelStep\nrun branches concurrently\nmerge outputs"]
        S4["BranchStep\ncondition(ctx) → key\nroute to matching step"]
        S5["LoopStep\nrepeat step until\n condition(ctx) or max_iter"]
    end

    Output["final ctx.output"]

    Input --> S1 --> S2 --> S3 --> S4 --> S5 --> Output
```

### Step Types in Detail

**`AgentStep`** — passes `ctx.output` to `agent.handle_message()` and replaces `ctx.output` with the response.

**`FunctionStep`** — calls `func(ctx) -> ctx`. Pure Python; use for data transformation, saving to metadata, etc.

**`ParallelStep`** — runs multiple sub-steps concurrently via `ThreadPoolExecutor`. Each branch gets a copy of `ctx`; a merge function combines the outputs.

```mermaid
graph LR
    Before["ctx (input)"]
    Split{{"deep copy per branch"}}
    B1["branch 1"]
    B2["branch 2"]
    B3["branch n"]
    Merge{{"merge(outputs)"}}
    After["ctx (output = merged)"]

    Before --> Split --> B1 & B2 & B3 --> Merge --> After
```

**`BranchStep`** — evaluates `condition(ctx)` to get a key, then runs the step at `branches[key]`. Raises `KeyError` for unknown keys.

**`LoopStep`** — runs the inner step repeatedly. Stops when `until(ctx)` returns `True` or `max_iterations` is reached.

### Nesting Pipelines

Pipelines can be nested inside `FunctionStep` using `pipeline.run_ctx(ctx)`:

```python
inner = Pipeline([AgentStep(writer), FunctionStep(format)])
outer = Pipeline([
    AgentStep(researcher),
    FunctionStep(lambda ctx: inner.run_ctx(ctx)),
])
```

---

## 6. Orchestration Patterns

### Simple Orchestrator

Routes a message to a named agent (from `kwargs["agent_name"]`) or the configured default:

```mermaid
sequenceDiagram
    App->>SimpleOrchestrator: orchestrate(thread_id, message, agent_name="researcher")
    SimpleOrchestrator->>AgentRegistry: get_agent("researcher")
    AgentRegistry-->>SimpleOrchestrator: ResearcherAgent
    SimpleOrchestrator->>ResearcherAgent: handle_message(message)
    ResearcherAgent-->>SimpleOrchestrator: response
    SimpleOrchestrator-->>App: response
```

### Multi-Agent Orchestrator

Uses an `LLMClassifier` to select the best agent based on the message content and available agent descriptions:

```mermaid
sequenceDiagram
    App->>MultiAgentOrchestrator: orchestrate(thread_id, message)
    MultiAgentOrchestrator->>AgentRegistry: list_agents()
    AgentRegistry-->>MultiAgentOrchestrator: [AgentInfo, ...]
    MultiAgentOrchestrator->>LLMClassifier: classify(message, agents)
    LLMClassifier->>LLM: "Given these agents, which should handle: ..."
    LLM-->>LLMClassifier: "researcher"
    LLMClassifier-->>MultiAgentOrchestrator: "researcher"
    MultiAgentOrchestrator->>AgentRegistry: get_agent("researcher")
    MultiAgentOrchestrator->>ResearcherAgent: handle_message(message)
    ResearcherAgent-->>MultiAgentOrchestrator: response
    MultiAgentOrchestrator-->>App: response
```

### ReAct Orchestrator

Implements the Thought → Action → Observation loop, letting the LLM reason about which agent to call next:

```mermaid
flowchart TB
    Start["User message"]
    Think["Thought: what do I need to do?"]
    Act["Action: delegate to AgentX with task T"]
    Observe["Observation: AgentX returned R"]
    Done{"Final answer\nreached?"}
    Answer["Return final answer"]

    Start --> Think --> Act --> Observe --> Done
    Done -- No --> Think
    Done -- Yes --> Answer
```

### DelegationManager

Provides programmatic sub-agent delegation with:

- **Depth limiting** — `MaxDelegationDepthError` prevents infinite delegation chains. Depth is tracked per-thread using `threading.local()`.
- **Parallel dispatch** — `delegate_parallel([(task, agent_name), ...])` runs tasks concurrently and returns results in the same order.
- **Tool wiring** — `setup_tools(tool_registry)` registers two callable tools into any agent's registry: `list_agents` (returns available agents) and `delegate_task` (delegates to a named agent).

```mermaid
sequenceDiagram
    participant Coordinator
    participant DM as DelegationManager
    participant AR as AgentRegistry
    participant Spec as SpecialistAgent

    Coordinator->>DM: delegate("analyse Q3 data", agent_name="analyst")
    DM->>DM: check depth (current < max_depth)
    DM->>DM: increment depth (thread-local)
    DM->>AR: get_agent("analyst")
    AR-->>DM: AnalystAgent
    DM->>Spec: handle_message("analyse Q3 data")
    Spec-->>DM: analysis result
    DM->>DM: decrement depth
    DM-->>Coordinator: analysis result
```

---

## 7. Skills System

A `Skill` bundles two optional additions to an agent:

| Field | Type | Effect |
|---|---|---|
| `prompt_snippet` | `str` | Appended to the agent's `system_prompt` at construction time |
| `tools_factory` | `Callable[[], List[Tool]]` | Called at construction; returned tools are registered in `tool_registry` |
| `tags` | `List[str]` | Used for `SkillRegistry.find_by_tag()` |
| `version` | `str` | Semver string for tracking skill evolution |

```mermaid
flowchart LR
    Skill["Skill\n(name, prompt_snippet, tools_factory)"]

    subgraph Agent Construction
        SP["config.system_prompt\n+= skill.prompt_snippet"]
        TR["tool_registry\n+= skill.tools_factory()"]
    end

    subgraph Runtime
        LLM_Prompt["LLM sees enriched\nsystem prompt"]
        LLM_Tools["LLM can call\nskill's tools"]
    end

    Skill --> SP --> LLM_Prompt
    Skill --> TR --> LLM_Tools
```

Skills are composable: attach multiple skills to one agent and all snippets are appended in order, all tools are registered.

---

## 8. Registry Subsystem

### AgentRegistry

Central catalogue of live agent objects. Supports multiple discovery methods:

```mermaid
flowchart TD
    AR["AgentRegistry"]
    GN["get_agent(name)\n→ Agent or None"]
    LA["list_agents()\n→ List[AgentInfo]"]
    FS["find_agents_with_skill(name)\n→ List[Agent]"]
    FT["find_agents_by_tag(tag)\n→ List[Agent]"]
    FD["find_agents_by_description(text)\n→ List[Agent]"]
    FY["find_agents_by_type(type)\n→ List[Agent]"]

    AR --> GN & LA & FS & FT & FD & FY
```

`list_agents()` returns `AgentInfo` snapshots (immutable metadata) rather than live agent references, so callers can inspect available agents without holding strong references.

### SkillRegistry

```mermaid
flowchart TD
    SR["SkillRegistry"]
    GET["get(name) → Skill"]
    LIST["list_skills() → List[Skill]"]
    TAG["find_by_tag(tag) → List[Skill]"]
    FRAG["find_by_name_fragment(text) → List[Skill]"]

    SR --> GET & LIST & TAG & FRAG
```

---

## 9. MCP Integration

MOYA implements the [Model Context Protocol](https://modelcontextprotocol.io/) on both sides:

### MCPServer

Wraps a `ToolRegistry` and exposes its tools to any MCP-compliant client. Supports two transports:

- **`stdio`** — run as a subprocess; communication over stdin/stdout (default for local tools).
- **`sse`** — run as an HTTP server for remote tool exposure.

### MCPClient

Connects to an MCP server and makes its tools available as regular `Tool` objects inside a `ToolRegistry`.

```mermaid
sequenceDiagram
    participant App
    participant MCPClient
    participant MCPServer
    participant Tools as Tool Functions

    App->>MCPClient: from_subprocess(python, [mcp_server.py])
    MCPClient->>MCPServer: spawn subprocess + stdio handshake
    App->>MCPClient: get_tools()
    MCPClient->>MCPServer: tools/list
    MCPServer-->>MCPClient: [{name, description, inputSchema}, ...]
    MCPClient-->>App: [Tool("trip_tools__get_facts", ...), ...]

    App->>MCPClient: call_tool("trip_tools__get_facts", destination="Paris")
    MCPClient->>MCPServer: tools/call
    MCPServer->>Tools: get_destination_facts("Paris")
    Tools-->>MCPServer: facts string
    MCPServer-->>MCPClient: result
    MCPClient-->>App: "Paris: capital of France, ..."
```

**Naming convention**: MCP tools are exposed with a `__` separator between server name and tool name (e.g. `trip_tools__get_destination_facts`) because `/` is not valid in OpenAI function names.

The `MCPClient` runs its async event loop in a background daemon thread and exposes a synchronous API, so it integrates seamlessly into synchronous agent code.

---

## 10. Data Flow: End-to-End Request

Putting it all together: a user message through a Multi-Agent Orchestrator with tool-calling agents and persistent memory.

```mermaid
sequenceDiagram
    participant User
    participant MAO as MultiAgentOrchestrator
    participant CL as LLMClassifier
    participant AR as AgentRegistry
    participant Agent as SelectedAgent
    participant TR as ToolRegistry
    participant Tool as Tool Function
    participant Repo as Repository

    User->>MAO: orchestrate("What are the cheapest flights to Tokyo?")

    MAO->>AR: list_agents()
    AR-->>MAO: [travel_agent, general_agent, ...]
    MAO->>CL: classify(message, agents)
    CL-->>MAO: "travel_agent"

    MAO->>AR: get_agent("travel_agent")
    AR-->>MAO: TravelAgent

    MAO->>Agent: handle_message(message, thread_id=T)
    Agent->>Repo: get_thread(T) → load history
    Agent->>TR: get_tool_definitions()
    Agent->>LLM: POST /chat (system + history + message + tools)
    LLM-->>Agent: tool_call: search_flights(origin="LHR", dest="TYO")

    Agent->>TR: handle_tool_call(response)
    TR->>Tool: search_flights(origin="LHR", dest="TYO")
    Tool-->>TR: [flight results]
    TR-->>Agent: {call_id → results}

    Agent->>LLM: POST /chat (with tool result appended)
    LLM-->>Agent: "The cheapest flights to Tokyo are..."

    Agent->>Repo: append user message + assistant response
    Agent-->>MAO: final text response
    MAO-->>User: "The cheapest flights to Tokyo are..."
```

---

## 11. Design Principles

**Provider-agnostic at every layer.** Tools, memory, skills, and the agent interface are all defined without reference to any LLM provider. Provider-specific concerns (schema format, streaming protocol, credential chain) are confined to each agent class.

**Composition over inheritance.** The framework favours small, focused objects assembled at runtime — agents gain capabilities through skills and tool registries, not subclassing. Pipelines compose steps; orchestrators compose agents.

**No global mutable state.** Every registry, repository, and memory object is explicitly constructed and passed. There are no module-level singletons that would cause test pollution or ordering effects.

**Lazy network I/O.** Agent constructors perform no network calls. Ollama calls its health check in `setup()`, which is deferred to first use. Bedrock imports boto3 lazily inside `__init__()` with a helpful error if not installed.

**Uniform streaming contract.** `handle_message_stream()` on every agent is a generator that yields `str` chunks. Callers can always `"".join(agent.handle_message_stream(...))` to get the full response, or stream tokens as they arrive.
