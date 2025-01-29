"""
AgentRegistry for Moya.

The AgentRegistry delegates to a BaseAgentRepository for actual storage
while offering discovery methods and a higher-level interface.
"""

from typing import List, Optional
from moya.agents.base_agent import Agent
from moya.registry.base_agent_repository import BaseAgentRepository
from moya.registry.in_memory_agent_repository import InMemoryAgentRepository


class AgentRegistry:
    """
    AgentRegistry holds references to Agent instances in a repository
    and provides methods to register, remove, and discover them at runtime.
    """

    def __init__(self, repository: Optional[BaseAgentRepository] = None):
        """
        :param repository: A BaseAgentRepository instance. If not provided,
                           defaults to an InMemoryAgentRepository.
        """
        self.repository = repository or InMemoryAgentRepository()

    def register_agent(self, agent: Agent) -> None:
        """
        Register (or update) an Agent in this registry.
        
        :param agent: The Agent instance to register.
        """
        self.repository.save_agent(agent)

    def remove_agent(self, agent_name: str) -> None:
        """
        Remove an Agent from the registry by its name.

        :param agent_name: The unique identifier (agent_name) of the Agent to remove.
        """
        self.repository.remove_agent(agent_name)

    def get_agent(self, agent_name: str) -> Optional[Agent]:
        """
        Retrieve an Agent by its agent_name.

        :param agent_name: The name of the Agent to retrieve.
        :return: The Agent instance if found, else None.
        """
        return self.repository.get_agent(agent_name)

    def list_agents(self) -> List[str]:
        """
        List the names of all currently registered Agents.

        :return: A list of agent_name strings.
        """
        return self.repository.list_agent_names()

    def find_agents_by_type(self, agent_type: str) -> List[Agent]:
        """
        Return a list of Agents that match the given agent_type.
        
        This is implemented by scanning all registered agents in the repository.
        For larger scale data, consider indexing or a specialized repository method.
        """
        matching_agents = []
        for agent_name in self.list_agents():
            agent = self.get_agent(agent_name)
            if agent and agent.agent_type == agent_type:
                matching_agents.append(agent)
        return matching_agents

    def find_agents_by_description(self, search_text: str) -> List[Agent]:
        """
        Return a list of Agents whose description contains the given search text
        (case-insensitive substring search for now, we'll do semantic/vector search later).
        
        This is implemented by scanning all registered agents in the repository.
        """
        search_text_lower = search_text.lower()
        matching_agents = []
        for agent_name in self.list_agents():
            agent = self.get_agent(agent_name)
            if agent and search_text_lower in agent.description.lower():
                matching_agents.append(agent)
        return matching_agents
