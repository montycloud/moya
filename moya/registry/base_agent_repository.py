"""
BaseAgentRepository for Moya.

Defines an abstract class that describes the interface for storing and
retrieving Agent instances. Future implementations might store agents
in memory, databases, files, etc.
"""

import abc
from typing import List, Optional
from moya.agents.base_agent import Agent


class BaseAgentRepository(abc.ABC):
    """
    Abstract interface for an Agent storage system.
    """

    @abc.abstractmethod
    def save_agent(self, agent: Agent) -> None:
        """
        Persist (or update) the given agent.

        :param agent: The Agent instance to store.
        """
        pass

    @abc.abstractmethod
    def remove_agent(self, agent_name: str) -> None:
        """
        Remove the agent with the given name from storage.

        :param agent_name: The unique identifier of the Agent to remove.
        """
        pass

    @abc.abstractmethod
    def get_agent(self, agent_name: str) -> Optional[Agent]:
        """
        Retrieve an agent by its name.

        :param agent_name: The name of the agent to retrieve.
        :return: The matching Agent instance if found, else None.
        """
        pass

    @abc.abstractmethod
    def list_agent_names(self) -> List[str]:
        """
        List the names of all agents currently stored.

        :return: A list of agent_name strings.
        """
        pass
