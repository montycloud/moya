"""
Support Desk — routed multi-agent delegation with tools and memory.

What it demonstrates
--------------------
* **Multiple agents** discovered through an ``AgentRegistry`` and driven by a
  ``DelegationManager``: a *billing* specialist and a *shipping* specialist.
* **Tools**: each specialist calls real Python functions (`lookup_order`,
  `refund_policy`) — see ``tools.py``.
* **Memory**: a shared ``CompositeMemory`` remembers the customer across turns,
  so a follow-up like "when will the refund arrive?" still knows which order
  they meant — even though a *different* agent handled the first turn.
* **Routing**: a small deterministic router picks the specialist, so the demo
  behaves the same on any backend (no reliance on the model to self-route).

Run it
------
    export OPENAI_API_KEY=sk-...          # optional; else uses local Ollama
    python -m examples.support_desk.main

    # Verify wiring (tools + memory + routing + build) without an LLM:
    python -m examples.support_desk.main --check
"""

from __future__ import annotations

import argparse
import os
import re

from moya import create_agent
from moya.conversation.message import Message
from moya.delegation.manager import DelegationManager
from moya.memory import ShortTermMemory, LongTermMemory, CompositeMemory
from moya.registry.agent_registry import AgentRegistry
from moya.tools.tool import Tool
from moya.tools.tool_registry import ToolRegistry

from examples.support_desk.tools import lookup_order, refund_policy

MEMORY_DIR = os.getenv("SUPPORT_MEMORY_DIR", "./moya_memory/support_desk")

_BILLING_WORDS = ("refund", "charge", "bill", "invoice", "payment", "money", "cost")
_SHIPPING_WORDS = ("ship", "track", "deliver", "where", "arrive", "status", "eta")


def _provider():
    if os.getenv("OPENAI_API_KEY"):
        return "openai", {"model": "gpt-4o-mini", "api_key": os.environ["OPENAI_API_KEY"]}
    return "ollama", {
        "model": os.getenv("OLLAMA_MODEL", "llama3.1"),
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    }


def route(question: str) -> str:
    """Deterministically pick the specialist agent for a question."""
    q = question.lower()
    billing = sum(w in q for w in _BILLING_WORDS)
    shipping = sum(w in q for w in _SHIPPING_WORDS)
    return "billing_agent" if billing >= shipping and billing > 0 else "shipping_agent"


def build():
    """Construct tools, shared memory, both specialists, registry + manager."""
    # Tools shared by both specialists.
    tools = ToolRegistry()
    tools.register_tool(Tool(
        name="lookup_order",
        description="Look up an order's status, item, ETA, and total by its id.",
        function=lookup_order,
    ))
    tools.register_tool(Tool(
        name="refund_policy",
        description="Return the store's refund policy.",
        function=refund_policy,
    ))

    memory = CompositeMemory([
        LongTermMemory(base_path=MEMORY_DIR),
        ShortTermMemory(window_size=10),
    ])

    provider, kw = _provider()
    billing = create_agent(
        provider,
        name="billing_agent",
        description="Handles refunds, charges, and payment questions.",
        system_prompt=(
            "You are a billing support specialist. Use refund_policy and lookup_order "
            "as needed. Be precise about amounts and timelines. If an order id appears "
            "in the conversation context, reuse it."
        ),
        tool_registry=tools,
        memory=memory,
        **kw,
    )
    shipping = create_agent(
        provider,
        name="shipping_agent",
        description="Handles delivery, tracking, and order-status questions.",
        system_prompt=(
            "You are a shipping support specialist. Use lookup_order to check status "
            "and ETA. If an order id appears in the conversation context, reuse it."
        ),
        tool_registry=tools,
        memory=memory,
        **kw,
    )

    registry = AgentRegistry()
    registry.register_agent(billing)
    registry.register_agent(shipping)
    manager = DelegationManager(registry)
    return manager, memory, tools, registry


def recall_context(memory, thread_id: str, n: int = 8) -> str:
    thread = memory.get_thread(thread_id)
    if not thread or not thread.messages:
        return ""
    recent = thread.get_last_n_messages(n)
    body = "\n".join(f"{m.sender}: {m.content}" for m in recent)
    return f"Conversation so far:\n{body}\n\n"


def handle(manager, memory, thread_id: str, question: str) -> tuple[str, str]:
    """Route, inject recalled context, delegate to the chosen specialist."""
    agent_name = route(question)
    context = recall_context(memory, thread_id)
    if context:
        print(f"  🧠 recalled {context.strip().count(chr(10))} prior message(s) from memory")
    task = f"{context}Customer says: {question}"
    answer = manager.delegate(task=task, agent_name=agent_name, thread_id=thread_id)
    return agent_name, answer


def demo() -> None:
    """Two turns: the follow-up relies on remembering the order id."""
    manager, memory, *_ = build()
    thread_id = "support-demo"

    turns = [
        "Where is my order A1001?",                 # → shipping, looks up A1001
        "And what's the refund policy if I send it back?",  # → billing, remembers A1001
    ]
    for q in turns:
        print(f"\n=== Customer: {q}")
        try:
            agent_name, answer = handle(manager, memory, thread_id, q)
        except Exception as exc:  # noqa: BLE001
            print(f"  ⚠ Could not reach the LLM backend: {exc}")
            print("    Set OPENAI_API_KEY, or start Ollama and `ollama pull llama3.1`.")
            return
        print(f"[{agent_name}]: {answer}")


def check() -> None:
    """Exercise tools + routing + memory + build with NO LLM calls."""
    print("• tools")
    print("   lookup_order('A1001') ->", lookup_order("A1001"))
    print("   refund_policy() ->", refund_policy()[:60], "...")

    print("• routing")
    assert route("Where is my order A1001?") == "shipping_agent"
    assert route("I want a refund for my charge") == "billing_agent"
    print("   'Where is my order?' ->", route("Where is my order A1001?"))
    print("   'I want a refund'    ->", route("I want a refund for my charge"))

    print("• build")
    manager, memory, tools, registry = build()
    print(f"   registered agents: {[a.name for a in registry.list_agents()]}")
    print(f"   shared tools: {list(tools.list_tools())}")

    print("• memory remembers the order across turns")
    tid = "check-thread"
    memory.append_message(tid, Message(thread_id=tid, sender="customer", content="Where is order A1001?"))
    memory.append_message(tid, Message(thread_id=tid, sender="shipping_agent", content="Order A1001 is shipped, ETA 2 days."))
    ctx = recall_context(memory, tid)
    assert "A1001" in ctx
    print("   recalled context mentions the order:", "A1001" in ctx)

    print("\n✓ support_desk check passed")


def main() -> None:
    parser = argparse.ArgumentParser(description="Support Desk demo")
    parser.add_argument("--check", action="store_true",
                        help="Verify tools/routing/memory/build without calling an LLM.")
    args = parser.parse_args()
    check() if args.check else demo()


if __name__ == "__main__":
    main()
