# Tools

A **Tool** is a plain Python function that an LLM can call during inference. MOYA auto-generates the JSON schema from the function's type hints and docstring — no manual schema writing needed.

---

## Defining a Tool

```python
from moya import Tool

def search_web(query: str, max_results: int) -> str:
    """Search the web and return a summary.

    Parameters:
    - query: The search query string.
    - max_results: Maximum number of results to return.
    """
    # your implementation
    return f"Results for '{query}'"

tool = Tool(name="search_web", function=search_web)
```

MOYA parses the docstring to extract:
- **description** — the first paragraph of the docstring.
- **parameter descriptions** — lines in the `Parameters:` section matching `- param_name: description`.
- **parameter types** — from Python type hints (`str → "string"`, `int → "integer"`, `bool → "boolean"`, `float → "number"`, `list/List → "array"`, `dict/Dict → "object"`).
- **required parameters** — all parameters without a default value.

### Docstring format

```python
def my_tool(required_arg: str, optional_arg: int = 5) -> str:
    """One-line description used as the tool description.

    Parameters:
    - required_arg: Description of the first parameter.
    - optional_arg: Description of the second parameter.
    """
```

The `Parameters:` section is optional for tools that take no arguments.

### Explicit schema

Override the auto-generated schema by passing `parameters` directly:

```python
tool = Tool(
    name="custom_tool",
    description="Does something custom",
    function=my_function,
    parameters={
        "input": {"type": "string", "description": "The input"},
        "mode":  {"type": "string", "description": "The mode"},
    },
    required=["input"],
)
```

---

## ToolRegistry

The `ToolRegistry` is the central catalogue of tools for an agent.

```python
from moya import ToolRegistry, Tool

registry = ToolRegistry()
registry.register_tool(Tool(name="search_web", function=search_web))
registry.register_tool(Tool(name="get_weather", function=get_weather))

# Lookup
tool = registry.get_tool("search_web")   # → Tool or None
names = registry.list_tools()            # → ["search_web", "get_weather"]
all_tools = registry.get_tools()         # → [Tool, Tool]
catalog = registry.get_catalog()         # → [{name, description, parameters}, ...]
```

Registering a tool with an existing name overwrites the previous entry.

### Passing a registry to an agent

```python
from moya import create_agent

agent = create_agent(
    "openai",
    name="assistant",
    description="Assistant with tools",
    tool_registry=registry,
    # is_tool_caller is set to True automatically
)
```

---

## How Tool Calling Works

When the LLM returns a tool call, the agent delegates execution to `ToolRegistry.handle_tool_call()`. This is handled automatically inside `handle_message()` — you don't need to call it manually.

```
LLM response → _extract_tool_calls() → tool.function(**args) → result appended to messages → LLM again
```

The loop runs up to `max_iterations` times (default 5) until the LLM returns a plain text response.

### Provider format translation

`ToolRegistry` formats tool definitions for each provider in the agent's `get_tool_definitions()` method:

| Provider | Format |
|---|---|
| OpenAI | `{"type": "function", "function": {"name": ..., "parameters": {"type": "object", ...}}}` |
| Bedrock Converse | `{"toolSpec": {"name": ..., "inputSchema": {"json": {...}}}}` |
| Ollama | Same structure as OpenAI |

---

## EphemeralMemory

`EphemeralMemory` provides memory-as-tools: the LLM can store and retrieve conversation snippets by calling tools rather than receiving a long history in its context.

```python
from moya import create_agent, ToolRegistry
from moya.tools.ephemeral_memory import EphemeralMemory

registry = ToolRegistry()

# Add memory tools to the registry
em = EphemeralMemory()
em.configure_memory_tools(registry)
# Registers: store_message, get_last_n_messages, get_thread_summary

agent = create_agent(
    "openai",
    name="bot",
    description="Assistant with memory tools",
    tool_registry=registry,
)
```

Each `EphemeralMemory` instance has its own isolated repository — two instances never share state.

### Legacy static API

The original class-level static methods are preserved for backward compatibility:

```python
EphemeralMemory.store_message_static(thread_id, sender, content)
EphemeralMemory.get_last_n_messages_static(thread_id, n=5)
EphemeralMemory.get_thread_summary_static(thread_id)
```

---

## MCP (Model Context Protocol)

MOYA can expose tools to MCP-compliant clients and consume tools from MCP servers.

### MCPServer — expose your tools

```python
from moya.mcp.server import MCPServer
from moya import ToolRegistry, Tool

registry = ToolRegistry()
registry.register_tool(Tool(name="get_facts", function=get_facts))

server = MCPServer(name="my_tools", tool_registry=registry)
server.run(transport="stdio")  # or "sse" for HTTP
```

Run as a script: `python my_mcp_server.py`

### MCPClient — consume remote tools

```python
from moya.mcp.client import MCPClient
import sys

client = MCPClient.from_subprocess(
    sys.executable,
    ["path/to/my_mcp_server.py"],
    name="my_tools",
)

# Discover tools from the server
tools = client.get_tools()   # → [Tool("my_tools__get_facts", ...), ...]

# Register them into a ToolRegistry
registry = ToolRegistry()
for tool in tools:
    registry.register_tool(tool)

# Use with any agent
agent = create_agent("openai", name="bot", description="...", tool_registry=registry)
```

Connect to a remote SSE server instead:

```python
client = MCPClient.from_url("http://tools-server:8080/sse", name="remote_tools")
```

### Naming convention

MCP tool names use `__` as the separator between server name and tool name (e.g. `my_tools__get_facts`) because `/` is not a valid character in OpenAI function names.

---

## Tool Best Practices

- Keep tools focused on one operation.
- Return strings (or JSON-serialisable values that MOYA converts to strings).
- Always provide a clear description in the first docstring line — the LLM uses it to decide when to call the tool.
- Describe each parameter — missing descriptions lead to incorrect calls.
- Mark parameters optional with a default value when the LLM should be able to omit them.
- Validate inputs at the tool boundary; don't rely on the LLM to pass correct types.
