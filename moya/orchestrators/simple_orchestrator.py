"""
SimpleOrchestrator for Moya.

A reference implementation of a basic orchestrator that:
- Selects a single agent or a set of agents based on naive matching,
- Calls handle_message on the selected agent(s),
- Returns the response(s).
"""

from typing import Optional
from moya.orchestrators.base_orchestrator import BaseOrchestrator
from moya.registry.agent_registry import AgentRegistry


class SimpleOrchestrator(BaseOrchestrator):
    """
    A naive orchestrator that picks a single agent or a simple list of
    agents to handle each user message. The logic here can be as simple
    or as advanced as needed for demonstration.
    """

    def __init__(
        self,
        agent_registry: AgentRegistry,
        default_agent_name: Optional[str] = None,
        config: Optional[dict] = None
    ):
        """
        :param agent_registry: The AgentRegistry to retrieve agents from.
        :param default_agent_name: The default agent to fall back on if no specialized match is found.
        :param config: Optional dictionary for orchestrator configuration.
        """
        super().__init__(agent_registry=agent_registry, config=config)
        self.default_agent_name = default_agent_name

    def orchestrate(self, thread_id: str, user_message: str, stream_callback=None, **kwargs) -> str:
        """
        The main orchestration method. In this simple implementation, we:
          1. Attempt to find an agent by name if one is specified in kwargs,
             else use the default agent if available,
             else just pick the first agent in the registry (if any).
          2. Pass the user_message to the chosen agent's handle_message().
          3. Return the agent's response.
          4. (Optionally) store the conversation message in memory via a MemoryTool.

        :param thread_id: The conversation thread ID.
        :param user_message: The message from the user.
        :param stream_callback: Optional callback function for streaming responses.
        :param kwargs: Additional context (e.g., 'agent_name' to override which agent to call).
        :return: The response from the chosen agent.
        """
        # 1. Determine which agent to call
        agent_name = kwargs.get("agent_name")
        agent = None

        if agent_name:
            agent = self.agent_registry.get_agent(agent_name)
        elif self.default_agent_name:
            agent = self.agent_registry.get_agent(self.default_agent_name)
        else:
            # If no default is specified, just pick the first agent available
            agent_list = self.agent_registry.list_agents()
            if (agent_list):
                agent = self.agent_registry.get_agent(agent_list[0])

        if not agent:
            return "[No suitable agent found to handle message.]"

        # 2. We could store the incoming user message in memory via a MemoryTool (optional):
        #    If agent.tool_registry is available, we can call a MemoryTool method to store the user's message.
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

        # 3. Let the agent handle the message with streaming support
        if stream_callback:
            response = ""
            for chunk in agent.handle_message_stream(user_message, thread_id=thread_id, **kwargs):
                stream_callback(chunk)
                response += chunk
        else:
            response = agent.handle_message(user_message, thread_id=thread_id, **kwargs)

        # 4. Store the agent's response in memory (optional)
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

        # 5. Return the agent's response
        return response
