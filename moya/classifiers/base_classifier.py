from abc import ABC, abstractmethod
from typing import List, Optional

from moya.agents.agent_info import AgentInfo


class BaseClassifier(ABC):
    """Base class for agent classifiers."""
    
    @abstractmethod
    def classify(self, message: str, thread_id: Optional[str] = None, available_agents: List[AgentInfo] = None) -> str:
        """
        Classify a message and return the most appropriate agent name.
        
        :param message: The user message to classify
        :param thread_id: Optional thread ID for context
        :param available_agents: List of available agent names to choose from
        :return: Selected agent name
        """
        pass
