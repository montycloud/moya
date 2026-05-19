"""
InMemoryAgentRepository for Moya.

Implements the AgentRepository using in-memory Python data structures.
"""

from typing import Dict, List, Optional

from moya.agents.agent_info import AgentInfo
from moya.agents.agent import Agent
from moya.registry.agent_repository import AgentRepository


class InMemoryAgentRepository(AgentRepository):
    """
    Stores Agent objects in a simple in-memory dictionary.

    AgentInfo objects are cached and reused across calls to list_agents()
    so that mutations (e.g. health updates) persist within the process.
    """

    def __init__(self):
        self._agents: Dict[str, Agent] = {}
        self._infos: Dict[str, AgentInfo] = {}

    def save_agent(self, agent: Agent) -> None:
        skill_names = [s.name for s in getattr(agent, "skills", [])]
        tags = getattr(agent, "tags", [])
        existing = self._infos.get(agent.agent_name)
        if existing:
            existing.description = agent.description
            existing.type = agent.agent_type
            existing.skills = skill_names
            existing.tags = tags
            info = existing
        else:
            info = AgentInfo(
                agent.agent_name,
                agent.description,
                agent.agent_type,
                skills=skill_names,
                tags=tags,
            )
        self._agents[agent.agent_name] = agent
        self._infos[agent.agent_name] = info
        agent._agent_info = info

    def remove_agent(self, agent_name: str) -> None:
        self._agents.pop(agent_name, None)
        self._infos.pop(agent_name, None)

    def get_agent(self, agent_name: str) -> Optional[Agent]:
        return self._agents.get(agent_name, None)

    def list_agents(self) -> List[AgentInfo]:
        return list(self._infos.values())
