"""
Research Assistant — a two-agent pipeline with tools and memory.

What it demonstrates
--------------------
* **Multiple agents** in a Pipeline: a *researcher* gathers facts, a *writer*
  turns them into a clear answer.
* **Tools**: the researcher calls real Python functions (`search_knowledge`,
  `list_related_topics`) — see ``tools.py``.
* **Memory**: a ``CompositeMemory`` (long-term on disk + a short-term window)
  is shared by both agents. Each turn is stored automatically; the previous
  turns are recalled and injected so the assistant remembers the conversation.

Run it
------
    # Uses OpenAI if OPENAI_API_KEY is set, otherwise a local Ollama model.
    export OPENAI_API_KEY=sk-...          # optional
    python -m examples.research_assistant.main

    # Verify wiring (tools + memory + build) without calling any LLM:
    python -m examples.research_assistant.main --check
"""

from __future__ import annotations

import argparse
import os

from moya import create_agent, Pipeline, AgentStep
from moya.conversation.message import Message
from moya.memory import ShortTermMemory, LongTermMemory, CompositeMemory
from moya.tools.tool import Tool
from moya.tools.tool_registry import ToolRegistry

from examples.research_assistant.tools import search_knowledge, list_related_topics

MEMORY_DIR = os.getenv("RESEARCH_MEMORY_DIR", "./moya_memory/research_assistant")


def _provider():
    """Pick a backend: OpenAI when a key is present, else local Ollama."""
    if os.getenv("OPENAI_API_KEY"):
        return "openai", {"model": "gpt-4o-mini", "api_key": os.environ["OPENAI_API_KEY"]}
    return "ollama", {
        "model": os.getenv("OLLAMA_MODEL", "llama3.1"),
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    }


def build():
    """Construct the tools, shared memory, agents, and pipeline."""
    tools = ToolRegistry()
    tools.register_tool(Tool(
        name="search_knowledge",
        description="Look up factual notes on a topic from the knowledge base.",
        function=search_knowledge,
    ))
    tools.register_tool(Tool(
        name="list_related_topics",
        description="List topics related to a given topic.",
        function=list_related_topics,
    ))

    # Composite memory: full history on disk + a fast recent-window in RAM.
    memory = CompositeMemory([
        LongTermMemory(base_path=MEMORY_DIR),
        ShortTermMemory(window_size=8),
    ])

    provider, kw = _provider()
    researcher = create_agent(
        provider,
        name="researcher",
        description="Gathers facts using tools before answering.",
        system_prompt=(
            "You are a meticulous researcher. ALWAYS call the search_knowledge tool "
            "to gather facts before answering, and mention what you found. If asked to "
            "compare with something discussed earlier, use the conversation context."
        ),
        tool_registry=tools,
        memory=memory,
        **kw,
    )
    writer = create_agent(
        provider,
        name="writer",
        description="Turns research notes into a clear, concise answer.",
        system_prompt=(
            "You are a clear writer. Rewrite the researcher's findings into a concise, "
            "friendly explanation for a curious non-expert. Keep it under 6 sentences."
        ),
        memory=memory,
        **kw,
    )

    pipeline = Pipeline([
        AgentStep(researcher, name="researcher"),
        AgentStep(writer, name="writer"),
    ])
    return pipeline, memory, tools, [researcher, writer]


def recall_context(memory, thread_id: str, n: int = 6) -> str:
    """Pull the last ``n`` messages from memory as injectable context."""
    thread = memory.get_thread(thread_id)
    if not thread or not thread.messages:
        return ""
    recent = thread.get_last_n_messages(n)
    body = "\n".join(f"{m.sender}: {m.content}" for m in recent)
    return f"Conversation so far:\n{body}\n\n"


def ask(pipeline, memory, thread_id: str, question: str) -> str:
    """Recall prior context, inject it, run the pipeline for one turn."""
    context = recall_context(memory, thread_id)
    if context:
        n_lines = context.strip().count("\n")  # minus the header line
        print(f"  🧠 recalled {n_lines} prior message(s) from memory")
    message = f"{context}User question: {question}"
    return pipeline.run(thread_id=thread_id, message=message)


def demo() -> None:
    """Scripted two-turn conversation; the 2nd turn relies on memory."""
    pipeline, memory, *_ = build()
    thread_id = "research-demo"

    questions = [
        "What is quantum computing?",
        "How is it different from classical computing?",  # needs turn 1 in memory
    ]
    for q in questions:
        print(f"\n=== You: {q}")
        try:
            answer = ask(pipeline, memory, thread_id, q)
        except Exception as exc:  # noqa: BLE001 — provider unreachable, etc.
            print(f"  ⚠ Could not reach the LLM backend: {exc}")
            print("    Set OPENAI_API_KEY, or start Ollama (https://ollama.com) and "
                  "`ollama pull llama3.1`. Then re-run.")
            return
        print(f"Assistant: {answer}")


def check() -> None:
    """Exercise tools + memory + construction with NO LLM calls (for CI/smoke)."""
    print("• tools")
    print("   search_knowledge('quantum computing') ->",
          search_knowledge("quantum computing")[:64], "...")
    print("   list_related_topics('quantum computing') ->",
          list_related_topics("quantum computing"))

    print("• build")
    pipeline, memory, tools, agents = build()
    print(f"   built pipeline with {len(agents)} agents and "
          f"{len(tools.list_tools())} tools")

    print("• memory store + recall")
    tid = "check-thread"
    memory.append_message(tid, Message(thread_id=tid, sender="user", content="What is quantum computing?"))
    memory.append_message(tid, Message(thread_id=tid, sender="researcher", content="Qubits use superposition."))
    ctx = recall_context(memory, tid)
    assert "Qubits use superposition." in ctx, "memory recall failed"
    print("   recalled context:\n     " + ctx.strip().replace("\n", "\n     "))
    print("\n✓ research_assistant check passed")


def main() -> None:
    parser = argparse.ArgumentParser(description="Research Assistant demo")
    parser.add_argument("--check", action="store_true",
                        help="Verify tools/memory/build without calling an LLM.")
    args = parser.parse_args()
    check() if args.check else demo()


if __name__ == "__main__":
    main()
