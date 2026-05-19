"""
MultiAgentOrchestrator for Moya.

Routes each message to the most appropriate agent using a Classifier,
then optionally stores the exchange in a memory repository.
"""

from typing import Optional

from moya.orchestrators.orchestrator import Orchestrator
from moya.registry.agent_registry import AgentRegistry
from moya.classifiers.classifier import Classifier


class MultiAgentOrchestrator(Orchestrator):
    """
    Classifier-driven orchestrator that selects the best agent for each message.

    Memory storage is opt-in: pass a ``memory`` repository to record every
    user message and agent response.  When omitted no messages are persisted.
    """

    def __init__(
        self,
        agent_registry: AgentRegistry,
        classifier: Classifier,
        default_agent_name: Optional[str] = None,
        config: Optional[dict] = None,
        memory=None,
    ):
        """
        :param agent_registry:      Registry of available agents.
        :param classifier:          Selects which agent handles each message.
        :param default_agent_name:  Fallback when classification returns nothing.
        :param config:              Optional orchestrator configuration.
        :param memory:              Optional Repository for conversation history.
        """
        super().__init__(agent_registry=agent_registry, config=config)
        self.classifier = classifier
        self.default_agent_name = default_agent_name
        self.memory = memory

    def orchestrate(
        self,
        thread_id: str,
        user_message: str,
        stream_callback=None,
        **kwargs,
    ) -> str:
        available_agents = self.agent_registry.list_agents()
        if not available_agents:
            return "[No agents available to handle message.]"

        # Classifier selects agent; caller can override via agent_name kwarg
        agent_name = kwargs.get("agent_name") or self.classifier.classify(
            message=user_message,
            thread_id=thread_id,
            available_agents=available_agents,
        )
        if not agent_name and self.default_agent_name:
            agent_name = self.default_agent_name

        agent = self.agent_registry.get_agent(agent_name) if agent_name else None
        if not agent:
            searched = [a.name for a in available_agents]
            return (
                f"[No suitable agent found for thread '{thread_id}'. "
                f"Classifier returned '{agent_name}'. "
                f"Registered agents: {searched}]"
            )

        agent_prefix = f"[{agent.agent_name}] "

        # Persist user message (if memory configured)
        self._remember(thread_id, sender="user", content=user_message)

        if stream_callback:
            stream_callback(agent_prefix)
            response = agent_prefix
            for chunk in (agent.handle_message_stream(user_message, thread_id=thread_id, **kwargs) or []):
                stream_callback(chunk)
                response += chunk
        else:
            response = agent_prefix + agent.handle_message(user_message, thread_id=thread_id, **kwargs)

        # Persist agent response
        self._remember(thread_id, sender=agent.agent_name, content=response)
        return response

    def _remember(self, thread_id: str, sender: str, content: str) -> None:
        """Store a single message if a memory repository is configured."""
        if not self.memory:
            return
        from moya.conversation.thread import Thread
        from moya.conversation.message import Message
        if self.memory.get_thread(thread_id) is None:
            self.memory.create_thread(Thread(thread_id=thread_id))
        self.memory.append_message(
            thread_id,
            Message(thread_id=thread_id, sender=sender, content=content),
        )
