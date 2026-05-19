# Agents

An **Agent** is MOYA's fundamental unit of intelligence. Every agent wraps an LLM provider behind a uniform interface: `handle_message()` and `handle_message_stream()`. Business logic never needs to know which provider is underneath.

---

## Common Interface

All agents share these methods and attributes, defined on the abstract `Agent` base class:

| Method / Property | Description |
|---|---|
| `handle_message(message, **kwargs) → str` | Send a message, receive a string response. |
| `handle_message_stream(message, **kwargs)` | Generator yielding `str` chunks as the response streams. |
| `call_tool(tool_name, **kwargs) → Any` | Directly invoke a registered tool by name. |
| `discover_tools() → List[str]` | Return names of all tools in the registry. |
| `get_last_n_messages(thread_id, n=5)` | Retrieve recent conversation history. |
| `get_conversation_summary(thread_id)` | Retrieve a summary of the thread. |
| `agent_name` | The agent's unique identifier string. |
| `system_prompt` | The full system prompt (base + any skill snippets). |
| `tags` | List of string tags (e.g. `["specialist", "travel"]`). |

Pass `thread_id` via kwargs to any `handle_message` call to enable conversation memory.

---

## create_agent() Factory

The recommended way to construct any agent:

```python
from moya import create_agent

agent = create_agent(
    provider,          # "openai" | "ollama" | "bedrock" | "azure" | "remote" | "crewai"
    name="my_agent",
    description="What this agent does",
    system_prompt="You are ...",  # optional
    model="gpt-4o",               # optional, provider default used if omitted
    api_key="sk-...",             # optional, falls back to env var
    tool_registry=registry,       # optional, auto-sets is_tool_caller=True
    memory=repo,                  # optional Repository instance
    skills=[skill1, skill2],      # optional list of Skill objects
    tags=["specialist"],          # optional string tags
)
```

---

## OpenAI Agent

**Provider string:** `"openai"`  
**Config class:** `OpenAIAgentConfig`  
**Requires:** `pip install "moya-ai[openai]"`

```python
from moya import create_agent

agent = create_agent(
    "openai",
    name="gpt_agent",
    description="General assistant",
    model="gpt-4o",           # default: "gpt-4o"
    api_key="sk-...",         # or OPENAI_API_KEY env var
    system_prompt="You are a concise assistant.",
)
```

**Config options:**

| Field | Default | Description |
|---|---|---|
| `model_name` | `"gpt-4o"` | Any chat-completion model |
| `api_key` | env `OPENAI_API_KEY` | OpenAI API key |
| `tool_choice` | `None` | Force a specific tool or `"auto"` |
| `max_iterations` | `5` | Maximum tool-call rounds per request |

---

## Azure OpenAI Agent

**Provider string:** `"azure"`  
**Config class:** `AzureOpenAIAgentConfig`  
**Requires:** `pip install "moya-ai[azure]"`

```python
from moya.agents.azure_openai_agent import AzureOpenAIAgent, AzureOpenAIAgentConfig

config = AzureOpenAIAgentConfig(
    agent_name="azure_agent",
    agent_type="azure",
    description="Azure-hosted GPT",
    model_name="gpt-4o",
    api_key="...",
    api_base="https://my-resource.openai.azure.com/",
    api_version="2024-02-01",
)
agent = AzureOpenAIAgent(config)
```

Supports Azure AD token authentication by setting `use_azure_ad_token_provider=True` (uses `azure-identity`).

---

## Bedrock Agent

**Provider string:** `"bedrock"`  
**Config class:** `BedrockAgentConfig`  
**Requires:** `pip install "moya-ai[awsbedrock]"` + AWS credentials

```python
from moya import create_agent

agent = create_agent(
    "bedrock",
    name="claude_agent",
    description="Claude on AWS Bedrock",
    model="anthropic.claude-3-haiku-20240307-v1:0",
)
```

Uses the **Bedrock Converse API** — model-agnostic; works with Claude, Llama, Mistral, Titan and any model that supports Converse.

Credentials are loaded via the standard boto3 chain: `AWS_*` environment variables → `~/.aws/credentials` → IAM instance role.

**Config options:**

| Field | Default | Description |
|---|---|---|
| `model_id` | `"anthropic.claude-3-haiku-20240307-v1:0"` | Any Bedrock Converse-compatible model |
| `region` | `"us-east-1"` | AWS region |
| `max_iterations` | `5` | Maximum tool-call rounds |

---

## Ollama Agent

**Provider string:** `"ollama"`  
**Config class:** `OllamaAgentConfig`  
**Requires:** `pip install "moya-ai[ollama]"` + Ollama running locally

```python
from moya import create_agent

agent = create_agent(
    "ollama",
    name="local",
    description="Local Llama assistant",
    model="llama3.1",
    base_url="http://localhost:11434",  # optional, this is the default
)
```

Pull models first: `ollama pull llama3.1`

The Ollama agent uses the `/api/chat` endpoint with OpenAI-compatible tool calling. The network health check is deferred to `setup()` (called on first use), so construction never blocks.

**Config options:**

| Field | Default | Description |
|---|---|---|
| `model_name` | `"llama3.1"` | Any model pulled via `ollama pull` |
| `base_url` | `"http://localhost:11434"` | Ollama server URL |
| `max_iterations` | `5` | Maximum tool-call rounds |

---

## Remote Agent

**Provider string:** `"remote"`  
**Config class:** `RemoteAgentConfig`  
**Requires:** `pip install "moya-ai[ollama]"` (uses `requests`)

Used to call agents hosted on a remote HTTP server, including other MOYA instances (Agent-to-Agent / A2A).

```python
from moya import create_agent

agent = create_agent(
    "remote",
    name="remote_specialist",
    description="Remote specialist agent",
    base_url="http://specialist-service:8080",
    auth_token="Bearer my-token",
)
```

See `examples/remote_agent_server_with_auth.py` for the server side.

---

## CrewAI Agent

**Provider string:** `"crewai"`  
**Config class:** `CrewAIAgentConfig`  
**Requires:** `pip install "moya-ai[crewai]"`

Wraps a [CrewAI](https://docs.crewai.com/) agent so it participates in MOYA orchestration:

```python
from moya import create_agent

agent = create_agent(
    "crewai",
    name="crew_analyst",
    description="CrewAI data analyst",
    model="gpt-4o",
    api_key="sk-...",
)
```

---

## Custom Agents

Subclass `Agent` and implement the two abstract methods:

```python
from moya.agents.agent import Agent, AgentConfig
from typing import Iterator

class MyAgent(Agent):
    def handle_message(self, message: str, **kwargs) -> str:
        thread_id = kwargs.get("thread_id", "default")
        # ... call your LLM or API ...
        response = "response text"
        self._remember(thread_id, message, response)  # optional memory
        return response

    def handle_message_stream(self, message: str, **kwargs) -> Iterator[str]:
        # yield tokens as they arrive; or yield the full response in one chunk
        yield self.handle_message(message, **kwargs)

config = AgentConfig(
    agent_name="my_agent",
    agent_type="custom",
    description="My custom agent",
)
agent = MyAgent(config)
```

`_remember()` is defined on the base class — call it to persist the turn to whatever `Repository` is configured.

---

## Skills

Attach `Skill` objects at construction to augment an agent's prompt and tools:

```python
from moya import create_agent, Skill, Tool

def eco_tip(destination: str) -> str:
    """Return eco travel tips for a destination.
    Parameters:
    - destination: The destination city.
    """
    return f"Take the train to {destination} instead of flying."

eco_skill = Skill(
    name="eco_travel",
    description="Adds eco-conscious travel advice",
    prompt_snippet="Always suggest low-carbon alternatives.",
    tools_factory=lambda: [Tool(name="eco_tip", function=eco_tip)],
)

agent = create_agent(
    "openai",
    name="travel_advisor",
    description="Travel planner",
    skills=[eco_skill],
)
# agent.system_prompt now ends with "Always suggest low-carbon alternatives."
# agent.tool_registry now includes "eco_tip"
```

See [Architecture — Skills System](architecture.md#7-skills-system) for the full explanation.
