"""
BaseOrchestrator for Moya.

Defines an abstract class that orchestrates conversations between
users (or other agents) and registered Moya agents.
"""

import abc
from typing import Any, Optional

from moya.registry.agent_registry import AgentRegistry


class BaseOrchestrator(abc.ABC):
    """
    BaseOrchestrator coordinates message flow among one or more agents
    in response to user or agent-initiated messages.

    Responsibilities:
    - Receiving and parsing incoming messages,
    - Selecting appropriate agent(s) to handle the message,
    - Optionally storing conversation history in memory,
    - Returning the aggregated response to the caller or next step.

    Concrete subclasses must implement the 'orchestrate' method (or
    a similar interface) to define how messages are routed.
    """

    def __init__(
        self,
        agent_registry: AgentRegistry,
        config: Optional[Any] = None,
        **kwargs
    ):
        """
        :param agent_registry: The AgentRegistry instance used to discover or retrieve agents.
        :param config: Optional orchestrator configuration parameters.
        :param kwargs: Additional orchestrator-specific parameters.
        """
        self.agent_registry = agent_registry
        self.config = config or {}

    @abc.abstractmethod
    def orchestrate(self, thread_id: str, user_message: str, stream_callback=None, **kwargs) -> str:
        """
        Orchestrate conversation flow given a user message (or agent-to-agent message).
        Subclasses decide which agent(s) to call and how to combine responses.

        :param thread_id: The identifier of the conversation thread.
        :param user_message: The latest message from the user (or external actor).
        :param stream_callback: Optional callback function for streaming responses.
        :param kwargs: Additional context that may be relevant (e.g., user_id, metadata).
        :return: A string response (could be aggregated from multiple agents).
        """
        raise NotImplementedError("Subclasses must implement orchestrate().")
