"""
Helpers for building A2A AgentCard protobuf messages from Moya agents.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill

if TYPE_CHECKING:
    from moya.agents.agent import Agent


def agent_card_from_moya(
    agent: "Agent",
    endpoint_url: str,
    version: str = "1.0.0",
    streaming: bool = False,
) -> AgentCard:
    """
    Build an A2A ``AgentCard`` from a Moya ``Agent``.

    Args:
        agent:        The Moya agent to describe.
        endpoint_url: The base URL at which this agent's A2A server is reachable
                      (e.g. ``"http://localhost:8000"``).
        version:      Semantic version string for the agent card.
        streaming:    Whether the server supports streaming responses.

    Returns:
        A populated ``AgentCard`` protobuf message.
    """
    card = AgentCard()
    card.name = agent.agent_name
    card.description = agent.description
    card.version = version

    # REST interface
    interface = AgentInterface()
    interface.url = endpoint_url
    card.supported_interfaces.append(interface)

    # Capabilities
    cap = AgentCapabilities()
    cap.streaming = streaming
    card.capabilities.CopyFrom(cap)

    # Skills — sourced from agent.skills (Moya Skill objects)
    for skill in getattr(agent, "skills", []):
        a2a_skill = AgentSkill()
        a2a_skill.id = skill.name
        a2a_skill.name = skill.name
        a2a_skill.description = skill.description
        if getattr(skill, "tags", None):
            a2a_skill.tags.extend(skill.tags)
        card.skills.append(a2a_skill)

    return card


def agent_card_to_dict(card: AgentCard) -> dict:
    """
    Serialise an ``AgentCard`` protobuf to a plain dict (for JSON responses).

    Uses the canonical A2A proto-to-dict conversion with camelCase field names
    preserved as snake_case for readability.
    """
    from google.protobuf.json_format import MessageToDict
    return MessageToDict(card, preserving_proto_field_name=True)
