# MOYA Documentation

MOYA is a lightweight, model-agnostic Python framework for building multi-agent AI systems.

## Navigation

| Document | What you'll find |
|---|---|
| [Architecture](architecture.md) | System design, component diagrams, data-flow walkthroughs, design principles |
| [Quickstart](quickstart.md) | Installation and first working examples |
| [Agents](agents.md) | All agent types, config options, streaming, custom agents |
| [Tools](tools.md) | Defining tools, ToolRegistry, MCP integration |
| [Orchestrators](orchestrators.md) | Simple, Multi-Agent, ReAct patterns; DelegationManager |
| [Memory](memory.md) | Repository pattern, EphemeralMemory, FileSystemRepository |
| [Examples](examples.md) | Walkthrough of the bundled example scripts |
| [API Reference](reference.md) | Detailed module and method reference |
| [ADRs](adr/) | Architecture Decision Records explaining key design choices |

## Getting Started

```bash
pip install "moya-ai[openai]"
export OPENAI_API_KEY=sk-...
```

```python
from moya import create_agent

agent = create_agent("openai", name="assistant", description="Helpful assistant")
print(agent.handle_message("Hello, what can you do?"))
```
