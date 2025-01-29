"""
InMemoryAgentRepository for Moya.

Implements the BaseAgentRepository using in-memory Python data structures.
"""

from typing import Dict, List, Optional
from moya.agents.base_agent import Agent
from moya.registry.base_agent_repository import BaseAgentRepository


class InMemoryAgentRepository(BaseAgentRepository):
    """
    Stores Agent objects in a simple in-memory dictionary.
    """

    def __init__(self):
        # Key: agent_name, Value: Agent instance
        self._agents: Dict[str, Agent] = {}

    def save_agent(self, agent: Agent) -> None:
        """
        Store or update the given agent in memory.
        """
        self._agents[agent.agent_name] = agent

    def remove_agent(self, agent_name: str) -> None:
        """
        Remove the agent from the in-memory store if it exists.
        """
        if agent_name in self._agents:
            del self._agents[agent_name]

    def get_agent(self, agent_name: str) -> Optional[Agent]:
        """
        Retrieve the agent by name.
        """
        return self._agents.get(agent_name, None)

    def list_agent_names(self) -> List[str]:
        """
        Return all agent names.
        """
        return list(self._agents.keys())
