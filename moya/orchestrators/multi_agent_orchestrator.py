from typing import Optional
from moya.orchestrators.base_orchestrator import BaseOrchestrator
from moya.registry.agent_registry import AgentRegistry
from moya.classifiers.base_classifier import BaseClassifier

class MultiAgentOrchestrator(BaseOrchestrator):
    """
    An orchestrator that uses a classifier to route messages to appropriate agents.
    """

    def __init__(
        self,
        agent_registry: AgentRegistry,
        classifier: BaseClassifier,
        default_agent_name: Optional[str] = None,
        config: Optional[dict] = None
    ):
        """
        :param agent_registry: The AgentRegistry to retrieve agents from
        :param classifier: The classifier to use for agent selection
        :param default_agent_name: Fallback agent if classification fails
        :param config: Optional configuration dictionary
        """
        super().__init__(agent_registry=agent_registry, config=config)
        self.classifier = classifier
        self.default_agent_name = default_agent_name

    def orchestrate(self, thread_id: str, user_message: str, stream_callback=None, **kwargs) -> str:
        """
        Orchestrate the message handling using intelligent agent selection.

        :param thread_id: The conversation thread ID
        :param user_message: The message from the user
        :param stream_callback: Optional callback for streaming responses
        :param kwargs: Additional context
        :return: The response from the chosen agent
        """
        # Get available agents
        available_agents = self.agent_registry.list_agents()
        if not available_agents:
            return "[No agents available to handle message.]"

        # Use classifier to select agent
        agent_name = kwargs.get("agent_name")  # Allow override
        if not agent_name:
            agent_name = self.classifier.classify(
                message=user_message,
                thread_id=thread_id,
                available_agents=available_agents
            )
            
        # Fallback to default if classification fails
        if not agent_name and self.default_agent_name:
            agent_name = self.default_agent_name

        # Get the agent
        agent = self.agent_registry.get_agent(agent_name) if agent_name else None
        if not agent:
            return "[No suitable agent found to handle message.]"

        # Add agent name prefix for the response
        agent_prefix = f"[{agent.agent_name}] "

        # Store user message in memory if possible
        if agent.tool_registry:
            try:
                agent.call_tool(
                    tool_name="MemoryTool",
                    method_name="store_message",
                    thread_id=thread_id,
                    sender="user",
                    content=user_message
                )
            except Exception as e:
                print(f"Error storing user message: {e}")

        # Handle message with streaming support
        if stream_callback:
            # Send agent prefix first
            stream_callback(agent_prefix)
            response = agent_prefix
            
            for chunk in agent.handle_message_stream(user_message, thread_id=thread_id, **kwargs):
                stream_callback(chunk)
                response += chunk
        else:
            agent_response = agent.handle_message(user_message, thread_id=thread_id, **kwargs)
            response = agent_prefix + agent_response

        # Store agent response in memory if possible
        if agent.tool_registry:
            try:
                agent.call_tool(
                    tool_name="MemoryTool",
                    method_name="store_message",
                    thread_id=thread_id,
                    sender=agent.agent_name,
                    content=response
                )
            except Exception as e:
                print(f"Error storing agent response: {e}")

        return response
