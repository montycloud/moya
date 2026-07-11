"""
Sub-agents example — task delegation in MOYA.

Demonstrates three delegation patterns:

1. **Programmatic delegation** — call ``manager.delegate()`` directly from
   Python code (useful in Pipelines or custom orchestrators).

2. **Parallel delegation** — dispatch multiple tasks concurrently and collect
   all results.

3. **LLM-driven delegation** — register delegation tools in a parent agent's
   ToolRegistry; the LLM decides when and to whom to delegate.

Requires: OPENAI_API_KEY environment variable.
"""

import os

from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
from moya.delegation import DelegationManager
from moya.orchestrators.simple_orchestrator import SimpleOrchestrator
from moya.registry.agent_registry import AgentRegistry
from moya.tools.tool_registry import ToolRegistry


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def make_agent(name: str, description: str, system_prompt: str) -> OpenAIAgent:
    config = OpenAIAgentConfig(
        agent_name=name,
        description=description,
        agent_type="OpenAIAgent",
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="gpt-4o-mini",
        system_prompt=system_prompt,
    )
    return OpenAIAgent(config)


# ---------------------------------------------------------------------------
# Build shared registry
# ---------------------------------------------------------------------------

def build_registry() -> AgentRegistry:
    registry = AgentRegistry()

    registry.register_agent(make_agent(
        "researcher",
        "Finds key facts about a topic.",
        "You are a research assistant. Given a topic, list 5 key facts in bullet points. Be concise.",
    ))
    registry.register_agent(make_agent(
        "summariser",
        "Condenses text into a short summary.",
        "You are a summariser. Condense the given text to 2–3 sentences. Be accurate and concise.",
    ))
    registry.register_agent(make_agent(
        "critic",
        "Reviews and critiques a piece of writing.",
        "You are a writing critic. Identify 2 strengths and 2 weaknesses in the given text. Be specific.",
    ))
    registry.register_agent(make_agent(
        "translator",
        "Translates text to Spanish.",
        "Translate the given text to Spanish. Return only the translation.",
    ))

    return registry


# ---------------------------------------------------------------------------
# Example 1: Programmatic delegation
# ---------------------------------------------------------------------------

def example_programmatic(registry: AgentRegistry) -> None:
    print("\n" + "=" * 60)
    print("Example 1: Programmatic delegation")
    print("=" * 60)

    manager = DelegationManager(registry, max_depth=3)

    # Delegate research, then summarise the result
    topic = "The James Webb Space Telescope"
    print(f"\nResearching: {topic}")
    facts = manager.delegate(task=topic, agent_name="researcher")
    print(f"\nFacts:\n{facts}")

    print("\nSummarising...")
    summary = manager.delegate(task=facts, agent_name="summariser")
    print(f"\nSummary:\n{summary}")


# ---------------------------------------------------------------------------
# Example 2: Parallel delegation
# ---------------------------------------------------------------------------

def example_parallel(registry: AgentRegistry) -> None:
    print("\n" + "=" * 60)
    print("Example 2: Parallel delegation")
    print("=" * 60)

    manager = DelegationManager(registry, max_depth=3)

    text = (
        "Quantum computing harnesses quantum mechanical phenomena such as superposition "
        "and entanglement to perform computations. Unlike classical bits that are either "
        "0 or 1, qubits can exist in multiple states simultaneously, enabling certain "
        "problems to be solved exponentially faster than classical computers."
    )

    print("\nRunning critic and translator in parallel...")
    results = manager.delegate_parallel(
        tasks=[
            (text, "critic"),
            (text, "translator"),
        ],
    )

    print(f"\nCritique:\n{results[0]}")
    print(f"\nSpanish translation:\n{results[1]}")


# ---------------------------------------------------------------------------
# Example 3: LLM-driven delegation
# ---------------------------------------------------------------------------

def example_llm_driven(registry: AgentRegistry) -> None:
    print("\n" + "=" * 60)
    print("Example 3: LLM-driven delegation")
    print("=" * 60)

    manager = DelegationManager(registry, max_depth=3)

    # Give the coordinator agent delegation tools
    tool_registry = ToolRegistry()
    manager.setup_tools(tool_registry)

    print(f"\nDelegation tools registered: {tool_registry.list_tools()}")

    # Coordinator agent — it decides how to fulfil the user's request
    coordinator_config = OpenAIAgentConfig(
        agent_name="coordinator",
        description="Coordinates tasks by delegating to specialist agents.",
        agent_type="OpenAIAgent",
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="gpt-4o-mini",
        tool_registry=tool_registry,
        is_tool_caller=True,
        system_prompt=(
            "You are a coordinator. You have access to specialist agents. "
            "Use list_agents to discover available agents, then use delegate_task "
            "to send the user's request to the most appropriate specialist. "
            "Return the specialist's response directly."
        ),
    )
    coordinator = OpenAIAgent(coordinator_config)
    registry.register_agent(coordinator)

    # Orchestrate via the coordinator
    agent_registry_for_orchestrator = AgentRegistry()
    agent_registry_for_orchestrator.register_agent(coordinator)

    orchestrator = SimpleOrchestrator(
        agent_registry=agent_registry_for_orchestrator,
        default_agent_name="coordinator",
    )

    requests = [
        "I need a summary of: 'Neural networks are computational models inspired by the human brain, consisting of interconnected nodes that process information using connectionist approaches. Modern deep learning uses many layers of these networks to learn representations of data.'",
        "Can you translate 'Good morning, how are you?' to Spanish?",
    ]

    thread_id = "subagents-demo"
    for req in requests:
        print(f"\nUser: {req[:80]}...")
        response = orchestrator.orchestrate(thread_id, req)
        print(f"Coordinator: {response}")


# ---------------------------------------------------------------------------
# Example 4: Depth limit enforcement
# ---------------------------------------------------------------------------

def example_depth_guard(registry: AgentRegistry) -> None:
    print("\n" + "=" * 60)
    print("Example 4: Depth limit guard")
    print("=" * 60)

    from moya.delegation import MaxDelegationDepthError

    manager = DelegationManager(registry, max_depth=1)

    try:
        # First call: depth 0 -> 1 (allowed)
        # If the sub-agent also tried to delegate, depth 1 -> 2 would be blocked
        result = manager.delegate("Quick research on AI", agent_name="researcher")
        print(f"Depth-1 delegation succeeded: {result[:80]}...")
    except MaxDelegationDepthError as e:
        print(f"Caught expected depth error: {e}")

    # Simulate exceeding depth
    manager._local.depth = 1  # pretend we're already at max
    try:
        manager.delegate("This should be blocked", agent_name="summariser")
    except MaxDelegationDepthError as e:
        print(f"Correctly blocked at max depth: {e}")
    finally:
        manager._local.depth = 0  # reset


# ---------------------------------------------------------------------------
# Run all examples
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    registry = build_registry()

    example_programmatic(registry)
    example_parallel(registry)
    example_llm_driven(registry)
    example_depth_guard(registry)
