"""
Entry point for the MOYA Trip Planner demo.

Runs three distinct demos in sequence to exercise every MOYA capability
implemented in Phase 1 and Phase 2.

Usage::

    python3 trip_planner/main.py

Prerequisites:
    export OPENAI_API_KEY=sk-...
    pip install openai mcp
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from trip_planner.agents import build_registry
from trip_planner.pipeline import build_pipeline

SEPARATOR = "=" * 70


def print_header(title: str) -> None:
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(f"{SEPARATOR}\n")


# ---------------------------------------------------------------------------
# Shared trip request used across all demos
# ---------------------------------------------------------------------------
TRIP_REQUEST = {
    "city": "Tokyo",
    "country": "Japan",
    "days": 7,
    "month": "October",
    "budget_usd": 4000,
    "style": "cultural",
    "passport": "US",
}


def demo1_pipeline(agent_registry, delegation_manager) -> None:
    """Demo 1 — Full pipeline: LoopStep → ParallelStep → BranchStep → Synthesis."""
    print_header("DEMO 1 — PIPELINE DEMO  (LoopStep · ParallelStep · BranchStep)")
    print("Running the trip-planning pipeline for:", TRIP_REQUEST)
    print("(This exercises LoopStep, ParallelStep, BranchStep, FunctionStep)\n")

    pipeline = build_pipeline(agent_registry, delegation_manager)

    initial_message = (
        f"I want to plan a {TRIP_REQUEST['days']}-day trip to "
        f"{TRIP_REQUEST['city']}, {TRIP_REQUEST['country']} in "
        f"{TRIP_REQUEST['month']}. My budget is ${TRIP_REQUEST['budget_usd']} USD "
        f"and I prefer {TRIP_REQUEST['style']} experiences. "
        f"I have a {TRIP_REQUEST['passport']} passport."
    )

    result = pipeline.run(
        thread_id="demo1",
        message=initial_message,
        **TRIP_REQUEST,
    )

    print(result)


def demo2_llm_delegation(agent_registry, delegation_manager) -> None:
    """Demo 2 — LLM-driven delegation via coordinator agent."""
    print_header("DEMO 2 — LLM-DRIVEN DELEGATION DEMO  (coordinator → specialists)")

    coordinator = agent_registry.get_agent("coordinator")

    follow_ups = [
        "What should I be careful about regarding safety in Tokyo?",
        "Can you suggest eco-friendly accommodation options for my Tokyo trip?",
        "Give me a revised budget if I want to add a day trip to Kyoto.",
    ]

    for i, question in enumerate(follow_ups, 1):
        print(f"Question {i}: {question}")
        print("-" * 50)
        response = coordinator.handle_message(question, thread_id="demo2")
        print(response)
        print()


def demo3_registry_discovery(agent_registry, skill_registry, tool_registry) -> None:
    """Demo 3 — Registry and skill/tag/tool discovery (no LLM calls)."""
    print_header("DEMO 3 — REGISTRY DISCOVERY DEMO  (no LLM calls)")

    # 3a. Agents with travel_safety skill
    print("Agents with 'travel_safety' skill:")
    agents_with_safety = agent_registry.find_agents_with_skill("travel_safety")
    for agent in agents_with_safety:
        print(f"  - {agent.agent_name}: {agent.description[:70]}...")
    print()

    # 3b. Agents tagged 'specialist'
    print("Agents tagged 'specialist':")
    specialists = agent_registry.find_agents_by_tag("specialist")
    for agent in specialists:
        print(f"  - {agent.agent_name}")
    print()

    # 3c. Agents tagged 'coordinator'
    print("Agents tagged 'coordinator':")
    coordinators = agent_registry.find_agents_by_tag("coordinator")
    for agent in coordinators:
        print(f"  - {agent.agent_name}")
    print()

    # 3d. Eco-related skills from SkillRegistry
    print("Eco-related skills in SkillRegistry (tag: 'eco'):")
    eco_skills = skill_registry.find_by_tag("eco")
    for skill in eco_skills:
        print(f"  - {skill.name} v{skill.version}: {skill.description}")
    print()

    # 3e. Full skill catalog
    print("All registered skills:")
    for skill in skill_registry.list_skills():
        tag_str = ", ".join(skill.tags)
        print(f"  - {skill.name} v{skill.version}  [{tag_str}]")
    print()

    # 3f. Tool catalog (MCP tools + local tools)
    print("Full tool catalog (MCP + local):")
    catalog = tool_registry.get_catalog()
    for tool_info in catalog:
        params = list(tool_info["parameters"].keys())
        param_str = ", ".join(params) if params else "no params"
        print(f"  - {tool_info['name']}({param_str})")
    print()

    # 3g. All agent summaries
    print("All registered agents:")
    for info in agent_registry.list_agents():
        skills_str = ", ".join(info.skills) if info.skills else "none"
        tags_str = ", ".join(info.tags) if info.tags else "none"
        print(f"  - {info.name}  skills=[{skills_str}]  tags=[{tags_str}]")
    print()


def main() -> None:
    print_header("MOYA TRIP PLANNER — FULL CAPABILITY DEMO")
    print("Initialising agents and MCP server...\n")

    agent_registry, skill_registry, tool_registry, delegation_manager, mcp_client = (
        build_registry()
    )

    print("Agents registered. MCP server running.\n")
    print("MCP tools discovered:")
    for t in tool_registry.get_catalog():
        print(f"  - {t['name']}")
    print()

    try:
        demo1_pipeline(agent_registry, delegation_manager)
        demo2_llm_delegation(agent_registry, delegation_manager)
        demo3_registry_discovery(agent_registry, skill_registry, tool_registry)
    finally:
        print("\nShutting down MCP server subprocess...")
        mcp_client.close()
        print("Done.")


if __name__ == "__main__":
    main()
