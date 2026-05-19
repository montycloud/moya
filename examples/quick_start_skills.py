"""
Skills example — reusable agent capabilities in MOYA.

A Skill bundles a prompt snippet and/or tools under a single name.
Attaching a Skill to an agent via AgentConfig automatically:
  - Appends the skill's prompt_snippet to the agent's system prompt.
  - Registers the skill's tools in the agent's ToolRegistry.

This example defines two custom skills and shows how to:
  1. Attach skills to individual agents.
  2. Discover agents by skill via the AgentRegistry.
  3. Use the SkillRegistry as a shared catalog.

Requires: OPENAI_API_KEY environment variable.
"""

import os

from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
from moya.registry.agent_registry import AgentRegistry
from moya.orchestrators.simple_orchestrator import SimpleOrchestrator
from moya.skills import Skill, SkillRegistry
from moya.tools.tool import Tool
from moya.tools.tool_registry import ToolRegistry


# ---------------------------------------------------------------------------
# Define reusable tools (normally these would live in moya-skills)
# ---------------------------------------------------------------------------

def word_count(text: str) -> str:
    """Count the number of words in a piece of text.

    Parameters:
    - text: The text to count words in.
    """
    count = len(text.split())
    return f"The text contains {count} words."


def reverse_text(text: str) -> str:
    """Reverse a piece of text word by word.

    Parameters:
    - text: The text to reverse.
    """
    return " ".join(text.split()[::-1])


# ---------------------------------------------------------------------------
# Define Skills
# ---------------------------------------------------------------------------

text_analysis_skill = Skill(
    name="text_analysis",
    description="Gives the agent word-counting and text-reversal tools.",
    version="1.0.0",
    tags=["text", "analysis", "utilities"],
    prompt_snippet=(
        "You have access to text analysis tools.\n"
        "- Use 'word_count' to count words in a text.\n"
        "- Use 'reverse_text' to reverse text word by word.\n"
        "Always use these tools when the user asks about word counts or reversal."
    ),
    tools_factory=lambda: [
        Tool(name="word_count", function=word_count),
        Tool(name="reverse_text", function=reverse_text),
    ],
)

friendly_tone_skill = Skill(
    name="friendly_tone",
    description="Makes the agent respond in a warm, friendly manner.",
    version="1.0.0",
    tags=["tone", "persona"],
    prompt_snippet=(
        "Always respond in a warm, friendly, and encouraging tone. "
        "Use the user's first name if provided. End every response with a positive note."
    ),
)


# ---------------------------------------------------------------------------
# Example 1: Attach skills directly via AgentConfig
# ---------------------------------------------------------------------------

def example_direct_skill_attachment():
    print("\n" + "=" * 60)
    print("Example 1: Attach skills directly to an agent")
    print("=" * 60)

    tool_registry = ToolRegistry()  # shared registry; skills will register their tools here

    config = OpenAIAgentConfig(
        agent_name="text_helper",
        description="A helpful text analysis agent.",
        agent_type="OpenAIAgent",
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="gpt-4o-mini",
        tool_registry=tool_registry,
        is_tool_caller=True,
        # --- Attach skills here ---
        skills=[text_analysis_skill, friendly_tone_skill],
    )

    agent = OpenAIAgent(config)

    # The skills have already modified the system prompt and registered their tools.
    print(f"Agent '{agent.agent_name}' has {len(agent.skills)} skill(s) attached:")
    for skill in agent.skills:
        print(f"  • {skill.name} v{skill.version} — {skill.description}")

    print(f"\nRegistered tools: {tool_registry.list_tools()}")

    registry = AgentRegistry()
    registry.register_agent(agent)
    orchestrator = SimpleOrchestrator(registry, default_agent_name="text_helper")

    thread_id = "skills-demo-1"
    questions = [
        "How many words are in the sentence: 'The quick brown fox jumps over the lazy dog'?",
        "Can you reverse the phrase 'Hello World from MOYA'?",
    ]
    for q in questions:
        print(f"\nUser: {q}")
        response = orchestrator.orchestrate(thread_id, q)
        print(f"Agent: {response}")


# ---------------------------------------------------------------------------
# Example 2: Use a SkillRegistry as a shared catalog
# ---------------------------------------------------------------------------

def example_skill_registry():
    print("\n" + "=" * 60)
    print("Example 2: SkillRegistry catalog")
    print("=" * 60)

    skill_registry = SkillRegistry()
    skill_registry.register(text_analysis_skill)
    skill_registry.register(friendly_tone_skill)

    # Discover skills by tag
    text_skills = skill_registry.find_by_tag("text")
    print(f"Skills tagged 'text': {[s.name for s in text_skills]}")

    tone_skills = skill_registry.find_by_tag("tone")
    print(f"Skills tagged 'tone': {[s.name for s in tone_skills]}")

    # Look up a skill by name and attach it manually
    skill = skill_registry.get("text_analysis")
    print(f"\nSkill '{skill.name}': {skill.description}")
    print(f"Tags: {skill.tags}")


# ---------------------------------------------------------------------------
# Example 3: Discover agents by skill via AgentRegistry
# ---------------------------------------------------------------------------

def example_skill_based_discovery():
    print("\n" + "=" * 60)
    print("Example 3: Find agents by skill")
    print("=" * 60)

    tool_registry = ToolRegistry()

    # Agent with text_analysis skill
    analyst_config = OpenAIAgentConfig(
        agent_name="analyst",
        description="Analyses text with specialised tools.",
        agent_type="OpenAIAgent",
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="gpt-4o-mini",
        tool_registry=tool_registry,
        is_tool_caller=True,
        skills=[text_analysis_skill],
    )
    analyst = OpenAIAgent(analyst_config)

    # Agent with no skills
    chat_config = OpenAIAgentConfig(
        agent_name="chat_agent",
        description="General-purpose chat agent.",
        agent_type="OpenAIAgent",
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="gpt-4o-mini",
    )
    chat_agent = OpenAIAgent(chat_config)

    registry = AgentRegistry()
    registry.register_agent(analyst)
    registry.register_agent(chat_agent)

    # Find agents with the text_analysis skill
    capable_agents = registry.find_agents_with_skill("text_analysis")
    print(f"Agents with 'text_analysis' skill: {[a.agent_name for a in capable_agents]}")

    # All agents
    all_agents = registry.list_agents()
    print(f"\nAll registered agents:")
    for info in all_agents:
        skills_str = ", ".join(info.skills) if info.skills else "none"
        print(f"  • {info.name} — skills: [{skills_str}]")


# ---------------------------------------------------------------------------
# Run all examples
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    example_skill_registry()
    example_skill_based_discovery()
    example_direct_skill_attachment()
