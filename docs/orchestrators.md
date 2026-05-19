# Orchestrators

An **Orchestrator** routes a user message to the right agent and returns the response. MOYA provides three built-in patterns plus a `DelegationManager` for agent-to-agent delegation.

---

## SimpleOrchestrator

Routes to a named agent. Useful when the caller knows which agent should handle the message.

```python
from moya import create_agent, AgentRegistry
from moya.orchestrators.simple_orchestrator import SimpleOrchestrator

registry = AgentRegistry()
registry.register_agent(create_agent("openai", name="researcher", description="..."))
registry.register_agent(create_agent("openai", name="writer",     description="..."))

orch = SimpleOrchestrator(registry, default_agent_name="researcher")

# Route to a specific agent
response = orch.orchestrate("t1", "What is quantum computing?", agent_name="researcher")

# Route to the default
response = orch.orchestrate("t1", "Summarise this for me.")
```

**With streaming:**

```python
def print_chunk(chunk: str):
    print(chunk, end="", flush=True)

orch.orchestrate("t1", "Tell me a story.", stream_callback=print_chunk)
```

---

## MultiAgentOrchestrator

Uses an `LLMClassifier` to pick the best agent automatically, based on agent descriptions and the user message.

```python
from moya import create_agent, AgentRegistry
from moya.orchestrators.multi_agent_orchestrator import MultiAgentOrchestrator
from moya.classifiers.llm_classifier import LLMClassifier

registry = AgentRegistry()
registry.register_agent(create_agent("openai", name="travel_agent",  description="Plans trips and answers travel questions"))
registry.register_agent(create_agent("openai", name="finance_agent", description="Answers financial and investment questions"))
registry.register_agent(create_agent("openai", name="general_agent", description="Handles all other questions"))

# A lightweight agent used only for classification
classifier_agent = create_agent("openai", name="classifier", description="Classifies questions", model="gpt-4o-mini")
classifier = LLMClassifier(llm_agent=classifier_agent, default_agent="general_agent")

orch = MultiAgentOrchestrator(registry, classifier, default_agent_name="general_agent")

response = orch.orchestrate("t1", "What's the cheapest way to fly to Tokyo?")
# → routes to travel_agent automatically
```

**With memory:**

```python
from moya import InMemoryRepository

memory = InMemoryRepository()
orch = MultiAgentOrchestrator(registry, classifier, memory=memory)
```

When `memory` is provided, each user/assistant turn is persisted to the repository under the `thread_id`.

---

## ReActOrchestrator

Implements the Thought → Action → Observation loop. The LLM reasons about which agent to call and what to ask, iterating until it has a final answer.

```python
from moya.orchestrators.react_orchestrator import ReActOrchestrator

# llm_agent drives the reasoning loop
llm_agent = create_agent("openai", name="reasoner", description="Reasons about tasks", model="gpt-4o")

orch = ReActOrchestrator(
    agent_registry=registry,
    classifier=classifier,
    llm_agent=llm_agent,
    verbose=True,   # prints Thought/Action/Observation to stdout
)

response = orch.orchestrate("t1", "Research quantum computing and write a 3-paragraph summary.")
```

The `verbose=True` flag prints the ReAct trace, useful for debugging agent reasoning.

---

## DelegationManager

`DelegationManager` is not an orchestrator in the strict sense — it's a tool-based delegation layer. It lets an agent (typically a coordinator) delegate tasks to specialist sub-agents programmatically or through LLM tool calls.

### Setup

```python
from moya import create_agent, AgentRegistry, ToolRegistry, DelegationManager

# Build specialist agents
registry = AgentRegistry()
registry.register_agent(create_agent("openai", name="analyst",  description="Analyses data", tags=["specialist"]))
registry.register_agent(create_agent("openai", name="writer",   description="Writes reports", tags=["specialist"]))

dm = DelegationManager(registry, max_depth=3)

# Wire delegation into the coordinator's tool registry
coord_tools = ToolRegistry()
dm.setup_tools(coord_tools)
# Registers two tools: list_agents, delegate_task

coordinator = create_agent(
    "openai",
    name="coordinator",
    description="Coordinates work between specialists",
    tool_registry=coord_tools,
)
```

When the coordinator calls `delegate_task(task="...", agent_name="analyst")` via tool calling, `DelegationManager.delegate()` is invoked.

### Programmatic delegation

```python
result = dm.delegate("Analyse Q3 sales data", agent_name="analyst")
```

### Parallel delegation

```python
results = dm.delegate_parallel([
    ("Analyse Q3 sales data",      "analyst"),
    ("Analyse Q3 marketing spend", "analyst"),
    ("Prepare executive summary",  "writer"),
])
# results[0], results[1], results[2] correspond to the three tasks, in order
```

### Depth limiting

`max_depth` prevents infinite delegation chains. If a delegated agent tries to delegate further and the depth limit is reached, `MaxDelegationDepthError` is raised.

```python
from moya.delegation.manager import MaxDelegationDepthError, AgentNotFoundError

try:
    dm.delegate("task", agent_name="analyst")
except MaxDelegationDepthError:
    print("Too many levels of delegation")
except AgentNotFoundError:
    print("No agent with that name")
```

Depth is tracked per-thread using `threading.local()`, so concurrent delegations in different threads do not interfere.

---

## Choosing an Orchestration Pattern

| Pattern | When to use |
|---|---|
| `SimpleOrchestrator` | You know at call time which agent should handle the message. |
| `MultiAgentOrchestrator` | The right agent depends on message content; let the LLM decide. |
| `ReActOrchestrator` | Complex tasks requiring iterative reasoning across multiple agents. |
| `DelegationManager` | A coordinator agent should dispatch sub-tasks to specialists via tool calls. |
| `Pipeline` | Deterministic multi-step workflows with branching and looping. |

---

## Custom Orchestrator

Subclass `Orchestrator` and implement `orchestrate()`:

```python
from moya.orchestrators.orchestrator import Orchestrator

class PriorityOrchestrator(Orchestrator):
    def orchestrate(self, thread_id, user_message, stream_callback=None, **kwargs):
        # Try premium agent first; fall back to standard
        agent = (
            self.agent_registry.get_agent("premium")
            or self.agent_registry.get_agent("standard")
        )
        if stream_callback:
            result = ""
            for chunk in agent.handle_message_stream(user_message, thread_id=thread_id):
                stream_callback(chunk)
                result += chunk
            return result
        return agent.handle_message(user_message, thread_id=thread_id)
```
