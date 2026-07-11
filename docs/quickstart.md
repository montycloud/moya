# Quickstart

## Installation

```bash
# Core framework only (no provider)
pip install moya-ai

# Add the provider(s) you need
pip install "moya-ai[openai]"       # OpenAI / Azure OpenAI
pip install "moya-ai[awsbedrock]"   # AWS Bedrock
pip install "moya-ai[ollama]"       # Ollama (local models)
pip install "moya-ai[crewai]"       # CrewAI

# Everything
pip install "moya-ai[all]"
```

Requires Python 3.11+.

---

## Your first agent

```python
from moya import create_agent

agent = create_agent(
    "openai",
    name="assistant",
    description="General-purpose assistant",
    api_key="sk-...",   # or set OPENAI_API_KEY env var
)

response = agent.handle_message("Explain MOYA in one sentence.")
print(response)
```

`create_agent()` is the single entry point for all providers. The first argument is the provider string; everything else is keyword-only.

---

## Streaming responses

```python
for chunk in agent.handle_message_stream("Tell me a short story."):
    print(chunk, end="", flush=True)
print()
```

All agents support `handle_message_stream()`. It is a generator that yields `str` chunks.

---

## Adding tools

Define a Python function with type hints and a docstring — MOYA builds the schema automatically.

```python
from moya import create_agent, Tool, ToolRegistry

def get_weather(city: str) -> str:
    """Return current weather for a city.

    Parameters:
    - city: The city name.
    """
    return f"Sunny, 22 °C in {city}"

registry = ToolRegistry()
registry.register_tool(Tool(name="get_weather", function=get_weather))

agent = create_agent(
    "openai",
    name="weather_bot",
    description="Answers weather questions",
    tool_registry=registry,
)

print(agent.handle_message("What's the weather in Paris?"))
```

The agent calls `get_weather` automatically when the LLM decides it's needed.

---

## Conversation memory

Pass a `Repository` to persist conversation history across calls:

```python
from moya import create_agent, InMemoryRepository

memory = InMemoryRepository()
agent = create_agent("openai", name="bot", description="Chat bot", memory=memory)

agent.handle_message("My name is Alice.", thread_id="session-1")
response = agent.handle_message("What is my name?", thread_id="session-1")
print(response)  # "Your name is Alice."
```

Use `FileSystemRepository(base_path="./memory")` for durable storage.

---

## Local model with Ollama

```bash
ollama pull llama3.1
```

```python
from moya import create_agent

agent = create_agent(
    "ollama",
    name="local",
    description="Local assistant",
    model="llama3.1",
)
print(agent.handle_message("Hello!"))
```

---

## AWS Bedrock

```python
from moya import create_agent

agent = create_agent(
    "bedrock",
    name="claude",
    description="Claude on Bedrock",
    model="anthropic.claude-3-haiku-20240307-v1:0",
)
# Credentials come from the boto3 chain: env vars, ~/.aws/credentials, IAM role
print(agent.handle_message("Hello!"))
```

---

## Multi-agent pipeline

```python
from moya import (
    create_agent, Pipeline, AgentStep, FunctionStep, FlowContext,
)

researcher = create_agent("openai", name="researcher", description="Researches topics")
writer     = create_agent("openai", name="writer",     description="Writes summaries")

def add_header(ctx: FlowContext) -> FlowContext:
    ctx.output = "## Summary\n\n" + ctx.output
    return ctx

pipeline = Pipeline([
    AgentStep(researcher),
    AgentStep(writer),
    FunctionStep(add_header),
])

result = pipeline.run(thread_id="t1", message="What is quantum computing?")
print(result)
```

---

## Next steps

- [Architecture](architecture.md) — how all the pieces fit together
- [Agents](agents.md) — all agent types and their config options
- [Tools](tools.md) — tool system and MCP integration
- [Orchestrators](orchestrators.md) — routing and delegation patterns
- [Memory](memory.md) — conversation persistence
