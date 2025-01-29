"""
RemoteAgent implementation for Moya.

This demonstrates how an agent could interact with a remote service
for generating responses (e.g., an external LLM API, or a custom
microservice).
"""

from typing import Any, Dict, Optional
from moya.agents.base_agent import Agent


class RemoteAgent(Agent):
    """
    A sample remote agent. In a real implementation, you might:
      - Store server URLs
      - Store authentication tokens
      - Use an HTTP or gRPC client library
    """

    def __init__(
        self,
        agent_name: str,
        description: str,
        remote_url: str,
        config: Optional[Dict[str, Any]] = None,
        tool_registry: Optional[Any] = None
    ):
        super().__init__(
            agent_name=agent_name,
            agent_type="RemoteAgent",      # Hard-coded agent type
            description=description,
            config=config,
            tool_registry=tool_registry
        )
        self.remote_url = remote_url

    def setup(self) -> None:
        """
        Initialize the remote agent.
        For example, authenticate to the remote service or verify connectivity.
        """
        # Example: self._session = requests.Session() or setting up gRPC stubs
        pass

    def handle_message(self, message: str, **kwargs) -> str:
        """
        Calls a remote service to handle the message.
        """
        # Example pseudo-code:
        # response = self._session.post(
        #     self.remote_url,
        #     json={"input": message, "params": kwargs}
        # )
        # return response.json().get("result", "")
        return f"[RemoteAgent placeholder response for message: {message}]"

    def handle_message_stream(self, message: str, **kwargs):
        """
        Calls a remote service to handle the message with streaming support.
        """
        # Example pseudo-code for streaming:
        # for chunk in self._session.post(
        #     self.remote_url,
        #     json={"input": message, "params": kwargs},
        #     stream=True
        # ).iter_content(chunk_size=1024):
        #     yield chunk.decode()
        yield f"[RemoteAgent placeholder response for message: {message}]"
