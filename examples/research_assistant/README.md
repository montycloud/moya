# Research Assistant

A two-agent **pipeline** that shows off MOYA **tools** and **memory**.

```
Input ─▶ researcher (tools: search_knowledge, list_related_topics) ─▶ writer ─▶ Answer
                         └── shared CompositeMemory (long-term on disk + short-term window) ──┘
```

- **Multiple agents** — a `researcher` gathers facts, a `writer` makes them readable.
- **Tools** — the researcher calls the plain Python functions in `tools.py`.
- **Memory** — both agents share a `CompositeMemory`. Each turn is stored; earlier
  turns are recalled and injected, so a follow-up question (“how is it *different*?”)
  remembers the previous one.

## Run

```bash
# OpenAI if OPENAI_API_KEY is set, otherwise a local Ollama model.
export OPENAI_API_KEY=sk-...            # optional
python -m examples.research_assistant.main

# Verify tools + memory + build with no LLM call:
python -m examples.research_assistant.main --check
```

Ollama users: install from https://ollama.com, then `ollama pull llama3.1`
(or set `OLLAMA_MODEL`). Long-term memory is written under `./moya_memory/research_assistant`.

## Files
| File | What it is |
|---|---|
| `tools.py` | The Python tool functions (a tiny knowledge base). |
| `main.py` | Builds the agents/memory/pipeline and runs a scripted 2-turn demo. |
